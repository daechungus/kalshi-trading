#!/usr/bin/env python3
"""
CME-to-Kalshi Arbitrage Backtest Runner

This script runs a backtest of the CME arbitrage strategy using:
1. CME Fed Funds Futures data (from CSV)
2. Kalshi market data (from API or mock data)

Usage:
    python backtest_cme_arbitrage.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.cme_client import CMEClient
from src.strategy import CMEArbitrageStrategy


def generate_kalshi_mock(cme_probs: pd.Series, drift_std: float = 0.05) -> pd.DataFrame:
    """
    Generate synthetic Kalshi market data that occasionally drifts from CME truth.
    
    Args:
        cme_probs: Series of CME probabilities (0.0-1.0)
        drift_std: Standard deviation of drift noise
    
    Returns:
        DataFrame with 'yes_bid' and 'yes_ask' columns
    """
    np.random.seed(42)  # Deterministic for reproducibility
    data = []
    
    for date, true_prob in cme_probs.items():
        # Add random drift/noise to create arbitrage opportunities
        noise = np.random.normal(0, drift_std)
        market_center_prob = true_prob + noise
        market_center_cents = market_center_prob * 100
        
        # Create bid/ask spread (4 cents wide)
        spread_width = 4
        bid = int(market_center_cents - (spread_width / 2))
        ask = int(market_center_cents + (spread_width / 2))
        
        # Clamp to valid range (1-99)
        bid = max(1, min(98, bid))
        ask = max(bid + 1, min(99, ask))
        
        data.append({'yes_bid': bid, 'yes_ask': ask})
    
    return pd.DataFrame(data, index=cme_probs.index)


def main():
    print("=" * 60)
    print("CME-to-Kalshi Arbitrage Backtest")
    print("=" * 60)
    print()
    
    # Configuration
    CSV_PATH = "CBOT 30-DAY Federal Fund Futures Historical Data.csv"
    CURRENT_EFFR = 5.33  # Current effective federal funds rate
    ENTRY_THRESHOLD = 4.5  # cents
    FEES_ROUND_TRIP = 2.0  # cents
    
    # 1. Load CME Data (The Source of Truth)
    print("[1/4] Loading CME Fed Funds Futures data...")
    try:
        cme = CMEClient(csv_path=CSV_PATH)
        cme_probs = cme.calculate_probabilities(current_effr=CURRENT_EFFR)
        print(f"    [OK] Loaded {len(cme_probs)} days of CME data")
        print(f"    [OK] Sample probabilities: {cme_probs.head(3).tolist()}")
        print()
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        print(f"    Please ensure '{CSV_PATH}' exists in the current directory")
        return 1
    except Exception as e:
        print(f"    [ERROR] Error loading CME data: {e}")
        return 1
    
    # 2. Generate/Load Kalshi Data
    print("[2/4] Generating synthetic Kalshi market data...")
    print("    (In production, this would come from Kalshi API)")
    kalshi_data = generate_kalshi_mock(cme_probs, drift_std=0.05)
    print(f"    [OK] Generated {len(kalshi_data)} days of Kalshi data")
    print(f"    [OK] Sample bid/ask: {kalshi_data.head(3).to_dict('records')}")
    print()
    
    # 3. Run Strategy Backtest
    print("[3/4] Running arbitrage strategy...")
    strategy = CMEArbitrageStrategy(
        cme_probs=cme_probs,
        entry_threshold=ENTRY_THRESHOLD,
        fees_round_trip=FEES_ROUND_TRIP
    )
    
    results_df = strategy.run_backtest(kalshi_data)
    trades = results_df[results_df['signal'] != 0].copy()
    
    print(f"    [OK] Analyzed {len(results_df)} days")
    print(f"    [OK] Found {len(trades)} trading opportunities")
    print()
    
    # 4. Calculate and Display Results
    print("[4/4] Calculating performance metrics...")
    print()
    
    if len(trades) > 0:
        total_pnl = trades['pnl_net'].sum()
        winning_trades = (trades['pnl_net'] > 0).sum()
        losing_trades = (trades['pnl_net'] <= 0).sum()
        win_rate = (trades['pnl_net'] > 0).mean() * 100
        avg_pnl = trades['pnl_net'].mean()
        
        print("=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Total Trades:        {len(trades)}")
        print(f"Winning Trades:       {winning_trades}")
        print(f"Losing Trades:        {losing_trades}")
        print(f"Win Rate:            {win_rate:.1f}%")
        print(f"Total P&L (cents):   {total_pnl:.2f}")
        print(f"Total P&L (dollars): ${total_pnl / 100:.2f}")
        print(f"Avg P&L per Trade:   ${avg_pnl / 100:.2f}")
        print("=" * 60)
        print()
        
        # Show sample trades
        print("Sample Trades (Top 5):")
        print("-" * 60)
        sample_cols = ['yes_bid', 'yes_ask', 'fv_cents', 'basis_long', 'basis_short', 'signal', 'pnl_net']
        print(trades[sample_cols].head().to_string())
        print()
        
        # Analysis
        if total_pnl > 0:
            print("[SUCCESS] Strategy is profitable!")
            if win_rate < 50:
                print("  [WARNING] Low win rate - consider increasing entry threshold")
        else:
            print("[FAILED] Strategy is not profitable")
            print("  Suggestions:")
            print("  - Increase ENTRY_THRESHOLD (currently {:.1f} cents)".format(ENTRY_THRESHOLD))
            print("  - Check if fees are too high")
            print("  - Verify CME probability calculations")
    else:
        print("=" * 60)
        print("NO TRADES TRIGGERED")
        print("=" * 60)
        print(f"Reason: Basis never exceeded entry threshold of {ENTRY_THRESHOLD} cents")
        print()
        print("Suggestions:")
        print("  - Decrease ENTRY_THRESHOLD (currently {:.1f} cents)".format(ENTRY_THRESHOLD))
        print("  - Increase drift_std in generate_kalshi_mock() to create more opportunities")
        print("  - Check if CME and Kalshi data are properly aligned")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

