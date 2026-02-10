# Hyperliquid Funding Rate Tracker

A comprehensive Streamlit dashboard for analyzing perpetual futures funding rates on Hyperliquid DEX. Track historical funding rates, volatility, and funding carry returns across 40+ perpetual contracts.

## 🎯 Features

### 📊 Interactive Visualizations

1. **Funding Carry Index** — Rebased performance index (starts at 100) showing total returns from collecting funding on a hedged short position
2. **7-Day Average Rates** — Current average funding rates with annualized APR metrics
3. **Funding Rate Time Series** — Hourly funding rates over time, fully annualized
4. **30-Day Trailing Average** — Rolling 30-day mean showing funding rate trends
5. **Average Rate Ranking** — Bar chart comparing mean rates across all symbols
6. **Daily Heatmap** — Color-coded daily average funding rates by symbol
7. **Risk-Return Scatter** — Mean funding rate vs volatility for all symbols
8. **Raw Data Table** — Searchable/sortable table with all historical observations

### 🔧 Advanced Features

- **40+ Symbols** — Coverage of top, middle, and bottom volume perpetuals
- **2.5+ Years of Data** — Historical funding rates since May 2023
- **Volatility Ranking** — Symbols ordered by funding rate volatility in selected period
- **Date Range Filtering** — Analyze any custom time period
- **Activity Filtering** — Auto-excludes low-activity symbols (<50% non-zero rates)
- **Annualized Metrics** — All rates displayed as annualized percentages for easy comparison
- **Hedged Strategy Simulation** — Assumes short perp + long spot (perfect hedge)

## 📈 Data Sources

### Historical Data
- **Source:** Hyperliquid API (`/info` endpoint, `fundingHistory` type)
- **Frequency:** Hourly observations
- **Coverage:** May 2023 - Present
- **Symbols:** 40 active perpetual contracts
- **File:** `data/funding_history.csv` (~617k rows, 36MB)

### Live Data Collection
- **Endpoint:** `metaAndAssetCtxs` (current snapshots)
- **Frequency:** Hourly (configurable)
- **Metrics:** Funding rate, mark price, 24h volume, open interest
- **File:** `data/funding_rates.csv`

## 🚀 Setup

### Prerequisites

```bash
Python 3.8+
pip install -r requirements.txt
```

### Installation

```bash
# Clone the repo
git clone https://github.com/MasterworksIO/research-perps-sandbox.git
cd research-perps-sandbox

# Install dependencies
pip install -r requirements.txt
```

### Required Files

Ensure `data/funding_history.csv` exists with historical data. If starting fresh, run the history fetcher:

```bash
python run_history.py --coins BTC,ETH,SOL,ARB,DOGE
```

## 🖥️ Usage

### Run the Dashboard Locally

```bash
streamlit run history_dashboard.py
```

Or via Python module:

```bash
python -m streamlit run history_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Hosted Version

Access the live dashboard on Streamlit Community Cloud:
- **URL:** [TBD - Update after deployment]

## 📊 Dashboard Sections

### 1. Funding Carry Index

Shows the compounded performance of a funding carry strategy:
- **Assumption:** Short perp position, hedged with spot bought off-platform
- **Returns:** Pure funding income (no price exposure)
- **Calculation:** `index[t] = index[t-1] × (1 + hourly_rate)`
- **Metrics:** Gross return (%) and annualized return (%)

### 2. Funding Rate Time Series

Hourly funding rates displayed as annualized percentages:
- **Formula:** `hourly_rate × 24 × 365 × 100`
- **Example:** 0.01% hourly = 87.6% APR

### 3. 30-Day Trailing Average

Rolling 30-day mean (720-hour window):
- Smooths out short-term volatility
- Shows longer-term funding trends
- Helps identify regime changes

### 4. Risk-Return Profile

Scatter plot comparing mean rate vs volatility:
- **X-axis:** Mean annualized funding rate
- **Y-axis:** Volatility (std dev, annualized)
- **Sweet spot:** Bottom-right quadrant (high carry, low volatility)
- **All symbols visible,** selected ones highlighted in blue

### 5. Average Rate Ranking

Horizontal bar chart showing:
- Top 20 and bottom 20 symbols by mean rate
- Green bars = positive carry (longs pay shorts)
- Red bars = negative carry (shorts pay longs)

## 🗂️ Project Structure

```
.
├── history_dashboard.py        # Main Streamlit dashboard
├── dashboard.py                # Legacy current rates dashboard
├── run_collector.py            # Hourly data collector (scheduler)
├── run_history.py              # Historical data fetcher
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── data/
│   ├── funding_history.csv     # Historical funding rates (40 symbols, ~617k rows)
│   └── funding_rates.csv       # Current snapshots (all symbols)
├── src/
│   ├── fetcher.py              # API client for current rates
│   ├── history_fetcher.py      # API client for historical rates
│   ├── storage.py              # CSV data persistence
│   ├── scheduler.py            # Scheduled collection logic
│   └── sheets.py               # Google Sheets export (optional)
└── .gitignore
```

## 🔢 Key Calculations

### Annualized Funding Rate

```python
annualized_rate = hourly_rate × 24 × 365 × 100
```

### Funding Carry Index (Compounding)

```python
index[t] = index[t-1] × (1 + hourly_funding_rate)
```

Starting at 100, compounds each hourly observation.

### Gross Return

```python
gross_return = (final_index - 100)
```

### Annualized Return

```python
days_in_period = (end_date - start_date).days
annualized_return = ((final_index / 100) ** (365 / days_in_period) - 1) × 100
```

### Volatility

```python
volatility = std_dev(hourly_rates) × 24 × 365 × 100
```

## 📡 Data Collection

### Manual Collection

Run once:
```bash
python run_collector.py --once
```

### Scheduled Collection (Hourly)

Run continuously:
```bash
python run_collector.py
```

This runs every hour via `schedule` library (requires process to stay running).

### Production Deployment

For always-on collection, consider:
1. **GitHub Actions** (recommended for this repo) — cron-based, serverless
2. **Cloud VM** — DigitalOcean, AWS, GCP with cron job
3. **Serverless Functions** — AWS Lambda, Google Cloud Functions

## 🔑 API Details

### Hyperliquid API

- **Base URL:** `https://api.hyperliquid.xyz/info`
- **Authentication:** None required (public endpoint)
- **Rate Limits:** ~2 requests/second (enforced in code with delays)

