import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "marketdesk.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
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

def add_trade(symbol, buy_at, sell_at, mode):
    with connect() as con:
        con.execute(
            "INSERT INTO trades(symbol,buy_at,sell_at,mode,created_at) VALUES(?,?,?,?,?)",
            (symbol, buy_at, sell_at, mode, datetime.now().isoformat(timespec="seconds"))
        )

def list_trades():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute("SELECT * FROM trades ORDER BY id DESC")]

def mark_closed(trade_id):
    with connect() as con:
        con.execute("UPDATE trades SET status='CLOSED' WHERE id=?", (trade_id,))
