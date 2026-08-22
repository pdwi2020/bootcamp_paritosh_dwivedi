"""Feature builders for the Weekly ETF Risk Monitor.

Every function returns a new frame and uses contemporaneous or past information
only, so no feature can see the window it is meant to predict. That constraint is
the reason each rolling window is closed on the current row and each forward
target is shifted, never centred.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
CALM_VIX, STRESSED_VIX = 15.0, 25.0


def add_vol_ratio(frame: pd.DataFrame, short: int = 5, long: int = 20) -> pd.DataFrame:
    """Add short-window realized volatility divided by the long-window value.

    A ratio above one says turbulence is building faster than the slow baseline
    has absorbed; below one says it is fading. The ratio is scale free, so it
    stays comparable across calm and stressed periods in a way that either
    window on its own does not.
    """

    if short < 2 or long <= short:
        raise ValueError("Require 2 <= short < long")
    result = frame.copy()
    returns = result["daily_return"]
    short_vol = returns.rolling(short).std() * np.sqrt(TRADING_DAYS)
    long_vol = returns.rolling(long).std() * np.sqrt(TRADING_DAYS)
    result[f"vol_{short}"] = short_vol
    result[f"vol_{long}"] = long_vol
    result["vol_ratio"] = (short_vol / long_vol).replace([np.inf, -np.inf], np.nan)
    return result


def add_vix_spread(frame: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add the gap between implied VIX and trailing realized volatility.

    VIX is a forward-looking option-implied number and realized volatility is
    backward looking. The spread between them is the market's view of what is
    coming versus what already happened, which neither series states on its own.
    """

    result = frame.copy()
    realized = (
        result["daily_return"].rolling(window).std() * np.sqrt(TRADING_DAYS) * 100
    )
    result["realized_vol_pct"] = realized
    result["vix_spread"] = result["vix_close"] - realized
    return result


def add_regime_dummies(frame: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode the VIX volatility regime.

    One-hot rather than label encoding because the bands are ordered but not
    evenly spaced: the distance from calm to normal is not the same quantity as
    normal to stressed, and a label encoding would assert that it is. Frequency
    encoding is rejected for a different reason: it maps a band to how often it
    occurred, which conflates rarity with severity.
    """

    result = frame.copy()
    result["vol_regime"] = pd.cut(
        result["vix_close"],
        bins=[-np.inf, CALM_VIX, STRESSED_VIX, np.inf],
        labels=["calm", "normal", "stressed"],
    )
    dummies = pd.get_dummies(result["vol_regime"], prefix="regime").astype(int)
    return pd.concat([result, dummies], axis=1)


def add_forward_volatility(frame: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Add realized volatility over the next ``horizon`` sessions as the target.

    Shifted backwards by one so the window starts the session after the decision
    date. Without that shift the target would include the day the features are
    measured on, which leaks.
    """

    result = frame.copy()
    forward = result["daily_return"].shift(-1).rolling(horizon).std().shift(
        -(horizon - 1)
    ) * np.sqrt(TRADING_DAYS)
    result[f"target_vol_{horizon}"] = forward
    return result