### Funding History Endpoint

```python
payload = {
    "type": "fundingHistory",
    "coin": "BTC",
    "startTime": 0  # Unix timestamp in ms
}
```

Returns up to 500 entries per page. Pagination handled automatically.

### Current Rates Endpoint

```python
payload = {
    "type": "metaAndAssetCtxs"
}
```

Returns current funding rates, mark prices, volume, and open interest for all symbols.

## 📊 Symbol Selection Criteria

### Included Symbols (40 total)

**Top 15 by Volume:**
PUMP, HMSTR, kPEPE, BLAST, MON, MEME, kBONK, BOME, kSHIB, NOT, LINEA, PENGU, TURBO, XPL, MEW

**Middle 15 by Volume:**
ZETA, MAV, MELANIA, MET, kLUNC, PNUT, MERL, WCT, INIT, EIGEN, TIA, ALGO, SPX, FET, IMX

**Bottom 15 by Volume:**
COMP, TRB, BCH, PAXG, BTC, MATIC, RNDR, FTM, MKR, FXS, HPOS, RLB, UNIBOT, OX, FRIEND

### Excluded Symbols (5 total)

Automatically filtered out due to <50% non-zero funding rates:
- FRIEND (28% active)
- OX (35% active)
- UNIBOT (36% active)
- RNDR (42% active)
- MATIC (47% active)

## 🎨 Customization

### Default Date Range

Change in `history_dashboard.py`:

```python
value=(max(min_date, pd.Timestamp("2024-12-31").date()), max_date)
```

### Default Symbols

Edit `config.py`:

```python
DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL", "ARB", "DOGE"]
```

### Chart Heights

Edit `config.py`:

```python
HISTORY_CHART_HEIGHT = 500  # Increase for taller charts
```

### Activity Threshold

Change in `history_dashboard.py`:

```python
if pct_nonzero >= 0.5:  # 50% threshold
```

## 🧪 Testing

### Test API Connection

```bash
cd src
python fetcher.py
```

Should print current funding rates for all symbols.

### Test Historical Fetcher

```bash
python run_history.py --coins BTC
```

Should fetch full BTC history and save to CSV.

## 📝 Notes

### Funding Rate Mechanics

- **Positive rate:** Longs pay shorts (bullish bias in market)
- **Negative rate:** Shorts pay longs (bearish bias in market)
- **Frequency:** Paid every hour on Hyperliquid (vs 8-hour on most CEXs)

### Hedged Strategy

The dashboard assumes a **fully hedged** position:
- Short perp on Hyperliquid → collect funding
- Long spot off-platform → hedge price risk
- **Net exposure:** Zero directional risk, pure funding income

This is a common market-neutral strategy used by:
- Arbitrage funds
- Market makers
- Yield-focused traders

### Data Integrity

- All timestamps are stored in UTC with timezone awareness
- Missing data (API failures) are logged but don't halt collection
- Duplicate rows are prevented by timestamp + symbol composite key

## 🐛 Troubleshooting

### Streamlit Cache Issues

If the dashboard shows stale data after updating CSV files:
1. Open the app
2. Press **C** on keyboard (or click menu → Clear cache)
3. Refresh the page

### SSL Certificate Errors

If you encounter SSL errors when fetching data:
- Check firewall/antivirus settings
- Try disabling SSL inspection
- Use a different network (VPN may interfere)

### Large File Size

`funding_history.csv` is 36MB and will grow over time:
- GitHub limit: 100MB (current: 36MB, safe)
- Streamlit Cloud limit: 1GB repo size
- Consider archiving old data if it exceeds limits

## 🔮 Future Enhancements

- [ ] Add historical mark price data (requires new data collection)
- [ ] Premium vs funding rate correlation chart
- [ ] Basis (perp - spot) time series
- [ ] Funding rate distribution histograms
- [ ] Export to CSV functionality
- [ ] GitHub Actions workflow for automated hourly collection
- [ ] Alerts for extreme funding rates
- [ ] Multi-exchange comparison (add Binance, Bybit, etc.)

## 📄 License

MIT License - See LICENSE file for details

## 🙋 Support

For questions or issues:
- Open an issue in this repo
- Contact the Masterworks research team

## 🙏 Acknowledgments

- **Hyperliquid** for providing free, public API access
- **Streamlit** for the excellent dashboard framework
- **Plotly** for interactive charting

---

**Built with Claude Code** 🤖
