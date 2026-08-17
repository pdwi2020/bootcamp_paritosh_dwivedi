"""Project configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Typed settings for data acquisition and evaluation."""

    project_root: Path = PROJECT_ROOT
    ticker: str = os.getenv("PRIMARY_TICKER", "SPY").upper()
    provider: str = os.getenv("DATA_PROVIDER", "auto").lower()
    start_date: str = os.getenv("DATA_START", "2010-01-01")
    end_date: str = os.getenv("DATA_END", "2026-08-17")
    raw_dir: Path = PROJECT_ROOT / os.getenv("DATA_DIR_RAW", "data/raw")
    processed_dir: Path = PROJECT_ROOT / os.getenv(
        "DATA_DIR_PROCESSED", "data/processed"
    )
    reports_dir: Path = PROJECT_ROOT / "reports"
    images_dir: Path = PROJECT_ROOT / "reports/images"
    model_dir: Path = PROJECT_ROOT / "model"
    alpha_vantage_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY") or None
    test_fraction: float = float(os.getenv("TEST_FRACTION", "0.20"))
    risk_quantile: float = float(os.getenv("RISK_QUANTILE", "0.75"))

    def ensure_directories(self) -> None:
        """Create every directory used for generated project artifacts."""

        for path in (
            self.raw_dir,
            self.processed_dir,
            self.reports_dir,
            self.images_dir,
            self.model_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Return validated settings and create output directories."""

    settings = Settings()
    if not 0.05 <= settings.test_fraction <= 0.50:
        raise ValueError("TEST_FRACTION must be between 0.05 and 0.50")
    if not 0.50 <= settings.risk_quantile <= 0.95:
        raise ValueError("RISK_QUANTILE must be between 0.50 and 0.95")
    settings.ensure_directories()
    return settings
