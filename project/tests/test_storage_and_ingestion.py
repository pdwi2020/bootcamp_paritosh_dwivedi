import pytest

from src.ingestion import fetch_alpha_vantage
from src.storage import build_manifest, validate_manifest


def test_manifest_validation_detects_modified_raw_file(tmp_path):
    raw = tmp_path / "spy_daily_test.csv"
    raw.write_text("date,close\n2026-08-17,100\n", encoding="utf-8")
    manifest = build_manifest(raw, {"provider": "test"})
    assert validate_manifest(raw, manifest)["valid"] is True
    raw.write_text("date,close\n2026-08-17,101\n", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest validation failed"):
        validate_manifest(raw, manifest)


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
    frame, metadata = fetch_alpha_vantage(
        "SPY", "2026-08-17", "2026-08-17", "example-key"
    )
    assert captured["params"]["function"] == "TIME_SERIES_DAILY_ADJUSTED"
    assert frame.loc[0, "adjusted_close"] == 97.5
    assert frame.loc[0, "volume"] == 123456
    assert metadata["function"] == "TIME_SERIES_DAILY_ADJUSTED"
