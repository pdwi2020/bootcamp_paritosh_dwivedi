from datetime import date

import pandas as pd
import pytest

from src.ingestion import acquire_market_data, fetch_alpha_vantage, fetch_yfinance
from src.storage import build_manifest, validate_manifest, write_immutable_csv


def test_manifest_validation_detects_modified_raw_file(tmp_path):
    raw = tmp_path / "spy_daily_test.csv"
    raw.write_text("date,close\n2026-08-17,100\n", encoding="utf-8")
    manifest = build_manifest(raw, {"provider": "test"})
    assert validate_manifest(raw, manifest)["valid"] is True
    raw.write_text("date,close\n2026-08-17,101\n", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest validation failed"):
        validate_manifest(raw, manifest)


def test_immutable_csv_refuses_to_overwrite_snapshot(tmp_path):
    raw = tmp_path / "spy_daily_test.csv"
    first = pd.DataFrame({"date": ["2026-08-17"], "close": [100]})
    second = pd.DataFrame({"date": ["2026-08-17"], "close": [101]})
    write_immutable_csv(first, raw)
    with pytest.raises(FileExistsError):
        write_immutable_csv(second, raw)
    assert pd.read_csv(raw).loc[0, "close"] == 100


def test_acquisition_uses_current_date_when_end_is_unspecified(monkeypatch):
    captured = {}
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime([date.today()]),
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "adjusted_close": [100.0],
            "volume": [1_000_000],
        }
    )

    def fake_fetch(symbol, start, end):
        captured.update({"symbol": symbol, "start": start, "end": end})
        return frame, {"provider": "test"}

    monkeypatch.setattr("src.ingestion.fetch_yfinance", fake_fetch)
    acquire_market_data("SPY", "2026-01-01", provider="yfinance")
    assert captured["end"] == date.today().isoformat()


def test_yfinance_adapter_requests_inclusive_end_and_normalizes_schema(monkeypatch):
    captured = {}
    provider_frame = pd.DataFrame(
        [[99.0, 102.0, 98.0, 100.0, 97.5, 123_456, 0.25, 1.0]],
        index=pd.DatetimeIndex(["2026-08-17"], name="Date"),
        columns=pd.MultiIndex.from_tuples(
            [
                ("Open", "SPY"),
                ("High", "SPY"),
                ("Low", "SPY"),
                ("Close", "SPY"),
                ("Adj Close", "SPY"),
                ("Volume", "SPY"),
                ("Dividends", "SPY"),
                ("Stock Splits", "SPY"),
            ]
        ),
    )

    def fake_download(symbol, **kwargs):
        captured.update({"symbol": symbol, **kwargs})
        return provider_frame

    monkeypatch.setattr("yfinance.download", fake_download)
    frame, metadata = fetch_yfinance("SPY", "2026-08-17", "2026-08-17")

    assert captured == {
        "symbol": "SPY",
        "start": "2026-08-17",
        "end": "2026-08-18",
        "auto_adjust": False,
        "actions": True,
        "progress": False,
        "threads": False,
    }
    assert frame.columns.tolist() == [
        "date",
        "open",
        "high",
        "low",
        "close",
        "adjusted_close",
        "volume",
        "dividends",
        "stock_splits",
    ]
    assert frame.loc[0, "adjusted_close"] == 97.5
    assert metadata["provider"] == "yfinance"
    assert metadata["end"] == "2026-08-17"


def test_alpha_vantage_uses_adjusted_daily_schema(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "Time Series (Daily)": {
                    "2026-08-17": {
                        "1. open": "99",
                        "2. high": "102",
                        "3. low": "98",
                        "4. close": "100",
                        "5. adjusted close": "97.5",
                        "6. volume": "123456",
                        "7. dividend amount": "0.25",
                        "8. split coefficient": "1.0",
                    }
                }
            }

    def fake_get(endpoint, *, params, timeout):
        captured.update({"endpoint": endpoint, "params": params, "timeout": timeout})
        return Response()

    monkeypatch.setattr("requests.get", fake_get)
    frame, metadata = fetch_alpha_vantage("SPY", "2026-08-17", "2026-08-17", "example-key")
    assert captured["params"]["function"] == "TIME_SERIES_DAILY_ADJUSTED"
    assert frame.loc[0, "adjusted_close"] == 97.5
    assert frame.loc[0, "volume"] == 123456
    assert metadata["function"] == "TIME_SERIES_DAILY_ADJUSTED"
