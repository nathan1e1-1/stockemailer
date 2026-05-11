from __future__ import annotations

from collections import defaultdict

from alphastream.providers.sec_filings import SECFilingProvider


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    @property
    def text(self) -> str:
        return str(self._payload)


class FakeSession:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls = defaultdict(int)

    def get(self, url: str, headers=None, timeout=None):
        self.calls[url] += 1
        payload = self.responses[url]
        return FakeResponse(payload)


def test_sec_provider_parses_recent_and_previous_filings_and_tolerates_bad_manager() -> None:
    submissions_good = {
        "name": "Pershing Square Capital Management, L.P.",
        "filings": {
            "recent": {
                "form": ["13F-HR", "13F-HR"],
                "accessionNumber": ["0001172661-26-001091", "0001172661-25-005039"],
                "filingDate": ["2026-02-17", "2025-11-14"],
            }
        },
    }
    submissions_bad = {
        "name": "Broken Manager",
        "filings": {
            "recent": {
                "form": ["13F-HR"],
                "accessionNumber": ["0000000000-26-000001"],
                "filingDate": ["2026-02-17"],
            }
        },
    }
    current_index = {"directory": {"item": [{"name": "infotable.xml"}]}}
    previous_index = {"directory": {"item": [{"name": "infotable.xml"}]}}
    ticker_directory = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [320193, "Apple Inc.", "AAPL", "Nasdaq"],
            [1045810, "NVIDIA CORP", "NVDA", "Nasdaq"],
        ],
    }
    current_xml = """
    <informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
      <infoTable>
        <nameOfIssuer>Apple Inc.</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>037833100</cusip>
        <value>30201000</value>
        <shrsOrPrnAmt>
          <sshPrnamt>232441</sshPrnamt>
          <sshPrnamtType>SH</sshPrnamtType>
        </shrsOrPrnAmt>
      </infoTable>
      <infoTable>
        <nameOfIssuer>NVIDIA CORP</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>67066G104</cusip>
        <value>26126000</value>
        <shrsOrPrnAmt>
          <sshPrnamt>108934</sshPrnamt>
          <sshPrnamtType>SH</sshPrnamtType>
        </shrsOrPrnAmt>
      </infoTable>
    </informationTable>
    """.strip()
    previous_xml = """
    <informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
      <infoTable>
        <nameOfIssuer>Apple Inc.</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>037833100</cusip>
        <value>28000000</value>
        <shrsOrPrnAmt>
          <sshPrnamt>200000</sshPrnamt>
          <sshPrnamtType>SH</sshPrnamtType>
        </shrsOrPrnAmt>
      </infoTable>
    </informationTable>
    """.strip()

    session = FakeSession(
        {
            "https://www.sec.gov/files/company_tickers_exchange.json": ticker_directory,
            "https://data.sec.gov/submissions/CIK0001336528.json": submissions_good,
            "https://data.sec.gov/submissions/CIK0000000001.json": submissions_bad,
            "https://www.sec.gov/Archives/edgar/data/1336528/000117266126001091/index.json": current_index,
            "https://www.sec.gov/Archives/edgar/data/1336528/000117266125005039/index.json": previous_index,
            "https://www.sec.gov/Archives/edgar/data/1336528/000117266126001091/infotable.xml": current_xml,
            "https://www.sec.gov/Archives/edgar/data/1336528/000117266125005039/infotable.xml": previous_xml,
            "https://www.sec.gov/Archives/edgar/data/1/000000000026000001/index.json": RuntimeError("bad manager filing"),
        }
    )

    provider = SECFilingProvider(
        session=session,
        user_agent="AlphaStream test@example.com",
    )

    positions = provider.fetch_positions(since="2026-01-01", investor_ids=["1336528", "0000000001"])

    assert [position.ticker for position in positions] == ["AAPL", "NVDA"]
    assert positions[0].is_new_position is False
    assert positions[0].stake_increase_pct == 16.22
    assert positions[1].is_new_position is True
    assert positions[1].stake_increase_pct == 100.0
    assert provider.last_errors == ["0000000001: bad manager filing"]
