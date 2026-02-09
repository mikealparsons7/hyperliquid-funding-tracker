"""Fetch full funding rate history for all Hyperliquid perps."""

import os
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from typing import List, Optional

from config import API_URL, MAX_RETRIES, RETRY_DELAY_SECONDS, FUNDING_HISTORY_FILE, DATA_DIR

logger = logging.getLogger(__name__)


def get_all_symbols() -> List[str]:
    """Get all perpetual symbols from Hyperliquid."""
    payload = {"type": "metaAndAssetCtxs"}
    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    universe = data[0]["universe"]
    return [asset["name"] for asset in universe]


def _fetch_funding_page(coin: str, start_time: int = 0) -> list:
    """Fetch a single page of funding history (up to 500 entries)."""
    payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": start_time,
    }

    response = requests.post(API_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch_funding_history(coin: str) -> List[dict]:
    """
    Fetch full funding rate history for a single coin, paginating through all pages.

    Args:
        coin: Symbol like "BTC", "ETH"

    Returns:
        List of dicts with: timestamp, symbol, funding_rate, premium
    """
    all_rows = []
    start_time = 0

    while True:
        data = _fetch_funding_page(coin, start_time)

        if not data:
            break

        for entry in data:
            all_rows.append({
                "timestamp": datetime.fromtimestamp(entry["time"] / 1000, tz=timezone.utc).isoformat(),
                "symbol": entry["coin"],
                "funding_rate": float(entry["fundingRate"]),
                "premium": float(entry["premium"]),
            })

        # If we got fewer than 500, we've reached the end
        if len(data) < 500:
            break

        # Next page starts after the last entry's timestamp
        start_time = data[-1]["time"] + 1
        time.sleep(1)

    return all_rows


def fetch_all_funding_history(coins: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fetch full funding history for all (or specified) coins and save to CSV.

    Args:
        coins: Optional list of symbols to fetch. If None, fetches all.

    Returns:
        DataFrame with all funding history.
    """
    if coins is None:
        logger.info("Fetching symbol list from Hyperliquid...")
        coins = get_all_symbols()
        logger.info(f"Found {len(coins)} symbols")

    all_rows = []
    total = len(coins)

    for idx, coin in enumerate(coins, 1):
        logger.info(f"Fetching {idx}/{total}: {coin}...")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rows = fetch_funding_history(coin)
                all_rows.extend(rows)
                logger.info(f"  Got {len(rows)} entries for {coin}")
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(f"  Attempt {attempt} failed for {coin}: {e}. Retrying in {RETRY_DELAY_SECONDS}s...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"  Failed to fetch {coin} after {MAX_RETRIES} attempts: {e}")

        # Rate limit: 2-second delay between requests
        if idx < total:
            time.sleep(2)

    # Build DataFrame and save
    df = pd.DataFrame(all_rows)

    if not df.empty:
        df.sort_values(["symbol", "timestamp"], inplace=True)
        df.reset_index(drop=True, inplace=True)

        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(FUNDING_HISTORY_FILE, index=False)
        logger.info(f"Saved {len(df)} rows to {FUNDING_HISTORY_FILE}")
    else:
        logger.warning("No data fetched.")

    return df
