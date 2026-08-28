# Orchestration plan

**Author:** Paritosh Dwivedi

How this project decomposes into tasks, what depends on what, and what I would
automate now versus leave manual.

## Task list

Real paths in this repository, not placeholders.

| # | Task | Input | Output | Implemented in |
|---|---|---|---|---|
| 1 | Ingest | yfinance API (`PRIMARY_TICKER`, `DATA_START`) | `data/raw/spy_daily_<UTC>.csv` + `.manifest.json` | `src/ingestion.py` |
| 2 | Validate | newest raw CSV | pass/fail report embedded in `reports/metrics.json` | `src/validation.py` |
| 3 | Clean | newest raw CSV | `data/processed/spy_clean.parquet` | `src/cleaning.py`, `src/run_step.py::step_clean` |
| 4 | Features | `spy_clean.parquet` | `data/processed/spy_model_dataset.parquet` | `src/features.py`, `src/run_step.py::step_features` |
| 5 | Model | `spy_model_dataset.parquet` | `model/risk_models.joblib`, `model/model.pkl`, `reports/model_predictions.csv` | `src/modeling.py`, `src/serving.py` |
| 6 | Evaluate | predictions | sensitivity CSVs, uncertainty block in `reports/metrics.json` | `src/evaluation.py`, `src/uncertainty.py` |
| 7 | Report | `reports/metrics.json` | `reports/final_summary.md`, `reports/images/*.png` | `src/plotting.py`, `run_pipeline.py` |
| 8 | Present | `reports/metrics.json`, figures | `reports/stakeholder_presentation.pptx` | `src/presentation.py` |

## Dependencies

```
1 ingest ─→ 2 validate ─→ 3 clean ─→ 4 features ─→ 5 model ─→ 6 evaluate ─→ 7 report ─→ 8 present
```

A strict chain, so the DAG is a path. Tasks 7 and 8 are the only pair that could
run in parallel: both consume `reports/metrics.json` and neither writes an input
of the other. Nothing else parallelises, because each task consumes the previous
task's artifact.

## Idempotency

| Task | Idempotent | Why |
|---|---|---|
| 1 Ingest | **No** | Each run writes a new timestamped snapshot. Deliberate: raw data is immutable evidence, so re-running adds a record rather than replacing one. |
| 2 Validate | Yes | Pure read; no writes. |
| 3 Clean | Yes | Deterministic transform to a fixed path. Verified: `--force` rebuild is byte-identical. |
| 4 Features | Yes | Same, verified byte-identical. Outlier parameters come from the production refit so this cannot diverge from `run_pipeline.py`. |
| 5 Model | Yes | Fixed random seeds and a fixed split; overwrites deterministically. |
| 6–8 Evaluate, report, present | Yes | Regenerated from `metrics.json`. The `.pptx` is not byte-reproducible because the zip container stores a timestamp, but its content is. |

## Logging and checkpoints

Checkpoints are the two processed Parquet files, which is where recomputation is
most expensive relative to its value. `src/run_step.py` skips a task whose
checkpoint exists unless `--force` is passed, so a failure at task 5 does not
recompute tasks 3 and 4.

Logging is at task boundaries rather than inside loops: task name, row counts in
and out, and the artifact written. That makes a failure locatable to a task
without drowning the log. `src/run_step.py` and `app.py` both use the stdlib
`logging` module at INFO, with `--verbose` for DEBUG.

## Failure points and retry policy

| Failure | Likelihood | Response |
|---|---|---|
| Provider unavailable or rate-limited | Most likely | Retry three times with exponential backoff, then fall back to the newest cached snapshot — already implemented, `metrics.json` records `pipeline_mode: cached_raw_input`. |
| Schema drift | Occasional | Fail fast at task 2. Never clean data whose shape you have not confirmed. |
| Missing trading day | Occasional | Tolerated; rolling windows are computed on the observed index. |
| Model divergence | Rare | Not a pipeline failure. Caught by monitoring, handled by the fallback in `docs/monitoring_plan.md`. |

## Automate now versus keep manual

**Automate now:** tasks 3 through 8. They are deterministic, fast (the full chain
runs in well under a minute), and already reachable through one command.

**Keep manual:** task 1, and the decision to promote a refit into
`model/model.pkl`. Ingestion writes a new immutable snapshot each time, so
scheduling it unattended would accumulate files with no one reading the
validation output. Promotion is a judgement call that should stay with a person.

**Right-sizing.** This does not need Airflow or Prefect. The chain is linear,
runs in under a minute, and has one consumer. A Makefile target plus
`src/run_step.py` delivers the useful part of orchestration — explicit inputs and
outputs, idempotency, checkpoints and logging — without a scheduler to operate.
