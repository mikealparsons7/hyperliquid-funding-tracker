"""CSV storage for funding rates data."""

import os
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from config import FUNDING_RATES_FILE, DATA_DIR


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_funding_rates(rates: List[Dict[str, Any]]) -> None:
    """
    Append funding rates to CSV file.

    Args:
        rates: List of funding rate records
    """
    ensure_data_dir()

    df = pd.DataFrame(rates)

    file_exists = os.path.exists(FUNDING_RATES_FILE)

    df.to_csv(
        FUNDING_RATES_FILE,
        mode='a',
        header=not file_exists,
        index=False
    )


def load_funding_rates(days: int = None) -> pd.DataFrame:
    """
    Load funding rates from CSV file.

    Args:
        days: Optional number of days to load (None = all data)

    Returns:
        DataFrame with funding rate data
    """
    if not os.path.exists(FUNDING_RATES_FILE):
        return pd.DataFrame(columns=["timestamp", "symbol", "funding_rate", "mark_price"])

    df = pd.read_csv(FUNDING_RATES_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        df = df[df["timestamp"] >= cutoff]

    return df.sort_values("timestamp")


def get_latest_rates() -> pd.DataFrame:
    """
    Get the most recent funding rates for all symbols.

    Returns:
        DataFrame with latest rates per symbol
    """
    df = load_funding_rates()

    if df.empty:
        return df

    # Get the most recent timestamp
    latest_timestamp = df["timestamp"].max()

    return df[df["timestamp"] == latest_timestamp]


def get_available_symbols() -> List[str]:
    """
    Get list of all symbols in the data.

    Returns:
        List of symbol names
    """
    df = load_funding_rates()

    if df.empty:
        return []

    return sorted(df["symbol"].unique().tolist())


if __name__ == "__main__":
    # Test loading data
    df = load_funding_rates()
    print(f"Loaded {len(df)} records")
    print(f"Symbols: {get_available_symbols()[:10]}")
