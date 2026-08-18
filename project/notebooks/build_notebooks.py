"""Populate the two course notebooks from the approved skill scaffolds."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = ROOT / "project/notebooks"


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


def save(name: str, cells: list, title: str) -> None:
    path = NOTEBOOKS / name
    notebook = nbf.read(path, as_version=4)
    notebook.cells = cells
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.11"}
    notebook.metadata["title"] = title
    _, notebook = nbf.validator.normalize(notebook)
    nbf.write(notebook, path)


fundamentals = [
    markdown(
        """
# Python Fundamentals for the Weekly ETF Risk Monitor

**Sole author:** Paritosh Dwivedi

## Audience, prerequisites, and learning goals

This tutorial records the Python, NumPy, and pandas foundations used by the cumulative project. It assumes basic Python syntax and a working project environment.

By the end, the reader can:

1. choose suitable Python data structures;
2. replace avoidable loops with NumPy vectorization;
3. inspect, group, and summarize tabular market-like data;
4. import a reusable function from `src/`.
"""
    ),
    markdown(
        """
## Outline

1. Reproducible setup
2. Core Python structures and functions
3. NumPy vectorization
4. pandas inspection and aggregation
5. A small visualization
6. Reusable project utilities
7. Exercise, pitfalls, and extensions
"""
    ),
    code(
        """
# --- run me first ---
from pathlib import Path
import os, sys
if Path.cwd().name == 'notebooks':
    os.chdir('..')
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.utils import clean_column_name

np.random.seed(42)
print('working from:', ROOT.name)
"""
    ),
    markdown(
        """
## 1. Core Python structures and functions

Lists preserve ordered observations, dictionaries attach meaning to values, and functions make repeated calculations explicit and testable.
"""
    ),
    code(
        """
weekly_returns = [0.012, -0.008, 0.004, 0.015, -0.003]
position = {
    'ticker': 'SPY',
    'units': 100,
    'review_frequency': 'weekly',
}

def compound_return(returns):
    # Compound decimal returns over a period.
    return np.prod(1 + np.asarray(returns)) - 1

print(position)
print(f"Compounded return: {compound_return(weekly_returns):.2%}")
"""
    ),
    markdown(
        """
## 2. NumPy vectorization

Vectorized operations apply a transformation to an entire array. They are usually clearer and faster than row-by-row Python loops for numerical work.
"""
    ),
    code(
        """
prices = np.array([100.0, 101.5, 100.8, 102.4, 103.1])
vectorized_returns = prices[1:] / prices[:-1] - 1
loop_returns = np.array([prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))])

assert np.allclose(vectorized_returns, loop_returns)
vectorized_returns
"""
    ),
    markdown(
        """
## 3. pandas inspection and aggregation

The example below uses small, deterministic market-like data. `.info()`, `.describe()`, and missing-value counts are fast first checks before analysis.
"""
    ),
    code(
        """
sample = pd.DataFrame({
    'date': pd.date_range('2026-08-03', periods=10, freq='B'),
    'ticker': ['SPY'] * 5 + ['QQQ'] * 5,
    'return': [0.004, -0.002, 0.007, 0.001, -0.003, 0.006, -0.009, 0.010, 0.002, -0.004],
    'volume_millions': [72, 68, 81, 66, 75, 49, 57, 64, 51, 55],
})

print(sample.dtypes)
display(sample.head())
display(sample[['return', 'volume_millions']].describe().round(3))
print('missing values:', int(sample.isna().sum().sum()))
"""
    ),
    markdown(
        """
## 4. Grouping and interpretation

Grouping answers a comparative question while retaining readable labels.
"""
    ),
    code(
        """
summary = (
    sample.groupby('ticker')
    .agg(
        mean_return=('return', 'mean'),
        return_volatility=('return', 'std'),
        mean_volume_millions=('volume_millions', 'mean'),
    )
    .reset_index()
)
display(summary.round(4))
"""
    ),
    markdown(
        """
## 5. Small visualization

The chart gives a quick view of sign, magnitude, and timing. The cumulative project saves final figures under `reports/images/`.
"""
    ),
    code(
        """
