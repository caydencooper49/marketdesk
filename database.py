import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "marketdesk.db"

STARTING_BALANCE = 100.00


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as con:

        # Existing strategy rules — preserved
        con.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                buy_at REAL NOT NULL,
                sell_at REAL NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL
            )
        """)

        # Simulated portfolio account
        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_accounts (
                account_id INTEGER PRIMARY KEY,
                starting_cash REAL NOT NULL,
                cash REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Simulated stock holdings
        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                symbol TEXT PRIMARY KEY,
                quantity REAL NOT NULL DEFAULT 0,
                avg_cost REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
        """)

        # Portfolio transaction history
        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                side TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Create the $100 account only if one does not exist
        con.execute("""
            INSERT OR IGNORE INTO portfolio_accounts
            (account_id, starting_cash, cash, created_at)
            VALUES (1, ?, ?, ?)
        """, (
            STARTING_BALANCE,
            STARTING_BALANCE,
            datetime.now().isoformat(timespec="seconds")
        ))


# EXISTING STRATEGY FUNCTIONS — PRESERVED

def add_trade(symbol, buy_at, sell_at, mode):
    with connect() as con:
        con.execute(
            """
            INSERT INTO trades
            (symbol, buy_at, sell_at, mode, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                symbol,
                buy_at,
                sell_at,
                mode,
                datetime.now().isoformat(timespec="seconds")
            )
        )


def list_trades():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute(
                "SELECT * FROM trades ORDER BY id DESC"
            )
        ]


def mark_closed(trade_id):
    with connect() as con:
        con.execute(
            "UPDATE trades SET status='CLOSED' WHERE id=?",
            (trade_id,)
        )


# NEW PORTFOLIO FUNCTIONS

def get_portfolio_account():
    with connect() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM portfolio_accounts WHERE account_id=1"
        ).fetchone()

        return dict(row) if row else None


def list_holdings():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute(
                "SELECT * FROM portfolio_holdings ORDER BY symbol"
            )
        ]


def list_portfolio_transactions():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute(
                """
                SELECT * FROM portfolio_transactions
                ORDER BY id DESC
                """
            )
        ]
