"""Reusable tabular-data utilities for Homework 03."""

from __future__ import annotations

import re

import pandas as pd


def get_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics with one row per numeric column."""

    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] == 0:
        return pd.DataFrame(
            columns=["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        )
    return numeric.describe().T


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with lowercase snake-case column names."""

    result = df.copy()
    result.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in result.columns
    ]
    return result
