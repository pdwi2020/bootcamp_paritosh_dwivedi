# Project execution checklist

**Sole owner and author:** Paritosh Dwivedi
**Project:** Weekly ETF Risk Monitor
**Status date:** August 18, 2026

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
- [x] Execute both notebooks top to bottom with the pinned project kernel.
- [x] Track the presentation generator and regenerate the deck with correct core authorship metadata.
- [x] Run the complete workflow in a clean clone.

## Final full-review fixes

- [x] Reject empty market-data snapshots during validation.
- [x] Recompute prediction metrics and the current model snapshot during final verification.
- [x] Make raw snapshot names collision-resistant and refuse overwrites.
- [x] Use the current date for refreshes unless `DATA_END` is set explicitly.
- [x] Correct the documented Ridge improvement to 20.8%.
- [x] Describe the intentionally empty `homework/` directory accurately.
- [x] Label the presentation's three-year chart window and regenerate the deck.

## Post-review hardening

- [x] Upgrade all dependency pins reported by the current vulnerability audit.
- [x] Reject duplicate and non-chronological prediction dates during artifact verification.
- [x] Clear the checkout-local fixed data cutoff so future refreshes advance automatically.

## Final integrity and release hardening

- [x] Recompute recent-volatility baseline metrics and the headline improvement during verification.
- [x] Correct the checklist so the final commit and push remain pending.
- [x] Add and pass a repository-local Ruff quality gate.
- [x] Lock the complete Python dependency graph.
- [x] Add direct yfinance adapter regression coverage.
- [x] Apply sentence-case documentation headings.

## Final release-review remediation

- [x] Preserve the newest observation in every downsampled presentation chart.
- [x] Derive presentation dates, row counts, and history spans from the declared dataset.
- [x] Build the presentation from the exact raw snapshot declared in `metrics.json`.
- [x] Verify every declared raw, processed, prediction, sensitivity, model, and figure artifact.
- [x] Reject artifact paths that are missing, absolute, or outside the project directory.
- [x] Enforce Ruff formatting and JavaScript syntax in the standard lint target.
- [x] Add regression coverage for presentation sampling and verifier integrity.
- [x] Execute notebooks with the pinned project environment and reject incompatible saved models.
- [x] Clear stale slide renders before presentation QA.
- [x] Rebuild and verify the complete project in a clean-room copy.

## Final comprehensive-review remediation

- [x] Document `make notebooks` as the supported notebook regeneration workflow.
- [x] Add a validated presentation build target built on `python-pptx`.
- [x] Build the presentation from a temporary runtime directory without repository-local dependencies.
- [x] Replace generic setup and run headings with descriptive task-oriented headings.
- [x] Recheck the course repository-structure PDF against the complete project inventory.
- [x] Rebuild and verify the documented notebook and presentation workflows in a clean-room copy.

## Reproducible presentation build

- [x] Replace the deleted Node deck generator with a tracked `python-pptx` module and CLI.
- [x] Build the editable stakeholder deck from validated committed inputs through `make presentation`, with no Node runtime dependency.
- [x] Add Python regression tests for date formatting, calendar spans, newest-row-preserving chart sampling, slide count, and core authorship metadata.

## Submission actions requiring Paritosh Dwivedi

- [ ] Review the notebook, README, and presentation until every method and conclusion can be explained without assistance.
- [ ] Rehearse the presentation and revise any explanation that exceeds the allotted time.
- [ ] Add or confirm the intended Git remote, then push the final commit.
- [ ] Open every submitted file or link from the grader-facing location.
- [ ] Complete the cumulative final-exam review.

The repository is technically complete; the unchecked items depend on Paritosh Dwivedi's presentation, submission destination, or exam activity.
