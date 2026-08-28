# Homework 11: Evaluation & Risk Communication

**Author:** Paritosh Dwivedi

Quantifies uncertainty with a bootstrap, compares two competing assumptions, checks subgroups for
hidden failure, and writes the result for a stakeholder.

## Files

- `homework11_evaluation-risk-communication_submission.ipynb` — the submission.
- `src/evaluation.py` — `bootstrap_ci`, `gaussian_ci`, `mae`, `rmse`, `subgroup_metrics`, imported by
  the notebook rather than defined inline.
- `data/raw/spy_daily_stage11.csv` — the immutable snapshot.
- `data/processed/stage11_model_dataset.parquet` — the derived feature table.

## What it found

Holdout MAE 0.0498. Bootstrap and Gaussian intervals for that metric agree closely (widths 0.0097 vs
0.0100), which is itself the finding: for a mean-style metric over 726 observations the normal
approximation is adequate. Adding polynomial terms moves MAE by 0.0007 and the intervals overlap, so
the simpler model stands.

The subgroup diagnostic is where the aggregate breaks down, and the two failures are different:

| Regime | n | MAE | Mean residual |
|---|---:|---:|---:|
| calm | 164 | 0.0495 | **+0.0217** |
| normal | 457 | 0.0375 | −0.0028 |
| stressed | 105 | **0.1036** | −0.0028 |

The stressed tercile carries nearly three times the normal-regime error, but roughly *unbiased* — it
is imprecise, not systematically wrong. The calm tercile is the opposite: moderate error with a
clearly positive bias, so realised volatility comes in above the forecast. One aggregate number hides
both.
