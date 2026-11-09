# MarketDesk — Python prototype

A small Streamlit dashboard for learning about market data and paper-trading workflows.

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`
4. Run `streamlit run app.py`

## Deploy
Push these files to a GitHub repository, then create an app at https://share.streamlit.io/.
Choose this repository, branch `main`, and main file `app.py`.

## Important limitations
- The quote values are illustrative placeholders, not live prices.
- This prototype checks rules only when you manually press the button.
- It does not place real trades or connect to a brokerage.
- The SQLite database is local to the running app and may not persist reliably on hosted free instances.
- Do not add brokerage credentials, passwords, or API keys to this repository.
