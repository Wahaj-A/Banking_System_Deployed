```python
"""Live cryptocurrency service for the five supported assets.

Uses CoinGecko's public market endpoint instead of Binance. This avoids
Binance region/IP restrictions that can return HTTP 451 from Vercel.

Optional Vercel environment variable:
    COINGECKO_API_KEY

If a CoinGecko Demo API key is configured, it is sent as the
``x-cg-demo-api-key`` header. No changes are required elsewhere in the app.
"""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
import os

from Backend.logger import logger


SUPPORTED_CRYPTO = {
    "Bitcoin": {"id": "bitcoin", "ticker": "BTC", "name": "Bitcoin"},
    "Ethereum": {"id": "ethereum", "ticker": "ETH", "name": "Ethereum"},
    "BNB": {"id": "binancecoin", "ticker": "BNB", "name": "BNB"},
    "Solana": {"id": "solana", "ticker": "SOL", "name": "Solana"},
    "XRP": {"id": "ripple", "ticker": "XRP", "name": "XRP"},
}


def _normalize_crypto(asset: str) -> str:
    if not asset:
        raise ValueError("Cryptocurrency is required.")

    value = asset.strip().lower()

    aliases = {
        "btc": "Bitcoin",
        "bitcoin": "Bitcoin",
        "eth": "Ethereum",
        "ethereum": "Ethereum",
        "bnb": "BNB",
        "binance coin": "BNB",
        "sol": "Solana",
        "solana": "Solana",
        "xrp": "XRP",
        "ripple": "XRP",
    }

    if value in aliases:
        return aliases[value]

    raise ValueError(
        "Unsupported cryptocurrency. Crypto data is available only for "
        "Bitcoin, Ethereum, BNB, Solana, and XRP."
    )


def _request_markets() -> list[dict]:
    """Fetch all supported assets in one CoinGecko request."""

    ids = ",".join(
        config["id"] for config in SUPPORTED_CRYPTO.values()
    )

    params = urlencode(
        {
            "vs_currency": "usd",
            "ids": ids,
            "price_change_percentage": "24h",
        }
    )

    url = (
        "https://api.coingecko.com/api/v3/coins/markets?"
        f"{params}"
    )

    headers = {
        "Accept": "application/json",
        "User-Agent": "Apex-Capital-Bank-Crypto/1.0",
    }

    api_key = os.getenv("COINGECKO_API_KEY")

    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        if not isinstance(payload, list):
            raise RuntimeError(
                "CoinGecko returned an unexpected response."
            )

        logger.info(
            "CRYPTO provider response received successfully from CoinGecko"
        )

        return payload

    except HTTPError as exc:

        if exc.code in (401, 403):
            raise RuntimeError(
                "CoinGecko rejected the request. Add a valid "
                "COINGECKO_API_KEY to Vercel Environment Variables."
            ) from exc

        if exc.code == 429:
            raise RuntimeError(
                "CoinGecko rate limit reached. Please try again shortly."
            ) from exc

        raise RuntimeError(
            f"CoinGecko request failed with HTTP {exc.code}."
        ) from exc

    except Exception as exc:
        logger.exception("CRYPTO provider request failed")

        raise RuntimeError(
            f"Crypto provider request failed: {exc}"
        ) from exc


def _build_market_map() -> dict[str, dict]:
    return {
        item.get("id"): item
        for item in _request_markets()
    }


def _parse_timestamp(value) -> int:
    """Convert CoinGecko timestamp to Unix milliseconds.

    CoinGecko returns last_updated in ISO 8601 format, for example:
    2026-08-19T07:44:30.000Z

    The frontend expects a numeric Unix timestamp in milliseconds.
    """

    if not value:
        return 0

    # Already numeric
    if isinstance(value, (int, float)):
        return int(value)

    try:
        timestamp = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        return int(timestamp.timestamp() * 1000)

    except (ValueError, TypeError, OverflowError):
        logger.warning(
            "Unable to parse crypto timestamp: %s",
            value,
        )

        return 0


def _fetch_asset(
    asset: str,
    market_map: dict[str, dict] | None = None,
) -> dict:
    asset = _normalize_crypto(asset)

    config = SUPPORTED_CRYPTO[asset]

    data = (
        market_map or _build_market_map()
    ).get(config["id"])

    if not data:
        raise RuntimeError(
            f"CoinGecko returned no market data for {asset}."
        )

    return {
        "name": config["name"],
        "symbol": config["ticker"],
        "pair": f"{config['ticker']}USD",

        "price_usd": float(
            data.get("current_price") or 0
        ),

        "price_change_24h_percent": float(
            data.get("price_change_percentage_24h") or 0
        ),

        "high_24h_usd": float(
            data.get("high_24h") or 0
        ),

        "low_24h_usd": float(
            data.get("low_24h") or 0
        ),

        "volume_24h": float(
            data.get("total_volume") or 0
        ),

        "quote_volume_24h_usd": float(
            data.get("total_volume") or 0
        ),

        "updated_at": _parse_timestamp(
            data.get("last_updated")
        ),

        "source": "CoinGecko",
    }


def get_crypto(asset: str) -> dict:
    """Get live 24-hour market data for one supported cryptocurrency."""
    return _fetch_asset(asset)


def get_all_crypto() -> list[dict]:
    """Get live market data for all five supported cryptocurrencies."""

    market_map = _build_market_map()

    results = [
        _fetch_asset(asset, market_map)
        for asset in SUPPORTED_CRYPTO
    ]

    order = list(SUPPORTED_CRYPTO)

    return sorted(
        results,
        key=lambda item: order.index(item["name"]),
    )
