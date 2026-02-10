#!/usr/bin/env python3
"""Streamlit dashboard for exploring full Hyperliquid funding rate history."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import DEFAULT_SYMBOLS, HISTORY_CHART_HEIGHT, FUNDING_HISTORY_FILE

# Page config
st.set_page_config(
    page_title="Funding History Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Funding Rate History Dashboard")


@st.cache_data
def load_history():
    """Load the full funding history CSV."""
    df = pd.read_csv(FUNDING_HISTORY_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True)
    df.sort_values(["symbol", "timestamp"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


df = load_history()

if df.empty:
    st.warning("No history data found. Ensure `data/funding_history.csv` exists.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Calculate historical funding rate volatility for each symbol
volatility = df.groupby("symbol")["funding_rate"].std().sort_values(ascending=False)
available_symbols = volatility.index.tolist()

# Create display labels with volatility rank
symbol_labels = []
for i, symbol in enumerate(available_symbols, 1):
    vol_value = volatility[symbol] * 100  # Convert to percentage
    if i <= 15:
        label = f"{symbol} (#{i} High Volatility - {vol_value:.4f}%)"
    elif i >= len(available_symbols) - 14:
        label = f"{symbol} (#{i} Low Volatility - {vol_value:.4f}%)"
    else:
        label = f"{symbol} (#{i} - {vol_value:.4f}%)"
    symbol_labels.append(label)

# Map labels back to symbols
label_to_symbol = {label: symbol for label, symbol in zip(symbol_labels, available_symbols)}

default_selection = [s for s in DEFAULT_SYMBOLS if s in available_symbols]
if not default_selection:
    default_selection = available_symbols[:5]

# Create default labels
default_labels = [label for label, symbol in label_to_symbol.items() if symbol in default_selection[:5]]

selected_labels = st.sidebar.multiselect(
    "Select Symbols (ranked by funding rate volatility)",
    options=symbol_labels,
    default=default_labels
)

# Convert labels back to symbols
selected_symbols = [label_to_symbol[label] for label in selected_labels]

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(max(min_date, pd.Timestamp("2024-12-31").date()), max_date),
    min_value=min_date,
    max_value=max_date
)

# Handle single-date selection gracefully
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0] if isinstance(date_range, (list, tuple)) else date_range
    end_date = max_date

# Filter data
filtered_df = df[
    (df["symbol"].isin(selected_symbols)) &
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
]

if not selected_symbols:
    st.info("Select at least one symbol from the sidebar.")
    st.stop()

st.caption(f"Showing data from {start_date} to {end_date} · {len(filtered_df):,} rows")

# ── 1. Funding Carry Index (Rebased to 100) ──
st.subheader("Funding Carry Index (Short + Spot Hedge)")
st.caption("Rebased to 100 at period start. Assumes short position collecting funding, hedged with spot bought off-platform.")

if not filtered_df.empty:
    index_df = filtered_df.copy()

    # Calculate compounding index per symbol: index[t] = index[t-1] * (1 + funding_rate)
    index_df = index_df.sort_values(["symbol", "timestamp"])
    index_df["index"] = index_df.groupby("symbol")["funding_rate"].transform(
        lambda x: (1 + x).cumprod() * 100
    )

    # Calculate metrics for each symbol
    metrics_data = []
    for symbol in selected_symbols:
        symbol_data = index_df[index_df["symbol"] == symbol]
        if not symbol_data.empty:
            start_idx = 100
            end_idx = symbol_data["index"].iloc[-1]
            gross_return = end_idx - 100

            # Annualized return
            days_in_period = (end_date - start_date).days + 1
            if days_in_period > 0:
                annualized_return = (pow(end_idx / 100, 365 / days_in_period) - 1) * 100
            else:
                annualized_return = 0

            metrics_data.append({
                "symbol": symbol,
                "end_idx": end_idx,
                "gross_return": gross_return,
                "annualized_return": annualized_return
            })

    # Display metrics cards
    if metrics_data:
        cols = st.columns(min(len(metrics_data), 5))
        for i, metric in enumerate(metrics_data[:5]):
            with cols[i]:
                st.metric(
                    label=metric["symbol"],
                    value=f"{metric['end_idx']:.1f}",
                    delta=f"{metric['gross_return']:+.1f}% total | {metric['annualized_return']:+.1f}% annual"
                )

    # Chart
    fig_index = px.line(
        index_df,
        x="timestamp",
        y="index",
        color="symbol",
        title="Funding Carry Performance Index",
        labels={
            "timestamp": "Time",
            "index": "Index (rebased to 100)",
            "symbol": "Symbol"
        },
        height=HISTORY_CHART_HEIGHT
    )
    fig_index.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig_index.update_layout(hovermode="x unified")
    st.plotly_chart(fig_index, use_container_width=True)

# ── 2. 7-Day Average Funding Rates ──
st.subheader("7-Day Average Funding Rates")

# Compute 7d average from the most recent 7 days in filtered data
latest_date = filtered_df["timestamp"].max()
seven_days_ago = latest_date - pd.Timedelta(days=7)
recent_df = filtered_df[filtered_df["timestamp"] >= seven_days_ago]

cols = st.columns(min(len(selected_symbols), 5))
for i, symbol in enumerate(selected_symbols[:5]):
    symbol_recent = recent_df[recent_df["symbol"] == symbol]
    if not symbol_recent.empty:
        avg_rate = symbol_recent["funding_rate"].mean()
        annualized = avg_rate * 24 * 365 * 100
        with cols[i]:
            st.metric(
                label=symbol,
                value=f"{annualized:.1f}% APR",
                delta_color="normal" if avg_rate >= 0 else "inverse"
            )

# ── 3. Funding Rate Time Series ──
st.subheader("Funding Rates Over Time")

if not filtered_df.empty:
    chart_df = filtered_df.copy()
    chart_df["funding_rate_apr"] = chart_df["funding_rate"] * 24 * 365 * 100

    fig_ts = px.line(
        chart_df,
        x="timestamp",
        y="funding_rate_apr",
        color="symbol",
        title="Funding Rate (Annualized %)",
        labels={
            "timestamp": "Time",
            "funding_rate_apr": "Annualized Rate (%)",
            "symbol": "Symbol"
        },
        height=HISTORY_CHART_HEIGHT
    )
    fig_ts.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_ts.update_layout(hovermode="x unified")
    st.plotly_chart(fig_ts, use_container_width=True)

# ── 4. 30-Day Trailing Average ──
st.subheader("30-Day Trailing Average")
st.caption("Rolling 30-day mean of hourly funding rates, annualized.")

if not filtered_df.empty:
    avg_df = filtered_df.copy()
    # 30 days * 24 hours = 720 hourly observations
    avg_df["trailing_30d_apr"] = (
        avg_df.groupby("symbol")["funding_rate"]
        .transform(lambda x: x.rolling(window=720, min_periods=1).mean())
        * 24 * 365 * 100
    )

    fig_avg = px.line(
        avg_df,
        x="timestamp",
        y="trailing_30d_apr",
        color="symbol",
        title="30-Day Trailing Average Funding Rate (Annualized %)",
        labels={
            "timestamp": "Time",
            "trailing_30d_apr": "30d Avg Annualized Rate (%)",
            "symbol": "Symbol"
        },
        height=HISTORY_CHART_HEIGHT
    )
    fig_avg.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_avg.update_layout(hovermode="x unified")
    st.plotly_chart(fig_avg, use_container_width=True)

# ── 5. Average Rate Ranking ──
st.subheader("Average Funding Rate Ranking")
st.caption("Mean funding rate over the selected date range — top 20 and bottom 20.")

# Use ALL symbols in the date range (not just selected) for ranking
ranking_df = df[
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
]

if not ranking_df.empty:
    mean_rates = (
        ranking_df.groupby("symbol")["funding_rate"]
        .mean()
        .sort_values(ascending=True)
        * 24 * 365 * 100
    )

    # Take top 20 and bottom 20
    if len(mean_rates) > 40:
        bottom_20 = mean_rates.head(20)
        top_20 = mean_rates.tail(20)
        display_rates = pd.concat([bottom_20, top_20])
    else:
        display_rates = mean_rates

    bar_colors = ["green" if v >= 0 else "red" for v in display_rates.values]

    fig_bar = go.Figure(go.Bar(
        x=display_rates.values,
        y=display_rates.index,
        orientation="h",
        marker_color=bar_colors
    ))
    fig_bar.update_layout(
        title="Mean Funding Rate (Annualized %) — Selected Date Range",
        xaxis_title="Mean Annualized Rate (%)",
        yaxis_title="Symbol",
        height=max(400, len(display_rates) * 22),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── 6. Heatmap ──
st.subheader("Daily Funding Rate Heatmap")
st.caption("Daily average funding rate for selected symbols.")

if not filtered_df.empty:
    heat_df = filtered_df.copy()
    heat_df["date"] = heat_df["timestamp"].dt.date

    pivot_df = heat_df.pivot_table(
        index="symbol",
        columns="date",
        values="funding_rate",
        aggfunc="mean"
    )

    if not pivot_df.empty:
        pivot_pct = pivot_df * 24 * 365 * 100

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot_pct.values,
            x=[str(d) for d in pivot_pct.columns],
            y=pivot_pct.index.tolist(),
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="APR (%)")
        ))
        fig_heatmap.update_layout(
            title="Daily Avg Funding Rate by Symbol (Annualized)",
            height=max(300, len(pivot_pct) * 40 + 100),
            xaxis_title="Date",
            yaxis_title="Symbol"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

# ── 7. Data Table ──
with st.expander("📋 Raw Data Table"):
    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df["funding_rate_apr"] = (display_df["funding_rate"] * 24 * 365 * 100).round(2)
        display_df["premium_pct"] = (display_df["premium"] * 100).round(6)
        display_df = display_df[["timestamp", "symbol", "funding_rate_apr", "premium_pct"]]
        display_df.columns = ["Timestamp", "Symbol", "Annualized Rate (%)", "Premium (%)"]

        st.dataframe(
            display_df.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data for selected filters.")

# Footer
st.divider()
st.caption("Data from Hyperliquid API. All rates are annualized (hourly rate × 24 × 365).")
