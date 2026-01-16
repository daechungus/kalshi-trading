"""
1. Take historical trades as input
2. Feed prices to your strategy
3. Simulate buying and selling based on strategy signals
4. Track P&L, win rate, and other performance metrics
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from .strategy import Signal
from ..ingestion.kalshi_client import Trade


@dataclass
class BacktestTrade:
    """Record of a simulated trade."""
    timestamp: datetime
    action: str      # 'buy' or 'sell'
    side: str        # 'yes' or 'no'
    price: int       # in cents
    contracts: int
    pnl: float = 0.0 # Realized P&L in cents


@dataclass
class BacktestResult:
    """Summary of backtest results."""
    total_round_trips: int   # Number of complete buy -> sell cycles
    winning_trades: int
    losing_trades: int
    total_pnl: float         # Total P&L in cents
    total_pnl_dollars: float # Total P&L in dollars
    max_drawdown: float      # Maximum drawdown in cents
    sharpe_ratio: float      # Simplified Sharpe ratio
    win_rate: float          # Percentage of winning trades
    avg_trade_pnl: float     # Average P&L per trade
    orders: list[BacktestTrade] = field(default_factory=list)

    def __str__(self) -> str:
        return f"""
=== Backtest Results ===
Round Trips:     {self.total_round_trips}
Winning:         {self.winning_trades}
Losing:          {self.losing_trades}
Win Rate:        {self.win_rate:.1f}%
Total P&L:       ${self.total_pnl_dollars:.2f}
Avg Trade P&L:   ${self.avg_trade_pnl / 100:.2f}
Max Drawdown:    ${self.max_drawdown / 100:.2f}
Sharpe Ratio:    {self.sharpe_ratio:.2f}
========================
"""


class Backtester:
    """
    1. Initialize with starting balance and trade parameters
    2. Loop through historical trades
    3. Feed prices to the strategy and get signals
    4. Simulate buying and selling based on signals
    5. Track P&L, positions, drawdown, and other metrics
    6. Return a BacktestResult with performance summary
    """

    def __init__(
        self,
        strategy: MomentumStrategy,
        initial_balance: float = 10000.0,  # in cents ($100)
        contracts_per_trade: int = 10,
        commission: float = 0.0,  # Commission per contract in cents
        side: str = "yes"  # 'yes' or 'no' - which side to trade
    ):
        """
        Initialize backtester.

        Args:
            strategy: The strategy to test
            initial_balance: Starting balance in cents
            contracts_per_trade: Fixed contracts per trade
            commission: Commission per contract (cents)
            side: Which side to trade ('yes' or 'no')
        """
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.contracts_per_trade = contracts_per_trade
        self.commission = commission
        self.side = side

    def run(self, trades: list[Trade]) -> BacktestResult:
        """
        1. Reset strategy state
        2. Initialize tracking variables (balance, position, etc.)
        3. Loop through all trades:
           - Extract price from trade
           - Update strategy with price
           - Execute buy/sell based on signal
           - Track P&L and metrics
        4. Calculate final statistics
        5. Return BacktestResult

        Args:
            trades: List of historical trades (should be sorted by time)

        Returns:
            BacktestResult with performance metrics
        """
        self.strategy.reset()

        # TODO: Initialize variables to track current balance, position, executed trades, P&L history, etc.

        # TODO: Loop through historical trades, get price, update strategy, get signal, execute trade, track P&L, update balance

        # TODO: Calculate metrics (win rate, sharpe ratio, max drawdown, etc.)

        # TODO: Return BacktestResult with performance metrics
        return BacktestResult(...)

    def run_from_prices(self, prices: list[tuple[datetime, float]]) -> BacktestResult:
        """
        Run backtest on a list of (timestamp, price) tuples.

        Convenience method for testing without full Trade objects.
        """
        fake_trades = [
            Trade(
                trade_id=str(i),
                ticker="TEST",
                yes_price=int(price),
                count=1,
                taker_side="yes",
                created_time=ts
            )
            for i, (ts, price) in enumerate(prices)
        ]
        return self.run(fake_trades)