fig, ax = plt.subplots(figsize=(8, 3.5))
for ticker, group in sample.groupby('ticker'):
    ax.plot(group['date'], group['return'], marker='o', label=ticker)
ax.axhline(0, color='black', linewidth=0.8)
ax.set(title='Illustrative daily returns', ylabel='Return', xlabel='Date')
ax.yaxis.set_major_formatter(lambda value, _: f'{value:.1%}')
ax.legend(frameon=False)
ax.grid(axis='y', alpha=0.2)
plt.show()
"""
    ),
    markdown(
        """
## 6. Reusable utility

Reusable behavior belongs in `src/`. The notebook imports and demonstrates the project column-name cleaner instead of copying its implementation.
"""
    ),
    code(
        """
raw_labels = ['Adjusted Close', 'Volume ($)', 'Review Date']
[clean_column_name(label) for label in raw_labels]
"""
    ),
    markdown(
        """
## 7. Exercise

Create a function that returns annualized volatility from decimal daily returns using 252 trading days. Then compare SPY and QQQ in the sample.
"""
    ),
    code(
        """
def annualized_volatility(daily_returns):
    values = np.asarray(daily_returns, dtype=float)
    return values.std(ddof=1) * np.sqrt(252)

exercise_answer = sample.groupby('ticker')['return'].apply(annualized_volatility)
exercise_answer.map(lambda value: f'{value:.1%}')
"""
    ),
    markdown(
        """
## Pitfalls and extension

- **Pitfall:** a random train/test split would mix later market information into an earlier evaluation. The cumulative project uses chronological splits.
- **Pitfall:** mutating a shared DataFrame can create hidden notebook state. Project functions return copies.
- **Extension:** replace the dummy data with a validated raw snapshot, then move repeated transformations into `src/features.py`.

The cumulative project notebook applies these foundations to the full SPY pipeline.
"""
    ),
]


pipeline = [
    markdown(
        """
# Weekly ETF Risk Monitor: End-to-End Project Pipeline

**Sole author:** Paritosh Dwivedi

## Objective and stakeholder question

This notebook builds a reproducible SPY risk-monitoring pipeline for a portfolio manager's weekly review.

**Decision question:** Should the portfolio manager maintain the current SPY exposure or investigate reducing it because near-term risk appears elevated?

**Success criteria:** validated immutable raw data, reproducible processed data, chronological out-of-sample evaluation, a clear current risk signal, and explicit assumptions and limitations.
"""
    ),
    code(
        """
# --- run me first: makes this notebook work wherever it lives ---
from pathlib import Path
import os, sys
if Path.cwd().name == 'notebooks':
    os.chdir('..')
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import pandas as pd
from IPython.display import Image, display

from run_pipeline import run
from src.config import get_settings

settings = get_settings()
print('working from:', ROOT.name)
print('sole author: Paritosh Dwivedi')
"""
    ),
    markdown(
        """
## Analysis plan

1. Acquire or reload a recorded daily SPY snapshot.
2. Validate schema, types, missingness, duplicates, ordering, and price ranges.
3. Clean without modifying the raw artifact.
4. Retain plausible tail observations and flag extreme returns.
5. Build lagged and rolling features without look-ahead.
6. Predict five-day realized volatility with Ridge regression.
7. Classify elevated-risk forecast windows using a training-derived threshold and a documented score cutoff.
8. Purge five sessions between training and holdout targets.
9. Compare with baselines, non-overlapping samples, walk-forward folds, and sensitivity checks.
10. Refit production models on all labeled history and translate the latest result into a stakeholder signal.

The smallest complete baseline is executed before any optional model expansion.
"""
    ),
    markdown(
        """
## 1. Execute the complete reproducible pipeline

The default run uses the latest validated raw snapshot. Pass `refresh=True` only when a new provider pull is intended; each refresh creates a new immutable raw file.
"""
    ),
    code(
        """
metrics = run(refresh=False)
print('pipeline completed for:', metrics['ticker'])
print('generated at:', metrics['generated_at_utc'])
"""
    ),
    markdown("## 2. Data source and validation"),
    code(
        """
