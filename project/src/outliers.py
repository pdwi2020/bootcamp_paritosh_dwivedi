"""Outlier diagnostics that preserve plausible market tail events."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ReturnOutlierParameters:
    """Robust return-location parameters learned from an allowed fit period."""

    median: float
    mad: float
    threshold: float = 6.0

    def to_dict(self) -> dict[str, float]:
        """Return JSON-serializable parameters for audit artifacts."""

        return asdict(self)


def fit_return_outlier_parameters(
    log_return: pd.Series, *, threshold: float = 6.0
) -> ReturnOutlierParameters:
    """Fit robust outlier parameters on a training-period return series."""

    clean = pd.to_numeric(log_return, errors="coerce").dropna()
    if clean.empty:
        raise ValueError("Cannot fit return-outlier parameters without valid returns")
    median = float(clean.median())
    mad = float((clean - median).abs().median())
    return ReturnOutlierParameters(median=median, mad=mad, threshold=float(threshold))


def score_return_outliers(
    log_return: pd.Series, parameters: ReturnOutlierParameters
) -> pd.DataFrame:
    """Apply already-fitted parameters without learning from scored observations."""

    values = pd.to_numeric(log_return, errors="coerce")
    if parameters.mad == 0 or pd.isna(parameters.mad):
        robust_z = pd.Series(0.0, index=values.index)
    else:
        robust_z = 0.6745 * (values - parameters.median) / parameters.mad
    return pd.DataFrame(
        {
            "return_outlier_score": robust_z,
            "return_outlier_flag": robust_z.abs().gt(parameters.threshold).astype(int),
        },
        index=values.index,
    )


def add_return_outlier_flag(
    frame: pd.DataFrame,
    *,
    price_column: str = "adjusted_close",
    threshold: float = 6.0,
    parameters: ReturnOutlierParameters | None = None,
) -> pd.DataFrame:
    """Flag extreme log returns using a robust median absolute-deviation score.

    Observations are retained because extreme market moves are relevant to the
    risk-monitoring decision. The flag is available as a model feature and for
    sensitivity analysis.
    """

    result = frame.copy()
    log_return = (
        result["log_return"]
        if "log_return" in result
        else np.log(result[price_column].astype(float)).diff()
    )
    fitted = parameters or fit_return_outlier_parameters(log_return, threshold=threshold)
    scores = score_return_outliers(log_return, fitted)
    result[["return_outlier_score", "return_outlier_flag"]] = scores
    return result
