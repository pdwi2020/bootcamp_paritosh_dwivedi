# Assumptions and risks

**Author:** Paritosh Dwivedi

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
| Time-series leakage | Performance is overstated | Use lagged features, train-only preprocessing, and a five-session embargo before each test fold. |
| Regime change | Historical model relationships weaken | Report time bounds, sensitivity, and out-of-sample performance. |
| Tail-event treatment | Removing extremes understates risk | Retain plausible extremes and flag them instead of deleting them. |
| Threshold sensitivity | Risk label changes with the selected quantile | Report results at the 70th, 75th, and 80th percentiles. |
| False reassurance | A normal flag is interpreted as safety | Describe the output as decision support, never a guarantee. |
| Overlapping targets | Daily five-session windows can make the holdout look more independent than it is | Report five non-overlapping offset samples and expanding walk-forward folds. |
| Score miscalibration | A class-weighted score is mistaken for a literal probability | Label it a risk score and publish Brier/log-loss diagnostics and the event rate. |
| Tail underprediction | The regression model understates the most volatile windows | Publish tail residual diagnostics and require human review for high-risk decisions. |

## Scenario and sensitivity commentary

Stage 11 asks not only what the model scores but how much that score can be
trusted, and how it moves when the assumptions behind it change. Three scenario
comparisons are run, and each one changes a different assumption.

### How precisely is the metric known?

Resampling the 837 holdout windows with replacement two thousand times gives a
95% interval of **[0.0366, 0.0436]** for the Ridge MAE and **[0.0461, 0.0555]**
for the trailing-volatility baseline. The intervals **do not overlap**, so the
21% improvement is not an artifact of which rows happened to fall in the holdout.

What this does *not* establish: that the model is correct, that it will hold in a
new regime, or that the residual independence assumption is satisfied — it is
not, with lag-1 autocorrelation of 0.747 from the overlapping five-day windows.
The bootstrap quantifies sampling variability in the metric and nothing else.

### Empirical versus gaussian prediction intervals

Two ways of asking where a *new* forecast might land, on the same residuals:

| Scenario | 95% interval | Assumption |
|---|---|---|
| Empirical residual percentiles | [−0.090, +0.135] | None beyond the residuals being representative |
| Gaussian approximation | [−0.129, +0.128] | Residuals are normally distributed |

The gaussian form is symmetric by construction and puts its upper bound at
+0.128, while the observed residuals reach +0.135. It is *wider* on the downside
and *narrower* on the upside. For a volatility monitor, understating the upside
is the dangerous direction: the error that matters is volatility coming in higher
than forecast, not lower. **Conclusion: report the empirical interval.** Assuming
normality on right-skewed residuals would have produced a falsely reassuring
upper bound.

### Threshold and feature-window choices

`reports/risk_threshold_sensitivity.csv` and
`reports/feature_window_sensitivity.csv` vary the elevated-risk quantile
(0.70/0.75/0.80) and the short/long feature windows (5-20, 10-30, 10-60). Neither
overturns the headline: MAE improvement stays in the 17.1%–23.7% band across
non-overlapping offsets. The longer 10-60 window reduces classification recall,
which is the expected cost of over-smoothing — a slower reaction to genuine
turns.

### What would change the conclusion

If the residual distribution were symmetric, the two interval scenarios would
agree and the choice would not matter. If the bootstrap intervals overlapped, the
improvement over the baseline could not be claimed. Both are worth re-checking on
any refit, because they are the checks that would fail first if the relationship
weakened.
