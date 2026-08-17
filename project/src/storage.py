"""Reproducible dataframe and metadata persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .utils import sha256_file


def write_dataframe(frame: pd.DataFrame, path: str | Path) -> Path:
    """Write CSV or Parquet based on the file suffix."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    if suffix == ".csv":
        frame.to_csv(destination, index=False)
    elif suffix in {".parquet", ".pq", ".parq"}:
        frame.to_parquet(destination, index=False)
    else:
        raise ValueError(f"Unsupported dataframe format: {destination.suffix}")
    return destination


def read_dataframe(path: str | Path) -> pd.DataFrame:
    """Read CSV or Parquet while parsing a conventional date column."""

    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(source)
    elif suffix in {".parquet", ".pq", ".parq"}:
        frame = pd.read_parquet(source)
    else:
        raise ValueError(f"Unsupported dataframe format: {source.suffix}")
    if "date" in frame:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame


def write_json(payload: dict[str, Any], path: str | Path) -> Path:
    """Write auditable JSON metadata."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return destination


def build_manifest(data_path: str | Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Combine acquisition metadata with the persisted file digest."""

    source = Path(data_path)
    return {
        **metadata,
        "file": source.name,
        "sha256": sha256_file(source),
        "bytes": source.stat().st_size,
    }
