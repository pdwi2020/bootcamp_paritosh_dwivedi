"""Uncertainty and scenario helpers for Stage 11 homework.

Kept in ``src/`` rather than the notebook so the same functions can be imported
and reused, which is what the course structure asks for at this stage.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats

DEFAULT_RESAMPLES = 1000
DEFAULT_CONFIDENCE = 0.95


def rmse(y_true, y_pred) -> float:
    """Root mean squared error."""

    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred) -> float:
    """Mean absolute error."""

    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.mean(np.abs(y_true - y_pred)))


def bootstrap_ci(
    y_true,
    y_pred,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = 42,
) -> dict[str, float]:
    """Bootstrap a paired metric: resample rows with replacement, recompute, take percentiles.

    Pairs are kept together so the association between truth and prediction survives
    resampling. This estimates uncertainty in the metric, not whether the model is right.
    """

    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    if y_true.size == 0:
        raise ValueError("cannot bootstrap an empty sample")

    rng = np.random.default_rng(seed)
    n = y_true.size
    draws = np.array(
        [
            metric(*(arr[idx] for arr in (y_true, y_pred)))
            for idx in (rng.integers(0, n, n) for _ in range(resamples))
        ]
    )
    tail = (1 - confidence) / 2
    lo, hi = np.percentile(draws, [100 * tail, 100 * (1 - tail)])
    return {
        "point": float(metric(y_true, y_pred)),
        "lo": float(lo),
        "hi": float(hi),
        "resamples": resamples,
        "method": "bootstrap percentile",
    }


def gaussian_ci(
    y_true,
    y_pred,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, float]:
    """Normal-approximation interval for a mean-style metric, for comparison."""

    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    per_row = np.abs(y_true - y_pred) if metric is mae else (y_true - y_pred) ** 2
    n = per_row.size
    centre = per_row.mean()
    se = per_row.std(ddof=1) / np.sqrt(n)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    lo, hi = centre - z * se, centre + z * se
    if metric is rmse:
        lo, hi, centre = np.sqrt(max(lo, 0)), np.sqrt(hi), np.sqrt(centre)
    return {
        "point": float(centre),
        "lo": float(lo),
        "hi": float(hi),
        "method": "gaussian approximation",
    }


def subgroup_metrics(
    frame: pd.DataFrame,
    group_column: str,
    truth_column: str,
    prediction_column: str,
) -> pd.DataFrame:
    """Metric per subgroup, so an aggregate cannot hide a localised failure."""

    rows = []
    for name, part in frame.groupby(group_column, observed=True):
        rows.append(
            {
                group_column: name,
                "n": len(part),
                "mae": mae(part[truth_column], part[prediction_column]),
                "rmse": rmse(part[truth_column], part[prediction_column]),
                "mean_residual": float(
                    (part[truth_column] - part[prediction_column]).mean()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(group_column).reset_index(drop=True)
