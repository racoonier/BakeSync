"""One activity log for the whole app: who did what, and when.

Every row is linked to the one before it with a SHA-256 hash, so if a row is
changed or removed outside BakeSync the chain breaks and verify_log() reports it.
Inside the database, triggers block UPDATE and DELETE on the table.
"""
import hashlib
import sqlite3
from datetime import datetime

# area -> label shown on the Audit Log page
AREAS = {
    "signin": "Sign-in",
    "account": "Accounts",
    "sale": "Sales",
    "void": "Voids",
    "stock": "Stock",
    "waste": "Waste",
    "price": "Prices",
    "money": "Money",
    "system": "System",
}

# actions that the owner should notice (shown in red)
WARNING_ACTIONS = {"sign-in failed", "account locked", "sale voided", "cash short",
                   "account archived", "account rejected", "password reset", "data restored"}


def ensure_table(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            username   TEXT,
            action     TEXT NOT NULL,
            area       TEXT NOT NULL,
            details    TEXT,
            prev_hash  TEXT,
            row_hash   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at);
        CREATE TRIGGER IF NOT EXISTS activity_log_no_update BEFORE UPDATE ON activity_log
        BEGIN SELECT RAISE(ABORT, 'The activity log cannot be changed'); END;
        CREATE TRIGGER IF NOT EXISTS activity_log_no_delete BEFORE DELETE ON activity_log
        BEGIN SELECT RAISE(ABORT, 'The activity log cannot be deleted'); END;
    """)


def _hash(prev_hash, created_at, username, action, area, details):
    raw = "|".join([prev_hash or "", created_at, username or "", action, area, details or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def log_activity(db, user, action, area, details=""):
    """Add one row. Never raises: a logging problem must not stop a sale or a sign-in."""
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last = db.fetch_one("SELECT row_hash FROM activity_log ORDER BY id DESC LIMIT 1")
        prev = last["row_hash"] if last else ""
        row_hash = _hash(prev, created_at, user, action, area, details)
        db.execute_query(
            "INSERT INTO activity_log (created_at, username, action, area, details, prev_hash, row_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (created_at, user or "System", action, area, details or "", prev, row_hash))
    except (sqlite3.Error, AttributeError, TypeError) as e:
        print(f"[Audit] could not log '{action}': {e}")


def verify_log(db):
    """Returns (ok, rows_checked, first_bad_id)."""
    rows = db.fetch_all("SELECT id, created_at, username, action, area, details, prev_hash, row_hash "
                        "FROM activity_log ORDER BY id")
    prev = ""
    for r in rows:
        if (r["prev_hash"] or "") != prev:
            return False, len(rows), r["id"]
        if _hash(prev, r["created_at"], r["username"], r["action"], r["area"], r["details"]) != r["row_hash"]:
            return False, len(rows), r["id"]
        prev = r["row_hash"]
    return True, len(rows), None
