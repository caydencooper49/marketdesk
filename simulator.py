import math

from database import (
    list_trades,
    mark_closed,
    execute_order,
)
from market_data import get_market_quotes


def place_paper_order(side, symbol, quantity):
    """Place a simulated order using the latest available daily close."""

    symbol = str(symbol).strip().upper()
    quantity = float(quantity)

    if not symbol:
        raise ValueError("Enter a stock symbol.")

    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError("Quantity must be a positive number.")

    market = get_market_quotes(symbols=[symbol])
    quote = market.get("quotes", {}).get(symbol)

    if not quote:
        raise ValueError(
            f"No daily closing price is available for {symbol}. "
            f"{market.get('message', '')}"
        )

    result = execute_order(
        side=side,
        symbol=symbol,
        quantity=quantity,
        price=float(quote["price"]),
    )

    result["price_date"] = quote["timestamp"]
    result["price_source"] = quote["source"]

    return result


def check_rules():
    """Check saved price rules. This does not place orders."""

    market = get_market_quotes()
    quotes = market.get("quotes", {})
    events = []

    if not quotes:
        return [
            f"Market data unavailable: "
            f"{market.get('message', 'Unknown error')}"
        ]

    for trade in list_trades():
        if trade["status"] != "OPEN":
            continue

        quote = quotes.get(trade["symbol"])

        if not quote:
            continue

        price = quote["price"]

        if price <= trade["buy_at"]:
            events.append(
                f"{trade['symbol']}: daily close ${price:.2f} "
                f"reached buy threshold ${trade['buy_at']:.2f}."
            )
        elif price >= trade["sell_at"]:
            events.append(
                f"{trade['symbol']}: daily close ${price:.2f} "
                f"reached sell threshold ${trade['sell_at']:.2f}."
            )

    return events


def close_trade(trade_id):
    mark_closed(trade_id)
