# Tooling setup practice

**Author:** Paritosh Dwivedi

Stage 02 practised creating a reproducible Python workspace, loading local settings without committing secrets, importing shared configuration helpers, freezing installed dependencies, and executing Jupyter notebooks from a defined working folder. The small SPY return-array check links this scaffold to the Weekly ETF Risk Monitor, where the same structure later supports a five-session volatility forecast and elevated-risk review.

The seven folders have separate roles:

- `data/raw/` holds direct, unedited source data.
- `data/processed/` holds reproducible data derived from raw inputs.
- `notebooks/` holds supplementary notebook-based setup checks.
- `src/` holds reusable Python modules imported by notebooks and scripts.
- `docs/` holds internal notes, assumptions, and design decisions.
- `reports/` holds reader-facing summaries, charts, and other deliverables.
- `model/` holds saved model objects.
