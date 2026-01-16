"""
TODO: Implement your strategy here
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import deque


@dataclass
class Signal:
    """Trading signal produced by the strategy."""
    action: Optional[str]  # 'buy', 'sell', or None (hold)
    side: str = "yes"      # 'yes' or 'no' side
    confidence: float = 0.0
    reason: str = ""


@dataclass
class MomentumStrategy:
    """
    This is a template for a momentum-based strategy, but you can implement
    any type of strategy you want. The key is to implement the update() method
    that takes in a new price and returns a Signal.

    Attributes:
        short_window: Period for the fast moving average (example parameter)
        long_window: Period for the slow moving average (example parameter)
        threshold: Minimum % difference to trigger a signal (example parameter)
    """
    short_window: int = 5
    long_window: int = 20
    threshold: float = 2.0

    prices: deque = field(default_factory=lambda: deque(maxlen=100))
    position: int = 0  # Current position: +1 long, 0 flat, -1 short

    def __post_init__(self):
        """Initialize any additional state needed by your strategy."""
        self.prices = deque(maxlen=max(self.long_window * 2, 100))

    def reset(self):
        """Reset strategy state."""
        self.prices.clear()
        self.position = 0

    def update(self, price: float) -> Signal:
        """
        Update strategy with new price and generate signal.

        This is the main method you need to implement! It should:
        1. Store/process the new price
        2. Calculate any indicators you need
        3. Generate a buy, sell, or hold signal based on your strategy

        Args:
            price: Latest price (in cents, 0-100)

        Returns:
            Signal indicating action to take (buy, sell, or hold)
        """
        self.prices.append(price)

        # TODO: Implement your strategy logic

        # For now, just return a hold signal
        return Signal(
            action=None,
            reason="Strategy not implemented yet"
        )

    def get_state(self) -> dict:
        """Get current strategy state for debugging."""
        return {
            "prices_count": len(self.prices),
            "position": self.position,
            "last_price": self.prices[-1] if self.prices else None
        }
