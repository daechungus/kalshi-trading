#!/usr/bin/env python3
"""
List Kalshi Contracts for Fed Funds Rate Series

This script queries the Kalshi API to find all available contracts
in a given series (e.g., KXFED-26JAN) and displays their tickers and prices.
"""

import requests
import sys
from src.ingestion.kalshi_client import KalshiClient


def list_contracts(series_ticker: str, use_demo: bool = True):
    """
    List all contracts in a Kalshi series.
    
    Args:
        series_ticker: The series ticker (e.g., "KXFED-26JAN")
        use_demo: Whether to use demo API (default: True)
    """
    # Build the API path
    path = f"/trade-api/v2/markets?series_ticker={series_ticker}"
    
    # Try public endpoint first (no auth required)
    base_url = "https://demo-api.kalshi.co" if use_demo else "https://api.elections.kalshi.com"
    url = f"{base_url}{path}"
    
    try:
        print(f"[INFO] Querying {base_url}...")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"[ERROR] API returned {response.status_code}: {response.text}")
            # Try authenticated request as fallback
            try:
                print("[INFO] Trying authenticated request...")
                client = KalshiClient(demo=use_demo)
                data = client._request("GET", path)
                markets = data.get("markets", [])
            except Exception as e:
                print(f"[ERROR] Authenticated request also failed: {e}")
                print(f"\n[DEBUG] Full response: {response.text}")
                return
        else:
            data = response.json()
            markets = data.get("markets", [])
            
            # Debug: show raw response structure
            if not markets:
                print(f"[DEBUG] Response keys: {list(data.keys())}")
                print(f"[DEBUG] Full response: {data}")
        
        print("=" * 70)
        print(f"Kalshi Contracts for Series: {series_ticker}")
        print("=" * 70)
        print(f"Found {len(markets)} contracts\n")
        
        for i, m in enumerate(markets, 1):
            ticker = m.get("ticker", "N/A")
            title = m.get("title", "N/A")
            status = m.get("status", "N/A")
            yes_bid = m.get("yes_bid")
            yes_ask = m.get("yes_ask")
            last_price = m.get("last_price")
            
            print(f"[{i}] Ticker: {ticker}")
            print(f"     Title: {title}")
            print(f"     Status: {status}")
            
            if yes_bid is not None and yes_ask is not None:
                print(f"     Yes Bid/Ask: {yes_bid}¢ / {yes_ask}¢")
            elif last_price is not None:
                print(f"     Last Price: {last_price}¢")
            else:
                print(f"     Price: N/A")
            
            print("-" * 70)
        
        # Summary of actionable contracts
        print("\n" + "=" * 70)
        print("SUMMARY - Contracts with Active Pricing:")
        print("=" * 70)
        active_contracts = [
            m for m in markets 
            if m.get("yes_bid") is not None and m.get("yes_ask") is not None
        ]
        
        if active_contracts:
            for m in active_contracts:
                ticker = m.get("ticker")
                title = m.get("title")
                yes_bid = m.get("yes_bid")
                yes_ask = m.get("yes_ask")
                mid_price = (yes_bid + yes_ask) / 2
                print(f"  {ticker:30s} | {title:40s} | Mid: {mid_price:5.1f}¢")
        else:
            print("  No contracts with active bid/ask prices found")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch contracts: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="List Kalshi contracts for a given series"
    )
    parser.add_argument(
        "--series", "-s",
        default="KXFED-26JAN",
        help="Series ticker (default: KXFED-26JAN)"
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Use production API instead of demo"
    )
    
    args = parser.parse_args()
    
    list_contracts(args.series, use_demo=not args.prod)


if __name__ == "__main__":
    main()

