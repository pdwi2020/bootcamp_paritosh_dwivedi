# Monitoring plan

**Author:** Paritosh Dwivedi

The model closest to production-ready is the production refit persisted at
`model/model.pkl` and served by `app.py`. If it were deployed, the following is
what I would watch and what I would do about it.

## Failure modes, metrics and starting thresholds

| # | Failure mode | Layer | Metric | Starting threshold |
|---|---|---|---|---|
| 1 | Provider outage or stale prices | Data | Age of newest row at scoring time | > 36 hours on a trading day |
| 2 | Schema drift from the provider | Data | Hash of the column-name/dtype signature | Any change from the recorded signature |
| 3 | Silent parse failure producing gaps | Data | Null fraction across the ten model features | > 1% in any feature |
| 4 | Regime shift degrading the model | Model | 60-session rolling MAE vs the 0.0399 holdout value | > 0.055 for five consecutive sessions |
| 5 | Score drift making the 0.5 cutoff wrong | Model | Population stability index on `ewma_vol_20` | PSI > 0.10 warn, > 0.25 alert |
| 6 | Serving failure | System | `/predict` error rate and p95 latency | > 2% errors, or p95 > 500 ms |

Thresholds are deliberately starting points, not settled values. Each would be
re-tuned after a month of observed data.

## Alerting and first response

Alerts route to the model owner by email, with the on-call operator copied for
items 1, 2 and 6. The first runbook step is always the same: check the data layer
before touching the model, because most apparent model failures are stale or
malformed inputs. If the data layer is clean and item 4 or 5 has fired, fall back
to the trailing-20-day volatility baseline — it is already implemented, needs no
fitting, and its holdout MAE of 0.0506 is a known quantity.

## Retraining triggers

Retrain when any of: PSI on `ewma_vol_20` exceeds 0.25; rolling MAE stays above
0.055 for ten sessions; or 90 days elapse since the last refit, whichever comes
first. Retraining is never automatic — a refit is proposed, reviewed against the
purged holdout, and approved before it replaces `model/model.pkl`.

## Ownership

Paritosh Dwivedi owns the model, the dashboards and the retraining decision. The
on-call operator owns detection and rollback and may revert to the previous
`model.pkl` without approval; re-deploying a *new* model requires review. Issues
are logged in the repository issue tracker, and every deployment or rollback is
recorded in `docs/decision_log.md` so the change history and the reasoning stay
in one place.
