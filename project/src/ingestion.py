"""Programmatic market-data acquisition with explicit provider metadata."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pandas as pd

from .utils import clean_columns
from .validation import validate_market_data


def _normalize_market_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize provider output to the project's canonical market schema."""

    result = frame.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [str(column[0]) for column in result.columns]
    result = result.reset_index() if "date" not in result.columns else result.reset_index(drop=True)
    result = clean_columns(result)
    result = result.rename(
        columns={
            "adj_close": "adjusted_close",
            "datetime": "date",
            "index": "date",
        }
    )
    if "adjusted_close" not in result and "close" in result:
        result["adjusted_close"] = result["close"]
    if "dividends" not in result:
        result["dividends"] = 0.0
    if "stock_splits" not in result:
        result["stock_splits"] = 0.0
    keep = [
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
    result = result[[column for column in keep if column in result.columns]]
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.tz_localize(None)
    for column in result.columns.difference(["date"]):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.sort_values("date").drop_duplicates("date").reset_index(drop=True)


def fetch_yfinance(symbol: str, start: str, end: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Download daily OHLCV data through yfinance."""

    import yfinance as yf

    inclusive_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    frame = yf.download(
        symbol,
        start=start,
        end=inclusive_end,
        auto_adjust=False,
        actions=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol}")
    normalized = _normalize_market_frame(frame)
    metadata = {
        "provider": "yfinance",
        "symbol": symbol,
        "start": start,
        "end": end,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "rows": int(len(normalized)),
        "limitations": [
            "Yahoo Finance is a third-party source and may change schema or availability.",
            "Adjusted prices can be revised after corporate-action updates.",
        ],
    }
    return normalized, metadata


def fetch_alpha_vantage(
    symbol: str, start: str, end: str, api_key: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Download split/dividend-adjusted daily data through Alpha Vantage."""

    import requests

    endpoint = "https://www.alphavantage.co/query"
    response = requests.get(
        endpoint,
        params={
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": api_key,
        },
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    series = payload.get("Time Series (Daily)")
    if not series:
        message = payload.get("Note") or payload.get("Information") or payload.get("Error Message")
        raise RuntimeError(
            f"Alpha Vantage returned no daily series: {message or 'unknown response'}"
        )

    frame = pd.DataFrame.from_dict(series, orient="index").rename_axis("date").reset_index()
    frame = frame.rename(
        columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. adjusted close": "adjusted_close",
            "6. volume": "volume",
            "7. dividend amount": "dividends",
            "8. split coefficient": "stock_splits",
        }
    )
    frame = _normalize_market_frame(frame)
    mask = frame["date"].between(pd.Timestamp(start), pd.Timestamp(end))
    normalized = frame.loc[mask].reset_index(drop=True)
    metadata = {
        "provider": "alpha_vantage",
        "endpoint": endpoint,
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "start": start,
        "end": end,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "rows": int(len(normalized)),
        "limitations": [
            "Adjusted daily access and rate limits depend on the Alpha Vantage subscription tier.",
            "If unavailable in auto mode, the documented yfinance adapter is used as fallback.",
        ],
    }
    return normalized, metadata


def acquire_market_data(
    symbol: str,
    start: str,
    end: str | None = None,
    *,
    provider: str = "auto",
    alpha_vantage_key: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Acquire, normalize, and validate data using the selected provider."""

    end = end or date.today().isoformat()
    provider = provider.lower()
    attempts: list[str] = []

    if provider in {"auto", "alpha_vantage"} and alpha_vantage_key:
        try:
            frame, metadata = fetch_alpha_vantage(symbol, start, end, alpha_vantage_key)
            validate_market_data(frame)
            metadata["validation"] = "passed"
            return frame, metadata
        except Exception as exc:
            attempts.append(f"alpha_vantage: {exc}")
            if provider == "alpha_vantage":
                raise

    if provider in {"auto", "yfinance"}:
        try:
            frame, metadata = fetch_yfinance(symbol, start, end)
            validate_market_data(frame)
            metadata["validation"] = "passed"
            if attempts:
                metadata["fallback_reason"] = attempts
            return frame, metadata
        except Exception as exc:  # noqa: BLE001 - record provider failure before fallback.
            attempts.append(f"yfinance: {exc}")

    raise RuntimeError("All configured acquisition attempts failed: " + " | ".join(attempts))
