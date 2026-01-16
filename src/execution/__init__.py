"""
Execution Module

Contains trading execution and strategy logic:
- LiveTrader: Live trading engine
- CMEArbitrageStrategy: CME-to-Kalshi arbitrage strategy
- Backtester: Backtesting engine
"""

from .live import LiveTrader, LiveConfig
from .strategy import Signal, CMEArbitrageStrategy
from .backtest import Backtester, BacktestResult, BacktestTrade

__all__ = [
    'LiveTrader', 'LiveConfig',
    'Signal', 'CMEArbitrageStrategy',
    'Backtester', 'BacktestResult', 'BacktestTrade'
]

