# Homework 03: Python fundamentals

**Author:** Paritosh Dwivedi

This homework covers the NumPy and pandas operations the rest of the course depends on, then extracts the reusable parts into a module so the notebook is not the only place the logic lives.

## Files

- `homework03_python-fundamentals_submission.ipynb` works through array operations, a loop-versus-vectorisation timing comparison, dataset inspection, grouped summary statistics, and a saved figure.
- `src/utils.py` holds the two functions worth reusing: `get_summary_stats(df)` returns the descriptive table, and `clean_column_names(df)` normalises header text so downstream code can rely on predictable column names.
- `data/raw/starter_data.csv` is the provided input and is left unmodified.
- `data/processed/summary.csv` and `data/processed/category_mean_values.png` are the reproducible outputs.

## Why vectorisation is measured, not asserted

The notebook times the same computation written as a Python loop and as a NumPy expression rather than stating that one is faster. The gap comes from moving the iteration into compiled code and operating on contiguous memory instead of per-element Python objects. The point carries into the project: the risk monitor computes rolling statistics over thousands of daily observations, and the same habit keeps the pipeline fast enough to re-run on every change.

## Connection to the project

`clean_column_names` is the direct ancestor of the header handling in `project/src/cleaning.py`, and the separation of raw inputs from derived outputs is the convention the project keeps throughout.
