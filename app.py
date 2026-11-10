import os

import pandas as pd
import streamlit as st

from market_data import get_market_quotes, DEFAULT_SYMBOLS
from database import (
    init_db,
    list_trades,
    add_trade,
    get_portfolio_account,
    list_holdings,
    list_portfolio_transactions,
)
from simulator import check_rules, close_trade, place_paper_order


st.set_page_config(
    page_title="MarketDesk",
    page_icon="📊",
    layout="wide",
)

init_db()

# Load the API key from Streamlit Secrets.
try:
    if "ALPHA_VANTAGE_API_KEY" in st.secrets:
        os.environ["ALPHA_VANTAGE_API_KEY"] = (
            st.secrets["ALPHA_VANTAGE_API_KEY"]
        )
except Exception:
    pass


def load_market_data(symbols=None):
    return get_market_quotes(symbols=symbols)


def money(value):
    return f"${value:,.2f}"


st.title("📊 MarketDesk")
st.caption("Market data and simulated trading control center")

st.warning(
    "SIMULATION ONLY — No brokerage account is connected. "
    "Orders use available daily closing prices, not real-time quotes."
)

pages = [
    "Home",
    "Mainframe",
    "Data Center",
    "Strategy Lab",
    "Trade Log",
    "Portfolio",
    "Order Ticket",
    "Transaction History",
]

page = st.sidebar.radio("Navigation", pages)


# ---------------- HOME ----------------

