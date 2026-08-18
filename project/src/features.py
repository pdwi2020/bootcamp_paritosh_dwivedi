"""Leakage-aware features and next-five-session risk targets."""

from __future__ import annotations

import numpy as np
import pandas as pd


BASE_FEATURE_COLUMNS = [
    "return_lag_1",
    "return_lag_5",
    "rolling_return_5",
    "rolling_vol_5",
    "rolling_vol_20",
    "ewma_vol_20",
    "vol_ratio",
    "drawdown",
    "volume_z_20",
]

FEATURE_COLUMNS = [
    *BASE_FEATURE_COLUMNS,
    "return_outlier_flag",
]


def _forward_sum(series: pd.Series, horizon: int) -> pd.Series:
    """Sum the next `horizon` observations, excluding the current row."""

    return series.shift(-1).rolling(horizon).sum().shift(-(horizon - 1))


def build_features(
    frame: pd.DataFrame,
    *,
    horizon: int = 5,
    short_window: int = 5,
    long_window: int = 20,
) -> pd.DataFrame:
    """Build time-series features using only contemporaneous and past data."""

    if horizon != 5:
        raise ValueError("The published model interface requires a five-session forecast horizon")
    if short_window < 2 or long_window <= short_window:
        raise ValueError("Feature windows must satisfy 2 <= short_window < long_window")

    result = frame.copy().sort_values("date").reset_index(drop=True)
    price = result["adjusted_close"].astype(float)
    result["daily_return"] = price.pct_change()
    result["log_return"] = np.log(price).diff()
    result["return_lag_1"] = result["daily_return"].shift(1)
    result["return_lag_5"] = result["daily_return"].shift(5)
    # Canonical column names are retained so saved models share one stable
    # interface; the window values are recorded alongside sensitivity results.
    result["rolling_return_5"] = price.pct_change(short_window)
    result["rolling_vol_5"] = (
        result["log_return"].rolling(short_window).std() * np.sqrt(252)
    )
    result["rolling_vol_20"] = (
        result["log_return"].rolling(long_window).std() * np.sqrt(252)
    )
    result["ewma_vol_20"] = (
        result["log_return"].ewm(span=long_window, adjust=False).std() * np.sqrt(252)
    )
    result["vol_ratio"] = result["rolling_vol_5"] / result["rolling_vol_20"]
    result["drawdown"] = price / price.cummax() - 1.0
    volume_mean = result["volume"].rolling(long_window).mean()
    volume_std = result["volume"].rolling(long_window).std()
    result["volume_z_20"] = (result["volume"] - volume_mean) / volume_std
    future_squared_returns = _forward_sum(result["log_return"].pow(2), horizon)
    result["target_next_week_vol"] = np.sqrt(future_squared_returns) * np.sqrt(252 / horizon)
    result["target_next_week_return"] = _forward_sum(result["daily_return"], horizon)
    result["forecast_horizon_days"] = horizon
    result["short_feature_window_days"] = short_window
    result["long_feature_window_days"] = long_window
    return result.replace([np.inf, -np.inf], np.nan)
