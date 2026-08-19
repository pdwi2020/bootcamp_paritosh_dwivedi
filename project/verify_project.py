"""Compact final verification for the Weekly ETF Risk Monitor."""

from __future__ import annotations

import json
import math
import re
import warnings
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning

from src.evaluation import classification_metrics, percentage_improvement, regression_metrics
from src.features import FEATURE_COLUMNS
from src.outliers import ReturnOutlierParameters, score_return_outliers
from src.storage import validate_manifest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def _resolve_declared_file(project_root: Path, value: object, label: str) -> Path:
    """Resolve one required metrics path without allowing absolute or escaping paths."""

    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Declared {label} artifact path is missing or invalid")
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise SystemExit(f"Declared {label} artifact path must be relative: {value}")

    resolved_root = project_root.resolve()
    resolved_path = (resolved_root / relative_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise SystemExit(
            f"Declared {label} artifact escapes the project directory: {value}"
        ) from error
    if not resolved_path.is_file():
        raise SystemExit(f"Declared {label} artifact is missing: {value}")
    return resolved_path


def _verify_declared_artifacts(metrics: dict, project_root: Path = ROOT) -> dict[str, Path]:
    """Resolve every data, model, report, and figure path declared in metrics."""

    data = metrics.get("data")
    artifacts = metrics.get("artifacts")
    if not isinstance(data, dict) or not isinstance(artifacts, dict):
        raise SystemExit("Metrics must declare data and artifact paths")

    declared = {
        "raw_file": data.get("raw_file"),
        "processed_clean_file": data.get("processed_clean_file"),
        "model_dataset_file": data.get("model_dataset_file"),
        "predictions": artifacts.get("predictions"),
        "risk_threshold_sensitivity": artifacts.get("risk_threshold_sensitivity"),
        "feature_window_sensitivity": artifacts.get("feature_window_sensitivity"),
        "model": artifacts.get("model"),
    }
    resolved = {
        label: _resolve_declared_file(project_root, value, label)
        for label, value in declared.items()
    }

    figures = artifacts.get("figures")
    if not isinstance(figures, list) or not figures:
        raise SystemExit("Metrics must declare at least one figure artifact")
    for index, figure in enumerate(figures):
        resolved[f"figure_{index}"] = _resolve_declared_file(
            project_root,
            figure,
            f"figure_{index}",
        )
    return resolved


def _load_model_artifact(model_path: Path) -> dict:
    """Load the model only when its scikit-learn version matches the runtime."""

    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        try:
            return joblib.load(model_path)
        except InconsistentVersionWarning as error:
            raise SystemExit(
                "Saved model uses an incompatible scikit-learn version; rerun make pipeline"
            ) from error


def _assert_close(actual: float, expected: float, label: str) -> None:
    """Fail verification when two persisted numeric values disagree."""

    actual_value = float(actual)
    expected_value = float(expected)
    if math.isnan(actual_value) and math.isnan(expected_value):
        return
    if not math.isclose(actual_value, expected_value, rel_tol=1e-10, abs_tol=1e-12):
        raise SystemExit(
            f"Artifact consistency check failed for {label}: "
            f"calculated {actual_value}, stored {expected_value}"
        )


def _verify_prediction_metrics(metrics: dict, predictions: pd.DataFrame) -> None:
    """Recompute the published holdout metrics from the prediction artifact."""

    models = metrics["models"]
    required_columns = {
        "date",
        "actual_next_five_day_vol",
        "recent_vol_baseline",
        "ridge_predicted_vol",
        "actual_elevated_risk",
        "predicted_elevated_risk",
        "elevated_risk_score",
    }
    if not required_columns.issubset(predictions.columns):
        raise SystemExit("Prediction artifact does not use the reviewed five-day score schema")

    dates = pd.to_datetime(predictions["date"], errors="coerce")
    if dates.isna().any():
        raise SystemExit("Prediction artifact contains an invalid date")
    if dates.duplicated().any():
        raise SystemExit("Prediction artifact contains duplicate dates")
    if not dates.is_monotonic_increasing:
        raise SystemExit("Prediction artifact dates are not chronological")
    if len(predictions) != models["test_rows"]:
        raise SystemExit("Prediction row count does not match metrics.json")
    if dates.min().date().isoformat() != models["test_start"]:
        raise SystemExit("Prediction start date does not match metrics.json")
    if dates.max().date().isoformat() != models["test_end"]:
        raise SystemExit("Prediction end date does not match metrics.json")

    expected_actual_class = (
        predictions["actual_next_five_day_vol"] >= models["risk_threshold_annualized_vol"]
    ).astype(int)
    if not expected_actual_class.equals(predictions["actual_elevated_risk"].astype(int)):
        raise SystemExit("Prediction labels do not match the training-derived risk threshold")
    cutoff = models["classification"]["risk_score_cutoff"]
    expected_prediction = (predictions["elevated_risk_score"] >= cutoff).astype(int)
    if not expected_prediction.equals(predictions["predicted_elevated_risk"].astype(int)):
        raise SystemExit("Prediction labels do not match the published risk-score cutoff")

    calculated_ridge = regression_metrics(
        predictions["actual_next_five_day_vol"], predictions["ridge_predicted_vol"]
    )
    regression = models["regression"]
    for name, value in calculated_ridge.items():
        _assert_close(value, regression["ridge"][name], f"ridge {name}")

    calculated_baseline = regression_metrics(
        predictions["actual_next_five_day_vol"], predictions["recent_vol_baseline"]
    )
    for name, value in calculated_baseline.items():
        _assert_close(
            value,
            regression["recent_volatility_baseline"][name],
            f"recent-volatility baseline {name}",
        )

    calculated_improvement = percentage_improvement(
        calculated_ridge["mae"], calculated_baseline["mae"]
    )
    _assert_close(
        calculated_improvement,
        regression["ridge_mae_improvement_vs_recent"],
        "Ridge MAE improvement versus recent-volatility baseline",
    )

    calculated_classification = classification_metrics(
        predictions["actual_elevated_risk"],
        predictions["predicted_elevated_risk"],
        predictions["elevated_risk_score"],
    )
    stored_classification = models["classification"]["logistic"]
    for name, value in calculated_classification.items():
        _assert_close(value, stored_classification[name], f"logistic {name}")

    classification = models["classification"]
    _assert_close(
        predictions["actual_elevated_risk"].mean(),
        classification["test_elevated_rate"],
        "test elevated rate",
    )
    caught = int(
        (
            (predictions["actual_elevated_risk"] == 1)
            & (predictions["predicted_elevated_risk"] == 1)
        ).sum()
    )
    missed = int(
        (
            (predictions["actual_elevated_risk"] == 1)
            & (predictions["predicted_elevated_risk"] == 0)
        ).sum()
    )
    if caught != classification["elevated_windows_caught"]:
        raise SystemExit("Caught elevated-window count does not match predictions")
    if missed != classification["elevated_windows_missed"]:
        raise SystemExit("Missed elevated-window count does not match predictions")


def _verify_purged_split(data: pd.DataFrame, models: dict) -> None:
    """Confirm the saved evaluation dates contain the stated target embargo."""

    labeled = (
        data.dropna(subset=["target_next_week_vol"]).sort_values("date").reset_index(drop=True)
    )
    train_matches = labeled.index[labeled["date"].eq(pd.Timestamp(models["train_end"]))]
    test_matches = labeled.index[labeled["date"].eq(pd.Timestamp(models["test_start"]))]
    if len(train_matches) != 1 or len(test_matches) != 1:
        raise SystemExit("Evaluation boundary dates are missing from the model dataset")
    actual_gap = int(test_matches[0] - train_matches[0] - 1)
    if actual_gap != models["embargo_rows"]:
        raise SystemExit(
            f"Model dataset contains a {actual_gap}-row embargo; "
            f"metrics.json reports {models['embargo_rows']}"
        )


def _verify_current_snapshot(metrics: dict, data: pd.DataFrame, model_artifact: dict) -> None:
    """Recompute the latest decision signal from the persisted production model."""

    models = metrics["models"]
    snapshot = metrics["latest_risk_snapshot"]
    if model_artifact.get("feature_columns") != FEATURE_COLUMNS:
        raise SystemExit("Saved model feature columns do not match the reviewed interface")
    if model_artifact.get("feature_columns") != models.get("feature_columns"):
        raise SystemExit("Saved model feature columns do not match metrics.json")

    model_metadata = model_artifact.get("fit_metadata", {})
    production_metadata = models.get("production_refit", {})
    for key, value in model_metadata.items():
        if production_metadata.get(key) != value:
            raise SystemExit(f"Saved production model metadata disagrees on {key}")

    latest = data.dropna(subset=["date"]).sort_values("date").iloc[-1].copy()
    outlier_parameters = ReturnOutlierParameters(**model_artifact["outlier_parameters"])
    outlier_score = score_return_outliers(pd.Series([latest["log_return"]]), outlier_parameters)
    latest["return_outlier_flag"] = int(outlier_score["return_outlier_flag"].iloc[0])
    feature_row = latest[FEATURE_COLUMNS].to_frame().T
    predicted_vol = float(
        np.clip(model_artifact["regression_model"].predict(feature_row)[0], 0.0, None)
    )
    risk_score = float(model_artifact["classification_model"].predict_proba(feature_row)[0, 1])
    cutoff = float(model_artifact["risk_score_cutoff"])
    classification = "elevated" if risk_score >= cutoff else "normal"

    if latest["date"].date().isoformat() != snapshot["as_of_date"]:
        raise SystemExit("Current snapshot date does not match the model dataset")
    _assert_close(latest["adjusted_close"], snapshot["adjusted_close"], "latest price")
    _assert_close(latest["rolling_vol_20"], snapshot["rolling_vol_20"], "latest actual volatility")
    _assert_close(predicted_vol, snapshot["predicted_next_five_day_vol"], "latest forecast")
    _assert_close(risk_score, snapshot["elevated_risk_score"], "latest risk score")
    _assert_close(cutoff, snapshot["risk_score_cutoff"], "latest score cutoff")
    _assert_close(
        cutoff,
        models["classification"]["risk_score_cutoff"],
        "model score cutoff",
    )
    _assert_close(
        model_artifact["risk_threshold"],
        snapshot["risk_threshold_annualized_vol"],
        "latest risk threshold",
    )
    _assert_close(
        model_artifact["risk_threshold"],
        production_metadata["risk_threshold_annualized_vol"],
        "production risk threshold",
    )
    if classification != snapshot["risk_classification"]:
        raise SystemExit("Current risk classification does not match the saved model")
    if snapshot.get("model_fit_scope") != model_metadata:
        raise SystemExit("Current snapshot fit metadata does not match the saved model")


def main() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "requirements.txt",
        ROOT / "requirements.lock.txt",
        ROOT / ".env.example",
        ROOT / "notebooks/project_pipeline.ipynb",
        ROOT / "notebooks/python_fundamentals_summary.ipynb",
        ROOT / "reports/metrics.json",
        ROOT / "reports/final_summary.md",
        ROOT / "reports/model_predictions.csv",
        ROOT / "reports/stakeholder_presentation.pptx",
        ROOT / "reports/risk_threshold_sensitivity.csv",
        ROOT / "reports/feature_window_sensitivity.csv",
        ROOT / "build_presentation.py",
        ROOT / "src/presentation.py",
        ROOT / "model/risk_models.joblib",
        ROOT / "data/processed/spy_clean.parquet",
        ROOT / "data/processed/spy_model_dataset.parquet",
        ROOT / "Makefile",
        ROOT / "pyproject.toml",
    ]
    missing = [str(path.relative_to(REPO)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    metrics = json.loads((ROOT / "reports/metrics.json").read_text(encoding="utf-8"))
    declared_artifacts = _verify_declared_artifacts(metrics)
    if metrics.get("author") != "Paritosh Dwivedi":
        raise SystemExit("Author metadata is missing or incorrect")

    data = pd.read_parquet(declared_artifacts["model_dataset_file"])
    if data.empty or data["date"].duplicated().any():
        raise SystemExit("Processed dataset is empty or contains duplicate dates")

    models = metrics.get("models", {})
    if models.get("embargo_rows") != 5:
        raise SystemExit("Evaluation must use a five-session embargo")
    if "production_refit" not in models:
        raise SystemExit("Production refit metadata is missing")
    snapshot = metrics.get("latest_risk_snapshot", {})
    if "elevated_risk_score" not in snapshot or "elevated_risk_probability" in snapshot:
        raise SystemExit("Current classifier output must be documented as a risk score")

    predictions = pd.read_csv(declared_artifacts["predictions"])
    _verify_prediction_metrics(metrics, predictions)
    _verify_purged_split(data, models)

    model_artifact = _load_model_artifact(declared_artifacts["model"])
    _verify_current_snapshot(metrics, data, model_artifact)

    raw_file = declared_artifacts["raw_file"]
    manifest_path = raw_file.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise SystemExit(f"Raw manifest is missing for {raw_file.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(raw_file, manifest)

    notebook_summaries: dict[str, int] = {}
    for notebook_path in (
        ROOT / "notebooks/project_pipeline.ipynb",
        ROOT / "notebooks/python_fundamentals_summary.ipynb",
    ):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        kernel_name = notebook.get("metadata", {}).get("kernelspec", {}).get("name")
        if kernel_name != "python3":
            raise SystemExit(f"Notebook must use the portable python3 kernel: {notebook_path.name}")
        code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
        if any(cell.get("execution_count") is None for cell in code_cells):
            raise SystemExit(f"Notebook has unexecuted code cells: {notebook_path.name}")
        errors = [
            output
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        if errors:
            raise SystemExit(f"Notebook contains execution errors: {notebook_path.name}")
        notebook_summaries[notebook_path.name] = len(code_cells)

    with zipfile.ZipFile(ROOT / "reports/stakeholder_presentation.pptx") as archive:
        core = ElementTree.fromstring(archive.read("docProps/core.xml"))
        namespace = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
        }
        creator = core.findtext("dc:creator", namespaces=namespace)
        modified_by = core.findtext("cp:lastModifiedBy", namespaces=namespace)
        if creator != "Paritosh Dwivedi" or modified_by != "Paritosh Dwivedi":
            raise SystemExit("Presentation core authorship metadata is incorrect")

    secret_patterns = [
        re.compile(r"(?m)^ALPHAVANTAGE_API_KEY[ \t]*=[ \t]*[^ \t\r\n#]+"),
        re.compile(r"apikey=[A-Za-z0-9]{8,}"),
    ]
    scanned = []
    excluded_directories = {
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        "class_materials",
        "tmp",
    }
    for path in REPO.rglob("*"):
        if not path.is_file() or excluded_directories.intersection(path.parts):
            continue
        if path.suffix.lower() not in {".py", ".md", ".txt", ".example", ".ipynb", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in secret_patterns:
            if pattern.search(text):
                scanned.append(str(path.relative_to(REPO)))
    if scanned:
        raise SystemExit(f"Possible secrets detected in: {sorted(set(scanned))}")

    print(
        json.dumps(
            {
                "required_artifacts": "passed",
                "author": metrics["author"],
                "processed_rows": int(len(data)),
                "duplicate_dates": int(data["date"].duplicated().sum()),
                "raw_manifest": "passed",
                "evaluation_embargo_sessions": models["embargo_rows"],
                "prediction_metrics": "passed",
                "current_model_snapshot": "passed",
                "notebooks": notebook_summaries,
                "presentation_author": creator,
                "secret_scan": "passed",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
