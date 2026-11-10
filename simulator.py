from database import list_trades, mark_closed
from market_data import get_market_quotes


def check_rules():
    market_data = get_market_quotes()
    quotes = market_data.get("quotes", {})
    events = []

    if not quotes:
        return [
            f"Market data unavailable: {market_data.get('message', 'Unknown error')}"
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
                f"reached simulated buy threshold ${trade['buy_at']:.2f}."
            )

        elif price >= trade["sell_at"]:
            events.append(
                f"{trade['symbol']}: daily close ${price:.2f} "
                f"reached simulated sell threshold ${trade['sell_at']:.2f}."
            )

    return events


def close_trade(trade_id):
    mark_closed(trade_id)
