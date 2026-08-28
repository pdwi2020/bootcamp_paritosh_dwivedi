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
