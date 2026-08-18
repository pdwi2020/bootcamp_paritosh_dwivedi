"""Purged time-series evaluation and production risk-model fitting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .evaluation import classification_metrics, percentage_improvement, regression_metrics
from .features import BASE_FEATURE_COLUMNS, FEATURE_COLUMNS, build_features
from .outliers import (
    ReturnOutlierParameters,
    fit_return_outlier_parameters,
    score_return_outliers,
)


RISK_SCORE_CUTOFF = 0.50


@dataclass
class ModelBundle:
    """Evaluation models, train-only preprocessing, and holdout artifacts."""

    regression_model: Pipeline
    classification_model: Pipeline
    outlier_parameters: ReturnOutlierParameters
    results: dict[str, Any]
    predictions: pd.DataFrame


@dataclass
class ProductionModelBundle:
    """Models refitted on every labeled observation for current scoring."""

    regression_model: Pipeline
    classification_model: Pipeline
    outlier_parameters: ReturnOutlierParameters
    risk_threshold: float
    fit_metadata: dict[str, Any]


def chronological_split(
    frame: pd.DataFrame, test_fraction: float, *, gap: int = 0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split ordered observations with an optional embargo before the test set."""

    if gap < 0:
        raise ValueError("gap must be non-negative")
    split_index = int(len(frame) * (1 - test_fraction))
    train_end = split_index - gap
    if train_end <= 20 or len(frame) - split_index <= 5:
        raise ValueError("Insufficient data for a purged chronological train/test split")
    return frame.iloc[:train_end].copy(), frame.iloc[split_index:].copy()


def _regression_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=10.0)),
        ]
    )


