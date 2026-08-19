# Weekly ETF risk monitor

**Author:** Paritosh Dwivedi
**Primary ETF:** SPY
**Decision cadence:** Weekly
**Data through:** August 17, 2026

## Project summary

This project builds a reproducible Python pipeline that helps a portfolio manager decide whether current SPY exposure merits additional investigation because near-term market risk appears elevated. It converts daily price and volume history into a five-trading-day volatility forecast, an elevated-risk score, and a concise stakeholder interpretation. The score comes from class-weighted logistic regression and is not presented as a calibrated event probability.

The project is intentionally narrow. It supports one recurring risk-review decision for one liquid ETF. It does not execute trades, optimize a portfolio, claim causal effects, or guarantee future performance.

## Stakeholder and useful answer

The stakeholder and user is a portfolio manager who reviews ETF exposure weekly. The useful answer contains:

- predicted next-five-session annualized realized volatility;
- a normal-risk or elevated-risk classification;
- recent volatility, return, drawdown, and volume context;
- a plain-language decision interpretation;
- explicit assumptions, uncertainty, and model limitations.

## Current result

Using data through August 17, 2026, the model produces a **NORMAL** relative-risk classification:

- Predicted next-five-session annualized volatility: **11.3%**
- Elevated-risk score: **25.2%**
- Elevated-risk decision rule: **score >= 50%**
- All-labeled-history elevated-risk threshold: **17.1%**
- Current 20-day annualized volatility: **13.5%**

Decision interpretation: the model does not flag elevated risk. Maintain exposure only within the existing mandate and continue monitoring; a normal flag is not a claim that the position is safe.

## Out-of-sample evidence

The split is chronological and purged: five observations are embargoed between the last training row and the holdout start so no training target contains a holdout date. The primary holdout contains 835 overlapping daily five-session forecast windows; five offset samples provide non-overlapping robustness checks.

| Measure | Result |
|---|---:|
| Ridge regression MAE | 0.0402 |
| Recent-volatility baseline MAE | 0.0507 |
| Ridge MAE improvement vs recent-volatility baseline | 20.8% |
| Ridge regression R-squared | 0.336 |
| Elevated-risk balanced accuracy | 72.7% |
| Elevated-risk recall | 61.3% |
| Elevated-risk ROC AUC | 0.777 |

The classifier sacrifices overall accuracy to identify more elevated-risk periods. The prior baseline obtains high raw accuracy by predicting the majority class but has zero elevated-risk recall, so balanced accuracy and recall are more useful decision metrics.

## Robustness and limits

- Across the five non-overlapping offsets, Ridge improves MAE over recent volatility by 16.6% to 23.5%; balanced accuracy ranges from 68.3% to 75.8%, and recall from 52.4% to 68.2%.
- Calendar-year recall varies from 33.3% in 2024 to 83.3% in 2025, confirming regime sensitivity.
- Four expanding walk-forward folds with a five-session embargo produce 18.6% aggregate MAE improvement, 79.3% balanced accuracy, and 74.1% recall across 3,340 forecast windows.
- Ridge underpredicts the highest realized-volatility decile by 8.5 percentage points on average; tail forecasts therefore require caution.
- Alternative 10/30- and 10/60-session feature windows do not overturn the general result, but the longer specification reduces classification recall.
- Removing the return-outlier flag changes results only slightly, so it is retained as contextual information rather than treated as a dominant signal.
- The class-weighted logistic score has a 33.9% holdout mean versus a 13.3% event rate; its Brier score is 0.143. Treat it as a ranking/decision score, not a literal probability.

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
|   |-- plotting.py
|   `-- presentation.py
|-- tests/
|-- docs/
|-- reports/
|   `-- images/
|-- model/
|-- build_presentation.py
|-- Makefile
|-- pyproject.toml
|-- run_pipeline.py
|-- verify_project.py
|-- requirements.lock.txt
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Install the locked environment

From the repository root, enter the project directory before using its Make targets:

```bash
cd project
make setup
cp .env.example .env
```

`make setup` installs the complete hash-locked dependency graph from `requirements.lock.txt`. After changing a direct pin in `requirements.txt`, run `make lock` from `project/` to regenerate the lockfile.

The default `.env.example` uses SPY, a January 2010 start date, a 20% chronological test set, and a training-period 75th-percentile elevated-risk threshold. `DATA_END` is blank by default, so `--refresh` acquires data through the current date. Set it explicitly when you need a frozen cutoff.

An Alpha Vantage key is optional. If `ALPHAVANTAGE_API_KEY` is empty and `DATA_PROVIDER=auto`, the pipeline uses the course-supported yfinance fallback.

## Run the pipeline and quality gates

From the repository root, enter `project/` once and use the latest validated immutable raw snapshot:

```bash
cd project
make pipeline
```

