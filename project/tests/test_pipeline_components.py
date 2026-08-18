import numpy as np
import pandas as pd

from src.cleaning import clean_market_data
from src.features import build_features
from src.modeling import chronological_split, fit_production_models, fit_risk_models
from src.outliers import (
    add_return_outlier_flag,
    fit_return_outlier_parameters,
    score_return_outliers,
)
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


def test_chronological_split_embargoes_target_horizon():
    frame = sample_market_data()
    train, test = chronological_split(frame, 0.20, gap=5)
    assert len(train) == 59
    assert len(test) == 16
    assert frame.loc[train.index.max() + 5, "date"] < test["date"].min()


def test_outlier_parameters_are_reused_without_refitting():
    training_returns = pd.Series([0.001, -0.001, 0.002, -0.002, 0.0005])
    parameters = fit_return_outlier_parameters(training_returns, threshold=3.0)
    scored = score_return_outliers(pd.Series([0.0, 0.25]), parameters)
    assert parameters.median == training_returns.median()
    assert scored.loc[1, "return_outlier_flag"] == 1


def test_evaluation_is_purged_and_production_refit_is_separate():
    rng = np.random.default_rng(42)
    rows = 420
    dates = pd.bdate_range("2023-01-03", periods=rows)
    returns = rng.normal(0.0003, 0.012, rows)
    returns[::47] *= 5
    close = 100 * np.cumprod(1 + returns)
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.999,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adjusted_close": close,
            "volume": 1_000_000 + rng.integers(0, 500_000, rows),
        }
    )
    features = build_features(frame)
    evaluation = fit_risk_models(features, include_diagnostics=False)
    production = fit_production_models(features)
    assert evaluation.results["embargo_rows"] == 5
    assert evaluation.results["train_end"] < evaluation.results["test_start"]
    assert "elevated_risk_score" in evaluation.predictions
    assert "elevated_risk_probability" not in evaluation.predictions
    assert production.fit_metadata["fit_rows"] > evaluation.results["train_rows"]
    assert production.fit_metadata["fit_end"] == features.dropna(
        subset=["target_next_week_vol"]
    )["date"].max().date().isoformat()
