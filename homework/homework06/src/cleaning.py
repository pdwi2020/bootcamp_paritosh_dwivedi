"""Copy-safe preprocessing functions for tabular data."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def fill_missing_median(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a copy with numeric missing values filled by column medians.

    When ``columns`` is ``None``, every numeric column is filled. Otherwise,
    each named column must exist and be numeric; nonnumeric columns raise a
    ``TypeError`` because their medians are undefined.
    """

    result = df.copy(deep=True)
    if columns is None:
        target_columns = result.select_dtypes(include="number").columns.tolist()
    else:
        if isinstance(columns, str):
            raise TypeError("columns must be a sequence of column names, not a string")
        target_columns = list(columns)
        unknown_columns = [
            column for column in target_columns if column not in result.columns
        ]
        if unknown_columns:
            raise KeyError(f"Unknown columns: {unknown_columns}")
        nonnumeric_columns = [
            column
            for column in target_columns
            if not pd.api.types.is_numeric_dtype(result[column])
        ]
        if nonnumeric_columns:
            raise TypeError(
                f"Median fill requires numeric columns: {nonnumeric_columns}"
            )

    for column in target_columns:
        result[column] = result[column].fillna(result[column].median())
    return result


def drop_missing(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
    threshold: float | None = None,
) -> pd.DataFrame:
    """Return a copy after applying one of two missing-value drop policies.

    With no ``threshold``, rows are dropped when they contain a missing value
    in any column, or only in ``columns`` when that sequence is supplied. With
    a ``threshold``, row dropping is not performed. Instead, columns whose
    missing fraction strictly exceeds the threshold are dropped; ``columns``
    optionally limits which columns are candidates. The threshold must be in
    the inclusive interval from 0 to 1.
    """

    result = df.copy(deep=True)
    if isinstance(columns, str):
        raise TypeError("columns must be a sequence of column names, not a string")

    target_columns = result.columns.tolist() if columns is None else list(columns)
    unknown_columns = [
        column for column in target_columns if column not in result.columns
    ]
    if unknown_columns:
        raise KeyError(f"Unknown columns: {unknown_columns}")

    if threshold is not None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1 inclusive")
        missing_fraction = result[target_columns].isna().mean()
        columns_to_drop = missing_fraction[missing_fraction > threshold].index.tolist()
        return result.drop(columns=columns_to_drop)

    subset = None if columns is None else target_columns
    return result.dropna(subset=subset)


def normalize_data(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a copy with numeric columns min-max scaled to the interval [0, 1].

    When ``columns`` is ``None``, every numeric column is scaled. Otherwise,
    each named column must exist and be numeric. A constant column has no
    meaningful range, so its nonmissing values are mapped to 0.0 while missing
    values remain missing. This avoids division by zero and generated NaNs.
    """

    result = df.copy(deep=True)
    if columns is None:
        target_columns = result.select_dtypes(include="number").columns.tolist()
    else:
        if isinstance(columns, str):
            raise TypeError("columns must be a sequence of column names, not a string")
        target_columns = list(columns)
        unknown_columns = [
            column for column in target_columns if column not in result.columns
        ]
        if unknown_columns:
            raise KeyError(f"Unknown columns: {unknown_columns}")
        nonnumeric_columns = [
            column
            for column in target_columns
            if not pd.api.types.is_numeric_dtype(result[column])
        ]
        if nonnumeric_columns:
            raise TypeError(
                f"Normalization requires numeric columns: {nonnumeric_columns}"
            )

    for column in target_columns:
        minimum = result[column].min()
        maximum = result[column].max()
        if pd.isna(minimum) or pd.isna(maximum):
            continue
        if maximum == minimum:
            result[column] = result[column] - minimum
        else:
            result[column] = (result[column] - minimum) / (maximum - minimum)
    return result
