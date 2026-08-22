"""Reusable profiling helper for exploratory data analysis.

Extracted from the stage 08 lecture and extended with the stretch goal: name the
columns that need attention before feature engineering.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
from scipy.stats import kurtosis, skew

HIGH_MISSING_FRACTION = 0.05
NEAR_ZERO_VARIANCE = 1e-12
DOMINANT_CATEGORY_FRACTION = 0.95


def eda_summary(
    df: pd.DataFrame, numeric_cols: Sequence[str] | None = None
) -> dict[str, Any]:
    """Profile a dataframe without modifying it.

    Returns shape, dtypes, per-column missing counts, and a numeric profile that
    extends ``describe`` with skew and excess kurtosis. ``attention`` lists the
    columns worth resolving before stage 09: high missingness, near-zero
    variance, or a single category covering almost every row.
    """

    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
    else:
        unknown = [c for c in numeric_cols if c not in df.columns]
        if unknown:
            raise KeyError(f"Unknown columns: {unknown}")
        numeric_cols = list(numeric_cols)

    profile = df[numeric_cols].describe().T if numeric_cols else pd.DataFrame()
    if not profile.empty:
        series = [df[c].dropna() for c in profile.index]
        profile["skew"] = [_moment(skew, s, 3) for s in series]
        profile["kurtosis"] = [_moment(kurtosis, s, 4) for s in series]

    return {
        "shape": df.shape,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": df.isna().sum().to_dict(),
        "numeric_profile": profile,
        "attention": columns_needing_attention(df),
    }


def _moment(function, series: pd.Series, minimum: int) -> float:
    """Return a shape statistic, or NaN where it is undefined.

    A constant column has no meaningful skew or kurtosis, and scipy warns about
    catastrophic cancellation instead of returning NaN, so screen those out.
    """

    if len(series) < minimum:
        return float("nan")
    variance = series.var()
    if pd.isna(variance) or variance < NEAR_ZERO_VARIANCE:
        return float("nan")
    return float(function(series))


def columns_needing_attention(df: pd.DataFrame) -> dict[str, list[str]]:
    """Name columns to resolve before feature engineering, one entry per reason."""

    rows = len(df)
    high_missing: list[str] = []
    near_zero_variance: list[str] = []
    dominant_category: list[str] = []

    for column in df.columns:
        series = df[column]
        if rows and series.isna().mean() > HIGH_MISSING_FRACTION:
            high_missing.append(column)
        if pd.api.types.is_numeric_dtype(series):
            variance = series.var(skipna=True)
            if pd.notna(variance) and variance < NEAR_ZERO_VARIANCE:
                near_zero_variance.append(column)
        else:
            counts = series.value_counts(dropna=True)
            if (
                len(counts)
                and counts.iloc[0] / max(counts.sum(), 1) > DOMINANT_CATEGORY_FRACTION
            ):
                dominant_category.append(column)

    return {
        "high_missing": high_missing,
        "near_zero_variance": near_zero_variance,
        "dominant_category": dominant_category,
    }
