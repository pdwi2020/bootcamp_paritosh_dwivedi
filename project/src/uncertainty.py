"""Uncertainty quantification for the weekly risk monitor.

Stage 11 asks for uncertainty made visible rather than a single point estimate.
Two complementary tools live here:

* :func:`bootstrap_metric` resamples the holdout with replacement to give a
  confidence interval for a *metric* (how precisely we know the score).
* :func:`prediction_interval` uses the spread of holdout residuals to give an
  interval for a *new observation* (how far an individual forecast may land).

The distinction matters and is examinable: a confidence interval covers the mean
response and is narrower; a prediction interval covers a new draw and is wider.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

DEFAULT_RESAMPLES = 2000
DEFAULT_CONFIDENCE = 0.95


def _percentiles(confidence: float) -> tuple[float, float]:
    """Return the two-sided percentile bounds for a confidence level."""

    tail = (1.0 - confidence) / 2.0
    return 100.0 * tail, 100.0 * (1.0 - tail)


def bootstrap_metric(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = 20260828,
) -> dict[str, float]:
    """Bootstrap a paired metric and return its point estimate and interval.

    Rows are resampled *with replacement* in matched pairs so the association
    between truth and prediction is preserved. This estimates uncertainty in the
    metric; it says nothing about whether the model is correct.
    """

    truth = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if truth.shape != predicted.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    if truth.size == 0:
        raise ValueError("cannot bootstrap an empty sample")

    rng = np.random.default_rng(seed)
    n = truth.size
    draws = np.empty(resamples, dtype=float)
    for i in range(resamples):
        idx = rng.integers(0, n, size=n)
        draws[i] = metric(truth[idx], predicted[idx])

    low_pct, high_pct = _percentiles(confidence)
    low, high = np.percentile(draws, [low_pct, high_pct])
    return {
        "point_estimate": float(metric(truth, predicted)),
        "bootstrap_mean": float(draws.mean()),
        "ci_low": float(low),
        "ci_high": float(high),
        "confidence": confidence,
        "resamples": resamples,
    }


def prediction_interval(
    residuals: pd.Series | np.ndarray,
    *,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, float]:
    """Empirical prediction interval half-widths from holdout residuals.

    Uses residual percentiles rather than a normal approximation, because the
    volatility target is right-skewed and a Gaussian interval would understate
    the upper tail.
    """

    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError("no finite residuals supplied")

    low_pct, high_pct = _percentiles(confidence)
    low, high = np.percentile(values, [low_pct, high_pct])
    return {
        "lower_offset": float(low),
        "upper_offset": float(high),
        "confidence": confidence,
        "residual_std": float(values.std(ddof=1)) if values.size > 1 else 0.0,
        "method": "empirical residual percentiles",
    }


def gaussian_interval(
    residuals: pd.Series | np.ndarray,
    *,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, float]:
    """Normal-approximation interval, kept for the Stage 11 scenario comparison.

    Reported alongside :func:`prediction_interval` so the effect of assuming
    normality on fat-tailed residuals is visible rather than assumed away.
    """

    from scipy.stats import norm

    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        raise ValueError("need at least two residuals for a gaussian interval")

    sigma = float(values.std(ddof=1))
    z = float(norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    return {
        "lower_offset": float(values.mean() - z * sigma),
        "upper_offset": float(values.mean() + z * sigma),
        "confidence": confidence,
        "residual_std": sigma,
        "method": "gaussian approximation",
    }
