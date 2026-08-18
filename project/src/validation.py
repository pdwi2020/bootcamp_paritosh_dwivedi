"""High-value validation checks for market data."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_MARKET_COLUMNS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
}


def validate_market_data(frame: pd.DataFrame, *, raise_on_error: bool = True) -> dict[str, Any]:
    """Validate schema, types, ordering, duplicates, and financial ranges."""

    errors: list[str] = []
    warnings: list[str] = []
    if frame.empty:
        errors.append("Market data contains no rows")
    missing_columns = sorted(REQUIRED_MARKET_COLUMNS.difference(frame.columns))
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")

    if not missing_columns:
        parsed_dates = pd.to_datetime(frame["date"], errors="coerce")
        if parsed_dates.isna().any():
            errors.append("One or more dates could not be parsed")
        if parsed_dates.duplicated().any():
            errors.append("Duplicate dates detected")
        if not parsed_dates.is_monotonic_increasing:
            errors.append("Dates are not in ascending order")

        numeric_columns = ["open", "high", "low", "close", "adjusted_close", "volume"]
        numeric = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any():
            errors.append("One or more market fields could not be parsed as numeric")
        if (numeric[["open", "high", "low", "close", "adjusted_close"]] <= 0).any().any():
            errors.append("Non-positive price detected")
        if (numeric["volume"] < 0).any():
            errors.append("Negative volume detected")
        if (numeric["high"] < numeric[["open", "close", "low"]].max(axis=1)).any():
            errors.append("High price is below another daily price field")
        if (numeric["low"] > numeric[["open", "close", "high"]].min(axis=1)).any():
            errors.append("Low price is above another daily price field")

        missing_total = int(frame[list(REQUIRED_MARKET_COLUMNS)].isna().sum().sum())
        if missing_total:
            warnings.append(f"Required fields contain {missing_total} missing values")

    report: dict[str, Any] = {
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "missing_required_columns": missing_columns,
        "duplicate_dates": int(frame["date"].duplicated().sum()) if "date" in frame else None,
        "missing_values": int(frame.isna().sum().sum()),
        "errors": errors,
        "warnings": warnings,
        "valid": not errors,
    }
    if errors and raise_on_error:
        raise ValueError("Market-data validation failed: " + "; ".join(errors))
    return report
