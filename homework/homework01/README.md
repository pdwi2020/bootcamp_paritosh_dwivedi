# Project Title

**Stage:** Problem Framing & Scoping (Stage 01)

**Project:** Weekly ETF risk monitor

## Problem Statement

A portfolio manager needs a consistent way to decide whether current SPY exposure warrants additional investigation before the weekly risk review. Raw daily returns describe what happened, but they do not directly answer how volatile the next week may be. The Weekly ETF risk monitor will use information available at the decision date to forecast annualized realized volatility over the next five trading sessions and classify the period as normal risk or elevated risk.

Success is decision-linked and measurable. On a purged chronological holdout, the volatility forecast must have lower mean absolute error than a trailing 20-day volatility baseline. The classifier must achieve at least 50% elevated-risk recall and report balanced accuracy so majority-class performance cannot hide missed elevated-risk periods. These metrics support comparison and monitoring; they do not guarantee future performance.

## Stakeholder & User

The portfolio manager is both the decision owner and primary user. The manager reviews the output before a weekly SPY exposure meeting and decides whether to maintain exposure within the existing mandate or open a deeper review of concentration, liquidity, hedging, and other permitted risk controls. Risk and operations colleagues may receive the artifact as secondary readers, but the monitor does not replace the manager's judgment or the firm's approval process.

## Useful Answer & Decision

The answer is predictive, not descriptive or causal. The weekly artifact contains:

- a forecast of next-five-session annualized realized volatility;
- a normal-risk or elevated-risk classification;
- an elevated-risk score and the decision threshold used;
- recent volatility, return, drawdown, and volume context;
- a plain-language interpretation with assumptions and limitations.

An elevated flag prompts additional review before the manager confirms the week's exposure. A normal flag supports continued monitoring within the existing mandate, but it is not evidence that SPY is safe. The elevated-risk score is a ranking and decision score, not a calibrated event probability, and it must not be interpreted as the literal chance of an adverse event.

## Assumptions & Constraints

- Adjusted daily SPY price and volume history is available, timely, and sufficiently accurate for a weekly monitor.
- The next five trading sessions are a practical proxy for the manager's weekly decision horizon.
- Historical relationships between lagged returns, volatility, drawdown, volume, and near-term volatility have some persistence.
- Features and thresholds use only information available at the decision date; evaluation must preserve time order and prevent target leakage.
- The first version covers one liquid ETF and daily data. It does not use intraday data, news, options-implied volatility, or portfolio-level exposures.
- The result must be available before the weekly review and reproducible on ordinary local computing resources.
- The monitor does not execute trades, optimize a portfolio, or override investment mandates, compliance rules, or human approval.

## Known Unknowns / Risks

- Market regime change may weaken historical relationships. Monitor rolling and calendar-period error, recall, and balanced accuracy.
- Extreme volatility may be systematically underpredicted. Report forecast error by realized-volatility decile and retain plausible market extremes in testing.
- Provider revisions or schema changes may alter the input history. Validate the schema and preserve dated raw snapshots with hashes.
- The elevated-risk threshold may be sensitive to the training period and quantile. Compare alternative quantiles and feature windows without choosing them from holdout results.
- A class-weighted score may be poorly calibrated. Track calibration diagnostics while continuing to label it as a decision score rather than a probability.
- False negatives can create false reassurance. Track elevated-risk recall and document every material missed-risk episode reviewed by the stakeholder.

## Lifecycle Mapping

Goal -> Stage -> Deliverable

- Define one decision-centered question -> Problem Framing & Scoping (Stage 01) -> Scoping paragraph, README, and stakeholder memo
- Create a reproducible working environment -> Tooling Setup (Stage 02) -> Isolated environment, configuration template, and repository scaffold
- Preserve auditable SPY history -> Data Acquisition & Ingestion (Stage 04) -> Validated raw snapshot and source manifest
- Construct information available at decision time -> Feature Engineering (Stage 09) -> Leakage-aware model dataset
- Forecast weekly volatility and elevated risk -> Modeling (Stage 10) -> Baseline, regression model, and classification model
- Test usefulness and failure modes -> Evaluation & Risk Communication (Stage 11) -> Purged chronological metrics, sensitivity checks, and risk register
- Support the weekly review -> Results Reporting & Delivery (Stage 12) -> Executed analysis, concise report, and stakeholder presentation

## Repo Plan

This Stage 01 homework folder intentionally contains only the submission notebook, this README, and `docs/stakeholder_memo.md`. It does not create data, source, report, model, or notebook subfolders because this stage only uses `docs/`. The notebook holds the scoping draft and verifies the submitted layout; the memo holds the stakeholder-facing context. Both are updated whenever the decision definition, five-session target, score interpretation, or trust conditions change.

Paritosh Dwivedi is the author and retains responsibility for understanding, validating, and presenting this work.
