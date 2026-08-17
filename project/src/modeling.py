"""Chronological regression and elevated-risk classification models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .evaluation import classification_metrics, percentage_improvement, regression_metrics
from .features import FEATURE_COLUMNS


@dataclass
class ModelBundle:
    """Fitted models and evaluation artifacts."""

    regression_model: Pipeline
    classification_model: Pipeline
    results: dict[str, Any]
    predictions: pd.DataFrame


def chronological_split(frame: pd.DataFrame, test_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split ordered observations without shuffling."""

    split_index = int(len(frame) * (1 - test_fraction))
    if split_index <= 20 or len(frame) - split_index <= 5:
        raise ValueError("Insufficient data for a chronological train/test split")
    return frame.iloc[:split_index].copy(), frame.iloc[split_index:].copy()


def fit_risk_models(
    feature_frame: pd.DataFrame,
    *,
    test_fraction: float = 0.20,
    risk_quantile: float = 0.75,
) -> ModelBundle:
    """Fit baseline, Ridge, and logistic models using a chronological split."""

    required = FEATURE_COLUMNS + ["date", "target_next_week_vol"]
    data = feature_frame[required].dropna(subset=["target_next_week_vol"]).copy()
    train, test = chronological_split(data, test_fraction)
    X_train = train[FEATURE_COLUMNS]
    X_test = test[FEATURE_COLUMNS]
    y_train = train["target_next_week_vol"]
    y_test = test["target_next_week_vol"]

    regression_model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ]
    )
    regression_model.fit(X_train, y_train)
    regression_prediction = np.clip(regression_model.predict(X_test), 0.0, None)
    recent_vol_baseline = test["rolling_vol_20"].fillna(y_train.mean()).to_numpy()
    mean_baseline = np.full(len(y_test), y_train.mean())

    risk_threshold = float(y_train.quantile(risk_quantile))
    y_train_class = (y_train >= risk_threshold).astype(int)
    y_test_class = (y_test >= risk_threshold).astype(int)
    classification_model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )
    classification_model.fit(X_train, y_train_class)
    risk_probability = classification_model.predict_proba(X_test)[:, 1]
    risk_prediction = (risk_probability >= 0.50).astype(int)

    dummy = DummyClassifier(strategy="prior", random_state=42)
    dummy.fit(np.zeros((len(y_train_class), 1)), y_train_class)
    dummy_probability = dummy.predict_proba(np.zeros((len(y_test_class), 1)))[:, 1]
    dummy_prediction = dummy.predict(np.zeros((len(y_test_class), 1)))

    regression_result = regression_metrics(y_test, regression_prediction)
    recent_result = regression_metrics(y_test, recent_vol_baseline)
    mean_result = regression_metrics(y_test, mean_baseline)
    classification_result = classification_metrics(y_test_class, risk_prediction, risk_probability)
    dummy_result = classification_metrics(y_test_class, dummy_prediction, dummy_probability)

    predictions = pd.DataFrame(
        {
            "date": test["date"].to_numpy(),
            "actual_next_week_vol": y_test.to_numpy(),
            "ridge_predicted_vol": regression_prediction,
            "recent_vol_baseline": recent_vol_baseline,
            "actual_elevated_risk": y_test_class.to_numpy(),
            "predicted_elevated_risk": risk_prediction,
            "elevated_risk_probability": risk_probability,
        }
    )

    results: dict[str, Any] = {
        "feature_columns": FEATURE_COLUMNS,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_start": train["date"].min().date().isoformat(),
        "train_end": train["date"].max().date().isoformat(),
        "test_start": test["date"].min().date().isoformat(),
        "test_end": test["date"].max().date().isoformat(),
        "risk_quantile": risk_quantile,
        "risk_threshold_annualized_vol": risk_threshold,
        "regression": {
            "ridge": regression_result,
            "recent_volatility_baseline": recent_result,
            "historical_mean_baseline": mean_result,
            "ridge_mae_improvement_vs_recent": percentage_improvement(
                regression_result["mae"], recent_result["mae"]
            ),
        },
        "classification": {
            "logistic": classification_result,
            "prior_baseline": dummy_result,
            "test_elevated_rate": float(y_test_class.mean()),
        },
    }
    return ModelBundle(regression_model, classification_model, results, predictions)


def risk_threshold_sensitivity(
    feature_frame: pd.DataFrame, *, test_fraction: float, quantiles=(0.70, 0.75, 0.80)
) -> list[dict[str, float]]:
    """Evaluate classification stability across training-derived risk thresholds."""

    records: list[dict[str, float]] = []
    for quantile in quantiles:
        bundle = fit_risk_models(
            feature_frame,
            test_fraction=test_fraction,
            risk_quantile=quantile,
        )
        metrics = bundle.results["classification"]["logistic"]
        records.append(
            {
                "risk_quantile": float(quantile),
                "risk_threshold_annualized_vol": float(
                    bundle.results["risk_threshold_annualized_vol"]
                ),
                "balanced_accuracy": metrics["balanced_accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
            }
        )
    return records
