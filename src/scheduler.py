"""Scheduler for periodic data collection."""

import time
import logging
import schedule
from datetime import datetime

from config import COLLECTION_INTERVAL_HOURS, MAX_RETRIES, RETRY_DELAY_SECONDS
from src.fetcher import fetch_funding_rates
from src.storage import save_funding_rates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_funding_rates(use_sheets: bool = False) -> bool:
    """
    Fetch and save funding rates with retry logic.

    Args:
        use_sheets: If True, also write to Google Sheets

    Returns:
        True if successful, False otherwise
    """
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Collecting funding rates (attempt {attempt + 1}/{MAX_RETRIES})")

            rates = fetch_funding_rates()
            save_funding_rates(rates)

            logger.info(f"Successfully saved {len(rates)} funding rates to CSV")

            # Also write to Google Sheets if enabled
            if use_sheets:
                try:
                    from src.sheets import append_funding_rates
                    url = append_funding_rates(rates)
                    if url:
                        logger.info(f"Successfully saved to Google Sheets: {url}")
                except Exception as e:
                    logger.warning(f"Failed to write to Google Sheets: {e}")
                    # Don't fail the whole collection if sheets fails

            return True

        except Exception as e:
            logger.error(f"Error collecting rates: {e}")

            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)

    logger.error("All retry attempts failed")
    return False


def run_scheduler(use_sheets: bool = False):
    """Start the hourly scheduler."""
    logger.info("Starting funding rate collector scheduler")
    if use_sheets:
        logger.info("Google Sheets export enabled")

    # Run immediately on start
    collect_funding_rates(use_sheets=use_sheets)

    # Schedule hourly collection
    schedule.every(COLLECTION_INTERVAL_HOURS).hours.do(
        collect_funding_rates, use_sheets=use_sheets
    )

    logger.info(f"Scheduled to run every {COLLECTION_INTERVAL_HOURS} hour(s)")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    run_scheduler()
