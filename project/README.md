# Weekly ETF Risk Monitor

**Sole author:** Paritosh Dwivedi
**Primary ETF:** SPY
**Decision cadence:** Weekly
**Data through:** August 17, 2026

## Project summary

This project builds a reproducible Python pipeline that helps a portfolio manager decide whether current SPY exposure merits additional investigation because near-term market risk appears elevated. It converts daily price and volume history into a five-trading-day volatility forecast, an elevated-risk probability, and a concise stakeholder interpretation.

The project is intentionally narrow. It supports one recurring risk-review decision for one liquid ETF. It does not execute trades, optimize a portfolio, claim causal effects, or guarantee future performance.

## Stakeholder and useful answer

The stakeholder and user is a portfolio manager who reviews ETF exposure weekly. The useful answer contains:

- predicted next-week annualized realized volatility;
- a normal-risk or elevated-risk classification;
- recent volatility, return, drawdown, and volume context;
- a plain-language decision interpretation;
- explicit assumptions, uncertainty, and model limitations.

## Current result

Using data through August 17, 2026, the model produces a **NORMAL** relative-risk classification:

- Predicted next-week annualized volatility: **11.1%**
- Elevated-risk probability: **22.2%**
- Training-derived elevated-risk threshold: **17.8%**
- Current 20-day annualized volatility: **13.5%**

Decision interpretation: the model does not flag elevated risk. Maintain exposure only within the existing mandate and continue monitoring; a normal flag is not a claim that the position is safe.

## Out-of-sample evidence

The split is chronological, with training observations preceding all test observations.

| Measure | Result |
|---|---:|
| Ridge regression MAE | 0.0402 |
| Recent-volatility baseline MAE | 0.0507 |
| Ridge MAE improvement vs recent-volatility baseline | 20.7% |
| Ridge regression R-squared | 0.335 |
| Elevated-risk balanced accuracy | 72.3% |
| Elevated-risk recall | 60.4% |
| Elevated-risk ROC AUC | 0.777 |

The classifier sacrifices overall accuracy to identify more elevated-risk periods. The prior baseline obtains high raw accuracy by predicting the majority class but has zero elevated-risk recall, so balanced accuracy and recall are more useful decision metrics.

## Repository structure

```text
project/
|-- data/
|   |-- raw/                  # immutable source snapshots and manifests
|   `-- processed/            # reproducible clean and feature datasets
|-- notebooks/
|   |-- python_fundamentals_summary.ipynb
|   `-- project_pipeline.ipynb
|-- src/
|   |-- config.py
|   |-- utils.py
|   |-- validation.py
|   |-- ingestion.py
|   |-- storage.py
|   |-- cleaning.py
|   |-- outliers.py
|   |-- features.py
|   |-- modeling.py
|   |-- evaluation.py
|   `-- plotting.py
|-- tests/
|-- docs/
|-- reports/
|   `-- images/
|-- model/
|-- run_pipeline.py
|-- verify_project.py
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Setup

From the repository root:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r project/requirements.txt
cp project/.env.example project/.env
```

The default `.env.example` uses SPY, a January 2010 start date, an August 17, 2026 end date, a 20% chronological test set, and a training-period 75th-percentile elevated-risk threshold.

An Alpha Vantage key is optional. If `ALPHAVANTAGE_API_KEY` is empty and `DATA_PROVIDER=auto`, the pipeline uses the course-supported yfinance fallback.

## Run

Use the latest validated immutable raw snapshot:

```bash
cd project
../.venv/bin/python run_pipeline.py
```

Acquire and preserve a new raw snapshot:

```bash
cd project
../.venv/bin/python run_pipeline.py --refresh
```

Run tests and final verification from the repository root:

```bash
.venv/bin/python -m pytest project/tests -q
cd project && ../.venv/bin/python verify_project.py
```

The cumulative notebook repeats the complete analysis in a stakeholder-readable sequence and has been executed top-to-bottom.

## Data acquisition and storage

The recorded raw dataset contains 4,180 daily SPY observations from January 4, 2010 through August 17, 2026. The successful refresh used yfinance. Each raw CSV is paired with a JSON manifest recording provider, symbol, requested dates, retrieval time, file size, limitations, and SHA-256 digest.

