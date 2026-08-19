# Data dictionary

**Author:** Paritosh Dwivedi

| Field | Meaning | Stage |
|---|---|---|
| `date` | Trading date | Raw |
| `open`, `high`, `low`, `close` | Daily market prices | Raw |
| `adjusted_close` | Close adjusted by the provider for applicable corporate actions | Raw |
| `volume` | Daily traded volume | Raw |
| `daily_return` | One-day percentage price change | Feature |
| `log_return` | One-day log price change | Feature |
| `return_lag_1`, `return_lag_5` | Lagged daily returns | Feature |
| `rolling_return_5` | Five-day trailing percentage return | Feature |
| `rolling_vol_5`, `rolling_vol_20` | Annualized trailing log-return volatility | Feature |
| `ewma_vol_20` | Exponentially weighted trailing volatility | Feature |
| `vol_ratio` | Five-day volatility divided by twenty-day volatility | Feature |
| `drawdown` | Percentage decline from the historical running maximum | Feature |
| `volume_z_20` | Volume standardized against the trailing twenty-day window | Feature |
| `return_outlier_flag` | Robust-MAD indicator for an extreme retained return; parameters are fit only on the allowed training history | Feature |
| `target_next_week_vol` | Annualized realized volatility over the next five trading days; adjacent daily targets overlap | Target |
| `target_next_week_return` | Sum of daily returns over the next five trading days | Supporting target |
| `elevated_risk_score` | Class-weighted logistic score used with a 0.50 cutoff; not a calibrated probability | Prediction |
