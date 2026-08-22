"""Profiling helpers for exploratory data analysis."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
from scipy.stats import kurtosis, skew

HIGH_MISSING_FRACTION = 0.05
NEAR_ZERO_VARIANCE = 1e-12
DOMINANT_CATEGORY_FRACTION = 0.95


def eda_summary(
    frame: pd.DataFrame,
    numeric_columns: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Profile a frame without modifying it.

    Returns the shape, dtypes, per-column missing counts, and a numeric profile
    that extends ``describe`` with skew and excess kurtosis. ``attention`` lists
    columns worth resolving before feature engineering: high missingness, a
    variance close to zero, or a single category covering almost every row.
    """

    if numeric_columns is None:
        numeric_columns = frame.select_dtypes(include="number").columns.tolist()
    else:
        unknown = [column for column in numeric_columns if column not in frame.columns]
        if unknown:
            raise KeyError(f"Unknown columns: {unknown}")
        numeric_columns = list(numeric_columns)

    profile = frame[numeric_columns].describe().T if numeric_columns else pd.DataFrame()
    if not profile.empty:
        values = [frame[column].dropna() for column in profile.index]
        profile["skew"] = [_moment(skew, series, minimum=3) for series in values]
        profile["kurtosis"] = [_moment(kurtosis, series, minimum=4) for series in values]

    return {
        "shape": frame.shape,
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing": frame.isna().sum().to_dict(),
        "numeric_profile": profile,
        "attention": flag_columns_needing_attention(frame),
    }


def _moment(function, series: pd.Series, minimum: int) -> float:
    """Return a shape statistic, or NaN where it is not defined.

    A constant column has no meaningful skew or kurtosis, and scipy warns about
    catastrophic cancellation rather than returning NaN, so screen those out here.
    """

    if len(series) < minimum:
        return float("nan")
    variance = series.var()
    if pd.isna(variance) or variance < NEAR_ZERO_VARIANCE:
        return float("nan")
    return float(function(series))


def flag_columns_needing_attention(frame: pd.DataFrame) -> dict[str, list[str]]:
    """Name the columns that should be resolved before feature engineering.

    A column is reported once per reason, so a constant column that is also
    mostly missing appears under both keys.
    """

    row_count = len(frame)
    high_missing: list[str] = []
    near_zero_variance: list[str] = []
    dominant_category: list[str] = []

    for column in frame.columns:
        series = frame[column]
        if row_count and series.isna().mean() > HIGH_MISSING_FRACTION:
            high_missing.append(column)
        if pd.api.types.is_numeric_dtype(series):
            variance = series.var(skipna=True)
            if pd.notna(variance) and variance < NEAR_ZERO_VARIANCE:
                near_zero_variance.append(column)
        else:
            counts = series.value_counts(dropna=True)
            if len(counts) and counts.iloc[0] / max(counts.sum(), 1) > DOMINANT_CATEGORY_FRACTION:
                dominant_category.append(column)

    return {
        "high_missing": high_missing,
        "near_zero_variance": near_zero_variance,
        "dominant_category": dominant_category,
    }
