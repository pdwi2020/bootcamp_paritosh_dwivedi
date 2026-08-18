# Project Execution Checklist

**Sole owner and author:** Paritosh Dwivedi
**Project:** Weekly ETF Risk Monitor
**Status date:** August 17, 2026

## Completed

- [x] Isolate the work in a dedicated Git repository.
- [x] Protect and Git-ignore instructor-provided course materials.
- [x] Define the SPY stakeholder decision, weekly horizon, scope, assumptions, and risks.
- [x] Create the Python 3.11 environment, dependency file, configuration, and secret-safe `.env.example`.
- [x] Implement reusable ingestion, validation, storage, cleaning, outlier, feature, modeling, evaluation, and plotting modules.
- [x] Acquire and preserve an immutable raw snapshot with a SHA-256 manifest.
- [x] Build validated clean and model-ready Parquet datasets.
- [x] Engineer leakage-aware trailing features and next-five-day targets.
- [x] Fit regression and classification models with chronological out-of-sample evaluation.
- [x] Compare the models with naive baselines and run risk-threshold sensitivity analysis.
- [x] Generate final figures, predictions, metrics, model bundle, and stakeholder summary.
- [x] Create and execute the Python fundamentals notebook from top to bottom.
- [x] Create and execute the cumulative project notebook from top to bottom.
- [x] Create and visually verify the editable stakeholder presentation.
- [x] Complete the README, data dictionary, decision log, assumptions/risk register.
- [x] Run unit tests, artifact checks, duplicate-date checks, secret scan, notebook error audit, and slide overflow test.
- [x] Confirm Paritosh Dwivedi is the only named author and presenter.

## Full-review remediation

- [x] Add a five-session embargo between training targets and the holdout period.
- [x] Fit return-outlier parameters on training data only and persist them with the models.
- [x] Describe classifier output as a risk score and add calibration diagnostics.
- [x] Keep holdout evaluation separate from a final production refit on all labeled data.
- [x] Report non-overlapping-window, calendar-year, residual-tail, feature-window, outlier-ablation, and walk-forward diagnostics.
- [x] Use one documented elevated-risk decision rule across code, reports, notebooks, and slides.
- [x] Validate cached raw-data manifests before reuse.
- [x] Correct Alpha Vantage adjusted-price ingestion.
- [x] Expand unit and artifact verification coverage.
- [x] Standardize notebook kernels on portable `python3` and execute both notebooks top to bottom.
- [x] Track the presentation generator and regenerate the deck with correct core authorship metadata.
- [x] Run the complete workflow in a clean clone and commit the verified result.

## Submission actions requiring Paritosh Dwivedi

- [ ] Review the notebook, README, and presentation until every method and conclusion can be explained without assistance.
- [ ] Rehearse the presentation and revise any explanation that exceeds the allotted time.
- [ ] Add or confirm the intended Git remote, then push the final commit.
- [ ] Open every submitted file or link from the grader-facing location.
- [ ] Complete the cumulative final-exam review.

The repository is technically complete; the unchecked items depend on Paritosh Dwivedi's presentation, submission destination, or exam activity.
