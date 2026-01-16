"""
Trading strategies for Kalshi markets.

Includes:
- MomentumStrategy: Template momentum-based strategy
- CMEArbitrageStrategy: CME-to-Kalshi basis trading strategy
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import deque
import pandas as pd
import numpy as np


@dataclass
class Signal:
    """Trading signal produced by the strategy."""
    action: Optional[str]  # 'buy', 'sell', or None (hold)
    side: str = "yes"      # 'yes' or 'no' side
    confidence: float = 0.0
    reason: str = ""

@dataclass
class CMEArbitrageStrategy:
    """
    CME-to-Kalshi Arbitrage Strategy.
    
    Trades the basis between CME Fed Funds Futures (the "Source of Truth")
    and Kalshi prediction markets. When Kalshi drifts away from CME pricing,
    we arbitrage the difference.
    
    Attributes:
        cme_probs: Series of CME-implied probabilities (0.0-1.0) indexed by date
        entry_threshold: Minimum basis (in cents) to trigger a trade (default: 4.5)
        fees_round_trip: Estimated fees per round trip in cents (default: 2.0)
    """
    cme_probs: pd.Series
    entry_threshold: float = 4.5  # cents
    fees_round_trip: float = 2.0  # cents
    
    def calculate_basis(self, kalshi_bid: int, kalshi_ask: int, fair_value_cents: float) -> tuple[float, float]:
        """
        Calculate the basis (edge) for long and short opportunities.
        
        Args:
            kalshi_bid: Kalshi bid price in cents
            kalshi_ask: Kalshi ask price in cents
            fair_value_cents: CME-implied fair value in cents (0-100)
        
        Returns:
            (basis_long, basis_short) where:
            - basis_long: Positive means Kalshi is cheap (buy opportunity)
            - basis_short: Positive means Kalshi is expensive (sell opportunity)
        """
        basis_long = fair_value_cents - kalshi_ask  # Buy cheap
        basis_short = kalshi_bid - fair_value_cents  # Sell expensive
        return basis_long, basis_short
    
    def update(
        self, 
        kalshi_bid: int, 
        kalshi_ask: int, 
        date: Optional[pd.Timestamp] = None,
        fair_value_cents: Optional[float] = None
    ) -> Signal:
        """
        Update strategy with current Kalshi market and generate signal.
        
        Args:
            kalshi_bid: Current Kalshi bid price in cents
            kalshi_ask: Current Kalshi ask price in cents
            date: Date for looking up CME probability (if None, uses latest)
            fair_value_cents: Pre-calculated fair value (if None, looks up from cme_probs)
        
        Returns:
            Signal indicating action (buy, sell, or hold)
        """
        # Get fair value from CME probabilities
        if fair_value_cents is None:
            if date is None:
                # Use most recent probability
                if len(self.cme_probs) == 0:
                    return Signal(action=None, reason="No CME data available")
                fair_value_prob = self.cme_probs.iloc[-1]
            else:
                # Look up probability for this date
                if date not in self.cme_probs.index:
                    # Find nearest date
                    nearest_idx = self.cme_probs.index.get_indexer([date], method='nearest')[0]
                    if nearest_idx == -1:
                        return Signal(action=None, reason=f"No CME data for date {date}")
                    fair_value_prob = self.cme_probs.iloc[nearest_idx]
                else:
                    fair_value_prob = self.cme_probs[date]
            
            fair_value_cents = fair_value_prob * 100
        
        # Calculate basis
        basis_long, basis_short = self.calculate_basis(kalshi_bid, kalshi_ask, fair_value_cents)
        
        # Generate signal
        if basis_long > self.entry_threshold:
            return Signal(
                action="buy",
                side="yes",
                confidence=min(basis_long / 10.0, 1.0),  # Normalize confidence
                reason=f"Long edge: {basis_long:.2f} cents (FV: {fair_value_cents:.2f}¢, Ask: {kalshi_ask}¢)"
            )
        elif basis_short > self.entry_threshold:
            return Signal(
                action="sell",
                side="yes",
                confidence=min(basis_short / 10.0, 1.0),
                reason=f"Short edge: {basis_short:.2f} cents (FV: {fair_value_cents:.2f}¢, Bid: {kalshi_bid}¢)"
            )
        else:
            return Signal(
                action=None,
                reason=f"No edge (Long: {basis_long:.2f}¢, Short: {basis_short:.2f}¢, Threshold: {self.entry_threshold}¢)"
            )
    
    def run_backtest(self, kalshi_data: pd.DataFrame) -> pd.DataFrame:
        """
        Run backtest on aligned CME and Kalshi data.
        
        Args:
            kalshi_data: DataFrame with 'yes_bid' and 'yes_ask' columns, indexed by date
        
        Returns:
            DataFrame with signals, basis, and PnL calculations
        """
        # Align dataframes by date (inner join)
        df = pd.concat([
            self.cme_probs.rename("fair_value_prob"),
            kalshi_data[['yes_bid', 'yes_ask']]
        ], axis=1).dropna()
        
        # Convert probability to cents
        df['fv_cents'] = df['fair_value_prob'] * 100
        
        # Calculate basis
        df['basis_long'] = df['fv_cents'] - df['yes_ask']
        df['basis_short'] = df['yes_bid'] - df['fv_cents']
        
        # Generate signals
        df['signal'] = 0  # 0 = Hold, 1 = Buy, -1 = Sell
        df.loc[df['basis_long'] > self.entry_threshold, 'signal'] = 1
        df.loc[df['basis_short'] > self.entry_threshold, 'signal'] = -1
        
        # Calculate PnL (simplified: assume exit at fair value)
        trades = df[df['signal'] != 0].copy()
        if not trades.empty:
            trades['pnl_gross'] = np.where(
                trades['signal'] == 1,
                trades['fv_cents'] - trades['yes_ask'],  # Long: buy at ask, exit at FV
                trades['yes_bid'] - trades['fv_cents']    # Short: sell at bid, exit at FV
            )
            trades['pnl_net'] = trades['pnl_gross'] - self.fees_round_trip
            df.loc[trades.index, 'pnl_gross'] = trades['pnl_gross']
            df.loc[trades.index, 'pnl_net'] = trades['pnl_net']
        else:
            df['pnl_gross'] = 0.0
            df['pnl_net'] = 0.0
        
        return df
    
    def get_state(self) -> dict:
        """Get current strategy state for debugging."""
        return {
            "cme_data_points": len(self.cme_probs),
            "entry_threshold": self.entry_threshold,
            "fees_round_trip": self.fees_round_trip,
            "latest_fair_value": (self.cme_probs.iloc[-1] * 100) if len(self.cme_probs) > 0 else None
        }
