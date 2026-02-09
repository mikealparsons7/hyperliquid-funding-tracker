"""Configuration for Hyperliquid Funding Rate Tracker."""

# Hyperliquid API
API_URL = "https://api.hyperliquid.xyz/info"

# Data storage
DATA_DIR = "data"
FUNDING_RATES_FILE = "data/funding_rates.csv"
FUNDING_HISTORY_FILE = "data/funding_history.csv"

# Collection settings
COLLECTION_INTERVAL_HOURS = 1
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30

# Dashboard settings
DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL", "ARB", "DOGE"]
CHART_HEIGHT = 400
HISTORY_CHART_HEIGHT = 500

# Google Sheets settings
GOOGLE_CREDENTIALS_FILE = "credentials.json"  # Service account JSON file
SPREADSHEET_NAME = "Hyperliquid Funding Rates"  # Name of the spreadsheet to create/use
WORKSHEET_NAME = "Funding Rates"  # Name of the worksheet