Acquire and preserve a new raw snapshot through `DATA_END` or the current date:

```bash
../.venv/bin/python run_pipeline.py --refresh
```

Run the local quality gates and pipeline from `project/`:

```bash
make lint
make test
make pipeline
make verify
```

The cumulative notebook repeats the complete analysis in a stakeholder-readable sequence and has been executed top-to-bottom. Regenerate and execute both notebooks with the locked project environment:

```bash
make notebooks
```

The editable presentation is generated entirely from the locked Python environment with `python-pptx`. From `project/`, run:

```bash
make presentation
```

The target runs `build_presentation.py`, which delegates to `src/presentation.py` and writes `reports/stakeholder_presentation.pptx`. The build has no Node dependency; charts remain editable PowerPoint charts, and every reported result is read from the committed project data and reports.

## Data acquisition and Data Storage

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

Extreme returns are detected with a robust median absolute-deviation score. Evaluation-period location and scale parameters are fit on the purged training data only; the production artifact refits them on all labeled history. Thirty-one observations were flagged in the current dataset. Plausible market extremes are retained because deleting them would understate the risk problem the project is designed to monitor.

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

The regression target is annualized realized volatility over the next five trading days. A target is constructed for each eligible day, so adjacent forecast windows overlap. Ridge regression is compared with recent-volatility and historical-mean baselines.

The elevated-risk label equals one when the regression target exceeds the training-period volatility quantile. Logistic regression uses class weighting because elevated-risk periods are less frequent. A risk score of at least 50% is the only classification trigger; the volatility forecast and training-derived target threshold provide context but do not independently change the classification. Threshold sensitivity is reported at the 70th, 75th, and 80th percentiles.

Holdout models are retained only for honest historical evaluation. The saved production bundle is a separate refit on all 4,175 labeled rows through August 10, 2026, and it is the model used for the current August 17 signal.

## Assumptions and risks

Key assumptions include a five-day weekly horizon, reliable provider history, and partial persistence of historical risk relationships. Important risks include provider schema changes, corporate-action revisions, regime change, false reassurance, model instability, target-threshold sensitivity, and time-series leakage.

Mitigations include immutable snapshots with hash validation, purged chronological splits, train-only preprocessing, lagged features, baseline comparisons, non-overlapping and walk-forward checks, sensitivity analysis, and explicit stakeholder caveats. See `docs/assumptions_and_risks.md` and `docs/decision_log.md` for the complete record.

## Lifecycle mapping

Goal -> lifecycle stage -> deliverable.

| Goal | Lifecycle stage | Deliverable |
|---|---|---|
| Define one decision-centered question | Problem Framing & Scoping | Stakeholder question, scope, assumptions, risks, README |
| Create a reproducible working environment | Tooling Setup | Isolated Python 3.11 environment, configuration, dependency pins, repository structure |
| Build reusable code the later stages import | Python Fundamentals | Executed fundamentals notebook and reusable utilities |
| Preserve auditable SPY history | Data Acquisition/Ingestion | Provider adapter, validation, timestamped raw CSV, manifest |
| Let anyone recreate the data state without path edits | Data Storage | Raw/processed separation, CSV/Parquet IO, environment-driven paths |
| Turn provider output into a trustworthy table | Data Preprocessing | Copy-safe cleaning, validation, processed Parquet output |
| Decide what to do with market extremes | Outlier Analysis | Robust flag, retained tails, policy and sensitivity rationale |
| Understand the risk behaviour before modeling | Exploratory Data Analysis | Saved price, drawdown, return, volatility, and prediction figures |
| Construct information available at decision time | Feature Engineering | Leakage-aware lagged and rolling features |
| Forecast weekly volatility and elevated risk | Modeling | Recent-volatility baseline, Ridge regression, logistic classification |
| Test usefulness and failure modes | Evaluation & Risk Communication | Chronological metrics, threshold sensitivity, confusion matrix, risk register |
| Support the weekly review | Results Reporting & Delivery | Executed cumulative notebook, final summary, stakeholder presentation |
| Make the signal repeatable outside a notebook | Productization | Saved model bundle and command-line pipeline |
| Keep the signal honest as data arrives | Deployment & Monitoring | Conceptual refresh, schema-validation, and performance-monitoring hooks |
| Keep the stages independently runnable | Orchestration & System Design | Modular stages controlled by one reproducible pipeline entry point |

## Final artifacts

- `notebooks/project_pipeline.ipynb`
- `notebooks/python_fundamentals_summary.ipynb`
- `reports/metrics.json`
- `reports/final_summary.md`
- `reports/stakeholder_presentation.pptx`
- `reports/images/`
- `model/risk_models.joblib`

## Authorship

Paritosh Dwivedi is the author, analyst, programmer, and presenter. Paritosh Dwivedi retains responsibility for understanding, validating, and presenting all submitted work.
