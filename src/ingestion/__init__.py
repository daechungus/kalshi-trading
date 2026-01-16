"""
Data Ingestion Module

Contains API clients for fetching data from external sources:
- KalshiClient: Kalshi API client
- CMEClient: CME Fed Funds Futures data client
"""

from .kalshi_client import KalshiClient, Market, Trade
from .cme_client import CMEClient

__all__ = ['KalshiClient', 'Market', 'Trade', 'CMEClient']

