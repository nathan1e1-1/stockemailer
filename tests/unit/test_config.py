from __future__ import annotations

import sys
from pathlib import Path

import pytest

import alphastream.config as config_module
from alphastream.cli import main
from alphastream.config import ConfigError, load_config


CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def test_load_config_defaults_blank_smtp_port_to_587(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("ALPHASTREAM_FILING_PROVIDER", "sec")
    monkeypatch.setenv("ALPHASTREAM_FINNHUB_API_KEY", "news-key")
    monkeypatch.setenv("ALPHASTREAM_EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("ALPHASTREAM_EMAIL_FROM", "bot@example.com")
    monkeypatch.setenv("ALPHASTREAM_EMAIL_TO", "user@example.com")
    monkeypatch.setenv("ALPHASTREAM_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("ALPHASTREAM_SMTP_PORT", "")
    monkeypatch.setenv("ALPHASTREAM_SMTP_USERNAME", "bot@example.com")
    monkeypatch.setenv("ALPHASTREAM_SMTP_PASSWORD", "secret")

    config = load_config(CONFIG_DIR)

    assert config.smtp_port == 587


def test_load_config_raises_clear_error_for_missing_required_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("ALPHASTREAM_EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("ALPHASTREAM_FILING_PROVIDER", "sec")
    for name in [
        "ALPHASTREAM_EMAIL_FROM",
        "ALPHASTREAM_EMAIL_TO",
        "ALPHASTREAM_SMTP_HOST",
        "ALPHASTREAM_SMTP_PORT",
        "ALPHASTREAM_SMTP_USERNAME",
        "ALPHASTREAM_SMTP_PASSWORD",
        "ALPHASTREAM_FINNHUB_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ConfigError) as error_info:
        load_config(CONFIG_DIR)

    message = str(error_info.value)
    assert "Missing required configuration" in message
    assert "ALPHASTREAM_EMAIL_FROM" in message
    assert "ALPHASTREAM_FINNHUB_API_KEY" in message
    assert "ALPHASTREAM_SMTP_HOST" in message


def test_cli_returns_1_with_readable_config_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    monkeypatch.setattr(sys, "argv", ["alphastream", "--config-dir", str(CONFIG_DIR)])
    monkeypatch.setenv("ALPHASTREAM_EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("ALPHASTREAM_FILING_PROVIDER", "sec")
    for name in [
        "ALPHASTREAM_EMAIL_FROM",
        "ALPHASTREAM_EMAIL_TO",
        "ALPHASTREAM_SMTP_HOST",
        "ALPHASTREAM_SMTP_PORT",
        "ALPHASTREAM_SMTP_USERNAME",
        "ALPHASTREAM_SMTP_PASSWORD",
        "ALPHASTREAM_FINNHUB_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Missing required configuration" in captured.err
