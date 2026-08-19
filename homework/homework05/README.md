# Homework 05: Data storage

This homework implements a small, reproducible storage layer for sample Weekly ETF Risk Monitor data. The notebook saves the same typed DataFrame in two formats, reloads each artifact, and reports shape and dtype checks.

## Data Storage

The folder structure separates source-like snapshots from analysis-ready artifacts:

- `data/raw/` stores timestamped CSV snapshots. CSV is portable, transparent, and easy to inspect, so it is suitable for a raw exchange artifact. Its text representation does not preserve pandas date or categorical dtypes automatically.
- `data/processed/` stores timestamped Parquet files. Parquet is compact and preserves the date, float, and categorical dtypes used by the risk-monitor sample, so it is suitable for repeatable analytical reloads.

The notebook loads `.env` with `python-dotenv` and reads `DATA_DIR_RAW` and `DATA_DIR_PROCESSED` with `os.getenv`. Those environment variables provide the relative paths `data/raw` and `data/processed`; the code does not embed personal or absolute paths. `write_df` and `read_df` select CSV or Parquet behavior from the file suffix. `write_df` also creates missing parent directories. The committed `.env.example` documents the required settings, while the matching `.env` remains ignored.

Homework05 has no `src/` folder under the course repository structure. The storage utilities therefore remain in the submission notebook for this stage. In the cumulative Weekly ETF Risk Monitor, the same responsibility moves into `project/src/storage.py` so the pipeline can reuse it.

Paritosh Dwivedi is the author and retains responsibility for understanding, validating, and presenting this work.
