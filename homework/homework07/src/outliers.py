"""Reusable outlier detection and treatment for one-dimensional numeric data.

These are the starter's sample implementations with four changes:

1. Missing values are excluded from every statistic and are never reported as
   outliers. The starter's z-score returned ``False`` for NaN by accident rather
   than by intent; here it is explicit.
2. The z-score detector can use a robust centre and scale. The classic version
   divides by a standard deviation that the outliers themselves inflate, so a
   single extreme value can mask every other one. That is the masking problem,
   and on fat-tailed financial returns it matters.
3. Degenerate input is handled. A constant series has zero spread, so nothing is
   an outlier rather than everything.
4. Returned masks keep the input index and name, so they align when assigned
   back to a frame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAD_TO_SIGMA = 0.6745


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Flag values outside the inter-quartile fence, Q1 - k*IQR to Q3 + k*IQR.

    Quartiles ignore the magnitude of extreme values, so the fence does not move
    much when a few points are very large. That makes this the safer default on
    skewed data. ``k=1.5`` is Tukey's convention; raise it to flag fewer points.
    """

    values = pd.to_numeric(series, errors="coerce")
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(False, index=series.index, name=series.name)
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return ((values < lower) | (values > upper)).fillna(False)


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0,
    *,
    robust: bool = False,
) -> pd.Series:
    """Flag values more than ``threshold`` standard deviations from the centre.

    With ``robust=False`` the centre and scale are the mean and standard
    deviation, which assumes roughly normal data and is pulled by the very
    points being tested. With ``robust=True`` they become the median and the
    median absolute deviation, rescaled to be comparable to a standard
    deviation, which resists that masking effect.
    """

    values = pd.to_numeric(series, errors="coerce")
    if robust:
        centre = values.median()
        mad = (values - centre).abs().median()
        scale = mad / MAD_TO_SIGMA if mad and not pd.isna(mad) else np.nan
    else:
        centre = values.mean()
        scale = values.std(ddof=0)
    if pd.isna(scale) or scale == 0:
        return pd.Series(False, index=series.index, name=series.name)
    return (((values - centre) / scale).abs() > threshold).fillna(False)


def winsorize_series(
    series: pd.Series,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Clip values to the given quantiles instead of dropping the rows.

    Winsorizing keeps every observation and every row alignment, trading the
    magnitude of extreme values for their influence. Prefer it to deletion when
    the row carries information in its other columns, or when dropping would
    break a time series by leaving gaps.
    """

    if not 0 <= lower < upper <= 1:
        raise ValueError("Require 0 <= lower < upper <= 1")
    values = pd.to_numeric(series, errors="coerce")
    low, high = values.quantile(lower), values.quantile(upper)
    if pd.isna(low) or pd.isna(high):
        return values
    return values.clip(lower=low, upper=high)
