# Weekly volatility outlook - stakeholder report

**Author:** Paritosh Dwivedi
**Data through:** 2026-08-18   |   **Holdout:** 726 sessions

## Executive summary

1. Volatility is predictable enough to rank weeks, with a typical error of
   5.0 volatility points - not precise enough to size positions on.
2. The model is roughly three times less accurate in the most turbulent third of weeks
   (10.4 vs
   3.8 volatility points).
3. The conclusion is robust to the analyst choices tested: no alternative assumption moved MAE by
   more than 0.45 volatility points.

## Charts

| Figure | What it shows |
|---|---|
| `reports/images/risk_return.png` | Volatility predicts dispersion, not direction |
| `reports/images/error_by_regime.png` | Error concentrated in turbulent weeks |
| `reports/images/forecast_vs_actual.png` | Forecast tracks the level, lags the spikes |
| `reports/images/tornado_assumptions.png` | Sensitivity to alternative assumptions |

## Assumptions and risks

- Trailing information only; the model cannot anticipate a shock, only respond to one.
- Regime terciles are cut on training data, so labels use no future information.
- One ETF and one historical period. Relationships may weaken in an unseen regime.
- The stressed bucket is the smallest, so its error estimate is the least stable.

## Sensitivity summary

| Scenario | MAE | Delta vs baseline | % change |
|---|---:|---:|---:|
| Baseline (linear, 75/25 split) | 0.0498 | +0.0000 | +0.0% |
| Polynomial (degree 2) | 0.0505 | +0.0007 | +1.4% |
| Longer training window (80/20) | 0.0534 | +0.0036 | +7.3% |
| Single feature (trailing vol only) | 0.0543 | +0.0045 | +9.0% |

## Decision implications

Use the forecast to rank weeks, not to size exposure. Discount it when trailing volatility is
already in the top tercile. Expect it to lag shocks. A quiet reading is the absence of a warning,
not evidence of safety.
