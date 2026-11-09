import streamlit as st
import pandas as pd
from market_data import get_demo_quotes
from database import init_db, list_trades, add_trade
from simulator import check_rules, close_trade

st.set_page_config(page_title="MarketDesk", page_icon="📊", layout="wide")
init_db()

st.title("📊 MarketDesk")
st.caption("A beginner-friendly paper-trading control center — demo data only.")
st.warning("Paper trading only. Prices below are illustrative demo values, not live market quotes. No brokerage connection or real-money orders.")

pages = ["Home", "Mainframe", "Data Center", "Strategy Lab", "Trade Log"]
page = st.sidebar.radio("Navigation", pages)

if page == "Home":
    st.subheader("Market overview")
    quotes = get_demo_quotes()
    cols = st.columns(len(quotes))
    for col, (symbol, info) in zip(cols, quotes.items()):
        col.metric(symbol, f"${info['price']:.2f}")
        col.caption(f"{info['source']} · {info['timestamp']}")
    st.subheader("Watchlist")
    st.dataframe(pd.DataFrame([
        {"Symbol": s, "Demo price": q["price"], "Source": q["source"], "Updated": q["timestamp"]}
        for s, q in quotes.items()
    ]), use_container_width=True, hide_index=True)
    st.info("Use the Strategy Lab to set simulated buy and sell levels. The app checks rules when you press the button; it does not run continuously in the background.")

elif page == "Mainframe":
    st.subheader("Mainframe")
    st.write("This is the control area for the paper-trading engine.")
    st.metric("Execution mode", "SIMULATION ONLY")
    st.metric("Brokerage connection", "Not connected")
    st.write("Current engine status: **Manual checks only**")
    if st.button("Check price rules now"):
        events = check_rules()
        if events:
            for event in events:
                st.success(event)
        else:
            st.info("No strategy rules were triggered.")

elif page == "Data Center":
    st.subheader("Data Center")
    st.write("Current prototype data source: built-in illustrative demo prices.")
    st.dataframe(pd.DataFrame([
        {"Symbol": s, **v} for s, v in get_demo_quotes().items()
    ]), use_container_width=True, hide_index=True)
    st.caption("No live feed or news provider is connected yet. A future version can add a properly licensed market-data source.")

elif page == "Strategy Lab":
    st.subheader("Strategy Lab")
    st.write("Create a simple simulated buy/sell rule.")
    symbols = list(get_demo_quotes().keys())
    symbol = st.selectbox("Symbol", symbols)
    buy_at = st.number_input("Simulate buying at or below ($)", min_value=0.01, value=200.00, step=1.0)
    sell_at = st.number_input("Simulate selling at or above ($)", min_value=0.01, value=220.00, step=1.0)
    mode = st.radio("Order handling", ["Require approval", "Auto-simulate"], horizontal=True)
    if st.button("Save simulated rule"):
        add_trade(symbol, buy_at, sell_at, mode)
        st.success("Rule saved to the local paper-trading database.")

elif page == "Trade Log":
    st.subheader("Trade Log")
    trades = list_trades()
    if trades:
        st.dataframe(pd.DataFrame(trades), use_container_width=True, hide_index=True)
        open_ids = [t["id"] for t in trades if t["status"] == "OPEN"]
        if open_ids:
            chosen = st.selectbox("Close simulated rule", open_ids)
            if st.button("Close selected rule"):
                close_trade(chosen)
                st.success("Rule closed.")
                st.rerun()
    else:
        st.info("No simulated rules yet.")
