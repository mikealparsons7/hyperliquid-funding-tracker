"""Google Sheets exporter for funding rates data."""

import os
import logging
from typing import List, Dict, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_FILE, SPREADSHEET_NAME, WORKSHEET_NAME

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_gspread_client() -> gspread.Client:
    """
    Get authenticated gspread client using service account credentials.

    Returns:
        Authenticated gspread client
    """
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"Credentials file not found: {GOOGLE_CREDENTIALS_FILE}\n"
            "Download your service account JSON from Google Cloud Console."
        )

    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_or_create_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    """
    Get existing spreadsheet or create a new one.

    Returns:
        Spreadsheet object
    """
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        logger.info(f"Opened existing spreadsheet: {SPREADSHEET_NAME}")
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SPREADSHEET_NAME)
        logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")
        # Make it accessible (you can also share with specific emails)
        spreadsheet.share(None, perm_type='anyone', role='reader')
        logger.info("Spreadsheet shared as view-only to anyone with link")

    return spreadsheet


def get_or_create_worksheet(
    spreadsheet: gspread.Spreadsheet,
    name: str = WORKSHEET_NAME
) -> gspread.Worksheet:
    """
    Get existing worksheet or create a new one with headers.

    Returns:
        Worksheet object
    """
    try:
        worksheet = spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=10)
        # Add headers
        headers = ["timestamp", "symbol", "funding_rate", "funding_rate_pct",
                   "annualized_rate", "mark_price"]
        worksheet.append_row(headers)
        logger.info(f"Created worksheet with headers: {name}")

    return worksheet


def append_funding_rates(rates: List[Dict[str, Any]]) -> Optional[str]:
    """
    Append funding rates to Google Sheet.

    Args:
        rates: List of funding rate records

    Returns:
        Spreadsheet URL if successful, None otherwise
    """
    try:
        client = get_gspread_client()
        spreadsheet = get_or_create_spreadsheet(client)
        worksheet = get_or_create_worksheet(spreadsheet)

        # Prepare rows
        rows = []
        for rate in rates:
            funding_rate = rate["funding_rate"]
            funding_pct = funding_rate * 100
            annualized = funding_pct * 24 * 365  # 8-hour funding * 3 * 365

            rows.append([
                rate["timestamp"],
                rate["symbol"],
                funding_rate,
                round(funding_pct, 6),
                round(annualized, 2),
                rate["mark_price"]
            ])

        # Batch append for efficiency
        worksheet.append_rows(rows, value_input_option="RAW")

        logger.info(f"Appended {len(rows)} rows to Google Sheet")
        return spreadsheet.url

    except Exception as e:
        logger.error(f"Failed to write to Google Sheets: {e}")
        return None


def get_spreadsheet_url() -> Optional[str]:
    """
    Get the URL of the spreadsheet.

    Returns:
        Spreadsheet URL or None if not found
    """
    try:
        client = get_gspread_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet.url
    except Exception as e:
        logger.error(f"Failed to get spreadsheet URL: {e}")
        return None


if __name__ == "__main__":
    # Test the sheets connection
    logging.basicConfig(level=logging.INFO)

    try:
        client = get_gspread_client()
        print("Successfully authenticated with Google Sheets!")

        spreadsheet = get_or_create_spreadsheet(client)
        print(f"Spreadsheet URL: {spreadsheet.url}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
