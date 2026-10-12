"""Owner dashboard: how the shop is doing today and what needs attention.
Fits on one screen (no page scroll); long lists scroll inside their own cards."""
import os
from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from bakesync.core.database import DatabaseManager
from bakesync.core.alerts import collect_alerts
from bakesync.widgets.store_hours import closing_time_today, fmt as fmt_time, end_of_day_from, is_open_on
from bakesync.widgets.leftover_dialog import LeftoverDialog
from bakesync.core.leftovers import leftover_bread
from bakesync.widgets.ui import (THEME as T, BarChart, StatCard, intro_row, title_row, legend_row, ProgressBar,
                                 icon_label, svg_icon, button, card, chip, InfoIcon)


def _scroll_list():
    sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
    sc.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                     f"QScrollBar:vertical {{ width: 6px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; }}")
    holder = QWidget(); holder.setStyleSheet("background: transparent;")
    lay = QVBoxLayout(holder); lay.setContentsMargins(0, 0, 4, 0); lay.setSpacing(6)
    sc.setWidget(holder)
    return sc, lay


def _clear(lay):
    while lay.count():
        it = lay.takeAt(0)
        w = it.widget()
        if w:
            w.deleteLater()


def _hour(h):
    return datetime(2000, 1, 1, h % 24).strftime("%I %p").lstrip("0")


