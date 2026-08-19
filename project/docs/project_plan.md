# Applied Financial Engineering Project Plan

**Working title:** Weekly ETF Risk Monitor  
**Author and project owner:** Paritosh Dwivedi  
**Course:** FRE-GY 5040 - Foundations of Applied Financial Engineering  
**Project window:** August 17-27, 2026  
**Final exam:** August 28, 2026

## 1. Project purpose

Build a reproducible Python pipeline that helps a portfolio manager evaluate the risk of holding a selected exchange-traded fund (ETF) over the next weekly decision window.

The project will transform raw daily market data into a stakeholder-ready weekly risk assessment. The final output will combine descriptive analysis, a forecast or risk score, an elevated-risk classification, and a concise explanation of assumptions and limitations.

This is an individual project. Paritosh Dwivedi is the only author, decision-maker, analyst, programmer, and presenter. No collaborator or co-author roles are part of the project.

## 2. Stakeholder and decision

### Stakeholder persona

A portfolio manager responsible for reviewing ETF exposure once per week. The manager needs a concise answer rather than a research notebook full of unprioritized statistics.

### Decision to support

At the weekly review, should the manager maintain the current ETF exposure or investigate reducing it because near-term market risk appears elevated?

### Useful answer

The project should produce:

- an estimate or risk band for next-week realized volatility;
- a classification of the coming week as normal-risk or elevated-risk;
- recent return, volatility, volume, and drawdown context;
- a plain-language conclusion with uncertainty, assumptions, and limitations.

The project will support a decision; it will not provide automated trading instructions or claim causal effects.

## 3. Scope

### Minimum viable scope

- One primary ETF, selected before ingestion begins.
- Daily adjusted price and volume history from a course-supported programmatic source.
- One benchmark ETF or index only if it materially improves interpretation.
- One regression target: next-week realized volatility or downside magnitude.
- One classification target: whether next-week risk exceeds a documented threshold.
- A naive baseline and one primary model for each target actually used.
- Time-aware evaluation with no random leakage across dates.
- One cumulative pipeline notebook, reusable source modules, a README, and a final slide deck.

### Explicitly out of scope

- Live trading or brokerage integration.
- Intraday or high-frequency data.
- Large universes of securities.
- Portfolio optimization across many assets.
- Automated deployment, monitoring infrastructure, or orchestration beyond a conceptual discussion.
- Claims that the model predicts crises or guarantees investment performance.

### Scope-control rule

If a proposed feature does not improve the stakeholder decision, satisfy a course milestone, or reduce a documented risk, it will not enter the minimum viable project.

## 4. Success criteria

The project is successful when:

1. A fresh environment can install the declared dependencies and run the pipeline.
2. Raw data is acquired programmatically, validated, timestamped, and never edited by hand.
3. Processed data can be deleted and regenerated entirely from raw data and code.
4. The cumulative notebook runs from top to bottom without hidden state.
5. Reusable acquisition, validation, cleaning, feature, and evaluation logic lives in `project/src/`.
6. Model evaluation uses chronological train/test separation and compares performance with a simple baseline.
7. The final conclusion answers the stated weekly decision question.
8. Assumptions, uncertainty, limitations, and possible failure modes are visible in both the notebook and presentation.
9. No secret, credential, or local absolute path is committed.
10. All submitted writing, code decisions, analysis, and presentation content remain attributable to Paritosh Dwivedi.

## 5. Repository plan

The course repository will use the following structure:

```text
bootcamp_paritosh_dwivedi/
|-- class_materials/              # instructor files; gitignored
|-- homework/                     # one self-contained folder per stage
|-- project/
|   |-- data/
|   |   |-- raw/                  # direct, immutable source data
|   |   `-- processed/            # reproducible derived datasets
|   |-- notebooks/
|   |   |-- python_fundamentals_summary.ipynb
|   |   `-- project_pipeline.ipynb
|   |-- src/
|   |   |-- config.py
|   |   |-- utils.py
|   |   |-- ingestion.py
|   |   |-- cleaning.py
|   |   |-- outliers.py
|   |   |-- features.py
|   |   `-- evaluation.py
|   |-- tests/
|   |-- reports/
|   |   `-- images/
|   |-- model/
|   |-- docs/
|   |-- requirements.txt
|   |-- .env.example
|   `-- README.md
|-- .gitignore
`-- README.md
```

