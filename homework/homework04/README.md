# Homework 04: data acquisition and ingestion

**Author:** Paritosh Dwivedi

This homework acquires data through two different paths and records enough metadata that either pull can be audited later.

## Files

- `homework04_data-acquisition-and-ingestion_submission.ipynb` performs both acquisitions, validates each result, and documents the assumptions.
- `data/raw/api_source-yfinance_symbol-SPY_20260818-194017.csv` is the API pull: daily SPY history from yfinance.
- `data/raw/scrape_site-wikipedia_table-sp500-constituents_20260818-194018.csv` is the scrape: the S&P 500 constituents table parsed with BeautifulSoup.

Filenames encode the acquisition method, source, subject, and UTC timestamp, so a raw snapshot can be traced back to how it was obtained without opening it.

## Validation

Each pull is checked for the expected columns, a non-empty result, and sensible types before it is saved. One case is worth noting: a single constituent row carries a blank CIK. Casting that column directly to an integer raises `IntCastingNaNError`, so the notebook coerces with `pd.to_numeric(..., errors="coerce")` into a nullable `Int64` and reports the count of missing identifiers instead of discarding the row or silently failing. A validation step that crashes on one imperfect row is not a validation step.

## Assumptions and risks

Yahoo Finance is a third-party source that can revise adjusted prices after corporate actions or change its schema without notice. The Wikipedia table is community-maintained, so its structure can change and its contents are not authoritative for index membership. Both risks are handled the same way: keep the dated raw snapshot, record how it was obtained, and validate on load rather than trusting the source.

Homework04 uses only `data/raw/` under the course repository structure. Nothing is cleaned or derived at this stage, so there is no `data/processed/`.
