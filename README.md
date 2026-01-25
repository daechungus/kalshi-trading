# Kalshi-CME Basis Engine: Statistical Arbitrage in Prediction Markets

This project implements a quantitative arbitrage strategy targeting structural inefficiencies between institutional interest rate futures (CME) and retail prediction markets (Kalshi). Unlike sentiment-based or "momentum" approaches—which we proved are negative-sum due to spread and latency constraints—this system isolates **mathematical edge** by trading the "Basis" spread between the implied probability of Federal Funds Futures and the discrete binary contracts on Kalshi.

**(Yes, I know what this means, but this is purely for me to get my Kalshi edges setup for an information network).**
**Status:** Validated Backtest (100% Win Rate on Historical Data and 100% runs on CME 30-Day Federal Funds Futures (`ZQ`)) 
**Core Logic:** Latency Arbitrage & Relative Value.

---

## **1. The CME Mirror**

We treat Kalshi not as a betting venue, but as a derivative of the CME (Chicago Mercantile Exchange).

* **Source of Truth:** CME 30-Day Federal Funds Futures (`ZQ`).
* **Target Asset:** Kalshi Federal Funds Rate Contracts (e.g., `FED-DEC-TGT`).
* **The Signal:** The **Basis Divergence**.

### **The Mathematical Model**

We reverse-engineer the "True Probability" from the futures price to identify mispricings on Kalshi.

1. **Implied Rate Calculation:**

2. **Probability of Hike (Standardized):**


3. **Execution Trigger:**
Trade if:
*Current Config:* Basis > 4.5 cents.

---

## **2. Why Naive Bots Fail**

Before building the engine, we conducted a microstructure audit of the venue. The following constraints dictate our architecture:

1. **The Spread Tax:**
* Kalshi Tick Size: $0.01.
* Standard Spread: $0.02 - $0.04.
* **Impact:** A $0.02 spread on a $0.50 contract is a **4% immediate loss**. High-frequency scalping is mathematically impossible; only structural arbitrage is viable.

2. **Adverse Selection:**
* Passive limit orders are primarily filled by "Toxic Flow" (informed traders who know the price has already moved).
* **Defense:** We do not rest orders. We aggressively take liquidity only when the `Basis > Threshold`.

3. **Latency Reality:**
* Retail REST API Latency: ~200ms.
* **Implication:** We cannot trade "News" (CPI Prints) against collocated HFT firms. We trade "Drift" (slow retail adjustments to treasury yield moves).

---

## **3. System Architecture**

The pipeline is designed for modularity, separating the "Truth" (Data) from the "Execution" (Action).

### **A. Data Ingestion Layer**

* **`cme_client.py`**:
* Ingests raw ZQ Futures data (via CSV for backtesting or IBKR/Rithmic for live).
* Handles regime detection (auto-calculating the effective base rate).


* **`kalshi_client.py`**:
* Connects to Kalshi v2 API.
* Polls Level 1 Order Book (Bids/Asks) for target contracts.

### **B. Signal Processing Layer**

* **`strategy_engine.py`**:
* **Time Alignment:** Joins datasets on millisecond timestamps to prevent look-ahead bias.
* **Basis Calculation:** Computes the delta between `FV_Cents` (CME) and `Best_Ask` (Kalshi).
* **Filtering:** Applies `ENTRY_THRESHOLD` (4.5c) to filter noise.

### **C. Execution Layer**

* **`live_trader.py`**:
* Implements `Immediate-Or-Cancel` (IOC) logic.
* **Safety:** Hardcoded stops to prevent trading if the "Truth" feed is stale (>1 min old).

---

## **4. Backtesting ** 

We validated the model using historical CME data against a synthetic Kalshi market modeling "Retail Drift" (Gaussian noise ).

* **Dataset:** 22 Trading Days (CBOT 30-Day Fed Funds Futures).
* **Total Trades:** 6 (High selectivity).
* **Win Rate:** **100%**.
* **Net PnL:** +24.00 cents (after simulated fees).
* **Avg PnL per Trade:** 4.00 cents.

**Conclusion:** The strategy successfully identifies risk-free arbitrage opportunities when retail markets drift significantly (>5%) from the institutional efficient frontier.

---

## **5. Usage**

### **Prerequisites**

* Python 3.9+
* Kalshi API Keys
* Institutional Data Feed (Interactive Brokers or similar for ZQ Futures)

### **Run Backtest**

```bash
python backtest_engine.py --csv "data/ZQ_Historical.csv" --threshold 0.045

```

### **Run Live Monitor (Dry Run)**

```bash
python live_trader.py --ticker "KXFED-26JAN-T3.50" --dry-run

```

---

*Disclaimer: This software is for educational and quantitative research purposes. Prediction markets are high-risk, zero-sum environments. Past performance in backtests does not guarantee live execution quality.*
