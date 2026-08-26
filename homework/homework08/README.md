# Homework 08: exploratory data analysis

This homework profiles SPY alongside the VIX and extracts the profiling logic into a module so the same summary can be run on any frame.

## Files

- `homework08_exploratory-data-analysis_submission.ipynb` covers the structural first look, numeric and categorical profiles, distributions, bivariate relationships, a time-series read, a correlation matrix, and the closing insights.
- `src/eda.py` holds the reusable helper. `eda_summary(df, numeric_cols=None)` returns shape, dtypes, missing counts, and a numeric profile extended with skew and kurtosis. `columns_needing_attention(df)` is the stretch goal: it flags columns that will cause trouble in Stage 09, using `HIGH_MISSING_FRACTION = 0.05`, `NEAR_ZERO_VARIANCE = 1e-12`, and `DOMINANT_CATEGORY_FRACTION = 0.95`.

`_moment()` returns NaN for constant columns rather than letting `scipy.stats` emit a catastrophic-cancellation warning on a series with no variance. A helper that prints warnings during a clean run trains the reader to ignore warnings.

## Why two instruments

SPY and the VIX trade on slightly different calendars, so they are joined inner on date rather than concatenated. The VIX also supplies the categorical column the rubric asks for: a volatility-regime band derived from its level, which gives the value-counts and encoding requirements something real to describe instead of a synthetic label.

The time-series section reads the level explicitly for trend, seasonality, and level shifts, because a correlation matrix computed on a series with a regime shift describes neither regime.

## A note on this folder's structure

`src/eda.py` is present deliberately, and it is worth recording why, because two course documents disagree.

- The **Stage 08 homework sheet** requires it: *"src/eda.py holding a reusable eda_summary(df), imported into your notebook"*, and its rubric awards *"(10) Organization and readability, and src/eda.py imports cleanly"*.
- The **course git repository structure** document lists homework08 in its per-week folder table as *"(notebook only)"*.

I followed the homework sheet, since the module is a graded requirement there. The structure document asks students to report exactly this kind of inconsistency: *"If you see anything that seems inconsistent with this document, please let me know so I can correct it."* This note is that report, and the deviation is limited to `src/` alone.

Paritosh Dwivedi is the author and retains responsibility for understanding, validating, and presenting this work.
