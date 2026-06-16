"""
dedup_store.py — SQLite-based message deduplication.
Tracks message hashes so the same job isn't processed twice.
"""
import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dedup.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                hash       TEXT PRIMARY KEY,
                group_name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        db.commit()


def is_seen(msg_hash: str) -> bool:
    with _conn() as db:
        row = db.execute("SELECT 1 FROM seen WHERE hash = ?", (msg_hash,)).fetchone()
        return row is not None


def mark_seen(msg_hash: str, group_name: str = ""):
    with _conn() as db:
        db.execute(
            "INSERT OR IGNORE INTO seen (hash, group_name) VALUES (?, ?)",
            (msg_hash, group_name),
        )
        db.commit()


def prune_old(days: int = 30):
    """Remove entries older than N days to keep DB small."""
    with _conn() as db:
        db.execute(
            "DELETE FROM seen WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        db.commit()


def stats() -> dict:
    with _conn() as db:
        total = db.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
        return {"total_seen": total}
