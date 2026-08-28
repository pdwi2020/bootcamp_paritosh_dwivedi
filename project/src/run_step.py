"""Run one pipeline task from the command line, with logging and checkpoints.

Stage 15 deliverable. ``notebooks/project_pipeline.ipynb`` runs the whole chain;
this module lets a single task run on its own so a failure can be retried
without recomputing everything before it.

Every task is **idempotent**: it writes a deterministic output path, so re-running
overwrites rather than appends or duplicates.

Usage
-----
::

    python -m src.run_step --list
    python -m src.run_step clean
    python -m src.run_step features --force
    python -m src.run_step score
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.cleaning import clean_market_data
from src.config import Settings, get_settings
from src.features import build_features
from src.modeling import fit_production_models
from src.outliers import add_return_outlier_flag
from src.serving import load_model, predict_one
from src.storage import read_dataframe, write_dataframe

logger = logging.getLogger("risk_monitor.step")

CLEAN_FILE = "spy_clean.parquet"
FEATURES_FILE = "spy_model_dataset.parquet"


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        stream=sys.stdout,
    )


def _latest_raw(settings: Settings) -> Path:
    """Return the newest raw snapshot, or fail with an actionable message."""

    candidates = sorted(settings.raw_dir.glob(f"{settings.ticker.lower()}_daily_*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"no raw snapshot in {settings.raw_dir}; run `python run_pipeline.py --refresh` first"
        )
    return candidates[-1]


def step_clean(settings: Settings, *, force: bool = False) -> Path:
    """Raw snapshot to validated clean frame. Checkpoint: data/processed/spy_clean.parquet."""

    target = settings.processed_dir / CLEAN_FILE
    if target.exists() and not force:
        logger.info("checkpoint hit, skipping clean: %s (use --force to rebuild)", target.name)
        return target

    source = _latest_raw(settings)
    logger.info("reading raw snapshot %s", source.name)
    raw = read_dataframe(source)
    cleaned, report = clean_market_data(raw)
    logger.info(
        "cleaned %d rows -> %d rows (%d removed)",
        report.get("rows_in", len(raw)),
        len(cleaned),
        report.get("rows_in", len(raw)) - len(cleaned),
    )
    write_dataframe(cleaned, target)
    logger.info("wrote checkpoint %s", target)
    return target


def step_features(settings: Settings, *, force: bool = False) -> Path:
    """Clean frame to model dataset. Checkpoint: data/processed/spy_model_dataset.parquet."""

    target = settings.processed_dir / FEATURES_FILE
    if target.exists() and not force:
        logger.info("checkpoint hit, skipping features: %s (use --force to rebuild)", target.name)
        return target

    clean_path = settings.processed_dir / CLEAN_FILE
    if not clean_path.exists():
        raise FileNotFoundError(f"{clean_path} missing; run the 'clean' step first")

    cleaned = read_dataframe(clean_path)
    logger.info("building features from %d clean rows", len(cleaned))
    # Mirror run_pipeline exactly: the outlier parameters come from the production
    # refit, not from a separate fit here. Diverging would make this step write a
    # different dataset than the pipeline and quietly break metrics reproducibility.
    engineered = build_features(cleaned, horizon=5)
    production = fit_production_models(engineered, risk_quantile=settings.risk_quantile)
    engineered = add_return_outlier_flag(engineered, parameters=production.outlier_parameters)
    flagged = int(engineered["return_outlier_flag"].sum())
    logger.info("feature frame %d rows, %d return outliers flagged", len(engineered), flagged)
    write_dataframe(engineered, target)
    logger.info("wrote checkpoint %s", target)
    return target


def step_score(settings: Settings, *, force: bool = False) -> dict:
    """Score the most recent observation with the saved serving model."""

    del force  # scoring is always cheap; no checkpoint to skip
    bundle = load_model(settings.model_dir)
    if bundle is None:
        raise FileNotFoundError("no model/model.pkl; run `python run_pipeline.py` first")

    features_path = settings.processed_dir / FEATURES_FILE
    if not features_path.exists():
        raise FileNotFoundError(f"{features_path} missing; run the 'features' step first")

    frame = read_dataframe(features_path)
    usable = frame[bundle.feature_columns].dropna()
    if usable.empty:
        raise ValueError("no complete feature rows available to score")

    payload = {name: float(value) for name, value in usable.iloc[-1].items()}
    result = predict_one(payload, bundle)
    logger.info(
        "latest signal: %s (score %.4f, predicted vol %.4f)",
        result["risk_classification"],
        result["elevated_risk_score"],
        result["predicted_next_five_day_vol"],
    )
    return result


STEPS = {
    "clean": step_clean,
    "features": step_features,
    "score": step_score,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", nargs="?", choices=sorted(STEPS), help="task to run")
    parser.add_argument(
        "--force", action="store_true", help="rebuild even if the checkpoint exists"
    )
    parser.add_argument("--verbose", action="store_true", help="debug-level logging")
    parser.add_argument("--list", action="store_true", help="list available tasks and exit")
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)

    if args.list or args.step is None:
        print("available steps (run in this order):")
        for name, func in STEPS.items():
            print(f"  {name:<10} {func.__doc__.splitlines()[0]}")
        return 0

    settings = get_settings()
    settings.ensure_directories()
    try:
        STEPS[args.step](settings, force=args.force)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("step '%s' failed: %s", args.step, exc)
        return 1
    logger.info("step '%s' completed", args.step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
