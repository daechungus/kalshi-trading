# Kalshi Systematic Trading Template

## Step 1: Set Up Environment

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Get Kalshi API credentials:
   - Sign up at [demo-api.kalshi.co](https://demo-api.kalshi.co)
   - Generate API keys from settings
   - Download private key file

3. Configure credentials:
   ```bash
   cp .env.example .env
   # Edit .env and add your KALSHI_DEMO_API_KEY_ID
   # Save your private key as kalshi_demo_api_private_key.txt
   ```

4. Test the setup:
   ```bash
   uv run python main.py info --ticker HIGHNY-25JAN16
   ```

## Step 2: Implement Your Strategy

Open `src/strategy.py` and implement the `update()` method:

```python
def update(self, price: float) -> Signal:
    # 1. Add the new price to your price history
    # 2. Check if you have enough data
    if len(self.prices) < self.long_window:
        return Signal(action=None, reason="Warming up")

    # 3. Calculate your indicators
    # 4. Generate buy/sell signals based on your strategy
    # 5. Return a Signal with action and reason
    return Signal(
        action="buy",  # or "sell" or None
        reason="Your reasoning here"
    )
```

**Suggested strategies to try:**
- Mean Reversion
- Momentum/Trend Following

## Step 3: Implement Backtesting

Open `src/backtest.py` and implement the `run()` method:

```python
def run(self, trades: list[Trade]) -> BacktestResult:
    # Initialize tracking variables
    # Loop through historical trades
    for trade in trades:
        # Get price
        # Update strategy and get signal
        # Execute trades based on signal
        if signal.action == "buy" and position is None:
            # Open position: deduct cost from balance
            # Save position info
            ...
        elif signal.action == "sell" and position is not None:
            # Close position: calculate P&L
            # Add to balance
            # Track in pnl_history
            ...

    # Calculate final metrics
    # Return BacktestResult
    return BacktestResult(...)
```

**Key metrics to track:**
- Total P&L
- Number of trades
- Win rate (% of profitable trades)
- Average trade P&L
- Maximum drawdown
- Sharpe ratio (optional but good to have)

## Step 4: Test Your Strategy

1. Run a backtest:
   ```bash
   uv run python main.py backtest --ticker HIGHNY-25JAN16 -v
   ```

2. Experiment with parameters:
   ```bash
   uv run python main.py backtest --ticker HIGHNY-25JAN16 \
       --short-window 3 \
       --long-window 10 \
       --threshold 1.5
   ```

3. Try different markets and time periods:
   ```bash
   uv run python main.py backtest --ticker SOME-TICKER \
       --lookback-hours 48
   ```

## Step 5: Implement Live Trading (Optional)

If you want to run your strategy live (dry run mode by default):

Open `src/live.py` and implement:

1. `_get_current_price()` - Fetch latest market price
2. `_execute_signal()` - Place buy/sell orders (or simulate in dry run)
3. `run()` - Main loop that polls prices and executes signals

## Expected Output

When your backtest works, you should see:

```
=== Backtest Results ===
Round Trips:     12
Winning:         8
Losing:          4
Win Rate:        66.7%
Total P&L:       $5.30
Avg Trade P&L:   $0.44
Max Drawdown:    $2.10
Sharpe Ratio:    0.85
========================
```

# Disclaimer

This is for educational purposes only. Trading prediction markets involves risk. Always test thoroughly with the demo API. We do not endorse using this template for real trading.
