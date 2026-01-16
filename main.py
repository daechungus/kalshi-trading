#!/usr/bin/env python3
"""
Kalshi Trading System - Student Template

TODO: Implement your trading strategy and backtesting logic!

This template provides the core structure for:
- Connecting to Kalshi API
- Fetching market data and historical trades
- Running backtests on historical data
- Live trading (paper and real)

Your task is to implement:
1. Trading strategy in src/strategy.py
2. Backtesting logic in src/backtest.py
3. Live trading logic in src/live.py (optional)

Usage:
    # Get market information
    uv run python main.py info --ticker SOME-TICKER

    # Backtest your strategy
    uv run python main.py backtest --ticker SOME-TICKER

    # Live trading (dry run)
    uv run python main.py live --ticker SOME-TICKER
"""

import argparse
import sys
from datetime import datetime, timedelta

from src.kalshi_client import KalshiClient
from src.strategy import MomentumStrategy
from src.backtest import Backtester
from src.live import LiveTrader, LiveConfig


def cmd_backtest(args):
    """Run backtesting on historical data."""
    print(f"\n{'='*50}")
    print("TRADING STRATEGY BACKTEST")
    print(f"{'='*50}")
    print(f"Market: {args.ticker}")
    print(f"Side: {args.side.upper()}")
    print(f"Strategy: short_window={args.short_window}, long_window={args.long_window}, threshold={args.threshold}%")
    print(f"{'='*50}\n")

    # Initialize client
    client = KalshiClient(demo=args.demo)

    # Fetch market info
    try:
        market = client.get_market(args.ticker)
        print(f"Market: {market.title}")
        print(f"Status: {market.status}")
        print(f"Volume: {market.volume}")
        print()
    except Exception as e:
        print(f"Error fetching market: {e}")
        return 1

    # Calculate time range
    end_ts = args.end_ts or int(datetime.now().timestamp())
    start_ts = args.start_ts or (end_ts - args.lookback_hours * 3600)

    print(f"Fetching trades from {datetime.fromtimestamp(start_ts)} to {datetime.fromtimestamp(end_ts)}...")

    # Fetch historical trades
    try:
        trades = client.get_trades(
            ticker=args.ticker,
            min_ts=start_ts,
            max_ts=end_ts,
            limit=args.max_trades
        )
        print(f"Fetched {len(trades)} trades\n")
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return 1

    if len(trades) < args.long_window:
        print(f"Not enough trades for backtest (need at least {args.long_window})")
        return 1

    # Initialize strategy
    strategy = MomentumStrategy(
        short_window=args.short_window,
        long_window=args.long_window,
        threshold=args.threshold
    )

    # Run backtest
    backtester = Backtester(
        strategy=strategy,
        initial_balance=args.initial_balance * 100,  # Convert to cents
        contracts_per_trade=args.contracts,
        side=args.side
    )

    result = backtester.run(trades)

    # Print results
    print(result)

    # Print trade log if verbose
    if args.verbose:
        print("\n===== Order Log =====")
        for t in result.orders:
            pnl_str = f" P&L: ${t.pnl/100:+.2f}" if t.pnl else ""
            print(f"{t.timestamp}: {t.action.upper()} {t.contracts} @ {t.price}¢{pnl_str}")

    return 0


def cmd_live(args):
    """Run live trading."""
    print(f"\n{'='*50}")
    print("TRADING STRATEGY - LIVE TRADING")
    print(f"{'='*50}")
    print(f"Market: {args.ticker}")
    print(f"Strategy: short_window={args.short_window}, long_window={args.long_window}, threshold={args.threshold}%")
    print(f"Dry Run: {not args.no_dry_run}")
    print(f"Poll Interval: {args.poll_interval}s")
    print(f"{'='*50}\n")

    if not args.no_dry_run:
        print("DRY RUN MODE - No real orders will be placed\n")
    else:
        print("LIVE MODE - Real orders will be placed!\n")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Aborted.")
            return 1

    # Initialize components
    client = KalshiClient(demo=args.demo)

    strategy = MomentumStrategy(
        short_window=args.short_window,
        long_window=args.long_window,
        threshold=args.threshold
    )

    config = LiveConfig(
        ticker=args.ticker,
        contracts_per_trade=args.contracts,
        poll_interval=args.poll_interval,
        max_position=args.max_position,
        dry_run=not args.no_dry_run
    )

    trader = LiveTrader(client, strategy, config)

    # Show initial state
    try:
        market = client.get_market(args.ticker)
        print(f"Market: {market.title}")
        print(f"Status: {market.status}")
        print(f"Current Price: {market.last_price}¢")
        print()
    except Exception as e:
        print(f"Warning: Could not fetch market info: {e}")

    # Run trader
    duration = args.duration * 60 if args.duration else None
    trader.run(duration=duration)

    return 0


