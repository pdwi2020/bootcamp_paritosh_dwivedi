# Homework 10a: Modeling — Linear Regression

**Author:** Paritosh Dwivedi

Fits a linear regression on SPY data to forecast next-week realised volatility, then diagnoses the
four OLS assumptions from the residuals and states plainly whether the model can be trusted.

## Files

- `homework10a_modeling-linear-regression_submission.ipynb` — the whole submission. Under the course
  structure homework10a is notebook-only, so the data is acquired in memory and nothing is written
  to disk.

## What the diagnostics found

R-squared 0.264 and RMSE 0.0868 on the held-out final 20%. Two of the four assumptions fail:
**independence**, because the five-day target windows overlap so consecutive residuals are
mechanically related (lag-1 autocorrelation 0.75), and **homoscedasticity**, because volatility of
volatility rises with its level. The consequence is that no p-value or confidence interval from this
fit should be reported; point predictions remain usable for ranking.

An earlier draft scored R-squared 0.81 by building the target as `ret.shift(-1).rolling(5).std()`.
That expression looks forward-looking but at row *t* covers days *t-3* to *t+1*, so the target
overlapped its own predictors. The correct form is `ret.rolling(5).std().shift(-5)`. The notebook
records this, because a suspiciously good score is the first symptom of a leak.
