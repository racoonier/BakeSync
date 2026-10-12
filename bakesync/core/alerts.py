"""Things the owner should know about now: low stock, items expiring soon, expired stock."""

LOW_BREAD = 10    # bread: fewer than this many pieces left
LOW_RETAIL = 5    # retail: this many or fewer left


def collect_alerts(db):
    """Returns {"low": [...], "expiring": [...], "expired": [...]}, each a list of
    (product name, short detail) tuples. Uses usable stock (expired pieces excluded)."""
    rows = db.fetch_all("""
        SELECT p.name, p.product_type,
               COALESCE(p.stock_qty, 0) AS stock,
               (SELECT COALESCE(SUM(b.quantity_remaining), 0) FROM product_batches b
                 WHERE b.product_id = p.id AND b.quantity_remaining > 0
                   AND b.expiry_date IS NOT NULL AND b.expiry_date <= date('now', 'localtime')) AS expired,
               (SELECT COALESCE(SUM(b.quantity_remaining), 0) FROM product_batches b
                 WHERE b.product_id = p.id AND b.quantity_remaining > 0
                   AND b.expiry_date = date('now', 'localtime', '+1 day')) AS expiring,
               NULL AS expiring_on
        FROM products p
        WHERE p.is_archived = 0
        ORDER BY p.name
    """)
    out = {"low": [], "expiring": [], "expired": []}
    for r in rows:
        usable = max(0, (r["stock"] or 0) - (r["expired"] or 0))
        is_bread = (r["product_type"] or "bread") == "bread"
        if (is_bread and usable < LOW_BREAD) or (not is_bread and usable <= LOW_RETAIL):
            out["low"].append((r["name"], "out of stock" if usable == 0 else f"only {usable:g} left"))
        if r["expiring"]:   # expiry date is tomorrow, so today is the last day it can be sold
            out["expiring"].append((r["name"], f"{r['expiring']:g} pcs, last day today"))
        if r["expired"]:
            out["expired"].append((r["name"], f"{r['expired']:g} pcs expired"))
    return out
