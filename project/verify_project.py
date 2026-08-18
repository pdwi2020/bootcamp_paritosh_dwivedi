"""Compact final verification for the Weekly ETF Risk Monitor."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import joblib
import pandas as pd

from src.storage import validate_manifest


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "requirements.txt",
        ROOT / ".env.example",
        ROOT / "notebooks/project_pipeline.ipynb",
        ROOT / "notebooks/python_fundamentals_summary.ipynb",
        ROOT / "reports/metrics.json",
        ROOT / "reports/final_summary.md",
        ROOT / "reports/stakeholder_presentation.pptx",
        ROOT / "reports/feature_window_sensitivity.csv",
        ROOT / "presentation/build_deck.mjs",
        ROOT / "model/risk_models.joblib",
        ROOT / "data/processed/spy_model_dataset.parquet",
    ]
    missing = [str(path.relative_to(REPO)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    metrics = json.loads((ROOT / "reports/metrics.json").read_text(encoding="utf-8"))
    if metrics.get("sole_author") != "Paritosh Dwivedi":
        raise SystemExit("Sole-author metadata is missing or incorrect")

    data = pd.read_parquet(ROOT / "data/processed/spy_model_dataset.parquet")
    if data.empty or data["date"].duplicated().any():
        raise SystemExit("Processed dataset is empty or contains duplicate dates")

    models = metrics.get("models", {})
    if models.get("embargo_rows") != 5:
        raise SystemExit("Evaluation must use a five-session embargo")
    if models.get("train_end", "") >= models.get("test_start", ""):
        raise SystemExit("Evaluation training dates overlap the test period")
    if "production_refit" not in models:
        raise SystemExit("Production refit metadata is missing")
    snapshot = metrics.get("latest_risk_snapshot", {})
    if "elevated_risk_score" not in snapshot or "elevated_risk_probability" in snapshot:
        raise SystemExit("Current classifier output must be documented as a risk score")

    predictions = pd.read_csv(ROOT / "reports/model_predictions.csv")
    required_prediction_columns = {
        "actual_next_five_day_vol",
        "ridge_predicted_vol",
        "actual_elevated_risk",
        "predicted_elevated_risk",
        "elevated_risk_score",
    }
    if not required_prediction_columns.issubset(predictions.columns):
        raise SystemExit("Prediction artifact does not use the reviewed five-day score schema")

    model_artifact = joblib.load(ROOT / "model/risk_models.joblib")
    if model_artifact.get("fit_metadata", {}).get("fit_rows") != models["production_refit"].get(
        "fit_rows"
    ):
        raise SystemExit("Saved production model metadata does not match metrics.json")
    if model_artifact.get("risk_score_cutoff") != snapshot.get("risk_score_cutoff"):
        raise SystemExit("Saved model and current decision rule disagree")

    raw_files = sorted((ROOT / "data/raw").glob("spy_daily_*.csv"))
    if not raw_files:
        raise SystemExit("No immutable raw snapshot is available")
    raw_file = raw_files[-1]
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
    excluded_directories = {".git", ".venv", ".pytest_cache", "__pycache__", "class_materials", "tmp"}
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
                "sole_author": metrics["sole_author"],
                "processed_rows": int(len(data)),
                "duplicate_dates": int(data["date"].duplicated().sum()),
                "raw_manifest": "passed",
                "evaluation_embargo_sessions": models["embargo_rows"],
                "notebooks": notebook_summaries,
                "presentation_author": creator,
                "secret_scan": "passed",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
