"""Evaluation metrics and sensitivity summaries."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """Return interpretable out-of-sample regression metrics."""

    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def classification_metrics(y_true, y_pred, y_probability) -> dict[str, float]:
    """Return classification metrics emphasizing elevated-risk recall."""

    result = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    result["roc_auc"] = (
        float(roc_auc_score(y_true, y_probability)) if len(set(y_true)) == 2 else float("nan")
    )
    return result


def percentage_improvement(model_value: float, baseline_value: float) -> float:
    """Return improvement for error metrics where lower is better."""

    return float((baseline_value - model_value) / baseline_value) if baseline_value else 0.0
