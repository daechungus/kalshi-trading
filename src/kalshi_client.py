import os
import time
import base64
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, ec
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv


@dataclass
class Trade:
    """Represents a historical trade on Kalshi."""
    trade_id: str
    ticker: str
    yes_price: int  # in cents
    count: int
    taker_side: str
    created_time: datetime


@dataclass
class Market:
    """Represents a Kalshi market."""
    ticker: str
    title: str
    status: str
    yes_ask: Optional[int]
    yes_bid: Optional[int]
    last_price: Optional[int]
    volume: int


class KalshiClient:
    """
    Client for interacting with the Kalshi API.

    This client handles authentication and provides methods to:
    - Get market information
    - Fetch historical trades
    - Place orders
    - Check positions and balance
    """

    DEMO_BASE_URL = "https://demo-api.kalshi.co"
    PROD_BASE_URL = "https://api.elections.kalshi.com"

    def __init__(
        self,
        private_key_path: str = "kalshi_api_private_key.txt",
        demo: bool = True
    ):
        """
        Initialize the Kalshi client.

        Args:
            private_key_path: Path to the PEM private key file.
            demo: If True, use demo API. Otherwise use production.
        """
        load_dotenv()

        if demo:
            private_key_path = "kalshi_demo_api_private_key.txt"
            api_key_env_var = "KALSHI_DEMO_API_KEY_ID"
            self.base_url = self.DEMO_BASE_URL
        else:
            private_key_path = "kalshi_api_private_key.txt"
            api_key_env_var = "KALSHI_API_KEY_ID"
            self.base_url = self.PROD_BASE_URL

        self.api_key_id = os.getenv(api_key_env_var)
        if not self.api_key_id:
            raise ValueError(f"{api_key_env_var} not found in environment")

        try:
            self.private_key = self._load_private_key(private_key_path)
        except FileNotFoundError:
            raise ValueError(f"Private key file not found: {private_key_path}")
        except Exception as e:
            raise ValueError(f"Error loading private key: {e}")

    def _load_private_key(self, file_path: str):
        """Load PEM private key from file."""
        with open(file_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key

    def _sign_message(self, message: str) -> str:
        """Sign a message using the private key with PSS padding."""
        message_bytes = message.encode("utf-8")

        # Handle both RSA and EC keys
        if hasattr(self.private_key, 'sign'):
            try:
                # Try RSA-PSS first
                signature = self.private_key.sign(
                    message_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            except (TypeError, AttributeError):
                # Fall back to EC signing
                signature = self.private_key.sign(
                    message_bytes,
                    ec.ECDSA(hashes.SHA256())
                )

        return base64.b64encode(signature).decode("utf-8")

    def _get_headers(self, method: str, path: str) -> dict:
        """Generate authenticated headers for a request."""
        timestamp_ms = int(time.time() * 1000)
        timestamp_str = str(timestamp_ms)

        # Strip query params for signing
        path_without_query = path.split("?")[0]
        message = timestamp_str + method + path_without_query
        signature = self._sign_message(message)

        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, json: dict = None) -> dict:
        """Make an authenticated request to the Kalshi API."""
        url = self.base_url + path
        headers = self._get_headers(method, path)

        response = requests.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()

    # ===== Public Endpoints (no auth required) =====

    def get_market(self, ticker: str) -> Market:
        """Get details for a single market."""
        path = f"/trade-api/v2/markets/{ticker}"
        data = self._request("GET", path)
        m = data["market"]
        return Market(
            ticker=m["ticker"],
            title=m.get("title", ""),
            status=m.get("status", ""),
            yes_ask=m.get("yes_ask"),
            yes_bid=m.get("yes_bid"),
            last_price=m.get("last_price"),
            volume=m.get("volume", 0)
        )

    def get_trades(
        self,
        ticker: str,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
        limit: int = 1000
    ) -> list[Trade]:
        """
        Get historical trades for a market.

        Args:
            ticker: Market ticker
            min_ts: Minimum timestamp (Unix seconds)
            max_ts: Maximum timestamp (Unix seconds)
            limit: Max trades to return (default 1000)

        Returns:
            List of Trade objects, ordered by time
        """
        path = f"/trade-api/v2/markets/trades?ticker={ticker}&limit={limit}"
        if min_ts:
            path += f"&min_ts={min_ts}"
        if max_ts:
            path += f"&max_ts={max_ts}"

        trades = []
        cursor = None

        while True:
            request_path = path + (f"&cursor={cursor}" if cursor else "")
            data = self._request("GET", request_path)

            for t in data.get("trades", []):
                trades.append(Trade(
                    trade_id=t["trade_id"],
                    ticker=t["ticker"],
                    yes_price=t["yes_price"],
                    count=t["count"],
                    taker_side=t["taker_side"],
                    created_time=datetime.fromisoformat(
                        t["created_time"].replace("Z", "+00:00")
                    )
                ))

            cursor = data.get("cursor")
            if not cursor or len(trades) >= limit:
                break

        return sorted(trades, key=lambda x: x.created_time)

    def get_candlesticks(
        self,
        series_ticker: str,
        market_ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: int = 1
    ) -> list[dict]:
        """
        Get candlestick data for a market.

        Args:
            series_ticker: The series ticker containing the market
            market_ticker: The specific market ticker
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Candle period in minutes (1, 60, or 1440)

        Returns:
            List of candlestick dictionaries
        """
        path = (
            f"/trade-api/v2/series/{series_ticker}/markets/{market_ticker}"
            f"/candlesticks?start_ts={start_ts}&end_ts={end_ts}"
            f"&period_interval={period_interval}"
        )
        data = self._request("GET", path)
        return data.get("candlesticks", [])

    # ===== Authenticated Endpoints =====

    def get_balance(self) -> dict:
        """Get account balance."""
        path = "/trade-api/v2/portfolio/balance"
        return self._request("GET", path)

    def get_positions(self, ticker: Optional[str] = None) -> list[dict]:
        """Get current positions."""
        path = "/trade-api/v2/portfolio/positions"
        if ticker:
            path += f"?ticker={ticker}"
        data = self._request("GET", path)
        return data.get("market_positions", [])

    def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        order_type: str = "market",
        yes_price: Optional[int] = None
    ) -> dict:
        """
        Create an order on Kalshi.

        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            order_type: 'market' or 'limit'
            yes_price: Price in cents (required for limit orders)

        Returns:
            Order response from API
        """
        path = "/trade-api/v2/portfolio/orders"
        payload = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": order_type
        }

        if order_type == "limit" and yes_price is not None:
            payload["yes_price"] = yes_price

        return self._request("POST", path, json=payload)

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an existing order."""
        path = f"/trade-api/v2/portfolio/orders/{order_id}"
        return self._request("DELETE", path)

    def get_orders(self, ticker: Optional[str] = None, status: str = "resting") -> list[dict]:
        """Get orders with optional filters."""
        path = f"/trade-api/v2/portfolio/orders?status={status}"
        if ticker:
            path += f"&ticker={ticker}"
        data = self._request("GET", path)
        return data.get("orders", [])
