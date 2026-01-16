# Finding Kalshi Contract Tickers

## Quick Command

Run this command to list all contracts in a series:

```bash
python -m uv run python list_kalshi_contracts.py --series KXFED-26JAN
```

Or for production API:
```bash
python -m uv run python list_kalshi_contracts.py --series KXFED-26JAN --prod
```

## If No Contracts Found

The series might:
1. Not exist in demo API (try `--prod`)
2. Be expired/closed
3. Have a different ticker format

## Alternative: Manual API Check

You can also check directly via browser or curl:

**Demo API:**
```
https://demo-api.kalshi.co/trade-api/v2/markets?series_ticker=KXFED-26JAN
```

**Production API:**
```
https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXFED-26JAN
```

## What to Look For

Based on your CME data showing **Rate = 3.64%**, you want contracts like:

- **"Fed Funds Rate > 3.50"** - Should trade at high probability (~60-80%)
- **"Fed Funds Rate > 3.75"** - Should trade at low probability (~10-30%)

Once you find the exact ticker (e.g., `KXFED-26JAN-T3.50`), update your strategy configuration.