- `data/raw/` contains direct provider output after schema normalization only. Files are never overwritten or manually repaired.
- `data/processed/spy_clean.parquet` contains validated, typed observations.
- `data/processed/spy_model_dataset.parquet` contains reproducible features and targets.
- CSV is used for the transparent raw exchange artifact; Parquet preserves types and supports efficient analytical reloads.
- Paths are configured through `.env` and resolved with `pathlib`; no personal absolute path is required.

Provider data can be revised and provider availability can change. The manifest and immutable snapshot make the analyzed state auditable.

## Preprocessing and outliers

The cleaning stage:

- parses dates and numeric market fields;
- removes incomplete required rows;
- removes non-positive prices, negative volume, and internally inconsistent OHLC rows;
- retains the final provider record for duplicate dates;
- falls back to close when adjusted close is missing;
- revalidates the result before feature construction.

Extreme returns are detected with a robust median absolute-deviation score. Thirty-one observations were flagged in the current dataset. Plausible market extremes are retained because deleting them would understate the risk problem the project is designed to monitor.

## Features, targets, and models

All features use contemporaneous or past information:

- one-day and five-day lagged returns;
- trailing five-day return;
- five-day and twenty-day annualized volatility;
- twenty-day exponentially weighted volatility;
- short-to-long volatility ratio;
- drawdown from the running high;
- twenty-day standardized volume;
- retained-return outlier flag.

The regression target is annualized realized volatility over the next five trading days. Ridge regression is compared with recent-volatility and historical-mean baselines.

The elevated-risk label equals one when the regression target exceeds the training-period volatility quantile. Logistic regression uses class weighting because elevated-risk periods are less frequent. Threshold sensitivity is reported at the 70th, 75th, and 80th percentiles.

## Assumptions and risks

Key assumptions include a five-day weekly horizon, reliable provider history, and partial persistence of historical risk relationships. Important risks include provider schema changes, corporate-action revisions, regime change, false reassurance, model instability, target-threshold sensitivity, and time-series leakage.

Mitigations include immutable snapshots, schema validation, chronological splits, lagged features, baseline comparisons, sensitivity analysis, and explicit stakeholder caveats. See `docs/assumptions_and_risks.md` and `docs/decision_log.md` for the complete record.

## Lifecycle mapping

| Lifecycle stage | Project artifact |
|---|---|
| Problem Framing & Scoping | Stakeholder question, scope, assumptions, risks, README |
| Tooling Setup | Isolated Python 3.11 environment, configuration, dependency pins, repository structure |
| Python Fundamentals | Executed fundamentals notebook and reusable utilities |
| Data Acquisition/Ingestion | Provider adapter, validation, timestamped raw CSV, manifest |
| Data Storage | Raw/processed separation, CSV/Parquet IO, environment-driven paths |
| Data Preprocessing | Copy-safe cleaning, validation, processed Parquet output |
| Outlier Analysis | Robust flag, retained tails, policy and sensitivity rationale |
| Exploratory Data Analysis | Saved price, drawdown, return, volatility, and prediction figures |
| Feature Engineering | Leakage-aware lagged and rolling features |
| Modeling | Recent-volatility baseline, Ridge regression, logistic classification |
| Evaluation & Risk Communication | Chronological metrics, threshold sensitivity, confusion matrix, risk register |
| Results Reporting & Delivery | Executed cumulative notebook, final summary, stakeholder presentation |
| Productization | Saved model bundle and command-line pipeline |
| Deployment & Monitoring | Conceptual refresh, schema-validation, and performance-monitoring hooks |
| Orchestration & System Design | Modular stages controlled by one reproducible pipeline entry point |

## Final artifacts

- `notebooks/project_pipeline.ipynb`
- `notebooks/python_fundamentals_summary.ipynb`
- `reports/metrics.json`
- `reports/final_summary.md`
- `reports/stakeholder_presentation.pptx`
- `reports/images/`
- `model/risk_models.joblib`

## Authorship

Paritosh Dwivedi is the sole author, analyst, programmer, and presenter. Paritosh Dwivedi retains responsibility for understanding, validating, and presenting all submitted work.
