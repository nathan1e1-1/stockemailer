from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date

import requests

from alphastream.types import FilingPosition


def _normalize_company_name(value: str) -> str:
    lowered = value.upper().replace("&", " AND ")
    lowered = re.sub(r"[^A-Z0-9]+", " ", lowered)
    lowered = re.sub(r"\b(CL A|CL B|CLASS A|CLASS B|COM|ORD|NEW)\b", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


@dataclass
class SECTickerDirectory:
    session: requests.Session | object
    user_agent: str
    timeout_seconds: int = 20
    url: str = "https://www.sec.gov/files/company_tickers_exchange.json"
    _cache: dict[str, str] | None = field(default=None, init=False)

    def resolve(self, issuer_name: str) -> str | None:
        if self._cache is None:
            self._cache = self._load_mapping()
        return self._cache.get(_normalize_company_name(issuer_name))

    def _load_mapping(self) -> dict[str, str]:
        response = self.session.get(self.url, headers={"User-Agent": self.user_agent}, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        mapping: dict[str, str] = {}
        if isinstance(payload, dict) and "fields" in payload and "data" in payload:
            for row in payload["data"]:
                record = dict(zip(payload["fields"], row))
                name = str(record.get("name") or "")
                ticker = str(record.get("ticker") or "").upper()
                if name and ticker:
                    mapping[_normalize_company_name(name)] = ticker
        elif isinstance(payload, list):
            for record in payload:
                if not isinstance(record, dict):
                    continue
                name = str(record.get("name") or "")
                ticker = str(record.get("ticker") or "").upper()
                if name and ticker:
                    mapping[_normalize_company_name(name)] = ticker
        return mapping


@dataclass
class SECFilingProvider:
    user_agent: str
    session: requests.Session | object | None = None
    timeout_seconds: int = 20
    submissions_base_url: str = "https://data.sec.gov/submissions"
    archives_base_url: str = "https://www.sec.gov/Archives/edgar/data"
    ticker_directory: SECTickerDirectory | None = None
    last_errors: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()
        self.ticker_directory = self.ticker_directory or SECTickerDirectory(
            session=self.session,
            user_agent=self.user_agent,
            timeout_seconds=self.timeout_seconds,
        )

    def fetch_positions(self, since: str | None, investor_ids: list[str]) -> list[FilingPosition]:
        self.last_errors = []
        since_date = date.fromisoformat(since) if since else None
        positions: list[FilingPosition] = []
        for investor_id in investor_ids:
            try:
                positions.extend(self._fetch_investor_positions(investor_id, since_date))
            except Exception as error:
                self.last_errors.append(f"{investor_id}: {error}")
        return positions

    def _fetch_investor_positions(self, investor_id: str, since_date: date | None) -> list[FilingPosition]:
        submissions = self._get_json(f"{self.submissions_base_url}/CIK{int(investor_id):010d}.json")
        investor_name = str(submissions.get("name") or investor_id)
        recent = submissions.get("filings", {}).get("recent", {})
        filings = self._extract_recent_13f_filings(recent)
        if not filings:
            return []
        current_filing = filings[0]
        current_date = date.fromisoformat(current_filing["filingDate"])
        if since_date and current_date < since_date:
            return []
        previous_filing = filings[1] if len(filings) > 1 else None
        current_holdings = self._load_filing_holdings(investor_id, investor_name, current_filing["accessionNumber"])
        previous_holdings = (
            self._load_filing_holdings(investor_id, investor_name, previous_filing["accessionNumber"])
            if previous_filing
            else {}
        )
        positions: list[FilingPosition] = []
        for ticker, current_holding in current_holdings.items():
            previous_shares = float(previous_holdings.get(ticker, {}).get("shares", 0.0))
            current_shares = float(current_holding["shares"])
            stake_increase_pct = (
                round(((current_shares - previous_shares) / previous_shares) * 100.0, 2)
                if previous_shares > 0
                else 100.0
            )
            positions.append(
                FilingPosition(
                    ticker=ticker,
                    company_name=str(current_holding["company_name"]),
                    investor_id=str(int(investor_id)),
                    investor_name=investor_name,
                    is_new_position=previous_shares == 0,
                    stake_increase_pct=stake_increase_pct,
                    reported_value=float(current_holding["reported_value"]),
                    sector="Unknown",
                )
            )
        return positions

    def _extract_recent_13f_filings(self, recent: dict[str, list[str]]) -> list[dict[str, str]]:
        entries = []
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        for form, accession, filing_date in zip(forms, accessions, filing_dates):
            if str(form).startswith("13F-HR"):
                entries.append(
                    {
                        "form": str(form),
                        "accessionNumber": str(accession),
                        "filingDate": str(filing_date),
                    }
                )
        return entries

    def _load_filing_holdings(
        self,
        investor_id: str,
        investor_name: str,
        accession_number: str,
    ) -> dict[str, dict[str, object]]:
        accession_compact = accession_number.replace("-", "")
        filing_index = self._get_json(
            f"{self.archives_base_url}/{int(investor_id)}/{accession_compact}/index.json"
        )
        items = filing_index.get("directory", {}).get("item", [])
        info_table_name = self._find_info_table_name(items)
        xml_text = self._get_text(
            f"{self.archives_base_url}/{int(investor_id)}/{accession_compact}/{info_table_name}"
        )
        return self._parse_information_table(xml_text, investor_name)

    def _find_info_table_name(self, items: list[dict[str, object]]) -> str:
        xml_names = [str(item.get("name") or "") for item in items if str(item.get("name") or "").lower().endswith(".xml")]
        prioritized = [
            name
            for name in xml_names
            if any(marker in name.lower() for marker in ("info", "13f", "table"))
        ]
        if prioritized:
            return prioritized[0]
        if xml_names:
            return xml_names[0]
        raise RuntimeError("No XML information table found in SEC filing index")

    def _parse_information_table(self, xml_text: str, investor_name: str) -> dict[str, dict[str, object]]:
        root = ET.fromstring(xml_text)
        holdings: dict[str, dict[str, object]] = {}
        for info_table in [element for element in root.iter() if self._local_name(element.tag) == "infoTable"]:
            issuer_name = self._child_text(info_table, "nameOfIssuer")
            if not issuer_name:
                continue
            if self._child_text(info_table, "putCall"):
                continue
            ticker = self.ticker_directory.resolve(issuer_name) if self.ticker_directory else None
            if not ticker:
                continue
            value = float(self._child_text(info_table, "value") or 0.0)
            shares = float(self._child_text(info_table, "sshPrnamt") or 0.0)
            if ticker in holdings:
                holdings[ticker]["shares"] = float(holdings[ticker]["shares"]) + shares
                holdings[ticker]["reported_value"] = float(holdings[ticker]["reported_value"]) + value
            else:
                holdings[ticker] = {
                    "company_name": issuer_name,
                    "shares": shares,
                    "reported_value": value,
                    "investor_name": investor_name,
                }
        return holdings

    def _child_text(self, parent: ET.Element, desired_name: str) -> str:
        for element in parent.iter():
            if self._local_name(element.tag) == desired_name:
                return (element.text or "").strip()
        return ""

    def _local_name(self, tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def _get_json(self, url: str):
        assert self.session is not None
        response = self.session.get(url, headers={"User-Agent": self.user_agent}, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _get_text(self, url: str) -> str:
        assert self.session is not None
        response = self.session.get(url, headers={"User-Agent": self.user_agent}, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text