if page == "Home":
    market = load_market_data()
    quotes = market.get("quotes", {})

    st.subheader("Market Overview")

    if market["status"] == "ok":
        st.success("Market data connected")
    elif market["status"] == "partial":
        st.warning("Some market data could not be retrieved")
    else:
        st.error("Market data unavailable")

    if market.get("message"):
        st.caption(market["message"])

    if quotes:
        cols = st.columns(len(quotes))

        for col, (symbol, info) in zip(cols, quotes.items()):
            col.metric(symbol, money(info["price"]))
            col.caption(info["timestamp"])

        st.subheader("Watchlist")

        st.dataframe(
            pd.DataFrame([
                {
                    "Symbol": symbol,
                    "Daily Close": info["price"],
                    "Source": info["source"],
                    "Date": info["timestamp"],
                }
                for symbol, info in quotes.items()
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Configure your market-data API key to load prices.")

    st.info(
        "Use Portfolio to monitor simulated holdings and "
        "Order Ticket to place manually approved paper orders."
    )


# ---------------- MAINFRAME ----------------

elif page == "Mainframe":
    st.subheader("Mainframe")

    col1, col2, col3 = st.columns(3)
    col1.metric("Execution Mode", "SIMULATION")
    col2.metric("Brokerage Connection", "Not connected")
    col3.metric("Engine Status", "Manual")

    st.write("Check your saved simulated price rules.")

    st.caption(
        "This checks the latest available daily closing prices. "
        "It does not execute orders or perform historical backtesting."
    )

    if st.button("Check Price Rules"):
        events = check_rules()

        if events:
            for event in events:
                if event.startswith("Market data unavailable"):
                    st.error(event)
                else:
                    st.info(event)
        else:
            st.success("No saved price rules were triggered.")


# ---------------- DATA CENTER ----------------

elif page == "Data Center":
    st.subheader("Data Center")

    if st.button("Refresh Market Data"):
        market = load_market_data()
    else:
        market = load_market_data()

    quotes = market.get("quotes", {})

    if quotes:
        st.dataframe(
            pd.DataFrame([
                {"Symbol": symbol, **info}
                for symbol, info in quotes.items()
            ]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.error(market.get("message", "No prices available."))

    st.caption(
        "Source: Alpha Vantage daily closing prices. "
        "These are not live streaming quotes."
    )


# ---------------- STRATEGY LAB ----------------

elif page == "Strategy Lab":
    st.subheader("Strategy Lab")
    st.write("Create a simulated buy and sell price rule.")

    symbol = st.selectbox("Symbol", DEFAULT_SYMBOLS)

    buy_at = st.number_input(
        "Simulated buy threshold ($)",
        min_value=0.01,
        value=100.00,
        step=1.00,
    )

    sell_at = st.number_input(
        "Simulated sell threshold ($)",
        min_value=0.01,
        value=120.00,
        step=1.00,
    )

    if buy_at >= sell_at:
        st.warning("The sell threshold must be higher than the buy threshold.")
    elif st.button("Save Simulated Rule"):
        add_trade(symbol, buy_at, sell_at, "Require approval")
        st.success("Simulated rule saved.")


# ---------------- TRADE LOG ----------------

elif page == "Trade Log":
    st.subheader("Trade Log")

    trades = list_trades()

    if trades:
        st.dataframe(
            pd.DataFrame(trades),
            use_container_width=True,
            hide_index=True,
        )

        open_ids = [
            trade["id"]
            for trade in trades
            if trade["status"] == "OPEN"
        ]

        if open_ids:
            chosen = st.selectbox("Select rule to close", open_ids)

            if st.button("Close Selected Rule"):
                close_trade(chosen)
                st.success("Rule closed.")
                st.rerun()
    else:
        st.info("No simulated rules have been created yet.")


# ---------------- PORTFOLIO ----------------

elif page == "Portfolio":
    st.subheader("Paper Portfolio")

    account = get_portfolio_account()
    holdings = list_holdings()

    if not account:
        st.error("Portfolio account could not be loaded.")
    else:
        symbols = sorted(
            set(DEFAULT_SYMBOLS)
            | {holding["symbol"] for holding in holdings}
        )

        market = load_market_data(symbols=symbols)
        quotes = market.get("quotes", {})

        cash = float(account["cash"])
        starting_cash = float(account["starting_cash"])

        holdings_value = 0.0
        unrealized_pl = 0.0
        holding_rows = []

        for holding in holdings:
            symbol = holding["symbol"]
            quantity = float(holding["quantity"])
            avg_cost = float(holding["avg_cost"])
            quote = quotes.get(symbol)

            if quote:
                current_price = float(quote["price"])
                market_value = quantity * current_price
                position_pl = (current_price - avg_cost) * quantity

                holdings_value += market_value
                unrealized_pl += position_pl

                holding_rows.append({
                    "Symbol": symbol,
                    "Quantity": quantity,
                    "Average Cost": avg_cost,
                    "Daily Close": current_price,
                    "Market Value": market_value,
                    "Unrealized P/L": position_pl,
                    "Price Date": quote["timestamp"],
                })
            else:
                holding_rows.append({
                    "Symbol": symbol,
                    "Quantity": quantity,
                    "Average Cost": avg_cost,
                    "Daily Close": None,
                    "Market Value": None,
                    "Unrealized P/L": None,
                    "Price Date": "Unavailable",
                })

        total_value = cash + holdings_value

        cols = st.columns(4)
        cols[0].metric("Starting Balance", money(starting_cash))
        cols[1].metric("Available Cash", money(cash))
        cols[2].metric("Holdings Value", money(holdings_value))
        cols[3].metric("Estimated Total", money(total_value))

        st.metric(
            "Unrealized P/L",
            money(unrealized_pl),
            delta=money(unrealized_pl),
        )

        st.caption(
            "Portfolio estimates use the latest available daily closes. "
            "Positions without a price are excluded from holdings value."
        )

        st.divider()
        st.subheader("Current Holdings")

        if holding_rows:
            st.dataframe(
                pd.DataFrame(holding_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No holdings yet. Visit Order Ticket to simulate a buy.")


# ---------------- ORDER TICKET ----------------

elif page == "Order Ticket":
    st.subheader("Paper Order Ticket")

    st.caption(
        "Orders are simulated manually using the latest available daily "
        "closing price. Nothing is sent to a brokerage."
    )

    account = get_portfolio_account()
    holdings = list_holdings()

    if not account:
        st.error("Portfolio account could not be loaded.")
    else:
        side = st.radio(
            "Order Side",
            ["BUY", "SELL"],
            horizontal=True,
        )

        symbols = sorted(
            set(DEFAULT_SYMBOLS)
            | {holding["symbol"] for holding in holdings}
        )

        symbol = st.selectbox("Symbol", symbols)

        market = load_market_data(symbols=[symbol])
        quote = market.get("quotes", {}).get(symbol)

        if quote:
            price = float(quote["price"])

            st.metric("Latest Available Daily Close", money(price))
            st.caption(
                f"Price date: {quote['timestamp']} · "
                f"Source: {quote['source']}"
            )

            quantity = st.number_input(
                "Quantity",
                min_value=0.01,
                value=0.1,
                step=0.1,
                format="%.4f",
            )

            estimated_total = round(quantity * price, 2)

            st.metric("Estimated Order Value", money(estimated_total))

            if side == "BUY":
                st.caption(
                    f"Available simulated cash: "
                    f"{money(account['cash'])}"
                )
            else:
                available_shares = next(
                    (
                        float(h["quantity"])
                        for h in holdings
                        if h["symbol"] == symbol
                    ),
                    0.0,
                )
                st.caption(
                    f"Available simulated shares: {available_shares:g}"
                )

            with st.form("paper_order_form"):
                confirmed = st.checkbox(
                    f"I confirm this simulated {side} order "
                    f"for {quantity:g} shares of {symbol}."
                )

                submitted = st.form_submit_button(
                    "Submit Paper Order",
                    disabled=not confirmed,
                )

            if submitted:
                try:
                    result = place_paper_order(
                        side,
                        symbol,
                        quantity,
                    )

                    st.success(
                        f"Simulated {result['side']} completed: "
                        f"{result['quantity']:g} {result['symbol']} "
                        f"at {money(result['price'])}."
                    )

                    st.write({
                        "Order Value": money(result["total"]),
                        "Remaining Cash": money(result["cash_remaining"]),
                        "Price Date": result["price_date"],
                        "Price Source": result["price_source"],
                    })

                    st.rerun()

                except ValueError as error:
                    st.error(str(error))
        else:
            st.error(
                market.get(
                    "message",
                    f"No daily closing price available for {symbol}.",
                )
            )


# ---------------- TRANSACTION HISTORY ----------------

elif page == "Transaction History":
    st.subheader("Paper Transaction History")

    transactions = list_portfolio_transactions()

    if transactions:
        st.dataframe(
            pd.DataFrame(transactions),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No simulated orders have been placed yet.")
