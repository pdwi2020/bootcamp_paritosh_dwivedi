"""Serving layer: persist the scoring model and reuse it without refitting.

Stage 13 asks that the project can save its model, reuse a saved model rather
than running the analysis anew, and expose prediction through a small API. The
prediction logic lives here rather than in ``app.py`` so the notebook, the CLI
and the API all call exactly the same function.

The artifact written here (``model/model.pkl``) is deliberately separate from
``model/risk_models.joblib``, which the full pipeline rewrites on every run:
``model.pkl`` is the serving copy, pinned until you explicitly refresh it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import get_settings
from src.features import FEATURE_COLUMNS

MODEL_FILENAME = "model.pkl"
RISK_SCORE_CUTOFF = 0.5


@dataclass
class ServingBundle:
    """Everything needed to score one observation, with no training data."""

    regression_model: Any
    classification_model: Any
    feature_columns: list[str]
    risk_threshold: float
    fit_metadata: dict[str, Any]

    def required_features(self) -> list[str]:
        return list(self.feature_columns)


def model_path(directory: Path | None = None) -> Path:
    """Resolve the serving artifact path, honouring configured directories."""

    base = directory or get_settings().model_dir
    return Path(base) / MODEL_FILENAME


def save_model(bundle: Any, directory: Path | None = None) -> Path:
    """Persist a production bundle as the serving artifact, overwriting any existing copy."""

    path = model_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "regression_model": bundle.regression_model,
            "classification_model": bundle.classification_model,
            "feature_columns": list(FEATURE_COLUMNS),
            "risk_threshold": float(bundle.risk_threshold),
            "fit_metadata": dict(bundle.fit_metadata),
        },
        path,
    )
    return path


def load_model(directory: Path | None = None) -> ServingBundle | None:
    """Return the saved serving bundle, or ``None`` when no artifact exists.

    Returning ``None`` rather than raising lets callers implement the Stage 13
    behaviour of "use a saved model if it exists, otherwise fit a new one"
    without wrapping every call in a try block.
    """

    path = model_path(directory)
    if not path.exists():
        return None
    payload = joblib.load(path)
    return ServingBundle(
        regression_model=payload["regression_model"],
        classification_model=payload["classification_model"],
        feature_columns=list(payload["feature_columns"]),
        risk_threshold=float(payload["risk_threshold"]),
        fit_metadata=dict(payload.get("fit_metadata", {})),
    )


def validate_features(payload: dict[str, Any], bundle: ServingBundle) -> dict[str, float]:
    """Coerce an incoming payload to the model's feature contract.

    Raises :class:`ValueError` with an actionable message when a feature is
    missing or non-numeric, so the API can answer 400 rather than 500.
    """

    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object of feature name to number")

    missing = [name for name in bundle.feature_columns if name not in payload]
    if missing:
        raise ValueError(f"missing required features: {', '.join(sorted(missing))}")

    cleaned: dict[str, float] = {}
    for name in bundle.feature_columns:
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"feature '{name}' must be numeric, got {type(value).__name__}")
        cleaned[name] = float(value)
    return cleaned


def predict_one(payload: dict[str, Any], bundle: ServingBundle | None = None) -> dict[str, Any]:
    """Score a single observation and return the stakeholder-facing fields.

    The elevated-risk figure is a ranking and decision score, not a calibrated
    probability, and the response says so explicitly so a downstream consumer
    cannot quietly reinterpret it.
    """

    resolved = bundle or load_model()
    if resolved is None:
        raise FileNotFoundError(
            f"no serving model at {model_path()}; run `python run_pipeline.py` first"
        )

    features = validate_features(payload, resolved)
    frame = pd.DataFrame([features], columns=resolved.feature_columns)
    predicted_vol = float(resolved.regression_model.predict(frame)[0])
    score = float(resolved.classification_model.predict_proba(frame)[0, 1])
    elevated = score >= RISK_SCORE_CUTOFF
    return {
        "predicted_next_five_day_vol": predicted_vol,
        "elevated_risk_score": score,
        "risk_score_cutoff": RISK_SCORE_CUTOFF,
        "risk_threshold_annualized_vol": resolved.risk_threshold,
        "risk_classification": "elevated" if elevated else "normal",
        "score_interpretation": ("Ranking and decision score, not a calibrated event probability."),
        "model_fit_end": resolved.fit_metadata.get("fit_end"),
    }
