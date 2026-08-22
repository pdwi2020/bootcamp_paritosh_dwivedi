# Outlier assumptions

**Author:** Paritosh Dwivedi

## What counts as an outlier here

An observation is flagged when its daily log return sits more than six robust standard deviations
from the training-period median, measured with the median absolute deviation rather than the mean
and standard deviation. MAD is used because the mean and standard deviation are themselves dragged
by the very observations being tested, so a handful of large moves can hide the rest.

The location and scale parameters are fit on the purged training window only and then applied to
later observations. Fitting them on the full history would let the evaluation period influence its
own flag, which is the same leakage the chronological split exists to prevent.

## Why extremes are flagged and retained, not removed

This project forecasts near-term volatility so a portfolio manager can decide whether risk is
elevated. The largest daily moves are the periods it exists to catch. Deleting them would train the
model on a market that never has a bad week, lower the measured error, and make the monitor
confidently wrong exactly when it matters.

So the flag is carried as a feature, `return_outlier_flag`, and no row is dropped for being extreme.
Rows are removed only when they are implausible as data rather than as markets: non-positive prices,
negative volume, or internally inconsistent OHLC values. That distinction is the whole policy —
**a market event is kept, a data error is removed.**

## What the flag is worth

The ablation in `reports/metrics.json` under `models.diagnostics.outlier_feature_ablation` compares
the model with and without the flag. The two are close, so the flag is retained as context rather
than presented as a dominant signal. Reporting that honestly matters more than claiming the feature
earns its place.

## Risks if these assumptions are wrong

| Risk | Consequence | What would show it |
|---|---|---|
| The six-MAD threshold is too loose | Genuine shocks are treated as ordinary and never flagged | Flagged count falls near zero in a volatile period |
| The threshold is too tight | Ordinary days are flagged, and the feature becomes noise | Flagged share climbs well above the historical rate |
| Training-period scale is unrepresentative | Flags drift as the market regime changes | Flag rate differs sharply between train and holdout |
| A provider error looks like a market event | A bad print is kept and modelled as signal | Validation catches OHLC inconsistency before this stage |

The threshold is a judgment call, not a fact about markets. It is recorded in
`metrics.json` under `models.outlier_preprocessing` so any published result can be traced back to
the exact parameters that produced it.
