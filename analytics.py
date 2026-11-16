
from database import (
    get_portfolio_account,
    list_holdings,
    list_portfolio_transactions,
)
from market_data import get_market_quotes


def get_performance_summary():
    """Calculate simulated portfolio performance from saved records."""

    account = get_portfolio_account()

    if not account:
        raise ValueError("Portfolio account could not be loaded.")

    holdings = list_holdings()
    transactions = list_portfolio_transactions()

    cash = float(account["cash"])
    starting_cash = float(account["starting_cash"])

    symbols = [holding["symbol"] for holding in holdings]

    market = get_market_quotes(symbols=symbols) if symbols else {
        "quotes": {},
        "message": "",
    }

    quotes = market.get("quotes", {})

    holdings_value = 0.0
    unrealized_pl = 0.0
    holding_details = []
    missing_prices = []

    for holding in holdings:
        symbol = holding["symbol"]
        quantity = float(holding["quantity"])
        avg_cost = float(holding["avg_cost"])

        quote = quotes.get(symbol)

        if not quote:
            missing_prices.append(symbol)
            continue

        current_price = float(quote["price"])
        market_value = quantity * current_price
        position_pl = (current_price - avg_cost) * quantity

        holdings_value += market_value
        unrealized_pl += position_pl

        holding_details.append({
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": avg_cost,
            "daily_close": current_price,
            "market_value": market_value,
            "unrealized_pl": position_pl,
            "price_date": quote["timestamp"],
        })

    # Realized P/L is recorded when simulated shares are sold.
    sell_transactions = [
        transaction
        for transaction in transactions
        if transaction["side"].upper() == "SELL"
    ]

    realized_pl = sum(
        float(transaction.get("realized_pl", 0) or 0)
        for transaction in sell_transactions
    )

    winning_sells = sum(
        1 for transaction in sell_transactions
        if float(transaction.get("realized_pl", 0) or 0) > 0
    )

    losing_sells = sum(
        1 for transaction in sell_transactions
        if float(transaction.get("realized_pl", 0) or 0) < 0
    )

    total_sells = len(sell_transactions)

    profitable_sell_rate = (
        winning_sells / total_sells * 100
        if total_sells else 0.0
    )

    total_value = cash + holdings_value
    total_pl = total_value - starting_cash

    total_return_pct = (
        total_pl / starting_cash * 100
        if starting_cash else 0.0
    )

    return {
        "starting_cash": starting_cash,
        "cash": cash,
        "holdings_value": holdings_value,
        "total_value": total_value,
        "realized_pl": realized_pl,
        "unrealized_pl": unrealized_pl,
        "total_pl": total_pl,
        "total_return_pct": total_return_pct,
        "total_sell_transactions": total_sells,
        "winning_sells": winning_sells,
        "losing_sells": losing_sells,
        "profitable_sell_rate": profitable_sell_rate,
        "holdings": holding_details,
        "missing_prices": missing_prices,
        "market_data_message": market.get("message", ""),
    }


def get_sell_performance():
    """Return individual simulated sell transactions with their P/L."""

    transactions = list_portfolio_transactions()

    sells = [
        transaction
        for transaction in transactions
        if transaction["side"].upper() == "SELL"
    ]

    return [
        {
            "id": transaction["id"],
            "symbol": transaction["symbol"],
            "quantity": float(transaction["quantity"]),
            "price": float(transaction["price"]),
            "total": float(transaction["total"]),
            "realized_pl": float(
                transaction.get("realized_pl", 0) or 0
            ),
            "created_at": transaction["created_at"],
        }
        for transaction in sells
    ]
