# Weekly ETF risk monitor: portfolio manager brief

**To:** Portfolio manager  
**From:** Paritosh Dwivedi  
**Review cadence:** Weekly  
**Decision supported:** Whether current SPY exposure needs additional investigation before the weekly review

## Decision context

Each week, you need to distinguish routine market movement from conditions that justify a closer look at SPY exposure. The current workflow can be inconsistent: raw returns do not translate directly into next-week volatility, recent calm can create false reassurance, and an ad hoc review makes it difficult to explain why one week received attention while another did not. The cost of a missed elevated-risk period is a late review of concentration, liquidity, or available risk controls. The cost of too many false alarms is attention diverted from other portfolio risks.

The monitor narrows this problem to one recurring question: based only on information available now, does the next five trading sessions appear normal or elevated relative to the historical SPY risk definition?

## What the monitor gives you

Before the weekly review, the monitor provides:

- a forecast of next-five-session annualized realized volatility;
- a normal-risk or elevated-risk flag;
- an elevated-risk score and its fixed decision threshold;
- recent return, drawdown, realized-volatility, and volume context;
- a short interpretation that states assumptions, uncertainty, and relevant limitations.

If the signal is elevated, the appropriate decision is to open a deeper review. That review can examine concentration, liquidity, planned trades, and permitted hedging or exposure changes before any action is proposed. If the signal is normal, the model alone creates no trade instruction. You continue monitoring and maintain exposure only within the existing mandate. Recording the signal and rationale each week also makes later review of good calls, misses, and false alarms possible.

## What it does not do

The monitor does not execute trades, optimize the portfolio, estimate causal effects, predict returns, or guarantee that a normal period is safe. It does not incorporate intraday conditions, news, options-implied information, or the rest of the portfolio. The elevated-risk score is a ranking and decision score from a classification model, not a calibrated event probability. A score of 60% must not be presented as a 60% chance of a loss, crisis, or volatility event.

The output is decision support. Investment judgment, mandate limits, compliance requirements, liquidity constraints, and the firm's approval process remain controlling.

## Trust conditions

You should stop relying on the signal and require investigation if any of the following occurs:

- the latest source data is stale, incomplete, fails schema checks, or cannot be tied to a dated raw snapshot;
- the forecast no longer improves on the trailing 20-day volatility baseline over an agreed monitoring window;
- elevated-risk recall or balanced accuracy deteriorates materially, especially through repeated missed-risk episodes;
- high-volatility periods show persistent underprediction that is not visible in the summary;
- small changes to the training window, feature windows, or risk threshold reverse the decision repeatedly;
- a model or data update cannot be reproduced from recorded inputs and code;
- the score is communicated as a calibrated probability or used as an automatic trade instruction.

Until the issue is resolved, use the monitor as context only and fall back to the established review process. Trust depends on fresh validated data, chronological out-of-sample evidence, transparent comparisons with simple baselines, stable decision rules, and visible limitations.
