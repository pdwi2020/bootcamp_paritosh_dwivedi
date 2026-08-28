# Stakeholder handoff summary

**Author:** Paritosh Dwivedi
**Project:** Weekly ETF Risk Monitor
**Data through:** 25 August 2026

## 1. Overview and purpose

A portfolio manager reviews SPY exposure once a week and needs to know whether the
coming week looks unusually turbulent before confirming that exposure. This
project answers that question repeatably: each week it forecasts annualised
realised volatility over the next five trading sessions and classifies the week
as normal or elevated.

It is built on 4,186 daily observations from January 2010 to August 2026, and runs
end to end from raw data to a stakeholder summary with one command.

## 2. Key findings and recommendations

- **The model beats the obvious alternative.** Holdout MAE is **0.0399** against
  **0.0506** for a trailing-20-day volatility baseline — a **21%** improvement.
- **That improvement is not luck.** Bootstrap 95% intervals of [0.0366, 0.0436]
  and [0.0461, 0.0555] do not overlap.
- **It catches most elevated weeks:** 67 of 111, at 72.4% balanced accuracy and
  0.779 ROC AUC.
- **Headline accuracy is the wrong metric here.** A model that never warns scores
  86.7%, higher than this one, purely because calm weeks dominate.

**Recommendation:** use the elevated flag as a trigger for a second look before
confirming weekly exposure — not as an instruction to change position. Read it
alongside the current 20-day volatility, which the same report provides.

## 3. Assumptions and limitations

- Adjusted daily prices are accurate enough for a weekly decision; the provider
  may revise history, so each snapshot is hashed and dated.
- Five trading sessions is a usable proxy for the manager's weekly horizon.
- Historical relationships between volatility, returns, drawdown and volume
  persist to some degree.
- One liquid ETF, daily frequency. No intraday data, no options-implied
  volatility, no portfolio-level exposure.
- Extreme days are flagged and **retained**, not deleted, because they are the
  risk being measured.

## 4. Risks and potential issues

- **Weakest where it matters most.** The top realised-volatility decile is
  under-predicted by about **8.5 percentage points**. The tool is least reliable
  in a crisis.
- **Regime dependence.** Calendar-year recall ranges from **33% to 83%**. The
  average conceals that.
- **The score is not a probability.** 0.25 does not mean a 25% chance. It is a
  ranking used with a 0.5 cutoff; its Brier score is 0.142 against a 13.3% event
  rate.
- **"Normal" is not "safe."** It means no flag was raised under the stated
  assumptions — the absence of a warning, not evidence of safety.
- **Residuals are autocorrelated** (lag-1 0.747) because five-day windows overlap,
  so any interval derived from a normality assumption would be too narrow.

## 5. Using the deliverables

| Deliverable | Location | For whom |
|---|---|---|
| Executive summary | `reports/final_summary.md` | The weekly read |
| Slide deck | `reports/stakeholder_presentation.pptx` | The review meeting |
| Figures | `reports/images/` | Charts, including the uncertainty panel |
| Full metrics | `reports/metrics.json` | Anything quantitative; every documented number comes from here |
| Live scoring | `python app.py`, then `POST /predict` | Systems that need a score on demand |
| One-off refresh | `python run_pipeline.py --refresh` | Bringing the data current |

Rerun everything from a fresh clone with `make setup && make pipeline`. The README
carries worked API examples with real responses.

## 6. Suggested next steps

1. **Fix the tail.** Model extreme weeks separately rather than expecting one
   model to cover both regimes — this is the most valuable single improvement.
2. **Calibrate the score** so it can honestly be read as a probability, then
   re-check the Brier score.
3. **Run it live for a quarter** with `docs/monitoring_plan.md` switched on before
   anyone leans on it. Everything reported here is historical testing; behaving
   well on the past is necessary, not sufficient.
4. **Widen coverage** beyond a single ETF once the above holds.
