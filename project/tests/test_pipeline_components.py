import copy
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import InconsistentVersionWarning

import verify_project
from src.cleaning import clean_market_data
from src.features import build_features
from src.modeling import chronological_split, fit_production_models, fit_risk_models
from src.outliers import (
    add_return_outlier_flag,
    fit_return_outlier_parameters,
    score_return_outliers,
)
from src.validation import validate_market_data
from verify_project import (
    _load_model_artifact,
    _verify_declared_artifacts,
    _verify_prediction_metrics,
)


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


def test_validation_rejects_empty_market_data():
    frame = sample_market_data(rows=0)
    report = validate_market_data(frame, raise_on_error=False)
    assert report["valid"] is False
    assert "Market data contains no rows" in report["errors"]


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
    assert (
        production.fit_metadata["fit_end"]
        == features.dropna(subset=["target_next_week_vol"])["date"].max().date().isoformat()
    )


def test_verifier_detects_prediction_metric_drift():
    project_root = Path(__file__).resolve().parents[1]
    metrics = json.loads((project_root / "reports/metrics.json").read_text())
    predictions = pd.read_csv(project_root / "reports/model_predictions.csv")
    _verify_prediction_metrics(metrics, predictions)

    altered = copy.deepcopy(metrics)
    altered["models"]["regression"]["ridge"]["mae"] += 0.01
    with pytest.raises(SystemExit, match="ridge mae"):
        _verify_prediction_metrics(altered, predictions)


def _declared_artifact_fixture(project_root: Path) -> dict:
    metrics = {
        "data": {
            "raw_file": "data/raw/snapshot.csv",
            "processed_clean_file": "data/processed/clean.parquet",
            "model_dataset_file": "data/processed/model.parquet",
        },
        "artifacts": {
            "predictions": "reports/predictions.csv",
            "risk_threshold_sensitivity": "reports/risk.csv",
            "feature_window_sensitivity": "reports/features.csv",
            "model": "model/model.joblib",
            "figures": ["reports/images/figure.png"],
        },
    }
    for relative_path in [
        *metrics["data"].values(),
        metrics["artifacts"]["predictions"],
        metrics["artifacts"]["risk_threshold_sensitivity"],
        metrics["artifacts"]["feature_window_sensitivity"],
        metrics["artifacts"]["model"],
        *metrics["artifacts"]["figures"],
    ]:
        path = project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")
    return metrics


def test_verifier_checks_every_declared_artifact(tmp_path):
    metrics = _declared_artifact_fixture(tmp_path)
    resolved = _verify_declared_artifacts(metrics, tmp_path)
    assert resolved["raw_file"] == tmp_path / metrics["data"]["raw_file"]

    (tmp_path / metrics["artifacts"]["risk_threshold_sensitivity"]).unlink()
    with pytest.raises(SystemExit, match="risk_threshold_sensitivity artifact is missing"):
        _verify_declared_artifacts(metrics, tmp_path)


def test_verifier_uses_manifested_raw_path(tmp_path):
    metrics = _declared_artifact_fixture(tmp_path)
    metrics["data"]["raw_file"] = "data/raw/nonexistent.csv"
    with pytest.raises(SystemExit, match="raw_file artifact is missing"):
        _verify_declared_artifacts(metrics, tmp_path)


def test_verifier_rejects_artifact_path_escape(tmp_path):
    metrics = _declared_artifact_fixture(tmp_path)
    metrics["data"]["raw_file"] = "../outside.csv"
    with pytest.raises(SystemExit, match="escapes the project directory"):
        _verify_declared_artifacts(metrics, tmp_path)


def test_verifier_rejects_incompatible_saved_model(monkeypatch, tmp_path):
    def load_with_version_warning(_):
        warnings.warn(
            InconsistentVersionWarning(
                estimator_name="Ridge",
                current_sklearn_version="1.7.1",
                original_sklearn_version="1.7.2",
            )
        )

    monkeypatch.setattr(verify_project.joblib, "load", load_with_version_warning)
    with pytest.raises(SystemExit, match="incompatible scikit-learn version"):
        _load_model_artifact(tmp_path / "model.joblib")


def test_verifier_detects_baseline_metric_and_headline_drift():
    project_root = Path(__file__).resolve().parents[1]
    metrics = json.loads((project_root / "reports/metrics.json").read_text())
    predictions = pd.read_csv(project_root / "reports/model_predictions.csv")

    altered_baseline = copy.deepcopy(metrics)
    altered_baseline["models"]["regression"]["recent_volatility_baseline"]["mae"] += 0.01
    with pytest.raises(SystemExit, match="recent-volatility baseline mae"):
        _verify_prediction_metrics(altered_baseline, predictions)

    altered_headline = copy.deepcopy(metrics)
    altered_headline["models"]["regression"]["ridge_mae_improvement_vs_recent"] += 0.01
    with pytest.raises(SystemExit, match="Ridge MAE improvement"):
        _verify_prediction_metrics(altered_headline, predictions)


def test_verifier_detects_baseline_prediction_drift():
    project_root = Path(__file__).resolve().parents[1]
    metrics = json.loads((project_root / "reports/metrics.json").read_text())
    predictions = pd.read_csv(project_root / "reports/model_predictions.csv")
    predictions.loc[0, "recent_vol_baseline"] += 0.05

    with pytest.raises(SystemExit, match="recent-volatility baseline"):
        _verify_prediction_metrics(metrics, predictions)


def test_verifier_rejects_duplicate_prediction_dates():
    project_root = Path(__file__).resolve().parents[1]
    metrics = json.loads((project_root / "reports/metrics.json").read_text())
    predictions = pd.read_csv(project_root / "reports/model_predictions.csv")
    predictions.loc[10, "date"] = predictions.loc[11, "date"]

    with pytest.raises(SystemExit, match="duplicate dates"):
        _verify_prediction_metrics(metrics, predictions)


def test_verifier_rejects_non_chronological_prediction_dates():
    project_root = Path(__file__).resolve().parents[1]
    metrics = json.loads((project_root / "reports/metrics.json").read_text())
    predictions = pd.read_csv(project_root / "reports/model_predictions.csv")
    predictions.loc[[10, 11]] = predictions.loc[[11, 10]].to_numpy()

    with pytest.raises(SystemExit, match="not chronological"):
        _verify_prediction_metrics(metrics, predictions)
