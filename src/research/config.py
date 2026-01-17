"""
Configuration for DHIN Research Module

Contains shared configuration for graph building, data paths, and model parameters.
"""

import os

# Data Paths
CSV_PATH = "CBOT 30-DAY Federal Fund Futures Historical Data.csv"
CME_CSV_PATH = os.getenv("CME_CSV_PATH", CSV_PATH)

# Market Parameters
CURRENT_EFFR = 5.33  # Current effective federal funds rate
HIKE_SIZE = 0.25     # Standard 25 bps hike
RATE_VOLATILITY = 0.05  # Uncertainty buffer (standard deviation)

# Trading Parameters
ENTRY_THRESHOLD = 4.5  # cents
FEES_ROUND_TRIP = 2.0  # cents

# Graph Building Parameters
KALSHI_DRIFT_STD = 0.05  # Standard deviation of Kalshi market drift
STRIKE_BASE = 3.50  # Base strike for probability calculation

