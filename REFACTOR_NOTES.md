# Monorepo Refactoring Notes

## Structure

The codebase has been refactored into a monorepo structure:

```
src/
├── ingestion/          # Data ingestion (API clients)
│   ├── kalshi_client.py
│   └── cme_client.py
├── execution/          # Trading execution
│   ├── live.py
│   ├── strategy.py
│   └── backtest.py
└── research/           # Future DHIN research
    └── (to be implemented)
```

## Tagged Version

The pre-refactor state is preserved as:
- **Tag:** `v1.0-execution`
- **Description:** "The HFT Arb Bot implementation before DHIN pivot"

To view the old structure:
```bash
git checkout v1.0-execution
```

## Import Updates

All imports have been updated to use the new structure:

### Old imports:
```python
from src.kalshi_client import KalshiClient
from src.strategy import CMEArbitrageStrategy
```

### New imports:
```python
from src.ingestion.kalshi_client import KalshiClient
from src.execution.strategy import CMEArbitrageStrategy
```

## Files Updated

- ✅ `src/execution/live.py` - Updated imports
- ✅ `src/execution/backtest.py` - Updated imports
- ✅ `backtest_cme_arbitrage.py` - Updated imports
- ✅ `list_kalshi_contracts.py` - Updated imports
- ⚠️ `main.py` - Legacy commands need updating (see below)

## TODO: Update main.py

The `main.py` file still references `MomentumStrategy` which has been removed. The backtest and live commands need to be updated to use `CMEArbitrageStrategy` or deprecated in favor of:
- `backtest_cme_arbitrage.py` - For CME arbitrage backtesting
- Future live trading script with CME integration

## Benefits

1. **Separation of Concerns:** Ingestion, execution, and research are clearly separated
2. **Reusability:** DHIN research can use the same ingestion clients
3. **Scalability:** Easy to add new research modules without touching execution code
4. **Maintainability:** Single source of truth for API clients

## Next Steps

1. Implement DHIN research in `src/research/`
2. Update `main.py` commands to use CMEArbitrageStrategy
3. Add integration tests for the new structure
4. Document the DHIN architecture

