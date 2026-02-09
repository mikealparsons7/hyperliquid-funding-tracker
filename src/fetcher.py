"""Hyperliquid API client for fetching funding rates."""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Any

from config import API_URL


def fetch_funding_rates() -> List[Dict[str, Any]]:
    """
    Fetch current funding rates from Hyperliquid API.

    Returns:
        List of dicts with: symbol, funding_rate, mark_price, timestamp
    """
    payload = {"type": "metaAndAssetCtxs"}

    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()

    # data[0] contains universe (metadata), data[1] contains asset contexts
    universe = data[0]["universe"]
    asset_ctxs = data[1]

    timestamp = datetime.now(timezone.utc).isoformat()

    results = []
    for i, asset_ctx in enumerate(asset_ctxs):
        symbol = universe[i]["name"]
        funding_rate = float(asset_ctx.get("funding", 0))
        mark_price = float(asset_ctx.get("markPx", 0))
        day_ntl_vlm = float(asset_ctx.get("dayNtlVlm", 0))
        open_interest = float(asset_ctx.get("openInterest", 0))

        results.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "day_ntl_vlm": day_ntl_vlm,
            "open_interest": open_interest
        })

    return results


def get_top_symbols_by_volume(limit: int = 10) -> List[str]:
    """
    Get top symbols by open interest/volume.

    Returns:
        List of symbol names
    """
    payload = {"type": "metaAndAssetCtxs"}

    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    universe = data[0]["universe"]
    asset_ctxs = data[1]

    # Sort by open interest
    symbols_with_oi = []
    for i, asset_ctx in enumerate(asset_ctxs):
        symbol = universe[i]["name"]
        oi = float(asset_ctx.get("openInterest", 0))
        symbols_with_oi.append((symbol, oi))

    symbols_with_oi.sort(key=lambda x: x[1], reverse=True)

    return [s[0] for s in symbols_with_oi[:limit]]


if __name__ == "__main__":
    # Test the fetcher
    rates = fetch_funding_rates()
    print(f"Fetched {len(rates)} funding rates")
    for rate in rates[:5]:
        print(f"  {rate['symbol']}: {rate['funding_rate']:.6f} (mark: ${rate['mark_price']:.2f})")
