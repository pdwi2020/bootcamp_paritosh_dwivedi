# Lifecycle framework guide

**Author:** Paritosh Dwivedi

One row per lifecycle stage: where that stage's work lives in this repository,
and the decision I made there.

| Stage | Where it lives | What I decided |
|---|---|---|
| 01 Problem Framing & Scoping | `README.md`, `docs/project_plan.md` | Forecast next-five-session annualised volatility for a weekly SPY exposure review, and classify normal vs elevated. Success defined before modelling: beat a trailing-20-day baseline on MAE and reach at least 50% elevated recall. |
| 02 Tooling Setup | `requirements.txt`, `requirements.lock.txt`, `.env.example`, `Makefile` | Python 3.11 venv with hash-pinned dependencies. Configuration through `.env`; secrets never committed. Verified by rebuilding from the lock file in a clean clone. |
| 03 Python Fundamentals | `src/utils.py`, `notebooks/python_fundamentals_summary.ipynb` | Logic lives in importable modules, not notebooks. Notebooks carry narrative and call `src/`. |
| 04 Data Acquisition & Ingestion | `src/ingestion.py`, `src/validation.py`, `data/raw/` | yfinance as provider. Every pull writes a timestamped CSV plus a manifest with SHA-256, so a result can be traced to its exact input. Validate before saving. |
| 05 Data Storage | `src/storage.py`, `data/raw/` vs `data/processed/` | Raw is immutable; anything derived goes to processed. Parquet for processed data because it preserves dtypes; CSV for raw because it is portable and diffable. |
| 06 Data Preprocessing | `src/cleaning.py` | Copy-safe, idempotent transforms. Cleaning rules documented rather than implicit. Nothing is imputed using statistics computed over the evaluation period. |
| 07 Outlier Analysis | `src/outliers.py`, `docs/outliers.md` | Robust median/MAD score, threshold 6.0, fitted on training data only. 31 of 4,186 rows flagged. Tails are flagged and **kept**, never deleted: a market event is the risk being measured. |
| 08 Exploratory Data Analysis | `src/eda.py`, `notebooks/eda.ipynb` | Profile with skew and kurtosis, and flag columns needing attention before feature work. Correlation used as a hint, not a claim. |
| 09 Feature Engineering | `src/features.py` | Ten features, all trailing so each is knowable at the decision date. Level, change, direction and participation are all represented so the model is not relying on one description of the same phenomenon. |
| 10a Modeling: Regression | `src/modeling.py`, `docs/model_interpretation.md` | Ridge inside a `Pipeline` with a scaler. Coefficients interpreted on the standardised scale; `ewma_vol_20` dominates. Collinearity means individual signs are not read as causal. |
| 10b Modeling: Time Series & Classification | `src/modeling.py` | Purged chronological split with a five-session embargo, because a five-day target overlaps the boundary. Class-weighted logistic for the elevated flag. Balanced accuracy and recall are the decision metrics, not accuracy. |
| 11 Evaluation & Risk Communication | `src/evaluation.py`, `src/uncertainty.py`, `docs/assumptions_and_risks.md` | Bootstrap CIs on both MAEs; the intervals do not overlap, so the improvement is not noise. Two prediction-interval scenarios show that assuming normality understates the upper tail. Reported by year and decile, because aggregates hide regime failure. |
| 12 Results Reporting & Delivery | `reports/final_summary.md`, `reports/stakeholder_presentation.pptx` | Decision first, then evidence, then caveats. Every number regenerated from `metrics.json` so the deck cannot drift from the data. |
| 13 Productization | `src/serving.py`, `app.py`, `model/model.pkl` | Prediction logic in one function that the notebook, CLI and API all call, so the served answer cannot differ from the analysed one. Verified: the API returns the same figures as `latest_risk_snapshot`. |
| 14 Deployment & Monitoring | `docs/monitoring_plan.md`, `docs/handoff_plan.md` | Six metrics across data, model, system and business layers, with thresholds, owners and a fallback to the trailing-volatility baseline. Retraining is proposed, never automatic. |
| 15 Orchestration & System Design | `docs/orchestration_plan.md`, `src/run_step.py` | Eight tasks in a linear DAG. Checkpoints at the two processed Parquet files; logging at task boundaries. Deliberately no scheduler — the chain runs in under a minute and has one consumer. |
| 16 Lifecycle Review | This file, `docs/project_summary.md`, `README.md` | The repo is the deliverable. A stranger should be able to install, run and understand it without asking me anything. |
