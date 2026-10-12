"""Clears test/practice TRANSACTIONS from a BakeSync database before real use.

Keeps:   accounts, products (prices, stock), ingredients, recipes, stock batches
Deletes: sales, POS sessions, reconciliations, waste logs, production schedule,
         expenses, voids, audit logs

A backup copy is saved next to the database first.

Usage (close BakeSync first):
    python tools/clear_test_data.py                                  # release app database
    python tools/clear_test_data.py data/bakesync.db                 # development database
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(ROOT, "release", "BakeSync", "data", "bakesync.db")

CLEAR = ["sales", "pos_sessions", "reconciliation", "waste_logs", "production_schedule",
         "operating_expenses", "void_logs", "financial_audit_log", "inventory_action_log",
         "inventory_movements"]


def main():
    db_path = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB)
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    tables = [t for t in CLEAR if t in existing]
    counts = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    conn.close()

    print(f"Database: {db_path}\n")
    print("These records will be DELETED:")
    for t, n in counts.items():
        print(f"  {t:24s} {n:>6}")
    print("\nAccounts, products, ingredients, recipes and stock batches are kept.")
    if input("\nType YES to continue: ").strip() != "YES":
        print("Cancelled. Nothing was changed.")
        return 0

    backup = f"{db_path[:-3]}_before_clear_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup)
    print(f"Backup saved: {backup}")

    conn = sqlite3.connect(db_path)
    with conn:
        for t in tables:
            conn.execute(f'DELETE FROM "{t}"')
            conn.execute("DELETE FROM sqlite_sequence WHERE name = ?", (t,))
    conn.execute("VACUUM")
    print("Integrity check:", conn.execute("PRAGMA integrity_check").fetchone()[0])
    conn.close()
    print("Done. Test transactions cleared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
