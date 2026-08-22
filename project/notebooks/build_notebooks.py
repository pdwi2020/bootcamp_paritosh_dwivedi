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
# Python fundamentals for the Weekly ETF Risk Monitor

**Author:** Paritosh Dwivedi

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
## Tutorial outline

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
import os
import sys
from pathlib import Path

if Path.cwd().name == 'notebooks':
    os.chdir('..')
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
# Weekly ETF Risk Monitor: end-to-end project pipeline

**Author:** Paritosh Dwivedi

## Objective and stakeholder question

This notebook builds a reproducible SPY risk-monitoring pipeline for a portfolio manager's weekly review.

**Decision question:** Should the portfolio manager maintain the current SPY exposure or investigate reducing it because near-term risk appears elevated?

**Success criteria:** validated immutable raw data, reproducible processed data, chronological out-of-sample evaluation, a clear current risk signal, and explicit assumptions and limitations.
"""
    ),
    code(
        """
# --- run me first: makes this notebook work wherever it lives ---
import os
import sys
from pathlib import Path

if Path.cwd().name == 'notebooks':
    os.chdir('..')
ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from IPython.display import Image, display

from run_pipeline import run
from src.config import get_settings

settings = get_settings()
print('working from:', ROOT.name)
print('author: Paritosh Dwivedi')
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
    markdown(
        """
## 3. Storage layer round trip

This section exercises `src/storage.py` directly so the Stage 05 storage work is visible rather than hidden inside the pipeline call. Directories come from `.env` through `get_settings()`, so no absolute path is written anywhere.
"""
    ),
    code(
        """
from src.storage import read_dataframe, write_dataframe

print('raw directory     :', settings.raw_dir.relative_to(ROOT))
print('processed directory:', settings.processed_dir.relative_to(ROOT))

storage_demo = processed[['date', 'adjusted_close', 'rolling_vol_20']].tail(5).reset_index(drop=True)
# A categorical column makes the format contrast visible: Parquet stores the schema,
# CSV stores only text and leaves pandas to guess on the way back in.
storage_demo['risk_band'] = pd.Categorical(
    ['normal', 'normal', 'elevated', 'normal', 'elevated'],
    categories=['normal', 'elevated'],
)
demo_csv = write_dataframe(storage_demo, settings.processed_dir / 'storage_roundtrip_demo.csv')
demo_parquet = write_dataframe(storage_demo, settings.processed_dir / 'storage_roundtrip_demo.parquet')
print('wrote:', demo_csv.name, 'and', demo_parquet.name)
"""
    ),
    code(
        """
from_csv = read_dataframe(demo_csv)
from_parquet = read_dataframe(demo_parquet)

print('shapes match original:', from_csv.shape == storage_demo.shape == from_parquet.shape)
display(
    pd.DataFrame(
        {
            'original': storage_demo.dtypes.astype(str),
            'from_csv': from_csv.dtypes.astype(str),
            'from_parquet': from_parquet.dtypes.astype(str),
        }
    )
)
"""
    ),
    markdown(
        """
Both formats reload to the same shape, but not to the same schema. Parquet stores the dtypes alongside the values, so `risk_band` returns as a category. CSV stores text, so the same column returns as a plain object and the ordered category is gone; the date survives only because `read_dataframe` parses that column by convention.

That difference is the reason for the split: CSV stays the transparent, human-readable exchange format for `data/raw/`, and Parquet carries typed derived tables in `data/processed/` where dtype fidelity matters to the next stage.
"""
    ),
    markdown(
        """
## 4. Preprocessing transformations

This section applies `clean_market_data` from `src/cleaning.py` to the immutable raw snapshot and compares the table before and after. The raw file is only read; cleaning returns a new frame and never edits `data/raw/`.
"""
    ),
    code(
        """
from src.cleaning import clean_market_data

raw_frame = read_dataframe(ROOT / metrics['data']['raw_file'])
cleaned_frame, cleaning_report = clean_market_data(raw_frame)

comparison = pd.DataFrame(
    {
        'raw': [
            len(raw_frame),
            int(raw_frame.isna().sum().sum()),
            int(raw_frame['date'].duplicated().sum()),
        ],
        'cleaned': [
            len(cleaned_frame),
            int(cleaned_frame.isna().sum().sum()),
            int(cleaned_frame['date'].duplicated().sum()),
        ],
    },
    index=['rows', 'missing values', 'duplicate dates'],
)
display(comparison)
"""
    ),
    code(
        """
display(pd.Series(cleaning_report['policy'], name='cleaning policy').to_frame())
print('rows removed:', cleaning_report['rows_removed'])
print('date range after cleaning:', cleaning_report['date_start'], 'to', cleaning_report['date_end'])
"""
    ),
    markdown(
        """
The recorded snapshot needs no repairs, which is the result a validated ingestion layer should produce. To show the transformations actually doing work, the cell below injects the four defect types the policy names into a throwaway copy. `data/raw/` is untouched.
"""
    ),
    code(
        """
damaged = raw_frame.copy()
damaged['date'] = damaged['date'].astype(object)                  # allow a bad date to be written
damaged.loc[len(damaged)] = damaged.iloc[-1]                      # duplicate date
damaged.iloc[0, damaged.columns.get_loc('close')] = -5.0          # non-positive price
damaged.iloc[1, damaged.columns.get_loc('volume')] = -100         # negative volume
damaged.iloc[2, damaged.columns.get_loc('high')] = 0.01           # high below low
damaged.iloc[3, damaged.columns.get_loc('date')] = 'not-a-date'   # unparseable date

repaired, damage_report = clean_market_data(damaged)

display(
    pd.DataFrame(
        {
            'damaged': [len(damaged), int(damaged['date'].astype(str).duplicated().sum())],
            'repaired': [len(repaired), int(repaired['date'].duplicated().sum())],
        },
        index=['rows', 'duplicate dates'],
    )
)
print('rows removed by the cleaner:', damage_report['rows_removed'])
"""
    ),
    markdown(
        """
The cleaner removes all five defective rows and leaves the rest untouched, returning a new frame each time. The original `raw_frame` still has its full row count, which is what "copy-safe" means in practice.
"""
    ),
    markdown(
        """
**Assumptions made during cleaning.** Required fields must parse as dates and numbers, so unparseable rows are dropped rather than guessed. Non-positive prices, negative volume, and internally inconsistent OHLC rows are treated as provider errors, not market events. A duplicate date keeps the final provider record because later records reflect corrections. A missing adjusted close falls back to the close.

Extreme returns are a different matter and are deliberately **not** removed here. They are flagged in `src/outliers.py` and retained, because a monitor built to detect elevated risk would understate exactly the periods it exists to catch if its largest moves were deleted.
"""
    ),
    markdown(
        """
## 5. Outlier analysis

Stage 07 work, run directly from `src/outliers.py`. The parameters are fit on the purged training
window only, then applied to later rows, so the evaluation period never influences its own flag.
"""
    ),
    code(
        """
from src.outliers import add_return_outlier_flag, fit_return_outlier_parameters

train_returns = processed.loc[: metrics['models']['train_rows'] - 1, 'log_return']
outlier_params = fit_return_outlier_parameters(train_returns)
flagged = add_return_outlier_flag(processed, parameters=outlier_params)

print('fitted on training rows only:', len(train_returns))
print(f"median {outlier_params.median:.6f} | MAD {outlier_params.mad:.6f}"
      f" | threshold {outlier_params.threshold:.1f}")
print('flagged observations:', int(flagged['return_outlier_flag'].sum()))
"""
    ),
    code(
        """
kept = flagged.loc[flagged['return_outlier_flag'] == 0, 'daily_return']
dropped = flagged.loc[flagged['return_outlier_flag'] == 1, 'daily_return']
display(
    pd.DataFrame(
        {
            'all observations': flagged['daily_return'].describe(),
            'excluding flagged': kept.describe(),
        }
    ).round(4)
)
print(f"largest flagged move: {dropped.abs().max() * 100:.2f}%")
"""
    ),
    markdown(
        """
Excluding the flagged days barely moves the centre but visibly shrinks the tails, which is the point:
those days carry most of the risk information. They are flagged and kept, never dropped. The policy
and the risks of getting the threshold wrong are written up in `docs/outliers.md`.
"""
    ),
    markdown(
        """
## 6. Exploratory data analysis

Stage 08 work, run from `src/eda.py`. `eda_summary` profiles the frame without modifying it and
names the columns that should be resolved before feature engineering.
"""
    ),
    code(
        """
from src.eda import eda_summary

eda = eda_summary(processed)
print('shape:', eda['shape'])
print('columns with missing values:', {k: v for k, v in eda['missing'].items() if v})
display(
    eda['numeric_profile']
    .loc[
        ['daily_return', 'rolling_vol_5', 'rolling_vol_20', 'drawdown', 'target_next_week_vol'],
        ['mean', 'std', 'min', 'max', 'skew', 'kurtosis'],
    ]
    .round(4)
)
"""
    ),
    code(
        """
display(pd.Series(eda['attention'], name='columns').to_frame())
"""
    ),
    markdown(
        """
Daily returns are mildly left skewed with kurtosis far above the normal value of zero, which is the
statistical statement of fat tails and the reason the outlier policy exists. Realized volatility is
strongly right skewed: most weeks are calm and a few are not, so the mean overstates the typical
week. The flagged columns are constants that record the run configuration, not measurements, so they
are correctly excluded from the feature set.
"""
    ),
    markdown(
        """
## 7. Feature engineering

Stage 09 work, run from `src/features.py`. Every feature uses contemporaneous or past information
only, so nothing here can see the forecast window it is trying to predict.
"""
    ),
    code(
        """
from src.features import build_features

# The pipeline builds features first, then attaches the outlier flag, so mirror
# that order here or the flag is missing from the model's feature list.
engineered = add_return_outlier_flag(build_features(cleaned_frame), parameters=outlier_params)
feature_columns = metrics['models']['feature_columns']
print('engineered rows:', len(engineered))
print('features used by the model:', len(feature_columns))
display(engineered[feature_columns].tail(3).round(4))
"""
    ),
    code(
        """
correlations = (
    engineered[feature_columns + ['target_next_week_vol']]
    .corr()['target_next_week_vol']
    .drop('target_next_week_vol')
    .sort_values(ascending=False)
)
display(correlations.round(3).to_frame('correlation with next-week volatility'))
"""
    ),
    markdown(
        """
The trailing volatility measures correlate most strongly with next-week realized volatility, which is
what makes the recent-volatility baseline hard to beat. Drawdown and standardized volume add a
different kind of information: they rise in stressed markets that trailing volatility has not caught
up with yet. Feature definitions and the reasoning behind each one are tabulated in `README.md`.
"""
    ),
    markdown("## 8. Market and risk context"),
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
    markdown("## 9. Chronological model evaluation"),
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
## 10. Robustness across non-overlapping windows and regimes

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
    markdown("## 11. Residual, outlier, threshold, and feature-window sensitivity"),
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
    markdown("## 12. Current stakeholder signal"),
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
## 13. Assumptions, risks, and conclusion

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
    "Python fundamentals for the Weekly ETF Risk Monitor",
)
save(
    "project_pipeline.ipynb",
    pipeline,
    "Weekly ETF Risk Monitor: end-to-end project pipeline",
)
