# SPY Weekly Risk Monitor - Results Summary

**Sole author:** Paritosh Dwivedi

**Data through:** 2026-08-17

## Current decision signal

- Risk classification: **NORMAL**
- Predicted next-five-session annualized volatility: **11.3%**
- Elevated-risk score: **25.2%**
- Elevated-risk decision rule: score >= **50%**
- All-labeled-history risk threshold: **17.1%**
- Decision interpretation: The model does not flag elevated risk; maintain exposure only within the existing mandate.

## Out-of-sample evidence

- Ridge MAE: 0.0402
- Recent-volatility baseline MAE: 0.0507
- Ridge MAE improvement versus recent-volatility baseline: 20.8%
- Elevated-risk balanced accuracy: 72.7%
- Elevated-risk recall: 61.3%
- Holdout forecast windows: 835 overlapping daily five-session windows

## Interpretation limits

The classifier output is a class-weighted risk score, not a calibrated event probability. This is a decision-support signal, not a trading instruction. Performance is historical and may change under new market regimes. Provider revisions, threshold choice, feature-window choice, and extreme events can materially affect the result.
