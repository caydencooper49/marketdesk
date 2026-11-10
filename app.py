import os

import pandas as pd
import streamlit as st

from market_data import get_market_quotes, DEFAULT_SYMBOLS
from database import init_db, list_trades, add_trade
from simulator import check_rules, close_trade


st.set_page_config(
    page_title="MarketDesk",
    page_icon="📊",
    layout="wide"
)

init_db()

# Read the API key from Streamlit secrets if configured.
try:
    if "ALPHA_VANTAGE_API_KEY" in st.secrets:
        os.environ["ALPHA_VANTAGE_API_KEY"] = (
            st.secrets["ALPHA_VANTAGE_API_KEY"]
        )
except Exception:
    pass


def load_market_data():
    return get_market_quotes()


st.title("📊 MarketDesk")
st.caption("Market data and paper-trading control center")

st.warning(
    "SIMULATION ONLY — MarketDesk does not place real orders. "
    "Market data uses daily closing prices, not real-time quotes."
)

pages = [
    "Home",
    "Mainframe",
    "Data Center",
    "Strategy Lab",
    "Trade Log"
]

page = st.sidebar.radio("Navigation", pages)


if page in ["Home", "Data Center"]:
    market = load_market_data()
    quotes = market.get("quotes", {})

    if market["status"] == "ok":
        st.success("Market data connected")
    elif market["status"] == "partial":
        st.warning("Some market data could not be retrieved")
    else:
        st.error("Market data is not available")

    if market.get("message"):
        st.caption(market["message"])

    if page == "Home":
        st.subheader("Market Overview")

        if quotes:
            cols = st.columns(len(quotes))

            for col, (symbol, info) in zip(cols, quotes.items()):
                col.metric(symbol, f"${info['price']:.2f}")
                col.caption(info["timestamp"])

            st.subheader("Watchlist")

            st.dataframe(
                pd.DataFrame([
                    {
                        "Symbol": symbol,
                        "Daily Close": info["price"],
                        "Source": info["source"],
                        "Date": info["timestamp"]
                    }
                    for symbol, info in quotes.items()
                ]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Configure your market-data API key to load prices.")

        st.info(
            "Use Strategy Lab to create simulated price rules. "
            "Rules are checked manually, not continuously."
        )

    else:
        st.subheader("Data Center")

        if quotes:
            st.dataframe(
                pd.DataFrame([
                    {"Symbol": symbol, **info}
                    for symbol, info in quotes.items()
                ]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No market prices are currently available.")

        st.caption(
            "Source: Alpha Vantage daily closing prices. "
            "These are not live streaming quotes."
        )


elif page == "Mainframe":
    st.subheader("Mainframe")

    st.metric("Execution Mode", "SIMULATION ONLY")
    st.metric("Brokerage Connection", "Not connected")
    st.metric("Engine Status", "Manual checks")

    st.write("Check your saved simulated price rules.")

    if st.button("Check Price Rules"):
        events = check_rules()

        if events:
            for event in events:
                if event.startswith("Market data unavailable"):
                    st.error(event)
                else:
                    st.info(event)
        else:
            st.success("No simulated rules were triggered.")


elif page == "Strategy Lab":
    st.subheader("Strategy Lab")
    st.write("Create a simulated buy and sell price rule.")

    symbol = st.selectbox("Symbol", DEFAULT_SYMBOLS)

    buy_at = st.number_input(
        "Simulated buy threshold ($)",
        min_value=0.01,
        value=200.00,
        step=1.00
    )

    sell_at = st.number_input(
        "Simulated sell threshold ($)",
        min_value=0.01,
        value=220.00,
        step=1.00
    )

    mode = st.radio(
        "Order handling",
        ["Require approval", "Auto-simulate"],
        horizontal=True
    )

    if buy_at >= sell_at:
        st.warning("The sell threshold must be higher than the buy threshold.")
    elif st.button("Save Simulated Rule"):
        add_trade(symbol, buy_at, sell_at, mode)
        st.success("Simulated rule saved.")


elif page == "Trade Log":
    st.subheader("Trade Log")

    trades = list_trades()

    if trades:
        st.dataframe(
            pd.DataFrame(trades),
            use_container_width=True,
            hide_index=True
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