data_summary = {
    'provider': metrics['data']['acquisition'].get('provider'),
    'raw_file': metrics['data']['raw_file'],
    'rows': metrics['data']['rows_raw'],
    'date_start': metrics['data']['date_start'],
    'date_end': metrics['data']['date_end'],
    'validation_passed': metrics['data']['raw_validation']['valid'],
    'missing_values': metrics['data']['raw_validation']['missing_values'],
    'duplicate_dates': metrics['data']['raw_validation']['duplicate_dates'],
}
pd.Series(data_summary, name='value').to_frame()
"""
    ),
    markdown(
        """
The raw file is preserved under `data/raw/` with a retrieval timestamp and SHA-256 manifest. Processed outputs are derived by code and can be regenerated.
"""
    ),
    code(
        """
processed = pd.read_parquet(ROOT / metrics['data']['model_dataset_file'])
display(processed[['date', 'adjusted_close', 'daily_return', 'rolling_vol_20', 'drawdown', 'target_next_week_vol']].tail())
print('processed rows:', len(processed))
print('flagged retained return outliers:', metrics['data']['return_outliers_flagged'])
"""
    ),
    markdown("## 3. Market and risk context"),
    code(
        """
display(Image(filename=str(ROOT / 'reports/images/price_and_drawdown.png'), width=900))
"""
    ),
    code(
        """
display(Image(filename=str(ROOT / 'reports/images/volatility_and_risk_threshold.png'), width=900))
"""
    ),
    markdown(
        """
Plausible extremes are retained because tail events are central to risk decisions. Robust outlier location and scale are fit only on the allowed training history during evaluation, then refit on all labeled history for production scoring. The flag supports diagnosis without deleting market stress.
"""
    ),
    code(
        """
display(Image(filename=str(ROOT / 'reports/images/return_distribution.png'), width=800))
"""
    ),
    markdown("## 4. Chronological model evaluation"),
    code(
        """
regression = metrics['models']['regression']
regression_table = pd.DataFrame({
    'Ridge': regression['ridge'],
    'Recent-vol baseline': regression['recent_volatility_baseline'],
    'Historical-mean baseline': regression['historical_mean_baseline'],
}).T
display(regression_table.round(4))
print(f"Ridge MAE improvement vs recent-vol baseline: {regression['ridge_mae_improvement_vs_recent']:.1%}")
"""
    ),
    code(
        """
display(Image(filename=str(ROOT / 'reports/images/regression_predictions.png'), width=900))
"""
    ),
    markdown(
        """
The split is chronological and purged. Because each target uses the next five sessions, a five-row embargo prevents any training target from containing a holdout date. The recent-volatility baseline represents the simple time-series answer; Ridge must improve on it to justify added complexity.
"""
    ),
    code(
        """
pd.Series({
    'Training rows': metrics['models']['train_rows'],
    'Training end': metrics['models']['train_end'],
    'Embargo sessions': metrics['models']['embargo_rows'],
    'Holdout start': metrics['models']['test_start'],
    'Holdout forecast windows': metrics['models']['test_rows'],
}, name='value').to_frame()
"""
    ),
    code(
        """
classification = metrics['models']['classification']
classification_table = pd.DataFrame({
    'Logistic model': classification['logistic'],
    'Prior baseline': classification['prior_baseline'],
}).T
display(classification_table.round(3))
print(classification['score_interpretation'])
"""
    ),
    code(
        """
display(Image(filename=str(ROOT / 'reports/images/classification_confusion_matrix.png'), width=600))
"""
    ),
    markdown(
        """
## 5. Robustness across non-overlapping windows and regimes

Adjacent daily five-session targets overlap. Each offset below samples every fifth holdout row, producing five non-overlapping sequences rather than calling all 835 observations independent weeks.
"""
    ),
    code(
        """
non_overlap = pd.DataFrame(metrics['models']['diagnostics']['non_overlapping_windows'])
display(non_overlap.round(3))
"""
    ),
    code(
        """
yearly = pd.DataFrame(metrics['models']['diagnostics']['calendar_year'])
display(yearly.round(3))
"""
    ),
    markdown(
        """
Year-by-year recall varies materially, so the aggregate score does not imply stable behavior in every regime. The expanding-window test below repeatedly refits on the past, keeps a five-session embargo, and evaluates the next block.
"""
    ),
    code(
        """
