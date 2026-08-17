"""Small reusable utilities shared across pipeline stages."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def safe_timestamp(moment: datetime | None = None) -> str:
    """Return a filename-safe UTC timestamp."""

    moment = moment or datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clean_column_name(value: object) -> str:
    """Convert a column label to lowercase snake case."""

    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with normalized column names."""

    result = frame.copy()
    result.columns = [clean_column_name(column) for column in result.columns]
    return result


def sha256_file(path: str | Path) -> str:
    """Return a SHA-256 digest for a reproducibility manifest."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
