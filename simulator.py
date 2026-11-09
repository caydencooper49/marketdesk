from database import list_trades, mark_closed
from market_data import get_demo_quotes

def check_rules():
    quotes = get_demo_quotes()
    events = []
    for trade in list_trades():
        if trade["status"] != "OPEN":
            continue
        price = quotes.get(trade["symbol"], {}).get("price")
        if price is None:
            continue
        if price <= trade["buy_at"]:
            events.append(
                f"{trade['symbol']}: demo price ${price:.2f} reached buy threshold "
                f"${trade['buy_at']:.2f}. This is a signal only; no simulated fill is recorded."
            )
        elif price >= trade["sell_at"]:
            events.append(
                f"{trade['symbol']}: demo price ${price:.2f} reached sell threshold "
                f"${trade['sell_at']:.2f}. This is a signal only; no simulated fill is recorded."
            )
    return events

def close_trade(trade_id):
    mark_closed(trade_id)
