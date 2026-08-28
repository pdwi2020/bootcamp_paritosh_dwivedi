# Model interpretation

**Author:** Paritosh Dwivedi

Stage 10a asks what the coefficients say and why these features were chosen. Both
models are fitted inside a `Pipeline` whose first step is a `StandardScaler`, so
every coefficient below is on a **standardised** scale: it is the effect of a one
standard-deviation move in that feature, and magnitudes are directly comparable
across features.

## Ridge regression — next-five-session annualised volatility

| Feature | Coefficient | Reading |
|---|---:|---|
| `ewma_vol_20` | +0.0379 | Dominant. Recent exponentially-weighted volatility is the strongest single predictor of next week's volatility — volatility clusters. |
| `rolling_return_5` | −0.0206 | Negative returns over the past week predict *higher* forward volatility. This is the leverage effect: markets fall faster than they rise. |
| `rolling_vol_5` | +0.0197 | Short-window volatility adds signal beyond the EWMA, capturing faster turns. |
| `drawdown` | −0.0154 | Deeper drawdown (a more negative value) predicts higher volatility, again the leverage effect. |
| `vol_ratio` | −0.0082 | Small. Once both volatility levels are in the model, their ratio adds little. |
| `return_outlier_flag` | +0.0073 | A flagged extreme day nudges the forecast up, but it is not a dominant driver. |
| `rolling_vol_20`, `volume_z_20`, `return_lag_5`, `return_lag_1` | ≤ 0.0067 | Marginal contributions. |
| intercept | +0.1381 | Roughly the unconditional mean annualised volatility. |

**Why these features.** All ten use only information available at the decision
date: lags look backward, rolling windows are trailing. The set deliberately
mixes level (`rolling_vol_20`, `ewma_vol_20`), change (`vol_ratio`,
`rolling_vol_5`), direction (`rolling_return_5`, `drawdown`) and participation
(`volume_z_20`), so the model is not relying on one description of the same
phenomenon.

**What not to conclude.** `rolling_vol_20` carries a small *negative* coefficient
despite volatility being positively autocorrelated. That is a collinearity
artifact — it shares most of its information with `ewma_vol_20` — and is a good
example of why individual coefficients in a correlated feature set should not be
read as isolated causal effects. Ridge shrinks rather than eliminates these, so
the sign is not stable enough to interpret on its own.

## Logistic classification — elevated-risk flag

The ordering is similar but the spread is much wider: `ewma_vol_20` (+1.156)
dominates, followed by `drawdown` (−0.610) and `rolling_return_5` (−0.559).
Direction of travel matters more for the binary elevated/normal decision than it
does for the continuous forecast.

`return_outlier_flag` carries a small **negative** logistic coefficient (−0.162)
while its ridge coefficient is positive. Do not over-read this: the flag fires on
0.74% of rows, so it is estimated from very few observations, and the ablation in
`reports/` shows removing it changes results only slightly. It is retained as
context, not as a driver.

## Trust

The purged chronological split with a five-session embargo means these
coefficients were never fitted on evaluation data. The bootstrap confidence
intervals in `reports/metrics.json` show the ridge MAE interval
[0.0366, 0.0436] does not overlap the baseline's [0.0461, 0.0555], so the
improvement is not sampling noise. The independence assumption is nonetheless
violated — residual lag-1 autocorrelation is 0.747, expected with overlapping
five-day windows — so coefficient standard errors would be too narrow and are
not reported as inference.
