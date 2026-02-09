#!/usr/bin/env python3
"""Streamlit dashboard for Hyperliquid funding rates."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

from src.storage import load_funding_rates, get_latest_rates, get_available_symbols
from config import DEFAULT_SYMBOLS, CHART_HEIGHT

# Page config
st.set_page_config(
    page_title="Hyperliquid Funding Rates",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("📊 Hyperliquid Funding Rate Tracker")

# Load data
df = load_funding_rates()

if df.empty:
    st.warning("No data available. Run the collector first: `python run_collector.py --once`")
    st.stop()

# Last update time
last_update = df["timestamp"].max()
st.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Sidebar filters
st.sidebar.header("Filters")

available_symbols = get_available_symbols()
default_selection = [s for s in DEFAULT_SYMBOLS if s in available_symbols]

selected_symbols = st.sidebar.multiselect(
    "Select Symbols",
    options=available_symbols,
    default=default_selection[:5] if default_selection else available_symbols[:5]
)

days_filter = st.sidebar.slider(
    "Days of History",
    min_value=1,
    max_value=30,
    value=7
)

# Filter data (use timezone-aware datetime to match stored data)
cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
filtered_df = df[
    (df["symbol"].isin(selected_symbols)) &
    (df["timestamp"] >= cutoff)
]

# Summary Cards
st.subheader("Current Funding Rates")

latest_rates = get_latest_rates()
if not latest_rates.empty and selected_symbols:
    cols = st.columns(min(len(selected_symbols), 5))

    for i, symbol in enumerate(selected_symbols[:5]):
        symbol_data = latest_rates[latest_rates["symbol"] == symbol]
        if not symbol_data.empty:
            rate = symbol_data["funding_rate"].values[0]
            rate_pct = rate * 100
            annualized = rate_pct * 24 * 365

            with cols[i]:
                # Color based on positive/negative
                color = "green" if rate >= 0 else "red"
                st.metric(
                    label=symbol,
                    value=f"{rate_pct:.4f}%",
                    delta=f"{annualized:.1f}% APR",
                    delta_color="normal" if rate >= 0 else "inverse"
                )

# Line Chart
st.subheader("Funding Rates Over Time")

if not filtered_df.empty:
    # Convert to percentage for display
    chart_df = filtered_df.copy()
    chart_df["funding_rate_pct"] = chart_df["funding_rate"] * 100

    fig = px.line(
        chart_df,
        x="timestamp",
        y="funding_rate_pct",
        color="symbol",
        title="Funding Rates (%)",
        labels={
            "timestamp": "Time",
            "funding_rate_pct": "Funding Rate (%)",
            "symbol": "Symbol"
        },
        height=CHART_HEIGHT
    )

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(hovermode="x unified")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected filters")

# Heatmap
st.subheader("Funding Rate Heatmap")

if not filtered_df.empty:
    # Pivot for heatmap
    pivot_df = filtered_df.pivot_table(
        index="symbol",
        columns=pd.Grouper(key="timestamp", freq="1H"),
        values="funding_rate",
        aggfunc="last"
    )

    if not pivot_df.empty:
        # Convert to percentage
        pivot_df = pivot_df * 100

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=[t.strftime("%m-%d %H:%M") for t in pivot_df.columns],
            y=pivot_df.index,
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Rate (%)")
        ))

        fig_heatmap.update_layout(
            title="Funding Rates by Symbol and Time",
            height=max(300, len(pivot_df) * 25),
            xaxis_title="Time",
            yaxis_title="Symbol"
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

# Data Table
st.subheader("Historical Data")

if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df["funding_rate_pct"] = (display_df["funding_rate"] * 100).round(6)
    display_df["mark_price"] = display_df["mark_price"].round(2)

    display_df = display_df[["timestamp", "symbol", "funding_rate_pct", "mark_price"]]
    display_df.columns = ["Timestamp", "Symbol", "Funding Rate (%)", "Mark Price ($)"]

    st.dataframe(
        display_df.sort_values("Timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )

# Footer
st.divider()
st.caption("Data from Hyperliquid API. Funding rates are 8-hourly rates shown as percentages.")