def cmd_info(args):
    """Get market information."""
    client = KalshiClient(demo=args.demo)

    try:
        market = client.get_market(args.ticker)
        print(f"\nMarket: {market.ticker}")
        print(f"Title: {market.title}")
        print(f"Status: {market.status}")
        print(f"Yes Bid: {market.yes_bid}¢")
        print(f"Yes Ask: {market.yes_ask}¢")
        print(f"Last Price: {market.last_price}¢")
        print(f"Volume: {market.volume}")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Kalshi Trading System - Student Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Global options
    parser.add_argument(
        "--demo", action="store_true", default=True,
        help="Use demo API (default: True)"
    )
    parser.add_argument(
        "--prod", action="store_true",
        help="Use production API"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # ===== Backtest command =====
    backtest_parser = subparsers.add_parser(
        "backtest", help="Run strategy backtest on historical data"
    )
    backtest_parser.add_argument(
        "--ticker", "-t", required=True,
        help="Market ticker to backtest"
    )
    backtest_parser.add_argument(
        "--side", "-s", choices=["yes", "no"], default="yes",
        help="Which side to trade: 'yes' or 'no' (default: yes)"
    )
    backtest_parser.add_argument(
        "--short-window", type=int, default=5,
        help="Short moving average window (default: 5)"
    )
    backtest_parser.add_argument(
        "--long-window", type=int, default=20,
        help="Long moving average window (default: 20)"
    )
    backtest_parser.add_argument(
        "--threshold", type=float, default=2.0,
        help="Momentum threshold percentage (default: 2.0)"
    )
    backtest_parser.add_argument(
        "--lookback-hours", type=int, default=24,
        help="Hours of historical data to fetch (default: 24)"
    )
    backtest_parser.add_argument(
        "--start-ts", type=int, default=None,
        help="Start timestamp (Unix). Overrides --lookback-hours"
    )
    backtest_parser.add_argument(
        "--end-ts", type=int, default=None,
        help="End timestamp (Unix). Defaults to now"
    )
    backtest_parser.add_argument(
        "--max-trades", type=int, default=10000,
        help="Maximum trades to fetch (default: 10000)"
    )
    backtest_parser.add_argument(
        "--initial-balance", type=float, default=100.0,
        help="Initial balance in dollars (default: 100)"
    )
    backtest_parser.add_argument(
        "--contracts", type=int, default=10,
        help="Contracts per trade (default: 10)"
    )
    backtest_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed trade log"
    )

    # ===== Live command =====
    live_parser = subparsers.add_parser(
        "live", help="Run live trading"
    )
    live_parser.add_argument(
        "--ticker", "-t", required=True,
        help="Market ticker to trade"
    )
    live_parser.add_argument(
        "--short-window", type=int, default=5,
        help="Short moving average window (default: 5)"
    )
    live_parser.add_argument(
        "--long-window", type=int, default=20,
        help="Long moving average window (default: 20)"
    )
    live_parser.add_argument(
        "--threshold", type=float, default=2.0,
        help="Momentum threshold percentage (default: 2.0)"
    )
    live_parser.add_argument(
        "--poll-interval", type=float, default=5.0,
        help="Seconds between price checks (default: 5.0)"
    )
    live_parser.add_argument(
        "--contracts", type=int, default=1,
        help="Contracts per trade (default: 1)"
    )
    live_parser.add_argument(
        "--max-position", type=int, default=10,
        help="Maximum position size (default: 10)"
    )
    live_parser.add_argument(
        "--duration", type=float, default=None,
        help="Max runtime in minutes (default: unlimited)"
    )
    live_parser.add_argument(
        "--no-dry-run", action="store_true",
        help="Execute real orders (default: dry run)"
    )

    # ===== Info command =====
    info_parser = subparsers.add_parser(
        "info", help="Get market information"
    )
    info_parser.add_argument(
        "--ticker", "-t", required=True,
        help="Market ticker"
    )

    args = parser.parse_args()

    # Handle --prod flag
    if args.prod:
        args.demo = False

    if args.command == "backtest":
        return cmd_backtest(args)
    elif args.command == "live":
        return cmd_live(args)
    elif args.command == "info":
        return cmd_info(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
