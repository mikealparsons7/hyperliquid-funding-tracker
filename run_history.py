#!/usr/bin/env python3
"""Entry point for fetching full funding rate history."""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.history_fetcher import fetch_all_funding_history


def main():
    """Fetch full funding rate history from Hyperliquid."""
    import argparse

    parser = argparse.ArgumentParser(description="Hyperliquid Funding Rate History Fetcher")
    parser.add_argument(
        "--coins",
        type=str,
        default=None,
        help="Comma-separated list of coins to fetch (e.g. BTC,ETH,SOL). Defaults to all."
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    coins = None
    if args.coins:
        coins = [c.strip().upper() for c in args.coins.split(",")]
        print(f"Fetching history for {len(coins)} coin(s): {', '.join(coins)}")
    else:
        print("Fetching history for ALL coins...")

    df = fetch_all_funding_history(coins=coins)

    if not df.empty:
        symbols = df["symbol"].nunique()
        print(f"\nDone! {len(df)} total rows across {symbols} symbol(s)")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Saved to: data/funding_history.csv")
    else:
        print("\nNo data was fetched.")
        sys.exit(1)


if __name__ == "__main__":
    main()
