"""Alpha Vantage daily market data for MarketDesk.

These are daily closing prices, not real-time quotes.
API keys must be stored securely, never directly in this file.
"""

from datetime import datetime, timezone
import os
import time

import requests

BASE_URL = "https://www.alphavantage.co/query"
DEFAULT_SYMBOLS = ("AAPL", "NVDA", "MSFT", "SPY", "QQQ")
CACHE_SECONDS = 6 * 60 * 60
_cache = {}


def get_market_quotes(symbols=None, api_key=None, force_refresh=False):
    """Return the latest available daily closing prices."""
    key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
    requested = tuple(symbols or DEFAULT_SYMBOLS)

    if not key:
        return {
            "status": "not_configured",
            "message": "API key has not been configured.",
            "quotes": {},
        }

    quotes = {}
    errors = []
    now = time.time()

    for symbol in requested:
        symbol = symbol.strip().upper()
        cached = _cache.get(symbol)

        if cached and not force_refresh and now - cached["cached_at"] < CACHE_SECONDS:
            quotes[symbol] = cached["quote"]
            continue

        try:
            response = requests.get(
                BASE_URL,
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "outputsize": "compact",
                    "apikey": key,
                },
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()

            if "Note" in payload or "Information" in payload:
                raise ValueError(
                    str(payload.get("Note") or payload.get("Information"))
                )

            if "Error Message" in payload:
                raise ValueError(payload["Error Message"])

            series = payload.get("Time Series (Daily)")
            if not series:
                raise ValueError("No daily price data was returned.")

            latest_date = max(series.keys())
            close = float(series[latest_date]["4. close"])

            quote = {
                "price": close,
                "source": "Alpha Vantage · daily close",
                "timestamp": latest_date,
                "price_type": "Daily closing price · not real-time",
            }

            _cache[symbol] = {
                "quote": quote,
                "cached_at": now,
            }
            quotes[symbol] = quote

        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{symbol}: {exc}")

    status = (
        "ok" if quotes and not errors
        else "partial" if quotes
        else "error"
    )

    return {
        "status": status,
        "message": (
            "Latest available daily closing prices."
            if not errors
            else "; ".join(errors)
        ),
        "quotes": quotes,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
