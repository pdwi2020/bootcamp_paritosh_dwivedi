# Assumptions and Risks

**Sole author:** Paritosh Dwivedi

## Assumptions

- Daily adjusted prices and volumes accurately represent the selected ETF's historical market data.
- Five trading days is an acceptable approximation of the stakeholder's weekly decision horizon.
- Historical lagged returns, volatility, drawdown, and volume contain some information about near-term volatility.
- Training-period relationships remain informative enough to evaluate on later observations.
- A training-period risk quantile is a useful relative risk threshold, not a regulatory or mandate limit.

## Risks and mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| Provider outage or schema drift | Refresh fails or fields silently change | Validate schema and use a documented fallback. |
| Corporate-action revision | Historical adjusted prices can change | Record retrieval time and preserve immutable raw snapshots. |
| Time-series leakage | Performance is overstated | Use lagged features and chronological splits. |
| Regime change | Historical model relationships weaken | Report time bounds, sensitivity, and out-of-sample performance. |
| Tail-event treatment | Removing extremes understates risk | Retain plausible extremes and flag them instead of deleting them. |
| Threshold sensitivity | Risk label changes with the selected quantile | Report results at the 70th, 75th, and 80th percentiles. |
| False reassurance | A normal flag is interpreted as safety | Describe the output as decision support, never a guarantee. |
