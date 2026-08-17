import numpy as np
import pandas as pd

from src.cleaning import clean_market_data
from src.features import build_features
from src.modeling import chronological_split
from src.outliers import add_return_outlier_flag
from src.validation import validate_market_data


def sample_market_data(rows: int = 80) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=rows)
    close = 100 * np.cumprod(1 + np.linspace(-0.002, 0.003, rows))
    return pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adjusted_close": close,
            "volume": np.arange(rows) + 1_000_000,
        }
    )


def test_validation_and_cleaning_preserve_valid_data():
    frame = sample_market_data()
    assert validate_market_data(frame)["valid"] is True
    clean, report = clean_market_data(frame)
    assert len(clean) == len(frame)
    assert report["rows_removed"] == 0


def test_features_use_future_window_only_for_target():
    frame = add_return_outlier_flag(sample_market_data())
    featured = build_features(frame, horizon=5)
    index = 30
    future = featured.loc[index + 1 : index + 5, "log_return"]
    expected = np.sqrt((future**2).sum()) * np.sqrt(252 / 5)
    assert np.isclose(featured.loc[index, "target_next_week_vol"], expected)


def test_chronological_split_keeps_dates_ordered():
    frame = sample_market_data()
    train, test = chronological_split(frame, 0.20)
    assert train["date"].max() < test["date"].min()
    assert len(train) == 64
    assert len(test) == 16
