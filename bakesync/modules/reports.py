"""Reports page: one period at a time, real numbers only, with a short list of highlights.

Pick a period (this week, last month, ...) and see sales, profit, customers,
waste, the busiest days and hours, which products to bake more or fewer of,
and how each cashier did. Everything can be saved as PDF or for Excel (CSV)."""
import csv
import html
import os
from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QDateEdit,
                             QFileDialog, QMenu)
from PyQt6.QtCore import Qt, QDate, QMargins
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.ui import (InfoIcon, button as ui_button, svg_icon as ui_icon, icon_label as ui_icon_label,
                               title_row as ui_title_row, nice_max, StatCard, BarChart, THEME as UI,
                               Highlights)

BROWN, BROWN_DARK, CREAM, MID, DARK = "#6B3F27", "#693903", "#FAF9F7", "#64748B", "#1F2937"
GREEN, RED, AMBER, BORDER = "#047857", "#B91C1C", "#B45309", "#E8E2D9"
PERIODS = ["This week", "Last week", "This month", "Last month", "Last 30 days", "Pick dates"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TABLE_STYLE = f"""
    QTableWidget {{ border: none; font-size: 13px; background: white; color: {DARK}; alternate-background-color: #FBF8F4; }}
    QHeaderView::section {{ background: #F3E9DE; color: {BROWN}; padding: 8px; border: none; font-weight: bold; font-size: 12px; }}
    QTableWidget::item {{ padding: 4px 10px; border-bottom: 1px solid #F3F4F6; }}
    QScrollBar:vertical {{ width: 6px; background: transparent; }} QScrollBar::handle:vertical {{ background: #EADFD3; border-radius: 3px; }}
"""


def _range(name):
    t = date.today()
    if name == "This week":
        return t - timedelta(days=t.weekday()), t
    if name == "Last week":
        start = t - timedelta(days=t.weekday() + 7)
        return start, start + timedelta(days=6)
    if name == "This month":
        return t.replace(day=1), t
    if name == "Last month":
        end = t.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    return t - timedelta(days=29), t


def _hour_label(h):
    return datetime(2000, 1, 1, h).strftime("%I %p").lstrip("0")


def _hour_short(h):
    return datetime(2000, 1, 1, h).strftime("%I%p").lstrip("0").lower()


class ReportsWidget(QWidget):
    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.data = {}
        self.setStyleSheet(f"background: {CREAM};")
        self._build()
        self.refresh()

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        """Everything fits on one screen: period bar, 5 cards, then charts/tables (left)
        and 'Highlights' (right). Long tables scroll inside their own box."""
        root = QVBoxLayout(self); root.setContentsMargins(28, 14, 28, 14); root.setSpacing(10)

        bar = QHBoxLayout(); bar.setSpacing(6)
        self._pbtn = {}
        for name in PERIODS:
            b = QPushButton(name); b.setCheckable(True); b.setFixedHeight(34)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ background: white; color: {MID}; border: 1px solid {BORDER}; border-radius: 17px; "
                            f"padding: 0 14px; font-size: 13px; font-weight: 600; }}"
                            f"QPushButton:checked {{ background: {BROWN}; color: white; border-color: {BROWN}; }}")
            b.clicked.connect(lambda _, n=name: self._set_period(n))
            bar.addWidget(b)
            self._pbtn[name] = b
        self.d_from, self.d_to = QDateEdit(), QDateEdit()
        for d, v in ((self.d_from, QDate.currentDate().addDays(-6)), (self.d_to, QDate.currentDate())):
            d.setCalendarPopup(True); d.setDisplayFormat("MMM d, yyyy"); d.setDate(v); d.setFixedHeight(34); d.setMinimumWidth(128)
            d.setMaximumDate(QDate.currentDate())
            d.setStyleSheet(f"QDateEdit {{ background: white; border: 1px solid {BORDER}; border-radius: 8px; padding: 0 8px; "
                            f"font-size: 12px; color: {DARK}; }}")
            d.dateChanged.connect(lambda *_: self.refresh() if self.period == "Pick dates" else None)
        self.to_lbl = QLabel("to"); self.to_lbl.setStyleSheet(f"color: {MID}; background: transparent;")
        bar.addSpacing(6)
        bar.addWidget(self.d_from); bar.addWidget(self.to_lbl); bar.addWidget(self.d_to)
        bar.addStretch()
        save = ui_button("Save report", "primary", icon="download", h=34)
        menu = QMenu(save)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #EADFD3; border-radius: 8px; padding: 4px; }"
                           "QMenu::item { padding: 8px 18px; border-radius: 6px; color: #1F2937; }"
                           "QMenu::item:selected { background: #F5ECE5; }")
        menu.addAction(ui_icon("file", "#A83535", 16), "Save as PDF (to print or send)").triggered.connect(self.export_pdf)
        menu.addAction(ui_icon("list", "#2F7A4B", 16), "Save for Excel").triggered.connect(self.export_csv)
        save.setMenu(menu)
        save.setStyleSheet(save.styleSheet() + " QPushButton { padding-right: 30px; }"
                           " QPushButton::menu-indicator { subcontrol-position: right center; subcontrol-origin: padding; right: 10px; }")
        bar.addWidget(save)
        root.addLayout(bar)

        self.period_lbl = QLabel("")
        self.period_lbl.setStyleSheet(f"color: {MID}; font-size: 12px; background: transparent;")
        root.addWidget(self.period_lbl)

        cards = QHBoxLayout(); cards.setSpacing(10)
        self.cards = {}
        for key, title, icon, info in (
                ("sales", "Total sales", "wallet", "All the money from the POS in this period. Voided sales are not counted. "
                                                   "The small line compares it with the same number of days just before."),
                ("profit", "Profit", "trend_up", "Sales minus what the sold items cost you (puhunan) minus your expenses. "
                                                 "This is what you really earned."),
                ("customers", "Customers", "users", "How many separate sales were made. One sale = one customer at the counter."),
                ("avg", "Average per customer", "cart", "How much one customer spends, on average. Bigger is better."),
                ("waste", "Wasted", "trash", "Bread and items thrown away or expired in this period, and what they cost you.")):
            colors = {"sales": (UI["green"], UI["green_bg"]), "profit": (UI["brown"], UI["cream_dark"]),
                      "customers": (UI["blue"], UI["blue_bg"]), "avg": (UI["amber"], UI["amber_bg"]), "waste": (UI["red"], UI["red_bg"])}
            sc_ = StatCard(title, icon, info, *colors[key])
            sc_.value.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
            self.cards[key] = (sc_.value, sc_.sub)
            cards.addWidget(sc_)
        root.addLayout(cards)

        body = QHBoxLayout(); body.setSpacing(12)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {BORDER}; background: white; border-radius: 12px; top: 6px; }}
            QTabBar::tab {{ background: white; color: {MID}; padding: 7px 16px; margin-right: 6px; font-size: 13px; font-weight: 600;
                            border: 1px solid {BORDER}; border-radius: 15px; }}
            QTabBar::tab:selected {{ background: {BROWN}; color: white; border-color: {BROWN}; }}
            QTabBar::tab:hover:!selected {{ background: #F5ECE5; }}""")
        self.day_chart = BarChart(money=True, empty_text="No sales in this period")
        self.hour_chart = BarChart(money=False, empty_text="No sales in this period", y_title="Customers")
        self.tbl_products = self._table(["Product", "Pieces sold", "Sales", "Profit", "Wasted", "What to do"])
        self.tbl_cashiers = self._table(["Cashier", "Customers", "Sales", "Average per customer", "Voids", "Money voided"])
        self.tbl_money = self._table(["", "Amount"])
        self.tbl_money.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.day_note, self.hour_note = QLabel(""), QLabel("")
        pages = [
            (self.day_chart, "Sales by day", "Sales per day",
             "Each bar is one day. A taller bar means more sales that day. The gold bar is your best day.", self.day_note),
            (self.hour_chart, "Busy hours", "When customers come",
             "Each bar is one hour of the day. It shows how many customers came in that hour, on an average day. "
             "The gold bar is your busiest hour: have bread ready and someone at the counter.", self.hour_note),
            (self.tbl_products, "Products", "How each product did",
             "Pieces sold, money made and pieces wasted for each product, with a simple tip on what to do.", None),
            (self.tbl_cashiers, "Cashiers", "How each cashier did",
             "Sales and voids for each person who used the POS in this period.", None),
            (self.tbl_money, "Money summary", "Where the money came from and went",
             "Start with sales, take away the cost of what was sold and each expense. What is left is your profit.", None)]
        for widget, tab, title, info, note in pages:
            page = QWidget(); pl = QVBoxLayout(page); pl.setContentsMargins(12, 10, 12, 8); pl.setSpacing(4)
            tr, _ = ui_title_row(title, info=info, size=12)
            pl.addWidget(tr)
            if note is not None:
                note.setStyleSheet(f"color: {MID}; font-size: 12px;"); note.setWordWrap(True)
                pl.addWidget(note)
            pl.addWidget(widget, 1)
            self.tabs.addTab(page, tab)
        body.addWidget(self.tabs, 13)

        self.highlights = Highlights("Highlights", info="The most important things in this period, worked out for you "
                                                     "from the numbers.", max_rows=6)
        side = self.highlights
        body.addWidget(side, 7)
        root.addLayout(body, 1)
        self._set_period("This week", refresh=False)

    def _table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.setShowGrid(False); t.setAlternatingRowColors(True)
        t.setStyleSheet(TABLE_STYLE)
        return t

    def _set_period(self, name, refresh=True):
        self.period = name
        for n, b in self._pbtn.items():
            b.setChecked(n == name)
        custom = name == "Pick dates"
        for w in (self.d_from, self.to_lbl, self.d_to):
            w.setVisible(custom)
        if refresh:
            self.refresh()

    def _dates(self):
        if self.period == "Pick dates":
            a, b = self.d_from.date().toPyDate(), self.d_to.date().toPyDate()
            return (a, b) if a <= b else (b, a)
        return _range(self.period)

    # ── data ──────────────────────────────────────────────────────────────
    def _collect(self, start, end):
        s, e = start.isoformat(), end.isoformat()
        q = self.db.fetch_one
        tot = q("""SELECT COALESCE(SUM(s.amount),0) AS sales, COALESCE(SUM(s.quantity),0) AS pcs,
                          COALESCE(SUM(s.quantity * COALESCE(p.production_cost,0)),0) AS cost,
                          COUNT(DISTINCT s.created_at) AS customers
                   FROM sales s LEFT JOIN products p ON p.id = s.product_id
                   WHERE COALESCE(s.is_voided,0) = 0 AND date(s.created_at) BETWEEN ? AND ?""", (s, e))
        exp = q("SELECT COALESCE(SUM(amount),0) AS t FROM operating_expenses WHERE date(expense_date) BETWEEN ? AND ?", (s, e))["t"]
        waste = q("""SELECT COALESCE(SUM(w.quantity),0) AS pcs, COALESCE(SUM(w.quantity * COALESCE(p.production_cost,0)),0) AS loss
                     FROM waste_logs w LEFT JOIN products p ON p.id = w.product_id
                     WHERE date(w.created_at) BETWEEN ? AND ?""", (s, e))
        voids = q("SELECT COUNT(*) AS n, COALESCE(SUM(amount),0) AS amt FROM void_logs WHERE date(created_at) BETWEEN ? AND ?", (s, e))
        return {"sales": tot["sales"], "pcs": tot["pcs"], "cost": tot["cost"], "customers": tot["customers"],
                "expenses": exp, "waste_pcs": waste["pcs"], "waste_loss": waste["loss"],
                "voids": voids["n"], "void_amt": voids["amt"],
                "profit": tot["sales"] - tot["cost"] - exp}

    def refresh(self):
        if self.db.is_closed():
            return
        start, end = self._dates()
        days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        cur, prev = self._collect(start, end), self._collect(prev_start, prev_end)
        s, e = start.isoformat(), end.isoformat()
        self.data = {"start": start, "end": end, "days": days, "cur": cur, "prev": prev}
        fmt = lambda d: d.strftime("%b %d, %Y")
        self.period_lbl.setText(f"{self.period if self.period != 'Pick dates' else 'Your dates'}:  {fmt(start)} – {fmt(end)}  "
                                f"({days} day{'s' if days != 1 else ''})  ·  compared with {fmt(prev_start)} – {fmt(prev_end)}")

        def change(a, b):
            if b <= 0:
                return "No earlier data to compare", MID
            d = (a - b) / b * 100
            return (f"Up {d:.0f}% from before" if d >= 0 else f"Down {-d:.0f}% from before"), (GREEN if d >= 0 else RED)

        def put(key, value, sub, color=MID, vcolor=DARK):
            v, sl = self.cards[key]
            v.setText(value); v.setStyleSheet(f"color: {vcolor};")
            sl.setText(sub); sl.setStyleSheet(f"color: {color}; font-size: 11px;")
        txt, col = change(cur["sales"], prev["sales"])
        put("sales", f"₱{cur['sales']:,.2f}", txt, col)
        put("profit", f"₱{cur['profit']:,.2f}" if cur["profit"] >= 0 else f"-₱{-cur['profit']:,.2f}",
            f"after ₱{cur['cost']:,.0f} cost and ₱{cur['expenses']:,.0f} expenses", MID, GREEN if cur["profit"] >= 0 else RED)
        txt, col = change(cur["customers"], prev["customers"])
        put("customers", f"{cur['customers']:,}", f"{cur['customers'] / days:,.0f} a day  ·  {txt}", col)
        avg = cur["sales"] / cur["customers"] if cur["customers"] else 0
        pavg = prev["sales"] / prev["customers"] if prev["customers"] else 0
        txt, col = change(avg, pavg)
        put("avg", f"₱{avg:,.2f}", txt, col)
        put("waste", f"{cur['waste_pcs']:,.0f} pcs", f"₱{cur['waste_loss']:,.2f} lost (cost)", RED if cur["waste_pcs"] else MID)

        # per day / per hour / per product / per cashier
        by_day = {r["d"]: r for r in self.db.fetch_all(
            "SELECT date(created_at) AS d, SUM(amount) AS t, COUNT(DISTINCT created_at) AS c FROM sales "
            "WHERE COALESCE(is_voided,0) = 0 AND date(created_at) BETWEEN ? AND ? GROUP BY d", (s, e))}
        by_hour = {int(r["h"]): r for r in self.db.fetch_all(
            "SELECT strftime('%H', created_at) AS h, SUM(amount) AS t, COUNT(DISTINCT created_at) AS c FROM sales "
            "WHERE COALESCE(is_voided,0) = 0 AND date(created_at) BETWEEN ? AND ? GROUP BY h", (s, e))}
        prods = [dict(r) for r in self.db.fetch_all("""
            SELECT p.name, p.product_type AS type, COALESCE(p.production_cost,0) AS unit_cost,
                   COALESCE(SUM(s.quantity),0) AS pcs, COALESCE(SUM(s.amount),0) AS sales,
                   COALESCE(SUM(s.amount - s.quantity * COALESCE(p.production_cost,0)),0) AS profit,
                   (SELECT COALESCE(SUM(w.quantity),0) FROM waste_logs w WHERE w.product_id = p.id
                     AND date(w.created_at) BETWEEN ? AND ?) AS wasted
            FROM products p LEFT JOIN sales s ON s.product_id = p.id AND COALESCE(s.is_voided,0) = 0
                 AND date(s.created_at) BETWEEN ? AND ?
            WHERE p.is_archived = 0 GROUP BY p.id ORDER BY sales DESC""", (s, e, s, e))]
        cashiers = [dict(r) for r in self.db.fetch_all("""
            SELECT COALESCE(s.cashier,'Unknown') AS who, COUNT(DISTINCT s.created_at) AS customers, SUM(s.amount) AS sales,
                   (SELECT COUNT(*) FROM void_logs v WHERE v.voided_by = s.cashier AND date(v.created_at) BETWEEN ? AND ?) AS voids,
                   (SELECT COALESCE(SUM(v.amount),0) FROM void_logs v WHERE v.voided_by = s.cashier AND date(v.created_at) BETWEEN ? AND ?) AS void_amt
            FROM sales s WHERE COALESCE(s.is_voided,0) = 0 AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY who ORDER BY sales DESC""", (s, e, s, e, s, e))]
        self.data.update(by_day=by_day, by_hour=by_hour, prods=prods, cashiers=cashiers)

        self._insights()
        self._day_chart()
        self._hour_chart()
        self._fill_products()
        self._fill_cashiers()
        self._fill_money()

    def _advice(self, p, avg_pcs):
        if p["pcs"] == 0 and p["wasted"] == 0:
            return "Not sold in this period", MID
        if p["unit_cost"] <= 0:
            return "No cost set — add it in Pricing to see real profit", AMBER
        if p["wasted"] > 0 and p["wasted"] >= 0.25 * max(p["pcs"], 1):
            return "Bake / order fewer — a lot is wasted", RED
        if p["pcs"] >= 1.5 * avg_pcs and p["wasted"] == 0:
            return "Best seller — make sure it never runs out", GREEN
        if p["pcs"] < 0.3 * avg_pcs:
            return "Slow seller — make fewer", AMBER
        return "Good", GREEN

    def _insights(self):
        """Fills the Highlights card. Each fact: (icon, tone, label, answer, one line under it).
        insight_lines keeps the same facts as plain sentences for the PDF."""
        d = self.data
        cur, prev = d["cur"], d["prev"]
        items, lines = [], []
        if cur["sales"] <= 0:
            self.highlights.set_items([])
            self.data["insight_lines"] = ["No sales in this period yet."]
            return
        if prev["sales"] > 0:
            diff = (cur["sales"] - prev["sales"]) / prev["sales"] * 100
            up = diff >= 0
            items.append(("trend_up" if up else "trend_down", "green" if up else "red", "Sales vs. before",
                          f"{'Up' if up else 'Down'} {abs(diff):.0f}%", f"₱{prev['sales']:,.0f} before, ₱{cur['sales']:,.0f} now"))
            lines.append(f"Sales are {'up' if up else 'down'} {abs(diff):.0f}% compared with the period before "
                         f"(₱{prev['sales']:,.0f} to ₱{cur['sales']:,.0f}).")
        sold = [p for p in d["prods"] if p["pcs"] > 0]
        top = max(sold, key=lambda p: p["pcs"]) if sold else None
        if top:
            items.append(("award", "gold", "Best seller", top["name"], f"{top['pcs']:,.0f} pcs  ·  ₱{top['sales']:,.0f}"))
            lines.append(f"Best seller: {top['name']} ({top['pcs']:,.0f} pcs, ₱{top['sales']:,.0f}).")
        if d["by_hour"]:
            h = max(d["by_hour"].items(), key=lambda x: x[1]["c"])[0]
            when = f"{_hour_label(h)} – {_hour_label((h + 1) % 24)}"
            items.append(("clock", "blue", "Busiest time", when, "Have bread ready and someone at the counter."))
            lines.append(f"Busiest time: {when} — have bread ready and a cashier at the counter.")
        if d["by_day"]:
            best = max(d["by_day"].values(), key=lambda r: r["t"])
            bd = date.fromisoformat(best["d"])
            sub = f"₱{best['t']:,.0f} from {best['c']} customers"
            wd = {}
            for k, r in d["by_day"].items():
                wd.setdefault(date.fromisoformat(k).weekday(), []).append(r["t"])
            if d["days"] >= 14 and len(wd) >= 5:
                busiest = max(wd.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]
                sub += f". {DAY_NAMES[busiest]}s are usually busiest."
                lines.append(f"On average, {DAY_NAMES[busiest]}s are your busiest day — bake more on that day.")
            items.append(("calendar", "green", "Best day", bd.strftime("%A, %b %d"), sub))
            lines.append(f"Best day: {bd.strftime('%A, %b %d')} with ₱{best['t']:,.0f} from {best['c']} customers.")
        wasted = [p for p in d["prods"] if p["wasted"] > 0]
        if wasted:
            w = max(wasted, key=lambda p: p["wasted"])
            items.append(("trash", "red", "Most wasted", w["name"], f"{w['wasted']:,.0f} pcs thrown away. Try making fewer."))
            lines.append(f"Most wasted: {w['name']} ({w['wasted']:,.0f} pcs) — try baking fewer.")
        no_cost = [p for p in sold if p["unit_cost"] <= 0]
        if no_cost:
            n = len(no_cost)
            items.append(("alert", "amber", "Missing puhunan", f"{n} product{'s' if n != 1 else ''} with no cost",
                          "Profit looks higher than it is. Set it in Pricing."))
            lines.append(f"{n} product{'s have' if n != 1 else ' has'} no cost set "
                         f"({', '.join(p['name'] for p in no_cost[:3])}{'…' if n > 3 else ''}), "
                         "so the profit shown is higher than it really is.")
        costed = [p for p in sold if p["unit_cost"] > 0]
        most_profit = max(costed, key=lambda p: p["profit"]) if costed else None
        if most_profit and most_profit is not top:
            items.append(("wallet", "brown", "Earns you the most", most_profit["name"], f"₱{most_profit['profit']:,.0f} profit"))
            lines.append(f"Earns you the most: {most_profit['name']} (₱{most_profit['profit']:,.0f} profit).")
        if cur["voids"]:
            v = cur["voids"]
            items.append(("ban", "red", "Voids", f"{v} void{'s' if v != 1 else ''}  ·  ₱{cur['void_amt']:,.0f}",
                          "See Finance > Voids & Refunds for the reasons."))
            lines.append(f"{v} void{'s' if v != 1 else ''} (₱{cur['void_amt']:,.0f} returned). "
                         "See Finance > Voids & Refunds for the reasons.")
        self.highlights.set_items(items)
        self.data["insight_lines"] = lines

    def _day_chart(self):
        d = self.data
        days = [d["start"] + timedelta(days=i) for i in range(d["days"])]
        if len(days) > 31:
            days = days[-31:]
        labels = [x.strftime("%a %d") if len(days) <= 7 else x.strftime("%d") for x in days]
        vals = [round(d["by_day"].get(x.isoformat(), {"t": 0})["t"]) for x in days]
        self.day_chart.set_data(labels, [("Sales", vals, BROWN)], full_labels=[x.strftime("%A, %b %d") for x in days])
        if any(vals):
            i = max(range(len(vals)), key=lambda k: vals[k])
            avg = sum(vals) / len(vals)
            self.day_note.setText(f"Best day: <b>{days[i].strftime('%A, %b %d')}</b> (₱{vals[i]:,}).  "
                                  f"An average day: ₱{avg:,.0f}.")
        else:
            self.day_note.setText("No sales in this period.")

    def _hour_chart(self):
        bh = self.data["by_hour"]
        hours = list(range(min(list(bh) + [6]), max(list(bh) + [19]) + 1))
        vals = [round(bh[h]["c"] / self.data["days"], 1) if h in bh else 0 for h in hours]
        self.hour_chart.set_data([_hour_short(h) for h in hours], [("Customers a day", vals, "#C4873F")],
                                 full_labels=[f"{_hour_label(h)} – {_hour_label((h + 1) % 24)}: customers on an average day" for h in hours])
        if any(vals):
            i = max(range(len(vals)), key=lambda k: vals[k])
            self.hour_note.setText(f"Busiest hour: <b>{_hour_label(hours[i])} – {_hour_label((hours[i] + 1) % 24)}</b>, "
                                   f"about {vals[i]:g} customers on an average day.")
        else:
            self.hour_note.setText("No sales in this period.")

    def _cell(self, t, r, c, text, color=None, bold=False):
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if color:
            it.setForeground(QColor(color))
        if bold:
            it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        t.setItem(r, c, it)

    def _fill_products(self):
        prods = [p for p in self.data["prods"] if p["pcs"] or p["wasted"]]
        avg = sum(p["pcs"] for p in prods) / len(prods) if prods else 0
        t = self.tbl_products
        t.setRowCount(len(prods))
        for r, p in enumerate(prods):
            advice, color = self._advice(p, avg)
            p["advice"] = advice
            self._cell(t, r, 0, p["name"], bold=True)
            self._cell(t, r, 1, f"{p['pcs']:,.0f}")
            self._cell(t, r, 2, f"₱{p['sales']:,.2f}")
            self._cell(t, r, 3, f"₱{p['profit']:,.2f}" if p["unit_cost"] > 0 else "—", (GREEN if p["profit"] >= 0 else RED) if p["unit_cost"] > 0 else MID)
            self._cell(t, r, 4, f"{p['wasted']:,.0f}" if p["wasted"] else "—", RED if p["wasted"] else MID)
            self._cell(t, r, 5, advice, color, True)
        t.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

    def _fill_cashiers(self):
        t = self.tbl_cashiers
        rows = self.data["cashiers"]
        t.setRowCount(len(rows))
        for r, c in enumerate(rows):
            self._cell(t, r, 0, c["who"], bold=True)
            self._cell(t, r, 1, f"{c['customers']:,}")
            self._cell(t, r, 2, f"₱{c['sales']:,.2f}")
            self._cell(t, r, 3, f"₱{c['sales'] / c['customers']:,.2f}" if c["customers"] else "—")
            self._cell(t, r, 4, f"{c['voids']}", RED if c["voids"] else MID)
            self._cell(t, r, 5, f"₱{c['void_amt']:,.2f}" if c["void_amt"] else "—", RED if c["void_amt"] else MID)

    def _fill_money(self):
        cur = self.data["cur"]
        s, e = self.data["start"].isoformat(), self.data["end"].isoformat()
        from bakesync.modules.financial import guess_category
        cats = {}
        for r in self.db.fetch_all("SELECT expense_name, category, amount FROM operating_expenses "
                                   "WHERE date(expense_date) BETWEEN ? AND ?", (s, e)):
            k = r["category"] or guess_category(r["expense_name"])
            cats[k] = cats.get(k, 0) + (r["amount"] or 0)
        rows = [("Sales", cur["sales"], DARK, True),
                ("−  Cost of what was sold", -cur["cost"], MID, False)]
        rows += [(f"−  Expense: {k}", -v, MID, False) for k, v in sorted(cats.items(), key=lambda x: -x[1])]
        rows += [("=  Profit", cur["profit"], GREEN if cur["profit"] >= 0 else RED, True),
                 ("Bread and items wasted (cost, already inside 'Cost')", cur["waste_loss"], RED, False),
                 ("Money returned for voids (not counted in sales)", cur["void_amt"], MID, False)]
        self.data["money_rows"] = rows
        t = self.tbl_money
        t.setRowCount(len(rows))
        for r, (label, val, color, bold) in enumerate(rows):
            self._cell(t, r, 0, label, color if bold else None, bold)
            self._cell(t, r, 1, f"₱{val:,.2f}" if val >= 0 else f"-₱{-val:,.2f}", color, bold)

    # ── export ────────────────────────────────────────────────────────────
    def _file_stub(self):
        return f"BakeSync_Report_{self.data['start']:%Y%m%d}-{self.data['end']:%Y%m%d}"

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save report for Excel", f"{self._file_stub()}.csv", "CSV (*.csv)")
        if not path:
            return
        d = self.data
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["BakeSync Report", f"{d['start']:%Y-%m-%d} to {d['end']:%Y-%m-%d}"])
                w.writerow([])
                for label, val, *_ in d["money_rows"]:
                    w.writerow([label.replace("−", "-"), f"{val:.2f}"])
                w.writerow(["Customers", d["cur"]["customers"]])
                w.writerow(["Pieces sold", f"{d['cur']['pcs']:.0f}"])
                w.writerow([])
                w.writerow(["Product", "Pieces sold", "Sales", "Profit", "Wasted", "What to do"])
                for p in d["prods"]:
                    if p["pcs"] or p["wasted"]:
                        w.writerow([p["name"], f"{p['pcs']:.0f}", f"{p['sales']:.2f}", f"{p['profit']:.2f}",
                                    f"{p['wasted']:.0f}", p.get("advice", "")])
                w.writerow([])
                w.writerow(["Date", "Sales", "Customers"])
                for k in sorted(d["by_day"]):
                    w.writerow([k, f"{d['by_day'][k]['t']:.2f}", d["by_day"][k]["c"]])
                w.writerow([])
                w.writerow(["Cashier", "Customers", "Sales", "Voids", "Money voided"])
                for c in d["cashiers"]:
                    w.writerow([c["who"], c["customers"], f"{c['sales']:.2f}", c["voids"], f"{c['void_amt']:.2f}"])
            BakeSyncAlert.show_success(self, "Saved", f"The report was saved as:\n{os.path.basename(path)}\n\nYou can open it in Excel.")
        except OSError as e:
            BakeSyncAlert.show_error(self, "Could not save", f"The file could not be saved.\n\n{e}")

    def export_pdf(self):
        from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QMarginsF
        path, _ = QFileDialog.getSaveFileName(self, "Save report as PDF", f"{self._file_stub()}.pdf", "PDF (*.pdf)")
        if not path:
            return
        d, esc = self.data, html.escape
        cards = "".join(f"<td class='card'><div class='t'>{esc(t)}</div><div class='v'>{esc(self.cards[k][0].text())}</div>"
                        f"<div class='s'>{esc(self.cards[k][1].text())}</div></td>"
                        for k, t in (("sales", "Total sales"), ("profit", "Profit"), ("customers", "Customers"),
                                     ("avg", "Average per customer"), ("waste", "Wasted")))
        money = "".join(f"<tr><td>{esc(l)}</td><td align='right'>{'₱' if v >= 0 else '-₱'}{abs(v):,.2f}</td></tr>"
                        for l, v, *_ in d["money_rows"])
        prods = "".join(f"<tr><td>{esc(p['name'])}</td><td>{p['pcs']:,.0f}</td><td>₱{p['sales']:,.2f}</td>"
                        f"<td>₱{p['profit']:,.2f}</td><td>{p['wasted']:,.0f}</td><td>{esc(p.get('advice', ''))}</td></tr>"
                        for p in d["prods"] if p["pcs"] or p["wasted"])
        cash = "".join(f"<tr><td>{esc(c['who'])}</td><td>{c['customers']}</td><td>₱{c['sales']:,.2f}</td>"
                       f"<td>{c['voids']}</td><td>₱{c['void_amt']:,.2f}</td></tr>" for c in d["cashiers"])
        doc_html = f"""<html><head><style>
            body {{ font-family: 'Segoe UI'; color: #0F172A; font-size: 10pt; }}
            h1 {{ color: #693903; font-size: 18pt; margin: 0; }} h3 {{ color: #693903; font-size: 12pt; margin-top: 14px; }}
            .meta {{ color: #64748B; }} table {{ border-collapse: collapse; width: 100%; }}
            th {{ background: #6B3F27; color: white; padding: 5px; text-align: left; }}
            td {{ padding: 4px 5px; border-bottom: 1px solid #E5E7EB; }}
            td.card {{ border: 1px solid #E2E8F0; padding: 8px; width: 20%; vertical-align: top; }}
            .t {{ color: #64748B; }} .v {{ font-size: 13pt; font-weight: bold; }} .s {{ color: #64748B; font-size: 8pt; }}
        </style></head><body>
            <h1>BakeSync — Business Report</h1>
            <p class='meta'>{d['start']:%B %d, %Y} – {d['end']:%B %d, %Y} · Generated {datetime.now():%B %d, %Y %I:%M %p}</p>
            <table><tr>{cards}</tr></table>
            <h3>Highlights</h3><p>{'<br>'.join('• ' + esc(l) for l in d.get('insight_lines', []))}</p>
            <h3>Money summary</h3><table>{money}</table>
            <h3>Products</h3><table><tr><th>Product</th><th>Pcs sold</th><th>Sales</th><th>Profit</th><th>Wasted</th><th>What to do</th></tr>{prods}</table>
            <h3>Cashiers</h3><table><tr><th>Cashier</th><th>Customers</th><th>Sales</th><th>Voids</th><th>Money voided</th></tr>{cash}</table>
            <p class='meta'>Profit uses the cost per piece from Inventory/Pricing. Voided sales are not counted.</p>
        </body></html>"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
                                              QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter))
            doc = QTextDocument(); doc.setHtml(doc_html); doc.print(printer)
            BakeSyncAlert.show_success(self, "Saved", f"The report was saved as:\n{os.path.basename(path)}")
        except Exception as e:
            BakeSyncAlert.show_error(self, "Could not save", f"The PDF could not be saved.\n\n{e}")
