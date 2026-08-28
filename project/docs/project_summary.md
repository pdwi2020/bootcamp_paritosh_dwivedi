# Weekly ETF Risk Monitor — project summary

**Author:** Paritosh Dwivedi
**Audience:** a non-technical reader who wants to know what this is, what it found, and how far to trust it.

## The problem

A portfolio manager reviews SPY exposure once a week. Daily returns describe what
already happened; they do not answer the question the manager actually faces,
which is whether the coming week looks unusually turbulent and therefore warrants
a closer look before exposure is confirmed.

This project builds a repeatable way to answer that. Each week it produces two
things: a forecast of how volatile the next five trading sessions are likely to
be, and a normal-or-elevated classification with the reasoning behind it.

## What I did

I pulled sixteen years of daily SPY price and volume history — 4,186 trading days
from January 2010 to August 2026 — and built a pipeline that runs end to end from
raw data to a stakeholder summary.

The work follows the course lifecycle. Data is acquired with a recorded
fingerprint so any result can be traced to the exact input that produced it.
Cleaning rules are written down rather than implied. Extreme days are flagged but
deliberately **kept**, because in a tool designed to measure risk, deleting the
worst days would remove the thing being measured. Ten features are derived, every
one of them using only information a person would actually have on the day the
decision is made.

Two models run on those features: one predicting the level of next week's
volatility, and one classifying the week as elevated or not.

## What I found

**The model beats the obvious alternative.** A natural baseline is to assume next
week looks like the last twenty days. The model's average error is 0.0399 against
that baseline's 0.0506 — about 21% better. I checked whether that gap could be
luck by resampling the test data two thousand times; the two ranges do not
overlap, so the improvement is real rather than noise.

**It catches most elevated weeks, at the cost of false alarms.** It identifies 67
of the 111 genuinely elevated weeks in the test period. It also raises alarms
that do not materialise. For a monitoring tool that trade is the right way round:
a missed warning is more costly than an unnecessary second look.

**The headline accuracy figure is misleading, and I did not use it.** A model
that simply never warns scores 86.7% accuracy, higher than mine, purely because
calm weeks are common. That number is worthless here. I report balanced accuracy
and recall instead, which cannot be inflated that way.

## What I would not rely on

**It is weakest exactly where it matters most.** In the most volatile weeks, the
forecast is too low by around 8.5 percentage points. The tool is least dependable
in a crisis, which is precisely when someone would most want to lean on it.

**Performance varies a lot by year.** It caught 83% of elevated weeks in one year
and 33% in another. The average hides that. Anyone using this should expect
periods where it works poorly.

**The risk score is not a probability.** A score of 0.25 does not mean a 25%
chance of a bad week. It is a ranking used to sort weeks and apply a cutoff.
Reading it as a probability would overstate what it knows.

**"Normal" is not "safe."** A normal reading means no elevated flag was raised
under the stated assumptions. It is the absence of a warning, not evidence that
nothing will happen.

**One asset, one horizon, daily data.** No intraday data, no options-implied
information, no portfolio-level view. Relationships learned from the past can
weaken when markets change character.

## What I would do next

Three things, in order of value. First, address the tail weakness directly, since
that is where the tool currently fails — likely by modelling extreme weeks
separately rather than expecting one model to cover both regimes. Second,
calibrate the risk score so it can honestly be read as a probability. Third,
widen coverage beyond a single ETF.

Before any of that, it needs to run for a quarter against live data with the
monitoring in `docs/monitoring_plan.md` switched on. Everything reported here
comes from historical testing. Behaving well on the past is a necessary condition,
not a sufficient one.
