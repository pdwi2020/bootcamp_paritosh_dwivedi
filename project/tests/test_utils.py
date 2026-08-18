from datetime import UTC, datetime

import pandas as pd

from src.utils import clean_columns, safe_timestamp


def test_clean_columns_normalizes_labels():
    frame = pd.DataFrame(columns=["Adjusted Close", "Volume ($)"])
    assert clean_columns(frame).columns.tolist() == ["adjusted_close", "volume"]


def test_safe_timestamp_is_utc_and_filename_safe():
    moment = datetime(2026, 8, 17, 14, 30, tzinfo=UTC)
    assert safe_timestamp(moment) == "20260817T143000000000Z"
