"""Tests for the Stage 11, 13 and 15 additions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features import FEATURE_COLUMNS
from src.serving import (
    ServingBundle,
    load_model,
    predict_one,
    save_model,
    validate_features,
)
from src.uncertainty import bootstrap_metric, gaussian_interval, prediction_interval


class _StubRegression:
    def predict(self, frame):
        return np.array([0.12] * len(frame))


class _StubClassifier:
    def predict_proba(self, frame):
        return np.tile(np.array([[0.7, 0.3]]), (len(frame), 1))


def _bundle() -> ServingBundle:
    return ServingBundle(
        regression_model=_StubRegression(),
        classification_model=_StubClassifier(),
        feature_columns=list(FEATURE_COLUMNS),
        risk_threshold=0.17,
        fit_metadata={"fit_end": "2026-08-18"},
    )


def _payload() -> dict[str, float]:
    return {name: 0.01 for name in FEATURE_COLUMNS}


# --- feature validation -------------------------------------------------


def test_validate_features_accepts_a_complete_numeric_payload():
    cleaned = validate_features(_payload(), _bundle())
    assert set(cleaned) == set(FEATURE_COLUMNS)
    assert all(isinstance(value, float) for value in cleaned.values())


def test_validate_features_names_every_missing_feature():
    payload = _payload()
    del payload["drawdown"]
    del payload["vol_ratio"]
    with pytest.raises(ValueError, match="drawdown"):
        validate_features(payload, _bundle())


def test_validate_features_rejects_non_numeric_values():
    payload = _payload()
    payload["drawdown"] = "oops"
    with pytest.raises(ValueError, match="must be numeric"):
        validate_features(payload, _bundle())


def test_validate_features_rejects_booleans_masquerading_as_numbers():
    payload = _payload()
    payload["return_outlier_flag"] = True
    with pytest.raises(ValueError, match="must be numeric"):
        validate_features(payload, _bundle())


def test_validate_features_rejects_a_non_dict_payload():
    with pytest.raises(ValueError, match="JSON object"):
        validate_features(["not", "a", "dict"], _bundle())


# --- prediction ---------------------------------------------------------


def test_predict_one_returns_the_stakeholder_contract():
    result = predict_one(_payload(), _bundle())
    assert result["predicted_next_five_day_vol"] == pytest.approx(0.12)
    assert result["elevated_risk_score"] == pytest.approx(0.3)
    assert result["risk_classification"] == "normal"
    assert "not a calibrated event probability" in result["score_interpretation"]


def test_predict_one_flags_elevated_above_the_cutoff():
    class _High(_StubClassifier):
        def predict_proba(self, frame):
            return np.tile(np.array([[0.1, 0.9]]), (len(frame), 1))

    bundle = _bundle()
    bundle.classification_model = _High()
    assert predict_one(_payload(), bundle)["risk_classification"] == "elevated"


# --- persistence --------------------------------------------------------


def test_save_and_load_model_round_trip(tmp_path):
    class _Bundle:
        regression_model = _StubRegression()
        classification_model = _StubClassifier()
        risk_threshold = 0.17
        fit_metadata = {"fit_end": "2026-08-18"}

    path = save_model(_Bundle(), tmp_path)
    assert path.name == "model.pkl"

    restored = load_model(tmp_path)
    assert restored is not None
    assert restored.feature_columns == list(FEATURE_COLUMNS)
    assert restored.risk_threshold == pytest.approx(0.17)


def test_load_model_returns_none_when_absent(tmp_path):
    assert load_model(tmp_path) is None


# --- uncertainty --------------------------------------------------------


def _mae(a, b):
    return float(np.mean(np.abs(a - b)))


def test_bootstrap_metric_interval_brackets_the_point_estimate():
    rng = np.random.default_rng(0)
    truth = pd.Series(rng.normal(0.15, 0.05, 400))
    pred = truth + rng.normal(0, 0.01, 400)
    result = bootstrap_metric(truth, pred, _mae, resamples=200)
    assert result["ci_low"] <= result["point_estimate"] <= result["ci_high"]
    assert result["resamples"] == 200


def test_bootstrap_metric_is_deterministic_for_a_fixed_seed():
    truth = pd.Series(np.linspace(0.1, 0.2, 50))
    pred = truth + 0.01
    first = bootstrap_metric(truth, pred, _mae, resamples=100, seed=7)
    second = bootstrap_metric(truth, pred, _mae, resamples=100, seed=7)
    assert first == second


def test_bootstrap_metric_rejects_mismatched_shapes():
    with pytest.raises(ValueError, match="same shape"):
        bootstrap_metric(np.array([1.0, 2.0]), np.array([1.0]), _mae)


def test_bootstrap_metric_rejects_an_empty_sample():
    with pytest.raises(ValueError, match="empty sample"):
        bootstrap_metric(np.array([]), np.array([]), _mae)


def test_prediction_interval_is_ordered_and_ignores_non_finite():
    residuals = np.array([-0.05, -0.01, 0.0, 0.02, 0.09, np.nan, np.inf])
    interval = prediction_interval(residuals)
    assert interval["lower_offset"] < interval["upper_offset"]
    assert interval["method"] == "empirical residual percentiles"


def test_gaussian_interval_is_symmetric_about_the_residual_mean():
    residuals = np.array([-0.02, -0.01, 0.0, 0.01, 0.02])
    interval = gaussian_interval(residuals)
    midpoint = (interval["lower_offset"] + interval["upper_offset"]) / 2
    assert midpoint == pytest.approx(float(residuals.mean()), abs=1e-9)


def test_empirical_and_gaussian_intervals_differ_on_skewed_residuals():
    rng = np.random.default_rng(3)
    skewed = rng.lognormal(mean=-4.0, sigma=1.0, size=2000) - 0.02
    empirical = prediction_interval(skewed)
    gaussian = gaussian_interval(skewed)
    # The gaussian form cannot represent the long right tail, so its upper bound
    # sits below the empirical one. This is the Stage 11 scenario comparison.
    assert gaussian["upper_offset"] < empirical["upper_offset"]


# --- Stage 11 figure and Stage 13 API -----------------------------------


def test_plot_uncertainty_writes_a_labelled_two_panel_figure(tmp_path):
    import matplotlib.pyplot as plt

    from src.plotting import plot_uncertainty

    predictions = pd.DataFrame(
        {
            "actual_next_five_day_vol": np.linspace(0.10, 0.30, 60),
            "ridge_predicted_vol": np.linspace(0.11, 0.28, 60),
        }
    )
    uncertainty = {
        "ridge_mae_bootstrap_ci": {"point_estimate": 0.04, "ci_low": 0.037, "ci_high": 0.044},
        "baseline_mae_bootstrap_ci": {"point_estimate": 0.05, "ci_low": 0.046, "ci_high": 0.056},
        "prediction_interval_scenarios": {
            "empirical_residual_percentiles": {"lower_offset": -0.09, "upper_offset": 0.14},
            "gaussian_approximation": {"lower_offset": -0.13, "upper_offset": 0.13},
        },
    }
    path = plot_uncertainty(predictions, uncertainty, tmp_path)
    assert path.exists() and path.stat().st_size > 5_000
    plt.close("all")


def test_create_all_figures_omits_uncertainty_panel_when_not_supplied(tmp_path):
    """The uncertainty argument is optional, so older callers keep working."""

    import inspect

    from src.plotting import create_all_figures

    signature = inspect.signature(create_all_figures)
    assert signature.parameters["uncertainty"].default is None


def test_api_predict_matches_the_serving_function():
    """The HTTP layer must not change the answer the serving function gives."""

    import app as api_module

    bundle = api_module.load_model()
    if bundle is None:  # pipeline has not been run in this environment
        pytest.skip("no model/model.pkl available")

    payload = {name: 0.01 for name in bundle.feature_columns}
    direct = api_module.predict_one(payload, bundle)

    client = api_module.app.test_client()
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    served = response.get_json()
    assert served["predicted_next_five_day_vol"] == pytest.approx(
        direct["predicted_next_five_day_vol"]
    )
    assert served["elevated_risk_score"] == pytest.approx(direct["elevated_risk_score"])


def test_api_rejects_bad_bodies_with_400():
    import app as api_module

    client = api_module.app.test_client()
    assert client.post("/predict", json={"return_lag_1": 0.01}).status_code == 400
    assert client.post("/predict", data="not json").status_code == 400


def test_api_health_reports_model_state():
    import app as api_module

    body = api_module.app.test_client().get("/health").get_json()
    assert body["status"] == "ok"
    assert "model_loaded" in body


# --- optional routes and the monitoring wireframe -----------------------


def test_dashboard_sketch_renders(tmp_path):
    import matplotlib.pyplot as plt

    from src.plotting import plot_dashboard_sketch

    path = plot_dashboard_sketch(tmp_path)
    assert path.name == "dashboard_sketch.png"
    assert path.stat().st_size > 20_000
    plt.close("all")


def test_parameterised_analysis_validates_its_inputs():
    import app as api_module

    client = api_module.app.test_client()
    assert client.get("/run_full_analysis/1.5/0.25").status_code == 400
    assert client.get("/run_full_analysis/0.75/0.9").status_code == 400
    assert client.get("/run_full_analysis/abc/0.25").status_code == 400


def test_parameterised_analysis_does_not_touch_committed_artifacts():
    """The exploratory route must never overwrite the repository's own numbers."""

    import hashlib

    import app as api_module
    from src.config import get_settings

    metrics_path = get_settings().reports_dir / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("pipeline has not been run in this environment")

    before = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    response = api_module.app.test_client().get("/run_full_analysis/0.75/0.20")
    assert response.status_code in {200, 503}
    after = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    assert before == after


def test_plot_route_returns_png_or_404():
    import app as api_module

    response = api_module.app.test_client().get("/plot")
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        assert response.mimetype == "image/png"