`class_materials/`, `.env`, caches, notebook checkpoints, and operating-system clutter will be ignored. Small course-required files under `project/data/` will be committed. Empty project directories will use `.gitkeep` until they contain real artifacts.

## 6. Data plan

### Source

Use one of the programmatic market-data paths demonstrated in the course material. The exact provider will be confirmed during implementation based on access and reliability. Any real API key will live only in `.env`.

### Environment variables

The project template should include placeholders for:

```text
ALPHAVANTAGE_API_KEY=
DATA_DIR_RAW=data/raw
DATA_DIR_PROCESSED=data/processed
```

### Raw-data rules

- Save source responses or source-equivalent tables under `project/data/raw/`.
- Include the source, symbol, and acquisition timestamp in filenames or metadata.
- Do not overwrite or manually repair raw files.
- Keep a short source record containing endpoint/table, parameters, retrieval time, and known limitations.

### Ingestion validation

Before a file is accepted, check:

- required columns;
- parseable dates and numeric fields;
- missing-value counts;
- duplicate dates or records;
- chronological ordering;
- impossible price or volume values;
- response shape and provider error messages.

### Processed-data rules

Every processed dataset must be generated by code. The pipeline will document missing-data treatment, filtering, type conversion, outlier treatment, scaling, feature construction, and the target definition.

## 7. Analytical plan

### Descriptive measures

- Daily and weekly returns.
- Rolling volatility.
- Drawdown and recent maximum drawdown.
- Volume level and change.
- Missingness, distribution, and outlier summaries.

### Candidate features

- Lagged returns.
- Rolling mean and standard deviation.
- Rolling downside volatility.
- Drawdown from a rolling high.
- Volume change or volume z-score.
- Calendar features only when justified.

All features must use information available before the prediction window. Any feature that looks ahead will be removed.

### Targets

- Regression: next-week realized volatility or downside return magnitude.
- Classification: whether next-week realized risk exceeds a threshold defined from training-period data.

### Evaluation

- Use chronological training and test periods.
- Prefer an expanding-window or walk-forward check if time permits.
- Compare with a naive historical-average or recent-volatility baseline.
- Report regression error and classification performance using metrics that match the target.
- Include performance by market regime or time segment when the sample supports it.
- Evaluate whether the result changes under alternate cleaning, outlier, threshold, or feature assumptions.

## 8. Milestones and schedule

### August 17 - Stages 1-6 baseline

#### Problem framing and scoping

- Finalize ETF, stakeholder, decision frequency, target, and useful answer.
- Write the project summary, persona, assumptions, constraints, risks, and lifecycle map in `project/README.md`.
- Create the repository and preserve Paritosh Dwivedi as the author.

#### Tooling setup

- Build the complete project folder scaffold.
- Create the Python environment and record the Python version.
- Add `requirements.txt`, `.gitignore`, `.env.example`, and `src/config.py`.
- Verify the interpreter, imports, configuration, and data paths.

#### Python fundamentals

- Complete `notebooks/python_fundamentals_summary.ipynb` with Python, NumPy, and pandas examples.
- Add at least one documented reusable utility to `src/utils.py`.
- Add a small unit test if time permits.

#### Data acquisition and storage

- Start `notebooks/project_pipeline.ipynb` with the required project-root setup cell.
- Acquire the primary dataset programmatically.
- Validate and save a timestamped raw file.
- Implement reusable read/write functions and reload checks.
- Document folder conventions and file formats in the README.

#### Preprocessing

- Correct types and invalid values.
- Diagnose missingness before selecting a treatment.
- Implement cleaning functions in `src/cleaning.py`.
- Save an analysis-ready processed dataset.
- Add a validation summary and preprocessing-assumptions section.

**Stage 1-6 exit criterion:** the notebook runs from acquisition through processed-data output without manual file edits.

### August 18 - Outliers and assumption sensitivity

- Detect outliers using visual and statistical methods.
- Separate likely data errors from rare but plausible financial events.
- Implement the chosen treatment in `src/outliers.py`.
- Compare results before and after treatment.
- Record the stakeholder impact of the decision.

