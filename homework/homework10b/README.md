# Homework 10b: Modeling — Time Series & Classification

**Author:** Paritosh Dwivedi

Track chosen: **classification** — predict whether SPY closes up or down on the next session.

## Files

- `homework10b_modeling-time-series-and-classification_submission.ipynb` — the whole submission.
  homework10b is notebook-only under the course structure, so data is acquired in memory.

## Approach

Six trailing features (two lags, a rolling mean, a rolling standard deviation, momentum and a volume
z-score), each ending in `.shift(1)` so the value used at row *t* was observable at *t-1*. The target
uses `.shift(-1)`, which belongs only in a target. A time-aware 75/25 split preserves order, and a
`Pipeline` puts the `StandardScaler` inside the fit so no test statistics reach it.

## The honest result

Accuracy **0.5612** against a majority-class baseline of **0.5722** — the model is 1.1 points *worse*
than a rule that says "up" every day. Recall 0.945 with precision 0.570 explains why: it has learned
to say "up" almost always. F1 of 0.711 looks respectable and is meaningless here, because it is high
precisely because the model stopped discriminating.

This is the correct answer rather than a bug. Next-day equity direction from daily bars is close to a
coin flip, and a reported high accuracy on this task usually indicates leakage.
