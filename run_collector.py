#!/usr/bin/env python3
"""Entry point for the funding rate data collector."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler import run_scheduler, collect_funding_rates


def main():
    """Run the funding rate collector."""
    import argparse

    parser = argparse.ArgumentParser(description="Hyperliquid Funding Rate Collector")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run collection once and exit (don't start scheduler)"
    )
    parser.add_argument(
        "--sheets",
        action="store_true",
        help="Also export data to Google Sheets (requires credentials.json)"
    )

    args = parser.parse_args()

    if args.once:
        print("Running single collection...")
        success = collect_funding_rates(use_sheets=args.sheets)
        sys.exit(0 if success else 1)
    else:
        print("Starting scheduler (press Ctrl+C to stop)...")
        try:
            run_scheduler(use_sheets=args.sheets)
        except KeyboardInterrupt:
            print("\nStopping collector...")


if __name__ == "__main__":
    main()
