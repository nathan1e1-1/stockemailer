from pathlib import Path

from alphastream.providers.fixture_filings import LocalFixtureFilingProvider


def test_local_fixture_provider_loads_positions_for_configured_investors(tmp_path: Path) -> None:
    fixture_path = tmp_path / "filings.json"
    fixture_path.write_text(
        """
        [
          {
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "investor_id": "1067983",
            "investor_name": "Berkshire Hathaway",
            "is_new_position": true,
            "stake_increase_pct": 12.5,
            "reported_value": 1000000,
            "sector": "Technology"
          },
          {
            "ticker": "XOM",
            "company_name": "Exxon Mobil",
            "investor_id": "0000000",
            "investor_name": "Other Fund",
            "is_new_position": true,
            "stake_increase_pct": 10.0,
            "reported_value": 500000,
            "sector": "Energy"
          }
        ]
        """.strip()
    )

    provider = LocalFixtureFilingProvider(fixture_path)

    positions = provider.fetch_positions(since="2026-01-01", investor_ids=["1067983"])

    assert len(positions) == 1
    assert positions[0].ticker == "NVDA"
    assert positions[0].investor_name == "Berkshire Hathaway"
