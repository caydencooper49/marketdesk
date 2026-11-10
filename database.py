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

        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_accounts (
                account_id INTEGER PRIMARY KEY,
                starting_cash REAL NOT NULL,
                cash REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                symbol TEXT PRIMARY KEY,
                quantity REAL NOT NULL DEFAULT 0,
                avg_cost REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                side TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                created_at TEXT NOT NULL,
                realized_pl REAL NOT NULL DEFAULT 0
            )
        """)

        # Add the P/L column if an older transaction table exists.
        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(portfolio_transactions)"
            )
        }

        if "realized_pl" not in columns:
            con.execute("""
                ALTER TABLE portfolio_transactions
                ADD COLUMN realized_pl REAL NOT NULL DEFAULT 0
            """)

        con.execute("""
            INSERT OR IGNORE INTO portfolio_accounts
            (account_id, starting_cash, cash, created_at)
            VALUES (1, ?, ?, ?)
        """, (
            STARTING_BALANCE,
            STARTING_BALANCE,
            datetime.now().isoformat(timespec="seconds")
        ))


# EXISTING STRATEGY RULES

def add_trade(symbol, buy_at, sell_at, mode):
    with connect() as con:
        con.execute("""
            INSERT INTO trades
            (symbol, buy_at, sell_at, mode, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            symbol.upper(),
            buy_at,
            sell_at,
            mode,
            datetime.now().isoformat(timespec="seconds")
        ))


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


# PORTFOLIO ACCOUNT

def get_portfolio_account():
    with connect() as con:
        con.row_factory = sqlite3.Row
        row = con.execute("""
            SELECT * FROM portfolio_accounts
            WHERE account_id=1
        """).fetchone()

        return dict(row) if row else None


def list_holdings():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute("""
                SELECT * FROM portfolio_holdings
                ORDER BY symbol
            """)
        ]


def list_portfolio_transactions():
    with connect() as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute("""
                SELECT * FROM portfolio_transactions
                ORDER BY id DESC
            """)
        ]


# PAPER ORDER EXECUTION

def execute_order(side, symbol, quantity, price):
    side = str(side).upper()
    symbol = str(symbol).strip().upper()
    quantity = float(quantity)
    price = float(price)

    if side not in ("BUY", "SELL"):
        raise ValueError("Order must be BUY or SELL.")

    if not symbol:
        raise ValueError("A stock symbol is required.")

    if quantity <= 0 or price <= 0:
        raise ValueError("Quantity and price must be positive.")

    total = round(quantity * price, 2)
    now = datetime.now().isoformat(timespec="seconds")

    with connect() as con:
        account = con.execute("""
            SELECT cash FROM portfolio_accounts
            WHERE account_id=1
        """).fetchone()

        if not account:
            raise ValueError("Portfolio account not initialized.")

        cash = float(account[0])

        holding = con.execute("""
            SELECT quantity, avg_cost
            FROM portfolio_holdings
            WHERE symbol=?
        """, (symbol,)).fetchone()

        old_quantity = float(holding[0]) if holding else 0.0
        old_avg_cost = float(holding[1]) if holding else 0.0
        realized_pl = 0.0

        if side == "BUY":
            if total > cash:
                raise ValueError(
                    f"Insufficient cash. Available: ${cash:.2f}; "
                    f"order total: ${total:.2f}."
                )

            new_quantity = old_quantity + quantity
            new_avg_cost = (
                (old_quantity * old_avg_cost + total) / new_quantity
            )

            con.execute("""
                INSERT INTO portfolio_holdings
                (symbol, quantity, avg_cost, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    quantity=excluded.quantity,
                    avg_cost=excluded.avg_cost,
                    updated_at=excluded.updated_at
            """, (symbol, new_quantity, new_avg_cost, now))

            cash = round(cash - total, 2)

        else:
            if quantity > old_quantity:
                raise ValueError(
                    f"Not enough {symbol} shares to sell. "
                    f"Available: {old_quantity:g}."
                )

            realized_pl = round(
                (price - old_avg_cost) * quantity, 2
            )

            new_quantity = old_quantity - quantity
            cash = round(cash + total, 2)

            if new_quantity <= 0.00000001:
                con.execute(
                    "DELETE FROM portfolio_holdings WHERE symbol=?",
                    (symbol,)
                )
            else:
                con.execute("""
                    UPDATE portfolio_holdings
                    SET quantity=?, updated_at=?
                    WHERE symbol=?
                """, (new_quantity, now, symbol))

        con.execute("""
            UPDATE portfolio_accounts
            SET cash=?
            WHERE account_id=1
        """, (cash,))

        con.execute("""
            INSERT INTO portfolio_transactions
            (side, symbol, quantity, price, total, created_at, realized_pl)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            side, symbol, quantity, price,
            total, now, realized_pl
        ))

    return {
        "side": side,
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "total": total,
        "cash_remaining": cash,
        "realized_pl": realized_pl
    }
