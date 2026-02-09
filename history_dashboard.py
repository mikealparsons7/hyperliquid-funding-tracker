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

available_symbols = sorted(df["symbol"].unique().tolist())
default_selection = [s for s in DEFAULT_SYMBOLS if s in available_symbols]
if not default_selection:
    default_selection = available_symbols[:5]

selected_symbols = st.sidebar.multiselect(
    "Select Symbols",
    options=available_symbols,
    default=default_selection[:5]
)

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
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

# ── 1. Summary Cards ──
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
        avg_rate_pct = avg_rate * 100
        annualized = avg_rate_pct * 24 * 365
        with cols[i]:
            st.metric(
                label=symbol,
                value=f"{avg_rate_pct:.4f}%",
                delta=f"{annualized:.1f}% APR",
                delta_color="normal" if avg_rate >= 0 else "inverse"
            )

# ── 2. Funding Rate Time Series ──
st.subheader("Funding Rates Over Time")

if not filtered_df.empty:
    chart_df = filtered_df.copy()
    chart_df["funding_rate_pct"] = chart_df["funding_rate"] * 100

    fig_ts = px.line(
        chart_df,
        x="timestamp",
        y="funding_rate_pct",
        color="symbol",
        title="Hourly Funding Rate (%)",
        labels={
            "timestamp": "Time",
            "funding_rate_pct": "Funding Rate (%)",
            "symbol": "Symbol"
        },
        height=HISTORY_CHART_HEIGHT
    )
    fig_ts.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_ts.update_layout(hovermode="x unified")
    st.plotly_chart(fig_ts, use_container_width=True)

# ── 3. Cumulative Funding Chart ──
st.subheader("Cumulative Funding")
st.caption("Running sum of funding rate per symbol — total funding earned/paid holding a 1× short position.")

if not filtered_df.empty:
    cum_df = filtered_df.copy()
    cum_df["cum_funding_pct"] = (
        cum_df.groupby("symbol")["funding_rate"].cumsum() * 100
    )

    fig_cum = px.line(
        cum_df,
        x="timestamp",
        y="cum_funding_pct",
        color="symbol",
        title="Cumulative Funding (%)",
        labels={
            "timestamp": "Time",
            "cum_funding_pct": "Cumulative Funding (%)",
            "symbol": "Symbol"
        },
        height=HISTORY_CHART_HEIGHT
    )
    fig_cum.update_layout(hovermode="x unified")
    st.plotly_chart(fig_cum, use_container_width=True)

# ── 4. Average Rate Ranking ──
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
        * 100
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
        title="Mean Funding Rate (%) — Selected Date Range",
        xaxis_title="Mean Funding Rate (%)",
        yaxis_title="Symbol",
        height=max(400, len(display_rates) * 22),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── 5. Heatmap ──
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
        pivot_pct = pivot_df * 100

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot_pct.values,
            x=[str(d) for d in pivot_pct.columns],
            y=pivot_pct.index.tolist(),
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Rate (%)")
        ))
        fig_heatmap.update_layout(
            title="Daily Avg Funding Rate by Symbol",
            height=max(300, len(pivot_pct) * 40 + 100),
            xaxis_title="Date",
            yaxis_title="Symbol"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

# ── 6. Data Table ──
with st.expander("📋 Raw Data Table"):
    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df["funding_rate_pct"] = (display_df["funding_rate"] * 100).round(6)
        display_df["premium_pct"] = (display_df["premium"] * 100).round(6)
        display_df = display_df[["timestamp", "symbol", "funding_rate_pct", "premium_pct"]]
        display_df.columns = ["Timestamp", "Symbol", "Funding Rate (%)", "Premium (%)"]

        st.dataframe(
            display_df.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data for selected filters.")

# Footer
st.divider()
st.caption("Data from Hyperliquid API. Funding rates are hourly rates shown as percentages.")
