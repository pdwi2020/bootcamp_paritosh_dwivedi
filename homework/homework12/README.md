# Homework 12: Results Reporting & Delivery Design

**Author:** Paritosh Dwivedi

Format chosen: **written report**, at `reports/stakeholder_report.md`.

## Files

- `homework12_results-reporting-delivery-design_submission.ipynb` — builds every figure and writes
  the report.
- `reports/stakeholder_report.md` — the deliverable.
- `reports/images/` — `risk_return.png`, `error_by_regime.png`, `forecast_vs_actual.png`,
  `tornado_assumptions.png`.
- `data/processed/stage12_dataset.parquet` — the derived dataset.

## The three headline claims, and where each comes from

1. **Typical error is 5.0 volatility points** — holdout MAE 0.0498.
2. **Roughly three times less accurate in turbulent weeks** — 10.4 against 3.8 volatility points
   across the volatility terciles.
3. **Robust to the analyst choices tested** — no alternative assumption moved MAE by more than 0.45
   volatility points; dropping to a single feature was the worst at +9.0%.

Every number in the report is computed in the notebook and interpolated, so the prose cannot drift
from the data. Charts share one palette, carry units on both axes, and each has a caption stating the
takeaway rather than describing the picture.
