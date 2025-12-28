from fastmcp import FastMCP
import aiosqlite
import asyncio
import os
from typing import Optional

DB_PATH = "/tmp/expenses.db"
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

# -------------------------
# Lazy DB init (FastMCP-safe)
# -------------------------
_db_initialized = False
_db_lock: Optional[asyncio.Lock] = None


async def ensure_db():
    global _db_initialized, _db_lock

    if _db_initialized:
        return

    # Create lock lazily to bind to the active event loop
    if _db_lock is None:
        _db_lock = asyncio.Lock()

    async with _db_lock:
        if _db_initialized:
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA busy_timeout = 3000;")
            await db.commit()

        _db_initialized = True


# -------------------------
# Tools
# -------------------------
@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    await ensure_db()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            INSERT INTO expenses(date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, amount, category, subcategory, note)
        )
        await db.commit()
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    await ensure_db()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


@mcp.tool()
async def summarize(
    start_date: str,
    end_date: str,
    category: Optional[str] = None
):
    await ensure_db()

    query = """
        SELECT category, SUM(amount) AS total_amount
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if category is not None:
        query += " AND category = ?"
        params.append(category)

    query += " GROUP BY category ORDER BY category ASC"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# -------------------------
# Resource
# -------------------------
@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    def _read():
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()

    return await asyncio.to_thread(_read)


# -------------------------
# Server
# -------------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
