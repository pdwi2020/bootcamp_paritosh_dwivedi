"""Compact final verification for the Weekly ETF Risk Monitor."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


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
                "secret_scan": "passed",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