class DashboardWidget(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setStyleSheet(f"background-color: {T['cream']};")
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_if_visible)
        self._timer.start(60_000)

    # ── lifecycle ──────────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_dashboard()

    def _refresh_if_visible(self):
        if self.isVisible():
            self.refresh_dashboard()

    def stop_timers(self):
        self._timer.stop()

    # ── layout ─────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 14, 24, 14)
        root.setSpacing(12)

        intro, il = intro_row("How your bakery is doing today, and what needs your attention.",
                              "Everything here is for today only and updates by itself every minute. "
                              "Click a button in 'To do' to go straight to the right page.", "Dashboard")
        self.updated = QLabel(""); self.updated.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
        il.addWidget(self.updated)
        from bakesync.widgets.ui import RefreshButton
        ref = RefreshButton(h=32)
        ref.clicked.connect(self.refresh_dashboard)
        il.addWidget(ref)
        root.addWidget(intro)

        cards = QHBoxLayout(); cards.setSpacing(12)
        self.c_sales = StatCard("Sales today", "wallet", "All the money from the POS today. The line below compares it with "
                                "yesterday up to this same time.", T["green"], T["green_bg"])
        self.c_profit = StatCard("Profit today", "trend_up", "Sales minus what the sold bread and items cost you (puhunan). "
                                 "Expenses are not included here; see Settings > Finance.", T["brown"], T["cream_dark"])
        self.c_cust = StatCard("Customers today", "users", "How many sales were made today. One sale = one customer at the counter.",
                               T["blue"], T["blue_bg"])
        self.c_waste = StatCard("Wasted today", "trash", "Bread and items thrown away today, counted at what they cost you.",
                                T["red"], T["red_bg"])
        for c in (self.c_sales, self.c_profit, self.c_cust, self.c_waste):
            cards.addWidget(c)
        root.addLayout(cards)

        # middle: chart + to do
        mid = QHBoxLayout(); mid.setSpacing(12)
        chart_card = card(14, name="chart")
        cl = QVBoxLayout(chart_card); cl.setContentsMargins(16, 12, 16, 10); cl.setSpacing(4)
        t, _ = title_row("Sales today, hour by hour", icon="chart", size=13,
                         info="Each bar is one hour. A taller bar means more sales in that hour. "
                              "The gold bar is the best hour so far. Point at a bar to see the exact amount.")
        cl.addWidget(t)
        self.chart_note = QLabel(""); self.chart_note.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
        cl.addWidget(self.chart_note)
        self.chart = BarChart(money=True, empty_text="No sales yet today")
        cl.addWidget(self.chart, 1)
        mid.addWidget(chart_card, 3)

        todo = card(14, name="todo")
        tl = QVBoxLayout(todo); tl.setContentsMargins(16, 12, 16, 10); tl.setSpacing(6)
        tt, ttl = title_row("To do", icon="check_circle", size=13,
                            info="Things that need your attention today. Red = do it now. Orange = soon.")
        self.todo_count = chip("", T["red"], T["red_bg"]); ttl.addWidget(self.todo_count)
        tl.addWidget(tt)
        sc, self.todo_list = _scroll_list()
        tl.addWidget(sc, 1)
        foot = QHBoxLayout()
        foot.addWidget(icon_label("clock", T["mid"], 14))
        self.lbl_closing = QLabel(""); self.lbl_closing.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
        foot.addWidget(self.lbl_closing)
        hours_btn = button("Change", "ghost", h=26)
        hours_btn.clicked.connect(self._edit_hours)
        foot.addWidget(hours_btn); foot.addStretch()
        tl.addLayout(foot)
        mid.addWidget(todo, 2)
        root.addLayout(mid, 5)

        # bottom: bread today + best sellers
        bot = QHBoxLayout(); bot.setSpacing(12)
        bread = card(14, name="bread")
        bl = QVBoxLayout(bread); bl.setContentsMargins(16, 12, 16, 10); bl.setSpacing(6)
        bt, btl = title_row("Bread today", icon="bread", size=13,
                            info="How much of each bread was sold today. The bar fills up as pieces are sold. "
                                 "The number on the right is how many pieces are left to sell.")
        btl.addWidget(legend_row([(T["green"], "Sold"), ("#EFE7DE", "Left")]))
        bl.addWidget(bt)
        sc, self.bread_list = _scroll_list()
        bl.addWidget(sc, 1)
        bot.addWidget(bread, 3)

        top = card(14, name="top")
        tpl = QVBoxLayout(top); tpl.setContentsMargins(16, 12, 16, 10); tpl.setSpacing(6)
        tpt, _ = title_row("Best sellers today", icon="award", size=13,
                           info="The 5 products that sold the most pieces today. The bar compares each one with the top seller.")
        tpl.addWidget(tpt)
        sc, self.top_list = _scroll_list()
        tpl.addWidget(sc, 1)
        bot.addWidget(top, 2)
        root.addLayout(bot, 4)

    # ── data ───────────────────────────────────────────────
    def refresh_dashboard(self):
        try:
            self._load_numbers()
            self._load_chart()
            self._load_todo()
            self._load_bread()
            self._load_top()
            self.updated.setText(f"Updated {datetime.now().strftime('%I:%M %p').lstrip('0')}")
        except Exception as e:
            print(f"[Dashboard] refresh error: {e}")

    def _load_numbers(self):
        today = date.today()
        now = datetime.now()
        t = self.db.fetch_one("""
            SELECT COALESCE(SUM(s.amount), 0) AS sales, COUNT(DISTINCT s.created_at) AS txns,
                   COALESCE(SUM(s.quantity * COALESCE(p.production_cost, 0)), 0) AS cost
            FROM sales s JOIN products p ON p.id = s.product_id
            WHERE COALESCE(s.is_voided, 0) = 0 AND date(s.created_at) = ?
        """, (today.isoformat(),))
        y = self.db.fetch_one("""
            SELECT COALESCE(SUM(amount), 0) AS sales FROM sales
            WHERE COALESCE(is_voided, 0) = 0 AND date(created_at) = ? AND created_at <= ?
        """, ((today - timedelta(days=1)).isoformat(), (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))
        sales, txns, cost = t["sales"], t["txns"], t["cost"]
        if y["sales"] > 0:
            ch = (sales - y["sales"]) / y["sales"] * 100
            cmp_txt = f"{'Up' if ch >= 0 else 'Down'} {abs(ch):.0f}% from yesterday at this time (₱{y['sales']:,.0f})"
            cmp_col = T["green"] if ch >= 0 else T["red"]
        else:
            cmp_txt, cmp_col = "No sales yesterday at this time to compare", None
        self.c_sales.set(f"₱{sales:,.2f}", cmp_txt, cmp_col, T["green"] if sales else None)
        profit = sales - cost
        self.c_profit.set(f"₱{profit:,.2f}", f"{profit / sales * 100:.0f}% of sales" if sales else "No sales yet",
                          value_color=T["green"] if profit > 0 else (T["red"] if profit < 0 else None))
        self.c_cust.set(f"{txns:,}", f"₱{sales / txns:,.2f} per customer" if txns else "No customers yet")
        w = self.db.fetch_one("""
            SELECT COALESCE(SUM(w.quantity), 0) AS pcs, COALESCE(SUM(w.quantity * COALESCE(p.production_cost, 0)), 0) AS loss
            FROM waste_logs w JOIN products p ON p.id = w.product_id WHERE date(w.created_at) = ?
        """, (today.isoformat(),))
        self.c_waste.set(f"₱{w['loss']:,.2f}", f"{w['pcs']:,.0f} pcs thrown away" if w["pcs"] else "Nothing wasted today",
                         T["red"] if w["pcs"] else T["green"], T["red"] if w["loss"] else None)

    def _load_chart(self):
        data = self.db.fetch_all("""
            SELECT CAST(strftime('%H', created_at) AS INTEGER) AS hr, SUM(amount) AS sales, COUNT(DISTINCT created_at) AS c
            FROM sales WHERE COALESCE(is_voided, 0) = 0 AND date(created_at) = date('now', 'localtime') GROUP BY hr
        """)
        by_hr = {r["hr"]: r for r in data}
        first = min(list(by_hr) + [6])
        last = min(max(list(by_hr) + [closing_time_today(self.db).hour, datetime.now().hour]), 23)
        hours = list(range(first, last + 1))
        self.chart.set_data([_hour(h).replace(" ", "").lower() for h in hours],
                            [("Sales", [by_hr[h]["sales"] if h in by_hr else 0 for h in hours], T["brown"])],
                            full_labels=[f"{_hour(h)} – {_hour(h + 1)}" + (f"  ·  {by_hr[h]['c']} customers" if h in by_hr else "")
                                         for h in hours])
        if by_hr:
            b = max(by_hr.values(), key=lambda r: r["sales"])
            self.chart_note.setText(f"Best hour so far: {_hour(b['hr'])} – {_hour(b['hr'] + 1)}  (₱{b['sales']:,.0f})")
        else:
            self.chart_note.setText("Sales will show here as soon as the first customer pays.")

    def _todo_items(self):
        """[(level, icon, text, button label, (page, settings_index))]. level: red / amber."""
        items = []
        alerts = collect_alerts(self.db)

        def names(lst):
            shown = ", ".join(n for n, _ in lst[:3])
            return shown + (f" and {len(lst) - 3} more" if len(lst) > 3 else "")

        def s(n, one, many):
            return one if n == 1 else many
        if alerts["expired"]:
            n = len(alerts["expired"])
            items.append(("red", "trash", f"<b>{n} product{s(n, '', 's')}</b> {s(n, 'has', 'have')} expired stock: {names(alerts['expired'])}",
                          "Remove", ("Waste Control", None)))
        if alerts["low"]:
            n = len(alerts["low"])
            items.append(("amber", "box", f"<b>{n} product{s(n, '', 's')}</b> {s(n, 'is', 'are')} low or out of stock: {names(alerts['low'])}",
                          "Restock", ("Inventory", None)))
        if alerts["expiring"]:
            n = len(alerts["expiring"])
            items.append(("amber", "calendar", f"<b>{n} product{s(n, '', 's')}</b> must be sold today: {names(alerts['expiring'])}",
                          "View", ("Inventory", None)))
        pending = self.db.fetch_one("SELECT COUNT(*) AS n FROM users WHERE status = 'Pending'")["n"]
        if pending:
            items.append(("amber", "users", f"<b>{pending} new account{s(pending, '', 's')}</b> waiting for approval",
                          "Approve", ("Settings", 3)))
        closing = closing_time_today(self.db)
        if is_open_on(self.db, datetime.now().date()) and datetime.now().time() >= end_of_day_from(self.db):
            closed = self.db.fetch_one(
                "SELECT COUNT(*) AS n FROM pos_sessions WHERE status = 'Closed' AND date(closed_at) = date('now', 'localtime')")["n"]
            if not closed:
                when = "It is past" if datetime.now().time() >= closing else "Closing soon, at"
                items.append(("red", "clock", f"{when} <b>{fmt_time(closing)}</b>: close today's sales (End of Day)",
                              "Go to POS", ("POS", None)))
            left = leftover_bread(self.db)
            if left:
                pcs = sum(r["left_qty"] for r in left)
                items.append(("amber", "bread", f"<b>{pcs:g} pcs</b> of bread left: sell tomorrow or throw away?",
                              "Decide", ("__leftovers__", None)))
            counted = self.db.fetch_one(
                "SELECT COUNT(*) AS n FROM reconciliation WHERE date(created_at) = date('now', 'localtime')")["n"]
            if not counted:
                items.append(("amber", "wallet", "Today's cash has not been counted yet", "Count Cash", ("Settings", 1)))
        backup_dir = os.path.join(os.path.dirname(self.db.db_path), "backups")
        try:
            newest = max((os.path.getmtime(os.path.join(backup_dir, f)) for f in os.listdir(backup_dir) if f.endswith(".db")), default=0)
        except OSError:
            newest = 0
        if datetime.now().timestamp() - newest > 2 * 86400:
            items.append(("amber", "database", "No backup in the last 2 days", "Back Up", ("Settings", 5)))
        return items

    def _load_todo(self):
        _clear(self.todo_list)
        allowed = getattr(self.window(), "_allowed", lambda p: True)
        items = self._todo_items()
        self.todo_count.setText(f"{len(items)}")
        self.todo_count.setVisible(bool(items))
        if not items:
            ok = QWidget(); okl = QVBoxLayout(ok); okl.setContentsMargins(0, 18, 0, 0); okl.setSpacing(6)
            okl.addWidget(icon_label("check_circle", T["green"], 34), alignment=Qt.AlignmentFlag.AlignCenter)
            okt = QLabel("Nothing to do right now. All good!")
            okt.setStyleSheet(f"color: {T['green']}; font-size: 13px; font-weight: 600;")
            okl.addWidget(okt, alignment=Qt.AlignmentFlag.AlignCenter)
            self.todo_list.addWidget(ok)
        for level, icon, text, btn_text, (page, sub) in items:
            fg, bg = (T["red"], T["red_bg"]) if level == "red" else (T["amber"], T["amber_bg"])
            row = QFrame(); row.setObjectName("todo")
            row.setStyleSheet(f"QFrame#todo {{ background: {T['cream']}; border-radius: 10px; }} QLabel {{ background: transparent; }}")
            rl = QHBoxLayout(row); rl.setContentsMargins(8, 6, 8, 6); rl.setSpacing(8)
            rl.addWidget(icon_label(icon, fg, 15, bg=bg, box=30, radius=15))
            lbl = QLabel(text); lbl.setWordWrap(True); lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setStyleSheet(f"color: {T['text']}; font-size: 12px;")
            rl.addWidget(lbl, 1)
            if page == "__leftovers__" or allowed(page):
                b = button(btn_text, "primary", h=28)
                b.setProperty("page", page); b.setProperty("sub", sub)
                b.clicked.connect(self._on_todo_clicked)
                rl.addWidget(b)
            self.todo_list.addWidget(row)
        self.todo_list.addStretch()
        self.lbl_closing.setText(f"Closing today at {fmt_time(closing_time_today(self.db))}")

    def _on_todo_clicked(self):
        b = self.sender()
        if b is not None:
            self._go(b.property("page"), b.property("sub"))

    def _go(self, page, settings_index=None):
        if page == "__leftovers__":
            user = getattr(self.window(), "username", "")
            if LeftoverDialog(self.db, user, self).exec():
                self.refresh_dashboard()
            return
        win = self.window()
        if hasattr(win, "change_page"):
            win.change_page(page)
            if settings_index is not None and "Settings" in getattr(win, "pages", {}):
                win.pages["Settings"].switch_view(settings_index)

    def _edit_hours(self):
        self._go("Settings", 6)   # the Store Hours page

    def _load_bread(self):
        rows = self.db.fetch_all("""
            SELECT p.name, COALESCE(p.stock_qty, 0) AS left_qty,
                   (SELECT COALESCE(SUM(s.quantity), 0) FROM sales s
                     WHERE s.product_id = p.id AND date(s.created_at) = date('now', 'localtime') AND COALESCE(s.is_voided, 0) = 0) AS sold
            FROM products p WHERE p.product_type = 'bread' AND p.is_archived = 0 ORDER BY sold DESC, p.name
        """)
        _clear(self.bread_list)
        if not rows:
            e = QLabel("No bread added yet. Add bread in Inventory."); e.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
            self.bread_list.addWidget(e)
        for r in rows:
            left, sold = max(0, r["left_qty"] or 0), r["sold"] or 0
            total = left + sold
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 2, 0, 2); h.setSpacing(10)
            n = QLabel(r["name"]); n.setFixedWidth(150); n.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 600;")
            h.addWidget(n)
            col = QVBoxLayout(); col.setSpacing(2)
            pb = ProgressBar(sold / total if total else 0, T["green"])
            col.addWidget(pb)
            sl = QLabel(f"{sold:g} sold of {total:g}" if total else "No stock today")
            sl.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
            col.addWidget(sl)
            h.addLayout(col, 1)
            h.addWidget(chip("Sold out", T["red"], T["red_bg"]) if left <= 0 else
                        chip(f"{left:g} left", T["amber"] if left <= 5 else T["brown"], T["amber_bg"] if left <= 5 else T["cream_dark"]))
            self.bread_list.addWidget(w)
        self.bread_list.addStretch()

    def _load_top(self):
        rows = self.db.fetch_all("""
            SELECT p.name, SUM(s.quantity) AS qty, SUM(s.amount) AS sales
            FROM sales s JOIN products p ON p.id = s.product_id
            WHERE COALESCE(s.is_voided, 0) = 0 AND date(s.created_at) = date('now', 'localtime')
            GROUP BY p.id ORDER BY qty DESC LIMIT 5
        """)
        _clear(self.top_list)
        if not rows:
            e = QWidget(); el = QVBoxLayout(e); el.setContentsMargins(0, 18, 0, 0); el.setSpacing(6)
            el.addWidget(icon_label("award", T["muted"], 30), alignment=Qt.AlignmentFlag.AlignCenter)
            m = QLabel("No sales yet today"); m.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
            el.addWidget(m, alignment=Qt.AlignmentFlag.AlignCenter)
            self.top_list.addWidget(e)
        top_qty = rows[0]["qty"] if rows else 1
        for i, r in enumerate(rows):
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 2, 0, 2); h.setSpacing(10)
            rank = QLabel(str(i + 1)); rank.setFixedSize(26, 26); rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rank.setStyleSheet(f"background: {T['gold'] if i == 0 else T['cream_dark']}; color: {T['choc'] if i == 0 else T['brown']}; "
                               "border-radius: 13px; font-size: 12px; font-weight: bold;")
            h.addWidget(rank)
            col = QVBoxLayout(); col.setSpacing(2)
            nl = QHBoxLayout()
            n = QLabel(r["name"]); n.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 600;")
            v = QLabel(f"{r['qty']:,.0f} pcs  ·  ₱{r['sales']:,.0f}"); v.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
            nl.addWidget(n); nl.addStretch(); nl.addWidget(v)
            col.addLayout(nl)
            col.addWidget(ProgressBar(r["qty"] / top_qty, T["gold"] if i == 0 else T["caramel"], 6))
            h.addLayout(col, 1)
            self.top_list.addWidget(w)
        self.top_list.addStretch()
