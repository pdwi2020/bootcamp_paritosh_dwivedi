"""Copy-safe cleaning functions for daily market data."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .validation import REQUIRED_MARKET_COLUMNS, validate_market_data


def clean_market_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Correct types, remove invalid rows, deduplicate, and report changes."""

    result = frame.copy()
    before_rows = len(result)
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.tz_localize(None)
    numeric_columns = ["open", "high", "low", "close", "adjusted_close", "volume"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result = result.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    result["adjusted_close"] = result["adjusted_close"].fillna(result["close"])
    valid_prices = (result[["open", "high", "low", "close", "adjusted_close"]] > 0).all(axis=1)
    valid_volume = result["volume"] >= 0
    internally_consistent = (
        (result["high"] >= result[["open", "close", "low"]].max(axis=1))
        & (result["low"] <= result[["open", "close", "high"]].min(axis=1))
    )
    result = result.loc[valid_prices & valid_volume & internally_consistent]
    result = result.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    validate_market_data(result)

    report = {
        "rows_before": int(before_rows),
        "rows_after": int(len(result)),
        "rows_removed": int(before_rows - len(result)),
        "date_start": result["date"].min().date().isoformat(),
        "date_end": result["date"].max().date().isoformat(),
        "missing_after": int(result[list(REQUIRED_MARKET_COLUMNS)].isna().sum().sum()),
        "duplicate_dates_after": int(result["date"].duplicated().sum()),
        "policy": [
            "Unparseable or incomplete required rows are removed.",
            "Non-positive prices, negative volume, and internally inconsistent OHLC rows are removed.",
            "Duplicate dates retain the final provider record.",
            "Missing adjusted close falls back to close.",
        ],
    }
    return result, report