walk_forward = metrics['models']['diagnostics']['walk_forward']
display(pd.DataFrame(walk_forward['folds']).round(3))
display(pd.Series(walk_forward['aggregate'], name='aggregate').to_frame())
"""
    ),
    markdown("## 6. Residual, outlier, threshold, and feature-window sensitivity"),
    code(
        """
display(pd.Series(metrics['models']['diagnostics']['residuals'], name='value').to_frame().round(4))
display(pd.DataFrame(metrics['models']['diagnostics']['outlier_feature_ablation']).T.round(4))
"""
    ),
    markdown(
        """
Residuals remain serially correlated, and Ridge underpredicts the highest realized-volatility decile. The outlier flag has only a small incremental effect, so it should not be interpreted as the model's main driver.
"""
    ),
    code(
        """
sensitivity = pd.DataFrame(metrics['sensitivity']['risk_threshold'])
formatted_sensitivity = sensitivity.copy()
for column in formatted_sensitivity.columns:
    formatted_sensitivity[column] = formatted_sensitivity[column].map(lambda value: f'{value:.1%}')
display(formatted_sensitivity)
display(pd.DataFrame(metrics['sensitivity']['feature_windows']).round(4))
"""
    ),
    code(
        """
display(pd.Series(metrics['feature_relationships'], name='correlation').to_frame().round(3))
"""
    ),
    markdown(
        """
Threshold and feature-window choices change precision, recall, and baseline improvement. Standardized volume is more related to absolute same-day return than to current rolling volatility; these are descriptive correlations, not causal claims.
"""
    ),
    markdown("## 7. Current stakeholder signal"),
    code(
        """
snapshot = metrics['latest_risk_snapshot']
pd.Series({
    'As-of date': snapshot['as_of_date'],
    'SPY adjusted close': f"${snapshot['adjusted_close']:,.2f}",
    '20-day annualized volatility': f"{snapshot['rolling_vol_20']:.1%}",
    'Predicted next-five-session volatility': f"{snapshot['predicted_next_five_day_vol']:.1%}",
    'Elevated-risk score': f"{snapshot['elevated_risk_score']:.1%}",
    'Decision cutoff': f"{snapshot['risk_score_cutoff']:.0%}",
    'All-history target threshold': f"{snapshot['risk_threshold_annualized_vol']:.1%}",
    'Classification': snapshot['risk_classification'].upper(),
    'Decision language': snapshot['decision_language'],
}, name='value').to_frame()
"""
    ),
    markdown(
        """
The current signal uses the separate production refit on all 4,175 labeled observations. Holdout metrics above remain tied to the purged evaluation fit.
"""
    ),
    markdown(
        """
## 8. Assumptions, risks, and conclusion

- The five-trading-day horizon approximates a weekly review cycle.
- Provider data and adjusted prices may be revised after retrieval.
- Historical relationships can break during regime changes.
- The 75th-percentile label is training-derived and sensitive to the selected quantile.
- The class-weighted logistic output is a risk score, not a calibrated event probability.
- Ridge materially underpredicts the most volatile realized windows.
- A normal signal does not mean the position is safe; it means the model does not detect elevated relative risk under its historical definition.
- The output is decision support, not an automated trade or guarantee.

The final recommendation is stored in `reports/final_summary.md`. The complete assumptions and risk register are maintained under `docs/`.
"""
    ),
    code(
        """
print(snapshot['decision_language'])
"""
    ),
    markdown(
        """
## Next steps

- Revisit the target threshold if the stakeholder supplies an explicit risk limit.
- Monitor provider schema and model performance after each refresh.
- Add a benchmark ETF only if it improves the decision rather than expanding scope.
- Stop model expansion when added complexity does not improve chronological out-of-sample evidence.
"""
    ),
]


save(
    "python_fundamentals_summary.ipynb",
    fundamentals,
    "Python Fundamentals for the Weekly ETF Risk Monitor",
)
save(
    "project_pipeline.ipynb",
    pipeline,
    "Weekly ETF Risk Monitor: End-to-End Project Pipeline",
)
