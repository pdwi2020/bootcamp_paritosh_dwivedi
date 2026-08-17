"""Outlier diagnostics that preserve plausible market tail events."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_return_outlier_flag(
    frame: pd.DataFrame, *, price_column: str = "adjusted_close", threshold: float = 6.0
) -> pd.DataFrame:
    """Flag extreme log returns using a robust median absolute-deviation score.

    Observations are retained because extreme market moves are relevant to the
    risk-monitoring decision. The flag is available as a model feature and for
    sensitivity analysis.
    """

    result = frame.copy()
    log_return = np.log(result[price_column]).diff()
    median = log_return.median()
    mad = (log_return - median).abs().median()
    if mad == 0 or pd.isna(mad):
        robust_z = pd.Series(0.0, index=result.index)
    else:
        robust_z = 0.6745 * (log_return - median) / mad
    result["return_outlier_score"] = robust_z
    result["return_outlier_flag"] = robust_z.abs().gt(threshold).astype(int)
    return result
