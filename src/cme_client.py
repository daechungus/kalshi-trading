"""
CME Fed Funds Futures Client

Parses historical CME data and converts ZQ futures prices to implied probabilities.
This is the "Source of Truth" for the CME-to-Kalshi arbitrage strategy.
"""

import pandas as pd
import numpy as np
import os
from typing import Optional
from datetime import datetime


class CMEClient:
    """
    Client for loading and processing CME Fed Funds Futures data.
    
    Converts ZQ futures prices to implied probabilities of rate hikes.
    Formula: Rate = 100 - Price, then Prob = (Rate - Base) / 0.25
    """
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize CME client.
        
        Args:
            csv_path: Path to CSV file with CME data. If None, uses default path.
        """
        self.csv_path = csv_path or "CBOT 30-DAY Federal Fund Futures Historical Data.csv"
        self.data: Optional[pd.DataFrame] = None
        self.hike_size = 0.25  # Standard 25 bps hike
        
    def load_data(self) -> pd.DataFrame:
        """
        Load and parse CME data from CSV.
        
        Expected CSV format:
        - Date column (MM/DD/YYYY format)
        - Price column (ZQ futures price, e.g., 96.36)
        
        Returns:
            DataFrame with Date index and Price column
        """
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CME data file not found: {self.csv_path}")
        
        print(f"[CME] Loading data from {self.csv_path}...")
        df = pd.read_csv(self.csv_path)
        
        # Parse date column
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df = df.sort_values('Date').set_index('Date')
        
        # Keep only Price column (close price)
        if 'Price' not in df.columns:
            raise ValueError("CSV must contain 'Price' column")
        
        self.data = df[['Price']].copy()
        print(f"[CME] Loaded {len(self.data)} days of data")
        return self.data
    
    def calculate_probabilities(
        self, 
        current_effr: float = 5.33,
        target_rate: Optional[float] = None
    ) -> pd.Series:
        """
        Convert ZQ futures prices to implied probabilities.
        
        Args:
            current_effr: Current effective federal funds rate (e.g., 5.33%)
            target_rate: Target rate for the probability calculation.
                        If None, uses current_effr + hike_size
        
        Returns:
            Series of probabilities (0.0 to 1.0) indexed by date
        """
        if self.data is None:
            self.load_data()
        
        # Calculate implied rate from futures price
        # Formula: Rate = 100 - Price
        self.data['implied_rate'] = 100 - self.data['Price']
        
        # Determine base rate (nearest 25bps increment below implied rate)
        # This estimates the "no hike" scenario
        self.data['base_rate_est'] = (self.data['implied_rate'] // 0.25) * 0.25
        
        # If target_rate not specified, use current_effr + hike_size
        if target_rate is None:
            target_rate = current_effr + self.hike_size
        
        # Calculate probability of rate being >= target_rate
        # Prob = (Implied - Base) / 0.25
        # This is simplified - in reality, you'd need to account for multiple meetings
        self.data['hike_prob'] = (self.data['implied_rate'] - self.data['base_rate_est']) / self.hike_size
        
        # Clip to valid probability range [0, 1]
        self.data['hike_prob'] = self.data['hike_prob'].clip(0.0, 1.0)
        
        return self.data['hike_prob']
    
    def get_price_series(self) -> pd.Series:
        """Get raw price series."""
        if self.data is None:
            self.load_data()
        return self.data['Price']
    
    def get_implied_rate_series(self) -> pd.Series:
        """Get implied rate series (100 - Price)."""
        if self.data is None:
            self.load_data()
        if 'implied_rate' not in self.data.columns:
            self.data['implied_rate'] = 100 - self.data['Price']
        return self.data['implied_rate']

