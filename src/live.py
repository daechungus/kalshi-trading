"""
1. Poll the market for current prices
2. Feed prices to your strategy
3. Execute buy/sell orders based on signals
4. Track current position and manage risk
"""

import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .kalshi_client import KalshiClient
from .strategy import MomentumStrategy, Signal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LiveConfig:
    """Configuration for live trading."""
    ticker: str                    # Market ticker to trade
    contracts_per_trade: int = 1   # Contracts per order
    poll_interval: float = 5.0     # Seconds between price checks
    max_position: int = 10         # Maximum position size
    dry_run: bool = True           # If True, don't execute real orders


class LiveTrader:
    """
    Live trading engine for Kalshi.

    TODO: Implement live trading logic!

    The live trader should:
    1. Initialize with client, strategy, and config
    2. Continuously poll market for current prices
    3. Update strategy with prices and get signals
    4. Execute orders based on signals (respecting position limits)
    5. Handle errors gracefully
    """

    def __init__(
        self,
        client: KalshiClient,
        strategy: MomentumStrategy,
        config: LiveConfig
    ):
        """
        Initialize live trader.

        Args:
            client: Authenticated Kalshi API client
            strategy: Strategy instance
            config: Trading configuration
        """
        self.client = client
        self.strategy = strategy
        self.config = config
        self.running = False
        self.position = 0  # Current position in contracts

    def _get_current_price(self) -> Optional[int]:
        """
        Fetch current market price using micro price calculation.

        Micro price is a volume-weighted average that considers both
        bid/ask prices and their sizes: ((bid_size * ask_price) + (ask_size * bid_price)) / total_volume
        """
        try:
            market = self.client.get_market(self.config.ticker)
            
            # If we have bid/ask sizes, calculate micro price
            if (market.yes_bid is not None and market.yes_ask is not None and
                market.yes_bid_size is not None and market.yes_ask_size is not None):
                total_volume = market.yes_bid_size + market.yes_ask_size
                if total_volume > 0:
                    micro_price = ((market.yes_bid_size * market.yes_ask) + 
                                  (market.yes_ask_size * market.yes_bid)) / total_volume
                    return int(round(micro_price))
            
            # Fallback to mid price if sizes not available
            if market.yes_bid is not None and market.yes_ask is not None:
                mid_price = (market.yes_bid + market.yes_ask) / 2
                return int(round(mid_price))
            
            # Final fallback to last_price
            return market.last_price
        except Exception as e:
            logger.error(f"Failed to get price: {e}")
            return None

    def _execute_signal(self, signal: Signal, price: int) -> bool:
        """
        Execute a trading signal.

        TODO: Implement order execution logic!

        This should:
        1. Check if we should execute (position limits, etc.)
        2. Calculate number of contracts to trade
        3. If dry_run: just log and update simulated position
        4. If not dry_run: use self.client.create_order() to place real order
        5. Update self.position
        6. Return True if order was placed

        Returns:
            True if order was placed successfully
        """
        if signal.action is None:
            return False

        # TODO: Check position limits
        # TODO: Calculate contracts to trade
        # TODO: Place order (or simulate if dry_run)
        # TODO: Update position

        logger.info(f"Signal received: {signal.action} (not implemented)")
        return False

    def run(self, duration: Optional[float] = None):
        """
        Start the live trading loop.

        TODO: Implement the main trading loop!

        This should:
        1. Log startup info
        2. Loop continuously (or until duration expires):
           a. Fetch current price
           b. Update strategy with price
           c. Execute any signals
           d. Sleep for poll_interval
        3. Handle KeyboardInterrupt gracefully
        4. Log final position

        Args:
            duration: Max runtime in seconds. None for infinite.
        """
        logger.info(f"Starting live trader for {self.config.ticker}")
        logger.info(f"Dry run: {self.config.dry_run}")

        self.running = True
        start_time = time.time()

        try:
            while self.running:
                # TODO: Implement trading loop
                # 1. Check duration limit
                # 2. Get current price
                # 3. Update strategy
                # 4. Execute signals
                # 5. Sleep

                logger.info("Trading loop not implemented yet")
                time.sleep(self.config.poll_interval)

                # Break after one iteration for now
                break

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.running = False
            logger.info(f"Final position: {self.position} contracts")

    def stop(self):
        """Stop the trading loop."""
        self.running = False