def _classification_pipeline() -> Pipeline:
    return Pipeline(
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


def _model_data(feature_frame: pd.DataFrame) -> pd.DataFrame:
    required = BASE_FEATURE_COLUMNS + ["date", "log_return", "target_next_week_vol"]
    missing = [column for column in required if column not in feature_frame]
    if missing:
        raise ValueError(f"Feature frame is missing required columns: {missing}")
    return (
        feature_frame[required]
        .dropna(subset=["date", "target_next_week_vol"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def _add_fitted_outlier_feature(
    frame: pd.DataFrame, parameters: ReturnOutlierParameters
) -> pd.DataFrame:
    result = frame.copy()
    scored = score_return_outliers(result["log_return"], parameters)
    result[["return_outlier_score", "return_outlier_flag"]] = scored
    return result


def _fit_pair(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    risk_quantile: float,
    feature_columns: Sequence[str],
) -> tuple[Pipeline, Pipeline, dict[str, Any], pd.DataFrame]:
    X_train = train[list(feature_columns)]
    X_test = test[list(feature_columns)]
    y_train = train["target_next_week_vol"]
    y_test = test["target_next_week_vol"]

    regression_model = _regression_pipeline()
    regression_model.fit(X_train, y_train)
    regression_prediction = np.clip(regression_model.predict(X_test), 0.0, None)
    recent_vol_baseline = test["rolling_vol_20"].fillna(y_train.mean()).to_numpy()
    mean_baseline = np.full(len(y_test), y_train.mean())

    risk_threshold = float(y_train.quantile(risk_quantile))
    y_train_class = (y_train >= risk_threshold).astype(int)
    y_test_class = (y_test >= risk_threshold).astype(int)
    if y_train_class.nunique() < 2:
        raise ValueError("Training period must contain both elevated and normal risk labels")

    classification_model = _classification_pipeline()
    classification_model.fit(X_train, y_train_class)
    risk_score = classification_model.predict_proba(X_test)[:, 1]
    risk_prediction = (risk_score >= RISK_SCORE_CUTOFF).astype(int)

    prior_score = float(y_train_class.mean())
    prior_scores = np.full(len(y_test_class), prior_score)
    prior_prediction = (prior_scores >= RISK_SCORE_CUTOFF).astype(int)

    regression_result = regression_metrics(y_test, regression_prediction)
    recent_result = regression_metrics(y_test, recent_vol_baseline)
    mean_result = regression_metrics(y_test, mean_baseline)
    classification_result = classification_metrics(y_test_class, risk_prediction, risk_score)
    prior_result = classification_metrics(y_test_class, prior_prediction, prior_scores)

    predictions = pd.DataFrame(
        {
            "date": test["date"].to_numpy(),
            "actual_next_five_day_vol": y_test.to_numpy(),
            "ridge_predicted_vol": regression_prediction,
            "recent_vol_baseline": recent_vol_baseline,
            "actual_elevated_risk": y_test_class.to_numpy(),
            "predicted_elevated_risk": risk_prediction,
            "elevated_risk_score": risk_score,
        }
    )

    results: dict[str, Any] = {
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
            "prior_baseline": prior_result,
            "test_elevated_rate": float(y_test_class.mean()),
            "test_elevated_windows": int(y_test_class.sum()),
            "elevated_windows_caught": int(
                ((y_test_class == 1) & (risk_prediction == 1)).sum()
            ),
            "elevated_windows_missed": int(
                ((y_test_class == 1) & (risk_prediction == 0)).sum()
            ),
            "risk_score_cutoff": RISK_SCORE_CUTOFF,
            "score_interpretation": (
                "Class-weighted logistic output used for ranking and the decision rule; "
                "it is not a calibrated event probability."
            ),
        },
    }
    return regression_model, classification_model, results, predictions


def _non_overlapping_diagnostics(
    predictions: pd.DataFrame, *, horizon: int
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for offset in range(horizon):
        sample = predictions.iloc[offset::horizon]
        regression = regression_metrics(
            sample["actual_next_five_day_vol"], sample["ridge_predicted_vol"]
        )
        recent = regression_metrics(
            sample["actual_next_five_day_vol"], sample["recent_vol_baseline"]
        )
        classification = classification_metrics(
            sample["actual_elevated_risk"],
            sample["predicted_elevated_risk"],
            sample["elevated_risk_score"],
        )
        records.append(
            {
                "offset": offset,
                "rows": int(len(sample)),
                "elevated_windows": int(sample["actual_elevated_risk"].sum()),
                "ridge_mae": regression["mae"],
                "ridge_mae_improvement_vs_recent": percentage_improvement(
                    regression["mae"], recent["mae"]
                ),
                "balanced_accuracy": classification["balanced_accuracy"],
                "recall": classification["recall"],
            }
        )
    return records


def _yearly_diagnostics(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    dated = predictions.assign(year=pd.to_datetime(predictions["date"]).dt.year)
    for year, sample in dated.groupby("year", sort=True):
        regression = regression_metrics(
            sample["actual_next_five_day_vol"], sample["ridge_predicted_vol"]
        )
        recent = regression_metrics(
            sample["actual_next_five_day_vol"], sample["recent_vol_baseline"]
        )
        classification = classification_metrics(
            sample["actual_elevated_risk"],
            sample["predicted_elevated_risk"],
            sample["elevated_risk_score"],
        )
        records.append(
            {
                "year": int(year),
                "rows": int(len(sample)),
                "elevated_rate": float(sample["actual_elevated_risk"].mean()),
                "ridge_mae": regression["mae"],
                "recent_volatility_baseline_mae": recent["mae"],
                "balanced_accuracy": classification["balanced_accuracy"],
                "recall": classification["recall"],
                "roc_auc": classification["roc_auc"],
            }
        )
    return records


def _residual_diagnostics(predictions: pd.DataFrame) -> dict[str, float]:
    actual = predictions["actual_next_five_day_vol"]
    residual = actual - predictions["ridge_predicted_vol"]
    high_quartile = actual >= actual.quantile(0.75)
    top_decile = actual >= actual.quantile(0.90)
    return {
        "mean_actual_minus_predicted": float(residual.mean()),
        "lag_1_autocorrelation": float(residual.autocorr(lag=1)),
        "highest_actual_vol_quartile_mean_actual_minus_predicted": float(
            residual[high_quartile].mean()
        ),
        "highest_actual_vol_quartile_mae": float(residual[high_quartile].abs().mean()),
        "top_actual_vol_decile_mean_actual_minus_predicted": float(
            residual[top_decile].mean()
        ),
        "top_actual_vol_decile_mae": float(residual[top_decile].abs().mean()),
    }


def _walk_forward_diagnostics(
    data: pd.DataFrame,
    *,
    horizon: int,
    risk_quantile: float,
    n_splits: int = 4,
) -> dict[str, Any]:
    splitter = TimeSeriesSplit(n_splits=n_splits, gap=horizon)
    fold_records: list[dict[str, Any]] = []
    fold_predictions: list[pd.DataFrame] = []
    for fold, (train_index, test_index) in enumerate(splitter.split(data), start=1):
        train_base = data.iloc[train_index].copy()
        test_base = data.iloc[test_index].copy()
        parameters = fit_return_outlier_parameters(train_base["log_return"])
        train = _add_fitted_outlier_feature(train_base, parameters)
        test = _add_fitted_outlier_feature(test_base, parameters)
        _, _, results, predictions = _fit_pair(
            train,
            test,
            risk_quantile=risk_quantile,
            feature_columns=FEATURE_COLUMNS,
        )
        fold_predictions.append(predictions)
        fold_records.append(
            {
                "fold": fold,
                "train_rows": int(len(train)),
                "test_rows": int(len(test)),
                "train_end": train["date"].max().date().isoformat(),
                "test_start": test["date"].min().date().isoformat(),
                "test_end": test["date"].max().date().isoformat(),
                "ridge_mae": results["regression"]["ridge"]["mae"],
                "ridge_mae_improvement_vs_recent": results["regression"][
                    "ridge_mae_improvement_vs_recent"
                ],
                "balanced_accuracy": results["classification"]["logistic"][
                    "balanced_accuracy"
                ],
                "recall": results["classification"]["logistic"]["recall"],
            }
        )

    combined = pd.concat(fold_predictions, ignore_index=True)
    aggregate_regression = regression_metrics(
        combined["actual_next_five_day_vol"], combined["ridge_predicted_vol"]
    )
    aggregate_recent = regression_metrics(
        combined["actual_next_five_day_vol"], combined["recent_vol_baseline"]
    )
    aggregate_classification = classification_metrics(
        combined["actual_elevated_risk"],
        combined["predicted_elevated_risk"],
        combined["elevated_risk_score"],
    )
    return {
        "method": f"expanding TimeSeriesSplit with {horizon}-session embargo",
        "folds": fold_records,
        "aggregate": {
            "rows": int(len(combined)),
            "ridge_mae": aggregate_regression["mae"],
            "ridge_mae_improvement_vs_recent": percentage_improvement(
                aggregate_regression["mae"], aggregate_recent["mae"]
            ),
            "balanced_accuracy": aggregate_classification["balanced_accuracy"],
            "recall": aggregate_classification["recall"],
            "roc_auc": aggregate_classification["roc_auc"],
        },
    }


def fit_risk_models(
    feature_frame: pd.DataFrame,
    *,
    test_fraction: float = 0.20,
    risk_quantile: float = 0.75,
    horizon: int = 5,
    include_diagnostics: bool = True,
) -> ModelBundle:
    """Evaluate Ridge and class-weighted logistic models on a purged holdout."""

    data = _model_data(feature_frame)
    train_base, test_base = chronological_split(data, test_fraction, gap=horizon)
    outlier_parameters = fit_return_outlier_parameters(train_base["log_return"])
    train = _add_fitted_outlier_feature(train_base, outlier_parameters)
    test = _add_fitted_outlier_feature(test_base, outlier_parameters)
    regression_model, classification_model, results, predictions = _fit_pair(
        train,
        test,
        risk_quantile=risk_quantile,
        feature_columns=FEATURE_COLUMNS,
    )

    results.update(
        {
            "feature_columns": FEATURE_COLUMNS,
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "embargo_rows": int(horizon),
            "train_start": train["date"].min().date().isoformat(),
            "train_end": train["date"].max().date().isoformat(),
            "test_start": test["date"].min().date().isoformat(),
            "test_end": test["date"].max().date().isoformat(),
            "risk_quantile": risk_quantile,
            "outlier_preprocessing": {
                "fit_scope": "purged training period only",
                **outlier_parameters.to_dict(),
            },
        }
    )

    if include_diagnostics:
        _, _, without_outlier, _ = _fit_pair(
            train,
            test,
            risk_quantile=risk_quantile,
            feature_columns=BASE_FEATURE_COLUMNS,
        )
        results["diagnostics"] = {
            "overlap_note": (
                "The primary holdout contains daily five-session forecast windows, which overlap. "
                "Each offset below samples one non-overlapping sequence."
            ),
            "non_overlapping_windows": _non_overlapping_diagnostics(
                predictions, horizon=horizon
            ),
            "calendar_year": _yearly_diagnostics(predictions),
            "residuals": _residual_diagnostics(predictions),
            "outlier_feature_ablation": {
                "with_flag": {
                    "ridge_mae": results["regression"]["ridge"]["mae"],
                    "balanced_accuracy": results["classification"]["logistic"][
                        "balanced_accuracy"
                    ],
                    "recall": results["classification"]["logistic"]["recall"],
                },
                "without_flag": {
                    "ridge_mae": without_outlier["regression"]["ridge"]["mae"],
                    "balanced_accuracy": without_outlier["classification"]["logistic"][
                        "balanced_accuracy"
                    ],
                    "recall": without_outlier["classification"]["logistic"]["recall"],
                },
            },
            "walk_forward": _walk_forward_diagnostics(
                data,
                horizon=horizon,
                risk_quantile=risk_quantile,
            ),
        }

    return ModelBundle(
        regression_model,
        classification_model,
        outlier_parameters,
        results,
        predictions,
    )


def fit_production_models(
    feature_frame: pd.DataFrame,
    *,
    risk_quantile: float = 0.75,
) -> ProductionModelBundle:
    """Refit preprocessing and both models on all currently labeled rows."""

    data = _model_data(feature_frame)
    outlier_parameters = fit_return_outlier_parameters(data["log_return"])
    fitted = _add_fitted_outlier_feature(data, outlier_parameters)
    X = fitted[FEATURE_COLUMNS]
    target = fitted["target_next_week_vol"]
    risk_threshold = float(target.quantile(risk_quantile))
    labels = (target >= risk_threshold).astype(int)

    regression_model = _regression_pipeline()
    classification_model = _classification_pipeline()
    regression_model.fit(X, target)
    classification_model.fit(X, labels)
    metadata = {
        "purpose": "current scoring only; holdout metrics come from the separate evaluation fit",
        "fit_rows": int(len(fitted)),
        "fit_start": fitted["date"].min().date().isoformat(),
        "fit_end": fitted["date"].max().date().isoformat(),
        "risk_quantile": risk_quantile,
        "risk_score_cutoff": RISK_SCORE_CUTOFF,
        "outlier_preprocessing": outlier_parameters.to_dict(),
    }
    return ProductionModelBundle(
        regression_model,
        classification_model,
        outlier_parameters,
        risk_threshold,
        metadata,
    )


def risk_threshold_sensitivity(
    feature_frame: pd.DataFrame, *, test_fraction: float, quantiles=(0.70, 0.75, 0.80)
) -> list[dict[str, float]]:
    """Evaluate classification stability across training-derived thresholds."""

    records: list[dict[str, float]] = []
    for quantile in quantiles:
        bundle = fit_risk_models(
            feature_frame,
            test_fraction=test_fraction,
            risk_quantile=quantile,
            include_diagnostics=False,
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


def feature_window_sensitivity(
    clean_frame: pd.DataFrame,
    *,
    test_fraction: float,
    risk_quantile: float,
    window_pairs: Sequence[tuple[int, int]] = ((5, 20), (10, 30), (10, 60)),
) -> list[dict[str, float | int]]:
    """Compare canonical and alternative trailing feature windows."""

    records: list[dict[str, float | int]] = []
    for short_window, long_window in window_pairs:
        features = build_features(
            clean_frame,
            horizon=5,
            short_window=short_window,
            long_window=long_window,
        )
        bundle = fit_risk_models(
            features,
            test_fraction=test_fraction,
            risk_quantile=risk_quantile,
            include_diagnostics=False,
        )
        records.append(
            {
                "short_window_days": short_window,
                "long_window_days": long_window,
                "ridge_mae": bundle.results["regression"]["ridge"]["mae"],
                "ridge_mae_improvement_vs_recent": bundle.results["regression"][
                    "ridge_mae_improvement_vs_recent"
                ],
                "balanced_accuracy": bundle.results["classification"]["logistic"][
                    "balanced_accuracy"
                ],
                "recall": bundle.results["classification"]["logistic"]["recall"],
            }
        )
    return records
