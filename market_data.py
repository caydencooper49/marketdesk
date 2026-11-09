from datetime import datetime

# Illustrative placeholders only. These are NOT live or current market prices.
DEMO_PRICES = {
    "AAPL": 210.00,
    "NVDA": 145.00,
    "MSFT": 425.00,
    "SPY": 590.00,
    "QQQ": 510.00,
}

def get_demo_quotes():
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        symbol: {"price": price, "source": "DEMO DATA — NOT LIVE", "timestamp": stamp}
        for symbol, price in DEMO_PRICES.items()
    }
