"""
DHIN Graph Builder

Transforms flat time-series data into Daily Graph Snapshots.
This is Phase 1 of the Dynamic Hierarchical Information Network (DHIN) project.

Input: CME Data (CSV) + Kalshi Data (Mocked/Live)
Output: NetworkX Graph Objects where nodes are assets and edges are relationships (Basis/Arb)
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from typing import Optional, Dict
from datetime import datetime

# Handle both relative import (when used as module) and absolute import (when run directly)
try:
    from .config import CME_CSV_PATH, KALSHI_DRIFT_STD, STRIKE_BASE
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.research.config import CME_CSV_PATH, KALSHI_DRIFT_STD, STRIKE_BASE


class DHINBuilder:
    """
    Builds Dynamic Hierarchical Information Networks from time-series data.
    
    Transforms:
    - CME Fed Funds Futures data → Asset nodes
    - Kalshi market data → Market nodes
    - Price relationships → Edges (basis, causal flow, etc.)
    """
    
    def __init__(self, cme_csv_path: Optional[str] = None):
        """
        Initialize the DHIN builder.
        
        Args:
            cme_csv_path: Path to CME CSV file. If None, uses config default.
        """
        self.cme_path = cme_csv_path or CME_CSV_PATH
        self.raw_data: Optional[pd.DataFrame] = None
        self.graphs: Dict[datetime, nx.MultiDiGraph] = {}  # Store G_t by Date

    def load_data(self) -> pd.DataFrame:
        """
        Ingests the CME Source of Truth (Asset Nodes).
        
        Returns:
            DataFrame with Date index and calculated implied rates
        """
        if not os.path.exists(self.cme_path):
            raise FileNotFoundError(f"Missing Data: {self.cme_path}")
            
        print(f"[INGEST] Loading Asset Data from {self.cme_path}...")
        df = pd.read_csv(self.cme_path)
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df = df.sort_values('Date').set_index('Date')
        
        # Calculate Implied Rate (The Asset Feature)
        df['implied_rate'] = 100 - df['Price']
        self.raw_data = df
        print(f"[INGEST] Loaded {len(df)} days of data")
        return df

    def _get_mock_nodes(self, cme_rate: float, date: pd.Timestamp) -> dict:
        """
        Simulates the full ecosystem:
        1. US02Y (Macro) usually leads CME.
        2. Sentiment (News) usually lags or overreacts.
        3. Kalshi is pulled between Truth (CME) and Noise (Sentiment).
        
        Args:
            cme_rate: Current CME implied rate
            date: Date for deterministic random seed
        
        Returns:
            Dictionary with all node states (macro_yield, sentiment_score, kalshi_price, etc.)
        """
        np.random.seed(int(date.timestamp()))
        
        # 1. Macro Node (US 2-Year Treasury)
        # Correlated with CME but leads it
        macro_yield = cme_rate + np.random.normal(0, 0.02)
        
        # 2. Sentiment Node (Retail News Score 0-100)
        # If Macro is high, 'Fear' (Sentiment) is usually high
        sentiment_score = 50 + (macro_yield - 3.50) * 100 + np.random.normal(0, 10)
        sentiment_score = np.clip(sentiment_score, 0, 100)

        # 3. Kalshi Node (The Target)
        # Drifts between Truth (CME) and Noise (Sentiment)
        # This is the "Pull" we want to model!
        kalshi_rate = (cme_rate * 0.7) + (macro_yield * 0.3) + np.random.normal(0, 0.05)
        kalshi_price = int(np.clip((kalshi_rate - STRIKE_BASE) / 0.25, 0, 1) * 100)
        
        return {
            "macro_yield": macro_yield,
            "sentiment_score": sentiment_score,
            "kalshi_price": kalshi_price,
            "kalshi_rate_implied": kalshi_rate
        }

    def build_snapshot(self, date: pd.Timestamp) -> Optional[nx.MultiDiGraph]:
        """
        Constructs the Heterogeneous Graph G_t for a specific timestamp.
        
        Creates a 4-node network showing the conflict between institutional (US02Y->CME) 
        and retail (NEWS->Kalshi) signals, with the basis edge (CME->Kalshi) as the arbitrage target.
        
        Args:
            date: Date to build graph for
        
        Returns:
            NetworkX MultiDiGraph representing the market state at this date
        """
        if self.raw_data is None:
            self.load_data()
            
        if date not in self.raw_data.index:
            print(f"[WARNING] No data for date {date.date()}")
            return None
            
        # Initialize Directed Graph
        G = nx.MultiDiGraph(timestamp=date)
        
        # Get CME data
        cme_row = self.raw_data.loc[date]
        cme_rate = cme_row['implied_rate']
        
        # Get all mock node states
        mock_data = self._get_mock_nodes(cme_rate, date)
        
        # --- NODES ---
        
        # 1. The Anchor (CME) - The Truth
        G.add_node("CME_ZQ", 
                   type="asset", 
                   rate=cme_rate, 
                   label="CME Futures",
                   price=cme_row['Price'])
        
        # 2. The Leader (Macro) - US 2-Year Treasury
        G.add_node("US02Y", 
                   type="macro", 
                   rate=mock_data['macro_yield'], 
                   label="2Y Treasury")
        
        # 3. The Noise (Sentiment) - Retail News/Reddit
        G.add_node("NEWS", 
                   type="sentiment", 
                   score=mock_data['sentiment_score'], 
                   label="News/Reddit")
        
        # 4. The Target (Kalshi) - The Market We Trade
        G.add_node("KALSHI", 
                   type="market", 
                   price=mock_data['kalshi_price'], 
                   label="Kalshi Fed",
                   rate_implied=mock_data['kalshi_rate_implied'])
        
        # --- EDGES (The Alpha) ---
        
        # Edge 1: Macro Drive (US02Y -> CME)
        # If spread is wide, CME is lagging Macro
        spread_macro = abs(mock_data['macro_yield'] - cme_rate)
        G.add_edge("US02Y", "CME_ZQ", 
                   type="lead_lag", 
                   weight=spread_macro, 
                   color='blue')
        
        # Edge 2: The Basis (CME -> Kalshi)
        # The Arb we want to trade
        spread_basis = abs(cme_rate - mock_data['kalshi_rate_implied'])
        G.add_edge("CME_ZQ", "KALSHI", 
                   type="basis", 
                   weight=spread_basis, 
                   color='green')
        
        # Edge 3: The Retail Trap (News -> Kalshi)
        # Does News drive Kalshi prices? (High weight = Retail Dominated)
        # We calculate 'Influence' as correlation of levels (simplified here as distance)
        influence_retail = abs(mock_data['sentiment_score'] - mock_data['kalshi_price']) / 100
        G.add_edge("NEWS", "KALSHI", 
                   type="noise_influence", 
                   weight=influence_retail, 
                   color='red')

        self.graphs[date] = G
        return G

    def visualize_snapshot(self, date: pd.Timestamp, save_path: Optional[str] = None):
        """
        Plots the graph topology showing the "Triangle of Conflict".
        
        Left Side (Institutional): US02Y -> CME (Smart Money pipeline)
        Right Side (Retail): NEWS -> KALSHI (Dumb Money pipeline)
        The Bridge: CME -> KALSHI (The Basis - arbitrage target)
        
        Args:
            date: Date to visualize
            save_path: Optional path to save the figure
        """
        G = self.graphs.get(date)
        if not G:
            print(f"[WARNING] Graph not built for date {date.date()}")
            return
            
        plt.figure(figsize=(12, 10))
        
        # Fixed Layout for consistency - shows the conflict structure
        pos = {
            "US02Y": (0, 1),
            "CME_ZQ": (0, 0),
            "NEWS": (1, 1),
            "KALSHI": (1, 0)
        }
        
        # Draw Nodes with type-based colors
        colors = {'asset': 'gold', 'macro': 'cyan', 'sentiment': 'salmon', 'market': 'lime'}
        node_c = [colors[G.nodes[n]['type']] for n in G.nodes]
        
        nx.draw_networkx_nodes(G, pos, node_color=node_c, node_size=3000, 
                              edgecolors='black', linewidths=2, alpha=0.9)
        
        # Draw node labels
        labels = {n: G.nodes[n].get('label', n) for n in G.nodes}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=11, font_weight='bold')
        
        # Draw Edges with Weights
        edges = list(G.edges(data=True))
        edge_colors = [d['color'] for u, v, d in edges]
        weights = [d['weight'] * 5 for u, v, d in edges]  # Thicker lines for bigger weights
        
        nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=weights, 
                              arrowsize=20, alpha=0.7)
        
        # Label Edges
        edge_labels = {(u, v): f"{d['type']}\n{d['weight']:.3f}" for u, v, d in edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', label='Macro Drive (US02Y → CME)'),
            Patch(facecolor='green', label='Arb Basis (CME → Kalshi)'),
            Patch(facecolor='red', label='Retail Noise (News → Kalshi)')
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Title with key metrics
        cme_rate = G.nodes['CME_ZQ']['rate']
        kalshi_price = G.nodes['KALSHI']['price']
        basis_weight = [d['weight'] for u, v, d in edges if d.get('type') == 'basis'][0]
        noise_weight = [d['weight'] for u, v, d in edges if d.get('type') == 'noise_influence'][0]
        
        plt.title(f"DHIN Market Topology: {date.date()}\n"
                f"CME Rate: {cme_rate:.2f}% | Kalshi: {kalshi_price}¢ | "
                f"Basis: {basis_weight:.4f} | Noise Influence: {noise_weight:.3f}",
                fontsize=13, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"[SAVE] Graph visualization saved to {save_path}")
        else:
            plt.show()

    def build_all_snapshots(self) -> Dict[datetime, nx.MultiDiGraph]:
        """
        Build graphs for all available dates.
        
        Returns:
            Dictionary mapping dates to graphs
        """
        if self.raw_data is None:
            self.load_data()
        
        print(f"[BUILD] Constructing graphs for {len(self.raw_data)} dates...")
        for date in self.raw_data.index:
            self.build_snapshot(date)
        
        print(f"[BUILD] Built {len(self.graphs)} graph snapshots")
        return self.graphs


# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # Point to your uploaded CSV
    CSV_FILE = "CBOT 30-DAY Federal Fund Futures Historical Data.csv" 
    
    builder = DHINBuilder(CSV_FILE)
    builder.load_data()
    
    # Visualizing the Conflict
    latest_date = builder.raw_data.index.max()
    print(f"\n[BUILD] Generating Heterogeneous Graph for {latest_date.date()}...")
    
    G = builder.build_snapshot(latest_date)
    
    # Inspect
    print("\n" + "="*70)
    print("GRAPH TOPOLOGY - The Triangle of Conflict")
    print("="*70)
    print("\nNodes:")
    for node, data in G.nodes(data=True):
        node_type = data.get('type', 'unknown')
        if node_type == 'asset':
            print(f"  {node} ({data.get('label', node)}): Rate={data.get('rate', 0):.2f}%")
        elif node_type == 'macro':
            print(f"  {node} ({data.get('label', node)}): Rate={data.get('rate', 0):.2f}%")
        elif node_type == 'sentiment':
            print(f"  {node} ({data.get('label', node)}): Score={data.get('score', 0):.1f}")
        elif node_type == 'market':
            print(f"  {node} ({data.get('label', node)}): Price={data.get('price', 0)}¢, Rate={data.get('rate_implied', 0):.2f}%")
    
    print("\nEdges (The Alpha):")
    for u, v, data in G.edges(data=True):
        edge_type = data.get('type', 'unknown')
        weight = data.get('weight', 0)
        color = data.get('color', 'gray')
        print(f"  {u} -> {v}: {edge_type} (weight={weight:.4f}, color={color})")
    
    print("\n" + "="*70)
    print("Graph Summary:")
    print(f"  Nodes: {G.number_of_nodes()} (4-node heterogeneous network)")
    print(f"  Edges: {G.number_of_edges()} (3 relationship types)")
    
    # Extract key metrics
    basis_weight = [d['weight'] for u, v, d in G.edges(data=True) if d.get('type') == 'basis'][0]
    noise_weight = [d['weight'] for u, v, d in G.edges(data=True) if d.get('type') == 'noise_influence'][0]
    lead_lag_weight = [d['weight'] for u, v, d in G.edges(data=True) if d.get('type') == 'lead_lag'][0]
    
    print(f"  Basis (CME->Kalshi): {basis_weight:.4f}")
    print(f"  Noise Influence (News->Kalshi): {noise_weight:.4f}")
    print(f"  Lead-Lag (US02Y->CME): {lead_lag_weight:.4f}")
    
    # Research Thesis
    print("\n" + "="*70)
    print("RESEARCH THESIS:")
    if noise_weight < basis_weight:
        print("  ✓ Market is EFFICIENT: Basis edge stronger than noise")
        print("    -> Kalshi follows CME truth, not retail sentiment")
    else:
        print("  ⚠ Market is INEFFICIENT: Noise edge stronger than basis")
        print("    -> Kalshi is driven by retail sentiment, ignoring CME truth")
        print("    -> THIS IS WHEN WE EXECUTE (arbitrage opportunity)")
    print("="*70)
    
    # Visualize
    print("\n[VISUALIZE] Generating graph visualization...")
    builder.visualize_snapshot(latest_date)

