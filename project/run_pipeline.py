"""Run the complete Weekly ETF Risk Monitor pipeline."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.cleaning import clean_market_data
from src.config import Settings, get_settings
from src.features import FEATURE_COLUMNS, build_features
from src.ingestion import acquire_market_data
from src.modeling import fit_risk_models, risk_threshold_sensitivity
from src.outliers import add_return_outlier_flag
from src.plotting import create_all_figures
from src.storage import build_manifest, read_dataframe, write_dataframe, write_json
from src.utils import safe_timestamp
from src.validation import validate_market_data


def _latest_raw_file(settings: Settings) -> Path | None:
    files = sorted(settings.raw_dir.glob(f"{settings.ticker.lower()}_daily_*.csv"))
    return files[-1] if files else None


def _load_or_acquire(settings: Settings, refresh: bool) -> tuple[pd.DataFrame, dict, Path]:
    cached = _latest_raw_file(settings)
    if cached is not None and not refresh:
        frame = read_dataframe(cached)
        manifest_path = cached.with_suffix(".manifest.json")
        metadata = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {"provider": "cached", "file": cached.name}
        )
        metadata["pipeline_mode"] = "cached_raw_input"
        validate_market_data(frame)
        return frame, metadata, cached

    frame, metadata = acquire_market_data(
        settings.ticker,
        settings.start_date,
        settings.end_date,
        provider=settings.provider,
        alpha_vantage_key=settings.alpha_vantage_key,
    )
    raw_path = settings.raw_dir / (
        f"{settings.ticker.lower()}_daily_{safe_timestamp()}.csv"
    )
    write_dataframe(frame, raw_path)
    manifest = build_manifest(raw_path, metadata)
    write_json(manifest, raw_path.with_suffix(".manifest.json"))
    return frame, manifest, raw_path


def _latest_risk_snapshot(feature_frame: pd.DataFrame, model_bundle) -> dict:
    latest = feature_frame.dropna(subset=["date"]).iloc[-1]
    features = latest[FEATURE_COLUMNS].to_frame().T
    predicted_vol = float(np.clip(model_bundle.regression_model.predict(features)[0], 0.0, None))
    probability = float(model_bundle.classification_model.predict_proba(features)[0, 1])
    threshold = float(model_bundle.results["risk_threshold_annualized_vol"])
    classification = "elevated" if probability >= 0.50 else "normal"
    return {
        "as_of_date": latest["date"].date().isoformat(),
        "adjusted_close": float(latest["adjusted_close"]),
        "rolling_vol_20": float(latest["rolling_vol_20"]),
        "predicted_next_week_vol": predicted_vol,
        "elevated_risk_probability": probability,
        "risk_threshold_annualized_vol": threshold,
        "risk_classification": classification,
        "decision_language": (
            "Investigate reducing exposure or adding a hedge before the next weekly review."
            if classification == "elevated"
            else "The model does not flag elevated risk; maintain exposure only within the existing mandate."
        ),
    }


def _write_summary(metrics: dict, path: Path, ticker: str) -> None:
    snapshot = metrics["latest_risk_snapshot"]
    regression = metrics["models"]["regression"]
    classification = metrics["models"]["classification"]
    lines = [
        f"# {ticker} Weekly Risk Monitor - Results Summary",
        "",
        "**Sole author:** Paritosh Dwivedi",
        "",
        f"**Data through:** {snapshot['as_of_date']}",
        "",
        "## Current decision signal",
        "",
        f"- Risk classification: **{snapshot['risk_classification'].upper()}**",
        f"- Predicted next-week annualized volatility: **{snapshot['predicted_next_week_vol']:.1%}**",
        f"- Elevated-risk probability: **{snapshot['elevated_risk_probability']:.1%}**",
        f"- Training-derived risk threshold: **{snapshot['risk_threshold_annualized_vol']:.1%}**",
        f"- Decision interpretation: {snapshot['decision_language']}",
        "",
        "## Out-of-sample evidence",
        "",
        f"- Ridge MAE: {regression['ridge']['mae']:.4f}",
        f"- Recent-volatility baseline MAE: {regression['recent_volatility_baseline']['mae']:.4f}",
        f"- Ridge MAE improvement versus recent-volatility baseline: {regression['ridge_mae_improvement_vs_recent']:.1%}",
        f"- Elevated-risk balanced accuracy: {classification['logistic']['balanced_accuracy']:.1%}",
        f"- Elevated-risk recall: {classification['logistic']['recall']:.1%}",
        "",
        "## Interpretation limits",
        "",
        "This is a decision-support signal, not a trading instruction. Performance is historical and may change under new market regimes. Provider revisions, threshold choice, feature-window choice, and extreme events can materially affect the result.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, refresh: bool = False) -> dict:
    """Execute acquisition through stakeholder artifacts and return metrics."""

    settings = get_settings()
    raw_frame, acquisition_metadata, raw_path = _load_or_acquire(settings, refresh)
    raw_validation = validate_market_data(raw_frame)
    clean_frame, cleaning_report = clean_market_data(raw_frame)
    outlier_frame = add_return_outlier_flag(clean_frame)
    feature_frame = build_features(outlier_frame, horizon=5)

    clean_path = settings.processed_dir / f"{settings.ticker.lower()}_clean.parquet"
    model_data_path = settings.processed_dir / f"{settings.ticker.lower()}_model_dataset.parquet"
    write_dataframe(clean_frame, clean_path)
    write_dataframe(feature_frame, model_data_path)

    model_bundle = fit_risk_models(
        feature_frame,
        test_fraction=settings.test_fraction,
        risk_quantile=settings.risk_quantile,
    )
    prediction_path = settings.reports_dir / "model_predictions.csv"
    write_dataframe(model_bundle.predictions, prediction_path)
    sensitivity = risk_threshold_sensitivity(
        feature_frame,
        test_fraction=settings.test_fraction,
    )
    sensitivity_path = settings.reports_dir / "risk_threshold_sensitivity.csv"
    write_dataframe(pd.DataFrame(sensitivity), sensitivity_path)

    model_path = settings.model_dir / "risk_models.joblib"
    joblib.dump(
        {
            "regression_model": model_bundle.regression_model,
            "classification_model": model_bundle.classification_model,
            "feature_columns": FEATURE_COLUMNS,
            "risk_threshold": model_bundle.results["risk_threshold_annualized_vol"],
        },
        model_path,
    )

    figure_paths = create_all_figures(
        feature_frame,
        model_bundle.predictions,
        settings.images_dir,
        threshold=model_bundle.results["risk_threshold_annualized_vol"],
        ticker=settings.ticker,
    )

    metrics = {
        "project": "Weekly ETF Risk Monitor",
        "sole_author": "Paritosh Dwivedi",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": settings.ticker,
        "data": {
            "raw_file": str(raw_path.relative_to(settings.project_root)),
            "processed_clean_file": str(clean_path.relative_to(settings.project_root)),
            "model_dataset_file": str(model_data_path.relative_to(settings.project_root)),
            "rows_raw": int(len(raw_frame)),
            "rows_model_dataset": int(len(feature_frame)),
            "date_start": clean_frame["date"].min().date().isoformat(),
            "date_end": clean_frame["date"].max().date().isoformat(),
            "acquisition": acquisition_metadata,
            "raw_validation": raw_validation,
            "cleaning": cleaning_report,
            "return_outliers_flagged": int(outlier_frame["return_outlier_flag"].sum()),
        },
        "models": model_bundle.results,
        "sensitivity": sensitivity,
        "latest_risk_snapshot": _latest_risk_snapshot(feature_frame, model_bundle),
        "artifacts": {
            "predictions": str(prediction_path.relative_to(settings.project_root)),
            "sensitivity": str(sensitivity_path.relative_to(settings.project_root)),
            "model": str(model_path.relative_to(settings.project_root)),
            "figures": [str(path.relative_to(settings.project_root)) for path in figure_paths],
        },
    }
    metrics_path = settings.reports_dir / "metrics.json"
    write_json(metrics, metrics_path)
    _write_summary(metrics, settings.reports_dir / "final_summary.md", settings.ticker)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Acquire a new raw file instead of using the latest validated cache.",
    )
    args = parser.parse_args()
    metrics = run(refresh=args.refresh)
    snapshot = metrics["latest_risk_snapshot"]
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
