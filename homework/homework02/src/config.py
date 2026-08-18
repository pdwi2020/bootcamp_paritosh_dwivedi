"""Load Stage 02 settings from the homework environment file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

HOMEWORK_ROOT = Path(__file__).resolve().parents[1]


def load_env() -> bool:
    """Load settings from the homework folder's local .env file."""

    return load_dotenv(HOMEWORK_ROOT / ".env", override=True)


def get_key(name: str, default: str | None = None) -> str | None:
    """Return an environment value or the supplied default when it is absent."""

    return os.getenv(name, default)