### August 19 - EDA and feature engineering

- Produce visual and statistical EDA.
- Save final-quality figures under `reports/images/`.
- Define features and their financial rationale.
- Add feature functions to `src/features.py`.
- Check correlation, redundancy, missingness after transformation, and leakage.

### August 20 - Regression

- Freeze the regression target and chronological split.
- Establish a naive baseline.
- Fit the primary regression model.
- Check residual behavior and relevant model assumptions.
- Explain performance in stakeholder terms.

### August 21 - Time series and classification

- Build the model type that best answers the project decision.
- Compare it with the baseline and regression result where appropriate.
- Record threshold selection and class-balance implications.
- Avoid adding models only to increase model count.

### August 24 - Evaluation and risk communication

- Consolidate out-of-sample metrics.
- Run sensitivity checks for preprocessing, feature windows, and target thresholds.
- Document regime-change, data-quality, model-instability, and decision risks.
- Write a short recommendation that distinguishes evidence from uncertainty.

### August 25-26 - Reproducibility and delivery buffer

- Recreate the environment from the dependency file.
- Restart and run the pipeline notebook from top to bottom.
- Scan for secrets, local paths, missing files, and stale outputs.
- Confirm that processed data and figures can be rebuilt.
- Draft and rehearse the final presentation.

### August 27 - Final delivery

- Finalize the stakeholder slide deck.
- Include the problem, data, method, key evidence, conclusion, assumptions, and risks.
- Update the README with complete run instructions and lifecycle mapping.
- Ensure the repository, notebook, figures, and presentation tell the same story.
- Freeze the submission before the final exam day.

### August 28 - Final exam

- Reserve the day for the cumulative exam.
- Do not leave essential project construction or debugging until this date.

## 9. Final deliverables

1. A structured GitHub repository authored by Paritosh Dwivedi.
2. A clean cumulative `project_pipeline.ipynb` with markdown explanations.
3. Reusable Python modules under `project/src/`.
4. Versioned raw and reproducible processed data.
5. Saved, presentation-quality charts.
6. A project README describing purpose, structure, execution, lifecycle mapping, assumptions, and risks.
7. A stakeholder-ready slide deck with concise conclusions.

## 10. Risk register

| Risk | Likely effect | Mitigation |
|---|---|---|
| Data provider failure or rate limit | Ingestion cannot run | Cache a valid raw pull, fail clearly, and keep a documented course-supported fallback |
| Secret committed to Git | Credential exposure | Ignore `.env`, commit only placeholders, inspect staged changes before every push, and rotate any exposed key |
| Path-dependent notebook | Pipeline fails outside one folder | Use the required project-root bootstrap cell and `pathlib` paths |
| Missing or inconsistent source data | Biased or broken analysis | Validate schema, dates, types, duplicates, ranges, and missingness before saving |
| Time-series leakage | Inflated model performance | Use chronological splits and lag all predictive features |
| Overly broad scope | Incomplete final delivery | Enforce one stakeholder, one decision, one primary dataset, and one main model |
| Regime change | Historical relationships stop holding | Report time-segment performance and state the limitation explicitly |
| Unjustified preprocessing | Distorted results | Compare alternatives and document each assumption |
| Course starter-file mismatch | Lecture examples fail | Treat supplied notebooks as references and adapt paths to the actual project structure |
| Compressed schedule | Insufficient verification | Finish the runnable stage 1-6 baseline first and reserve August 25-26 for QA |

## 11. Solo-author working method

- Paritosh Dwivedi owns every project decision and final artifact.
- Use small, stage-specific Git commits with descriptive messages.
- Keep a decision log in `project/docs/` for scope, data, preprocessing, feature, model, and threshold choices.
- After each stage, restart and run the cumulative notebook before committing.
- Use branches only when they reduce personal risk; no collaborative branch workflow is required.

## 12. Definition of done

The project is done only when a clean run can acquire or load the recorded raw input, recreate the processed dataset, regenerate the principal figures and metrics, and produce a conclusion that directly answers the weekly ETF risk decision. The repository and final presentation must clearly identify Paritosh Dwivedi as the author and must not attribute authorship to any other person, group, or tool.
