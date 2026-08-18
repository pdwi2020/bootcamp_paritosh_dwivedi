# Decision Log

**Sole author:** Paritosh Dwivedi

| Date | Decision | Rationale | Revisit trigger |
|---|---|---|---|
| 2026-08-17 | Use SPY as the primary ETF | It is liquid, widely understood, and matches the course ETF risk example. | A different ETF is required by the instructor or stakeholder. |
| 2026-08-17 | Support Alpha Vantage with yfinance fallback | This matches the course acquisition examples while allowing a credential-free reproducible run. | Provider availability, schema, or licensing changes. |
| 2026-08-17 | Predict five-trading-day realized volatility | A five-day horizon matches the stakeholder's weekly review cadence. | Stakeholder cadence changes. |
| 2026-08-17 | Define elevated risk from the training-period 75th percentile | The label is interpretable and avoids test-period leakage. | Sensitivity results show instability or the stakeholder supplies a risk limit. |
| 2026-08-17 | Retain plausible extreme returns and flag them | Tail observations are decision-relevant in a risk-monitoring project. | Validation identifies a provider or data error. |
| 2026-08-17 | Use chronological evaluation | Random splits would leak time information and overstate performance. | Never; this is a core validity constraint. |
| 2026-08-17 | Embargo five sessions before each test window | The target uses the next five sessions, so a gap prevents training targets from containing test dates. | The forecast horizon changes. |
| 2026-08-17 | Treat logistic output as a risk score | Class weighting improves minority detection but changes probability calibration. | A time-aware calibration study is added. |
| 2026-08-17 | Separate evaluation and production fits | Holdout models support honest metrics; an all-labeled-history refit uses the latest available labels for current scoring. | The deployment protocol changes. |
| 2026-08-17 | Use score >= 50% as the sole elevated-risk trigger | One explicit rule avoids conflicting forecast-threshold and classifier instructions. | The stakeholder selects a cost-based cutoff. |
