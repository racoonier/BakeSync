"""Leftover bread and expired stock — one set of rules for Waste, Inventory and Dashboard.

Expiry rule (same as the POS): a batch can no longer be sold ON its expiry date,
so "expired" means expiry_date <= today.
"""
from datetime import date, timedelta
from bakesync.core.audit import log_activity

SELL_NOW, SELL_TOMORROW, THROW = "sell_now", "tomorrow", "waste"


def expire_old_batches(db, user="System"):
    """Write off every batch whose expiry date has arrived (any product).
    Returns the number of pieces written off."""
    today = date.today().isoformat()
    batches = db.fetch_all(
        "SELECT b.id, b.product_id, b.quantity_remaining AS qty FROM product_batches b "
        "JOIN products p ON p.id = b.product_id "
        "WHERE b.quantity_remaining > 0 AND b.expiry_date IS NOT NULL AND b.expiry_date <= ? AND p.is_archived = 0",
        (today,))
    total = 0
    with db.transaction():
        for b in batches:
            db.execute_query(
                "INSERT INTO waste_logs (product_id, waste_type, quantity, reason) VALUES (?, 'Expired', ?, 'Expired')",
                (b["product_id"], b["qty"]))
            db.execute_query("UPDATE product_batches SET quantity_remaining = 0 WHERE id = ?", (b["id"],))
            db.execute_query("UPDATE products SET stock_qty = MAX(0, COALESCE(stock_qty, 0) - ?) WHERE id = ?",
                             (b["qty"], b["product_id"]))
            total += b["qty"]
    if total:
        log_activity(db, user or "System", "expired stock removed", "waste",
                     f"{total:g} pcs past their sell-by date were recorded as waste")
    return total


def leftover_bread(db):
    """Bread that still has pieces left, with value and how many must be sold today."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return db.fetch_all("""
        SELECT p.id, p.name, COALESCE(p.stock_qty, 0) AS left_qty,
               COALESCE(p.retail_price, 0) AS price, COALESCE(p.production_cost, 0) AS cost,
               (SELECT COALESCE(SUM(b.quantity_remaining), 0) FROM product_batches b
                 WHERE b.product_id = p.id AND b.quantity_remaining > 0 AND b.expiry_date <= ?) AS last_day_qty
        FROM products p
        WHERE p.product_type = 'bread' AND p.is_archived = 0 AND COALESCE(p.stock_qty, 0) > 0
        ORDER BY p.name
    """, (tomorrow,))


def apply_leftover_decisions(db, decisions, user=""):
    """decisions: {product_id: SELL_NOW | SELL_TOMORROW | THROW}.
    - SELL_NOW: nothing changes (still on sale today).
    - SELL_TOMORROW: batches that could not be sold tomorrow get their expiry moved so they can.
    - THROW: all remaining pieces are logged as waste ("Hindi nabenta") and removed from stock.
    Returns {"tomorrow": pcs, "waste": pcs}."""
    keep_until = (date.today() + timedelta(days=2)).isoformat()   # sellable tomorrow (expiry day itself is not)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    result = {"tomorrow": 0, "waste": 0}
    with db.transaction():
        for pid, choice in decisions.items():
            row = db.fetch_one("SELECT COALESCE(stock_qty, 0) AS qty FROM products WHERE id = ?", (pid,))
            qty = row["qty"] if row else 0
            if qty <= 0:
                continue
            if choice == SELL_TOMORROW:
                db.execute_query(
                    "UPDATE product_batches SET expiry_date = ? WHERE product_id = ? AND quantity_remaining > 0 "
                    "AND (expiry_date IS NULL OR expiry_date <= ?)", (keep_until, pid, tomorrow))
                result["tomorrow"] += qty
            elif choice == THROW:
                db.execute_query(
                    "INSERT INTO waste_logs (product_id, waste_type, quantity, reason) "
                    "VALUES (?, 'Market Spoilage', ?, 'Not sold (End of Day)')", (pid, qty))
                db.execute_query("UPDATE product_batches SET quantity_remaining = 0 WHERE product_id = ?", (pid,))
                db.execute_query("UPDATE products SET stock_qty = 0 WHERE id = ?", (pid,))
                result["waste"] += qty
        if result["tomorrow"] or result["waste"]:
            db.execute_query(
                "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                ("bread", 0, f"End of Day: {result['tomorrow']:g} kept for tomorrow, {result['waste']:g} thrown away",
                 "leftovers decided", user or "Unknown"))
    return result
