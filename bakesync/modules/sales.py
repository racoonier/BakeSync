from bakesync.paths import IMAGES_DIR
import os
import csv
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QScrollArea, QFileDialog, QDialog, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QByteArray, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, QMargins
from bakesync.widgets.ui import svg_pixmap as _ui_pix
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor, QIcon, QPixmap, QPainter
from bakesync.core.database import DatabaseManager


# ─────────────────────────────────────────────────────────────
#  MODAL DIALOG  (replaces all QMessageBox calls)
# ─────────────────────────────────────────────────────────────
class ToastNotification(QWidget):
    """Slim toast that slides in from the top-right and auto-dismisses."""

    def __init__(self, parent, message: str, kind: str = "success"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        colors = {
            "success": ("#10B981", "#D1FAE5", "✓"),
            "error":   ("#EF4444", "#FEE2E2", "✕"),
            "info":    ("#3B82F6", "#DBEAFE", "ℹ"),
        }
        accent, bg, icon = colors.get(kind, colors["info"])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1.5px solid {accent};
                border-radius: 10px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 45))
        card.setGraphicsEffect(shadow)

        inner = QHBoxLayout(card)
        inner.setContentsMargins(14, 12, 14, 12)
        inner.setSpacing(10)

        ico = QLabel(); ico.setPixmap(_ui_pix({"✓": "check_circle", "✕": "x_circle", "ℹ": "info", "⚠": "alert", "🔑": "key"}.get(icon, 'info'), accent, 20))
        ico.setStyleSheet(f"color: {accent}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        msg = QLabel(message)
        msg.setStyleSheet(f"color: #1e293b; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        msg.setWordWrap(True)
        msg.setMaximumWidth(320)

        inner.addWidget(ico)
        inner.addWidget(msg)
        outer.addWidget(card)

        self.adjustSize()
        self._reposition(parent)
        self.show()

        QTimer.singleShot(3200, self.close)

    def _reposition(self, parent):
        if parent:
            pr = parent.rect()
            pw = parent.mapToGlobal(pr.topLeft())
            x = pw.x() + pr.width() - self.width() - 24
            y = pw.y() + 24
            self.move(x, y)


class ModalDialog(QDialog):
    """Clean modal for confirmations, info and error messages."""

    def __init__(self, parent, title: str, body: str, kind: str = "info",
                 primary_label: str = "OK", show_cancel: bool = False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        palette = {
            "success": ("#10B981", "#D1FAE5", "✓"),
            "error":   ("#EF4444", "#FEE2E2", "✕"),
            "info":    ("#6B3F27", "#FEF3EC", "ℹ"),
            "warning": ("#F59E0B", "#FEF9C3", "⚠"),
        }
        accent, bg_light, icon_char = palette.get(kind, palette["info"])

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border-radius: 14px;
                border: 1.5px solid #E2E8F0;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)
        card.setMinimumWidth(380)

        vl = QVBoxLayout(card)
        vl.setContentsMargins(28, 28, 28, 24)
        vl.setSpacing(0)

        # Icon badge
        badge = QLabel(); badge.setPixmap(_ui_pix({"✓": "check_circle", "✕": "x_circle", "ℹ": "info", "⚠": "alert", "🔑": "key"}.get(icon_char, 'info'), accent, 22))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(54, 54)
        badge.setStyleSheet(f"""
            background: {bg_light};
            color: {accent};
            border-radius: 27px;
            font-size: 24px;
            font-weight: bold;
            border: none;
        """)
        vl.addWidget(badge, alignment=Qt.AlignmentFlag.AlignHCenter)
        vl.addSpacing(14)

        # Title
        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; border: none; background: transparent;")
        vl.addWidget(t)
        vl.addSpacing(8)

        # Body
        b = QLabel(body)
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b.setWordWrap(True)
        b.setStyleSheet("font-size: 13px; color: #475569; border: none; background: transparent;")
        vl.addWidget(b)
        vl.addSpacing(24)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        if show_cancel:
            cancel = QPushButton("Cancel")
            cancel.setFixedHeight(38)
            cancel.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    color: #475569;
                    padding: 0 20px;
                }
                QPushButton:hover { background: #E2E8F0; }
            """)
            cancel.clicked.connect(self.reject)
            btn_row.addWidget(cancel)

        ok = QPushButton(primary_label)
        ok.setFixedHeight(38)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                color: white;
                padding: 0 24px;
            }}
            QPushButton:hover {{ background: {accent}dd; }}
        """)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)

        vl.addLayout(btn_row)
        root.addWidget(card)
        self.adjustSize()

    @staticmethod
    def show_info(parent, title, body):
        d = ModalDialog(parent, title, body, kind="info")
        d.exec()

    @staticmethod
    def show_success(parent, title, body):
        d = ModalDialog(parent, title, body, kind="success")
        d.exec()

    @staticmethod
    def show_error(parent, title, body):
        d = ModalDialog(parent, title, body, kind="error")
        d.exec()


# ─────────────────────────────────────────────────────────────
#  MAIN WIDGET
# ─────────────────────────────────────────────────────────────
class SalesWidget(QWidget):
    """Sales overview: 4 key numbers, quick insights, best sellers and a day/month breakdown.
    Every number comes from the same period + category filter."""

    PERIODS = ["Today", "Yesterday", "Last 7 Days", "This Month", "Last Month", "This Year", "All Time"]

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.report = {}
        self.init_ui()

    # ── lifecycle ──────────────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        self.load_dashboard_data()

    def refresh_after_void(self):
        """Called automatically from POS after a void to keep sales figures accurate."""
        self.load_dashboard_data()

    # ── SVG helpers ────────────────────────────────────────────
    def _create_vector_icon(self, svg_string, color):
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode("utf-8")), "SVG")
        return QIcon(pixmap)

    def _create_vector_pixmap(self, svg_string, color, size=20):
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode("utf-8")), "SVG")
        return pixmap.scaled(size, size,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)

    # ── init_ui ────────────────────────────────────────────────
    def init_ui(self):
        from bakesync.widgets.ui import (THEME as T, StatCard, BarChart, intro_row, title_row, button as ui_button,
                                         svg_icon, InfoIcon, card as ui_card, RefreshButton, Highlights)
        from PyQt6.QtWidgets import QMenu
        self.c = {"brown": "#693903", "brown_mid": "#8B5A2B", "cream": T["cream"], "cream_2": "#F5ECE5", "white": "#FFFFFF",
                  "text_dark": T["text"], "text_mid": T["mid"], "border": T["line"], "green": T["green"], "red": T["red"]}
        self.setStyleSheet(f"background-color: {T['cream']};")
        root = QVBoxLayout(self); root.setContentsMargins(24, 14, 24, 14); root.setSpacing(12)

        # filters + save
        top = QHBoxLayout(); top.setSpacing(8)
        intro, _ = intro_row("", "Pick a period and what to include. Every number on this page follows that choice. "
                                 "Voided sales are never counted.", "Sales")
        self.lbl_period_text = intro.text_label
        self.lbl_period_text.setStyleSheet(f"color: {T['brown_dark']}; font-size: 15px; font-weight: 600;")
        top.addWidget(intro, 1)
        self.date_filter = QComboBox(); self.date_filter.addItems(self.PERIODS); self.date_filter.setCurrentText("Today")
        self.cat_filter = QComboBox(); self.cat_filter.addItems(["All Products", "Bread Only", "Retail Only"])
        for combo in (self.date_filter, self.cat_filter):
            combo.setCursor(Qt.CursorShape.PointingHandCursor)
            combo.setFixedHeight(38); combo.setMinimumWidth(150)
            combo.currentTextChanged.connect(self.load_dashboard_data)
            top.addWidget(combo)
        save = ui_button("Save report", "primary", icon="download", h=38)
        menu = QMenu(save)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #EADFD3; border-radius: 8px; padding: 4px; }"
                           "QMenu::item { padding: 8px 18px; border-radius: 6px; color: #1F2937; }"
                           "QMenu::item:selected { background: #F5ECE5; }")
        menu.addAction(svg_icon("file", "#A83535", 16), "Save as PDF").triggered.connect(self.export_pdf)
        menu.addAction(svg_icon("list", "#2F7A4B", 16), "Save for Excel").triggered.connect(self.export_csv)
        save.setMenu(menu)
        save.setStyleSheet(save.styleSheet() + " QPushButton { padding-right: 30px; }"
                           " QPushButton::menu-indicator { subcontrol-position: right center; subcontrol-origin: padding; right: 10px; }")
        top.addWidget(save)
        ref = RefreshButton()
        ref.clicked.connect(self.load_dashboard_data)
        top.addWidget(ref)
        root.addLayout(top)

        # everything below the filters scrolls as one page (no small boxes that scroll on their own)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}"
                             f"QScrollBar:vertical {{ width: 8px; background: transparent; margin: 2px; }}"
                             f"QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 4px; min-height: 40px; }}"
                             f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}")
        body = QWidget(); body.setObjectName("salesbody"); body.setStyleSheet(f"QWidget#salesbody {{ background: {T['cream']}; }}")
        page = QVBoxLayout(body); page.setContentsMargins(0, 0, 6, 0); page.setSpacing(12)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # four numbers
        cards = QHBoxLayout(); cards.setSpacing(12)
        self.c_sales = StatCard("Total sales", "wallet", "All the money from the POS in this period. "
                                "The coloured line compares it with the same length of time just before.", T["green"], T["green_bg"])
        self.c_profit = StatCard("Profit", "trend_up", "Sales minus what the sold items cost you (puhunan). "
                                 "'After waste' also takes away the cost of wasted pieces.", T["brown"], T["cream_dark"])
        self.c_waste = StatCard("Lost to waste", "trash", "What the bread and items thrown away cost you in this period.",
                                T["red"], T["red_bg"])
        self.c_avg = StatCard("Average sale", "cart", "How much one customer spends, on average. 'Biggest' is the largest single sale.",
                              T["blue"], T["blue_bg"])
        for c in (self.c_sales, self.c_profit, self.c_waste, self.c_avg):
            cards.addWidget(c)
        page.addLayout(cards)
        self.lbl_sales, self.lbl_sales_cmp = self.c_sales.value, self.c_sales.sub
        self.lbl_sales_sub = QLabel(""); self.lbl_sales_sub.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
        self.c_sales.layout().insertWidget(self.c_sales.layout().count() - 1, self.lbl_sales_sub)
        self.lbl_profit, self.lbl_profit_sub = self.c_profit.value, self.c_profit.sub
        self.lbl_waste, self.lbl_waste_sub = self.c_waste.value, self.c_waste.sub
        self.lbl_avg, self.lbl_avg_sub = self.c_avg.value, self.c_avg.sub

        # chart + plain words
        mid = QHBoxLayout(); mid.setSpacing(12)
        chart_card = ui_card(14, name="schart")
        cl = QVBoxLayout(chart_card); cl.setContentsMargins(16, 12, 16, 10); cl.setSpacing(4)
        self.chart_title_w, _ = title_row("Sales", icon="chart", size=13,
                                          info="Each bar is one hour, day or month (it depends on the period). A taller bar "
                                               "means more sales. The gold bar is the best one. Point at a bar to see the exact amount.")
        cl.addWidget(self.chart_title_w)
        self.chart_note = QLabel(""); self.chart_note.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
        cl.addWidget(self.chart_note)
        self.sales_bars = BarChart(money=True, empty_text="No sales in this period")
        cl.addWidget(self.sales_bars, 1)
        mid.addWidget(chart_card, 3)
        self.highlights = Highlights("Highlights", info="The most useful facts for this period, worked out from the numbers for you.",
                                     max_rows=4)
        mid.addWidget(self.highlights, 2)
        mid.setContentsMargins(0, 0, 0, 0)
        chart_row = QWidget(); chart_row.setObjectName("chartrow"); chart_row.setLayout(mid); chart_row.setFixedHeight(340)
        chart_row.setStyleSheet("QWidget#chartrow { background: transparent; }")
        page.addWidget(chart_row)

        # tables
        TABLE_STYLE = f"""
            QTableWidget {{ border: none; font-size: 13px; background: white; color: {T['text']}; gridline-color: transparent;
                            alternate-background-color: #FBF8F4; }}
            QHeaderView::section {{ background: {T['cream_dark']}; color: {T['brown']}; padding: 7px 10px; border: none; font-weight: bold; font-size: 12px; }}
            QTableWidget::item {{ padding: 4px 10px; border-bottom: 1px solid #F3F4F6; }}
            QTableWidget::item:selected {{ background: #FEF0E6; color: {T['text']}; }}
            QScrollBar:vertical {{ width: 6px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; }}
        """

        def make_table(headers, stretch_col):
            t = QTableWidget(); t.setColumnCount(len(headers)); t.setHorizontalHeaderLabels(headers)
            hh = t.horizontalHeader(); hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setSectionResizeMode(stretch_col, QHeaderView.ResizeMode.Stretch)
            t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            t.verticalHeader().setVisible(False); t.setShowGrid(False); t.setAlternatingRowColors(True)
            t.setStyleSheet(TABLE_STYLE)
            t.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            return t

        def titled(title, icon, info):
            f = ui_card(14, name="tc")
            v = QVBoxLayout(f); v.setContentsMargins(14, 10, 14, 10); v.setSpacing(6)
            w, _ = title_row(title, icon=icon, size=13, info=info)
            v.addWidget(w)
            return f, v, w.title_label

        bot = QHBoxLayout(); bot.setSpacing(12)
        top_card, top_vl, _ = titled("What sold best", "award", "Products ranked by sales in this period. 'Share' = part of all sales.")
        self.tbl_top = make_table(["#", "Item", "Pcs Sold", "Sales", "Share"], 1)
        top_vl.addWidget(self.tbl_top)
        top_vl.addStretch()
        brk_card, brk_vl, self.lbl_breakdown_title = titled("Day by Day", "calendar",
                                                            "Totals for each day (or month, for long periods), newest first.")
        self.tbl_breakdown = make_table(["Date", "Customers", "Pcs Sold", "Sales", "Profit", "Waste Loss", "Cashier"], 6)
        bh = self.tbl_breakdown.horizontalHeader()
        bh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        bh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch); bh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        brk_vl.addWidget(self.tbl_breakdown)
        brk_vl.addStretch()
        bot.addWidget(top_card, 2)
        bot.addWidget(brk_card, 3)
        page.addLayout(bot)
        page.addStretch()

    def _fit_table(self, table, empty_text):
        """Show every row (the page scrolls instead of the table). An empty table shows one muted line."""
        if table.rowCount() == 0:
            table.setRowCount(1); table.setSpan(0, 0, 1, table.columnCount())
            it = self._c_item(empty_text, self.c["text_mid"]); it.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(0, 0, it); table.setRowHeight(0, 44)
            table.setProperty("empty", True)
        else:
            table.setProperty("empty", False)
        h = table.horizontalHeader().sizeHint().height() + sum(table.rowHeight(r) for r in range(table.rowCount())) + 4
        table.setFixedHeight(h)

    # ══════════════════════════════════════════════════════════
    # PERIOD & FILTER HELPERS
    # ══════════════════════════════════════════════════════════
    @staticmethod
    def _shift_months(d, months):
        m = d.month - 1 + months
        y = d.year + m // 12
        m = m % 12 + 1
        last_day = [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        return d.replace(year=y, month=m, day=min(d.day, last_day))

    def _period(self, name, today=None):
        """(start, end, previous_start, previous_end, compare_label) as dates, end exclusive.
        Returns Nones for "All Time"."""
        today = today or date.today()
        one = timedelta(days=1)
        if name == "Today":
            s, e = today, today + one
            return s, e, s - one, s, "vs yesterday"
        if name == "Yesterday":
            s, e = today - one, today
            return s, e, s - one, s, "vs the day before"
        if name == "Last 7 Days":
            s, e = today - 6 * one, today + one
            return s, e, s - 7 * one, s, "vs the 7 days before"
        if name == "This Month":
            s, e = today.replace(day=1), today + one
            ps = self._shift_months(s, -1)
            return s, e, ps, min(ps + (e - s), s), "vs same days last month"
        if name == "Last Month":
            first_this = today.replace(day=1)
            s = self._shift_months(first_this, -1)
            ps = self._shift_months(first_this, -2)
            return s, first_this, ps, s, "vs the month before"
        if name == "This Year":
            s, e = today.replace(month=1, day=1), today + one
            ps = s.replace(year=s.year - 1)
            return s, e, ps, ps + (e - s), "vs same days last year"
        return None, None, None, None, ""

    def _cat_sql(self):
        cat = self.cat_filter.currentText()
        if cat == "Bread Only":
            return "p.product_type = 'bread'"
        if cat == "Retail Only":
            return "COALESCE(p.product_type, '') != 'bread'"
        return "1=1"

    def _range_sql(self, column, start, end):
        if start is None:
            return "1=1", ()
        return f"{column} >= ? AND {column} < ?", (start.isoformat(), end.isoformat())

    def _sales_totals(self, start, end):
        rng, params = self._range_sql("s.created_at", start, end)
        return self.db.fetch_one(f"""
            SELECT COALESCE(SUM(s.amount), 0) AS sales,
                   COALESCE(SUM(s.quantity * COALESCE(p.production_cost, 0)), 0) AS cost,
                   COALESCE(SUM(s.quantity), 0) AS pcs,
                   COUNT(DISTINCT s.created_at) AS txns
            FROM sales s JOIN products p ON s.product_id = p.id
            WHERE COALESCE(s.is_voided, 0) = 0 AND {self._cat_sql()} AND {rng}
        """, params)

    # ══════════════════════════════════════════════════════════
    # DATA LOADING
    # ══════════════════════════════════════════════════════════
    def load_dashboard_data(self):
        period = self.date_filter.currentText()
        start, end, pstart, pend, cmp_label = self._period(period)
        cat = self._cat_sql()
        s_rng, s_par = self._range_sql("s.created_at", start, end)
        w_rng, w_par = self._range_sql("w.created_at", start, end)
        base = f"COALESCE(s.is_voided, 0) = 0 AND {cat} AND {s_rng}"

        if start is None:
            self.lbl_period_text.setText("All recorded sales")
        elif end - start == timedelta(days=1):
            self.lbl_period_text.setText(start.strftime("%A, %B %d, %Y").replace(" 0", " "))
        else:
            last = end - timedelta(days=1)
            self.lbl_period_text.setText(f"{start.strftime('%b %d, %Y')} – {last.strftime('%b %d, %Y')}".replace(" 0", " "))

        # ── Key numbers ──
        t = self._sales_totals(start, end)
        sales, cost, pcs, txns = t["sales"], t["cost"], t["pcs"], t["txns"]
        profit = sales - cost
        margin = profit / sales * 100 if sales > 0 else 0
        waste = self.db.fetch_one(f"""
            SELECT COALESCE(SUM(w.quantity), 0) AS pcs,
                   COALESCE(SUM(w.quantity * COALESCE(p.production_cost, 0)), 0) AS loss
            FROM waste_logs w JOIN products p ON w.product_id = p.id
            WHERE {cat} AND {w_rng}
        """, w_par)
        txn_rows = self.db.fetch_all(f"""
            SELECT SUM(s.amount) AS total FROM sales s JOIN products p ON s.product_id = p.id
            WHERE {base} GROUP BY s.created_at
        """, s_par)
        txn_totals = [r["total"] for r in txn_rows]
        avg_sale = sum(txn_totals) / len(txn_totals) if txn_totals else 0
        biggest = max(txn_totals) if txn_totals else 0

        self.lbl_sales.setText(f"₱{sales:,.2f}")
        self.lbl_sales_sub.setText(f"{txns:,} transaction{'s' if txns != 1 else ''} · {pcs:,.0f} pcs sold")
        cmp_text, cmp_color = "", self.c["text_mid"]
        if pstart is not None:
            prev = self._sales_totals(pstart, pend)["sales"]
            if prev > 0:
                change = (sales - prev) / prev * 100
                cmp_text = f"{'Up' if change >= 0 else 'Down'} {abs(change):.0f}% {cmp_label} (₱{prev:,.0f})"
                cmp_color = self.c["green"] if change >= 0 else self.c["red"]
            else:
                cmp_text = f"Nothing to compare {cmp_label.replace('vs ', 'with ')}"
        self.lbl_sales_cmp.setText(cmp_text)
        self.lbl_sales_cmp.setStyleSheet(f"color: {cmp_color}; font-size: 11px; font-weight: 600;")

        self.lbl_profit.setText(f"₱{profit:,.2f}")
        self.lbl_profit.setStyleSheet(f"color: {self.c['green'] if profit >= 0 else self.c['red']};")
        after_waste = profit - waste["loss"]
        self.lbl_profit_sub.setText(f"Margin {margin:.0f}% · ₱{after_waste:,.2f} after waste")

        self.lbl_waste.setText(f"₱{waste['loss']:,.2f}")
        self.lbl_waste.setStyleSheet(f"color: {self.c['red'] if waste['loss'] > 0 else self.c['text_dark']};")
        self.lbl_waste_sub.setText(f"{waste['pcs']:,.0f} pcs at cost" + (f" · {waste['loss'] / sales * 100:.1f}% of sales" if sales > 0 else ""))

        self.lbl_avg.setText(f"₱{avg_sale:,.2f}")
        self.lbl_avg_sub.setText(f"per transaction · biggest ₱{biggest:,.2f}" if biggest else "per transaction")

        # ── What sold best ──
        top = self.db.fetch_all(f"""
            SELECT p.name, SUM(s.quantity) AS qty, SUM(s.amount) AS sales
            FROM sales s JOIN products p ON s.product_id = p.id
            WHERE {base} GROUP BY p.id ORDER BY sales DESC LIMIT 10
        """, s_par)
        self.tbl_top.clearSpans()
        self.tbl_top.setRowCount(len(top))
        for r, row in enumerate(top):
            share = row["sales"] / sales * 100 if sales > 0 else 0
            self.tbl_top.setItem(r, 0, self._c_item(f"{r + 1}", self.c["brown"]))
            self.tbl_top.setItem(r, 1, self._c_item(row["name"], align=Qt.AlignmentFlag.AlignLeft))
            self.tbl_top.setItem(r, 2, self._c_item(f"{row['qty']:,.0f}"))
            self.tbl_top.setItem(r, 3, self._c_item(f"₱{row['sales']:,.2f}", self.c["green"]))
            self.tbl_top.setItem(r, 4, self._c_item(f"{share:.0f}%"))
            self.tbl_top.setRowHeight(r, 34)

        # ── Breakdown: by day for short periods, by month for year / all time ──
        by_month = period in ("This Year", "All Time")
        self.lbl_breakdown_title.setText("Month by Month" if by_month else "Day by Day")
        self.tbl_breakdown.horizontalHeaderItem(0).setText("Month" if by_month else "Date")
        self.tbl_breakdown.setColumnHidden(6, by_month)
        bh = self.tbl_breakdown.horizontalHeader()
        bh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch if by_month else QHeaderView.ResizeMode.ResizeToContents)
        bh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents if by_month else QHeaderView.ResizeMode.Stretch)
        bucket = "strftime('%Y-%m', {col})" if by_month else "date({col})"
        s_bucket, w_bucket = bucket.format(col="s.created_at"), bucket.format(col="w.created_at")
        rows = self.db.fetch_all(f"""
            SELECT {s_bucket} AS bucket,
                   COUNT(DISTINCT s.created_at) AS txns,
                   SUM(s.quantity) AS pcs,
                   SUM(s.amount) AS sales,
                   SUM(s.amount) - SUM(s.quantity * COALESCE(p.production_cost, 0)) AS profit,
                   GROUP_CONCAT(DISTINCT COALESCE(s.cashier, 'Unknown')) AS cashiers
            FROM sales s JOIN products p ON s.product_id = p.id
            WHERE {base} GROUP BY bucket ORDER BY bucket DESC
        """, s_par)
        waste_by = {r["bucket"]: r["loss"] for r in self.db.fetch_all(f"""
            SELECT {w_bucket} AS bucket, SUM(w.quantity * COALESCE(p.production_cost, 0)) AS loss
            FROM waste_logs w JOIN products p ON w.product_id = p.id
            WHERE {cat} AND {w_rng} GROUP BY bucket
        """, w_par)}
        self.tbl_breakdown.clearSpans()
        self.tbl_breakdown.setRowCount(len(rows))
        for r, row in enumerate(rows):
            if by_month:
                label = datetime.strptime(row["bucket"], "%Y-%m").strftime("%B %Y")
            else:
                label = datetime.strptime(row["bucket"], "%Y-%m-%d").strftime("%a, %b %d").replace(" 0", " ")
            loss = waste_by.get(row["bucket"], 0) or 0
            self.tbl_breakdown.setItem(r, 0, self._c_item(label, align=Qt.AlignmentFlag.AlignLeft))
            self.tbl_breakdown.setItem(r, 1, self._c_item(f"{row['txns']:,}"))
            self.tbl_breakdown.setItem(r, 2, self._c_item(f"{row['pcs']:,.0f}"))
            self.tbl_breakdown.setItem(r, 3, self._c_item(f"₱{row['sales']:,.2f}", self.c["green"]))
            self.tbl_breakdown.setItem(r, 4, self._c_item(f"₱{row['profit']:,.2f}", self.c["green"] if row["profit"] >= 0 else self.c["red"]))
            self.tbl_breakdown.setItem(r, 5, self._c_item(f"₱{loss:,.2f}" if loss else "—", self.c["red"] if loss else self.c["text_mid"]))
            self.tbl_breakdown.setItem(r, 6, self._c_item((row["cashiers"] or "Unknown").replace(",", ", "), self.c["brown"]))
            self.tbl_breakdown.setRowHeight(r, 34)
        self._fit_table(self.tbl_top, "No sales in this period yet.")
        self._fit_table(self.tbl_breakdown, "No sales in this period yet.")

        # ── Highlights ──
        items, insights = [], []
        if top:
            best = top[0]
            share = best["sales"] / sales * 100 if sales else 0
            items.append(("award", "gold", "Best seller", best["name"],
                          f"{best['qty']:,.0f} pcs  ·  ₱{best['sales']:,.2f}  ·  {share:.0f}% of sales"))
            insights.append(f"Best seller: {best['name']} — {best['qty']:,.0f} pcs, ₱{best['sales']:,.2f} ({share:.0f}% of sales)")
        hour = self.db.fetch_one(f"""
            SELECT strftime('%H', s.created_at) AS hr, SUM(s.amount) AS sales, COUNT(DISTINCT s.created_at) AS txns
            FROM sales s JOIN products p ON s.product_id = p.id
            WHERE {base} GROUP BY hr ORDER BY sales DESC LIMIT 1
        """, s_par)
        if hour and hour["hr"] is not None:
            h = int(hour["hr"])
            fmt = lambda x: datetime(2000, 1, 1, x % 24).strftime("%I %p").lstrip("0")
            n = hour["txns"]
            items.append(("clock", "blue", "Busiest time", f"{fmt(h)} – {fmt(h + 1)}",
                          f"₱{hour['sales']:,.2f} from {n:,} customer{'s' if n != 1 else ''}. Have bread ready by then."))
            insights.append(f"Busiest time: {fmt(h)} – {fmt(h + 1)} — ₱{hour['sales']:,.2f} from {n:,} transaction{'s' if n != 1 else ''}")
        if len(rows) > 1:
            best_b = max(rows, key=lambda x: x["sales"])
            if by_month:
                when = datetime.strptime(best_b["bucket"], "%Y-%m").strftime("%B %Y")
            else:
                when = datetime.strptime(best_b["bucket"], "%Y-%m-%d").strftime("%A, %b %d").replace(" 0", " ")
            unit = "month" if by_month else "day"
            items.append(("calendar", "green", f"Best {unit}", when, f"₱{best_b['sales']:,.2f} in sales"))
            insights.append(f"Best {unit}: {when} — ₱{best_b['sales']:,.2f}")
        most_wasted = self.db.fetch_one(f"""
            SELECT p.name, SUM(w.quantity) AS pcs, SUM(w.quantity * COALESCE(p.production_cost, 0)) AS loss
            FROM waste_logs w JOIN products p ON w.product_id = p.id
            WHERE {cat} AND {w_rng} GROUP BY p.id ORDER BY loss DESC, pcs DESC LIMIT 1
        """, w_par)
        if most_wasted and most_wasted["pcs"]:
            items.append(("trash", "red", "Most wasted", most_wasted["name"],
                          f"{most_wasted['pcs']:,.0f} pcs (₱{most_wasted['loss']:,.2f}). Think about making fewer."))
            insights.append(f"Most wasted: {most_wasted['name']} — {most_wasted['pcs']:,.0f} pcs (₱{most_wasted['loss']:,.2f}). "
                            "Consider baking fewer of this.")
        self.highlights.set_items(items)
        if not insights:
            insights.append("No sales recorded for this period yet.")
        self._update_chart(period, by_month, rows, base, s_par)

        # Kept for CSV / PDF export
        self.report = {
            "period": self.date_filter.currentText(), "category": self.cat_filter.currentText(),
            "period_text": self.lbl_period_text.text(),
            "numbers": [
                ("Total Sales", self.lbl_sales.text(), self.lbl_sales_sub.text(), self.lbl_sales_cmp.text()),
                ("Profit", self.lbl_profit.text(), self.lbl_profit_sub.text(), ""),
                ("Lost to Waste", self.lbl_waste.text(), self.lbl_waste_sub.text(), ""),
                ("Average Sale", self.lbl_avg.text(), self.lbl_avg_sub.text(), ""),
            ],
            "insights": insights,
        }

    def _update_chart(self, period, by_month, rows, base, s_par):
        """Sales per hour (single day), per day, or per month."""
        start, end, *_ = self._period(period)
        single_day = start is not None and end - start == timedelta(days=1)
        hour = lambda h: datetime(2000, 1, 1, h % 24).strftime("%I %p").lstrip("0")
        if single_day:
            data = self.db.fetch_all(f"""
                SELECT CAST(strftime('%H', s.created_at) AS INTEGER) AS hr, SUM(s.amount) AS sales
                FROM sales s JOIN products p ON s.product_id = p.id
                WHERE {base} GROUP BY hr ORDER BY hr
            """, s_par)
            by_hr = {r["hr"]: r["sales"] for r in data}
            hours = list(range(min(list(by_hr) + [6]), min(max(list(by_hr) + [18]), 23) + 1))
            labels = [hour(h).replace(" ", "").lower() for h in hours]
            full = [f"{hour(h)} – {hour(h + 1)}" for h in hours]
            values = [by_hr.get(h, 0) for h in hours]
            title = "Sales by hour"
        else:
            ordered = list(reversed(rows))[-31:]
            src = "%Y-%m" if by_month else "%Y-%m-%d"
            dts = [datetime.strptime(r["bucket"], src) for r in ordered]
            labels = [d.strftime("%b") if by_month else (d.strftime("%a %d") if len(dts) <= 7 else d.strftime("%d")) for d in dts]
            full = [d.strftime("%B %Y") if by_month else d.strftime("%A, %b %d") for d in dts]
            values = [r["sales"] for r in ordered]
            title = "Sales by month" if by_month else "Sales by day"
        self.chart_title_w.title_label.setText(title)
        self.sales_bars.set_data(labels, [("Sales", values, "#8B5A2B")], full_labels=full)
        if values and any(values):
            i = max(range(len(values)), key=lambda k: values[k])
            avg = sum(values) / len([v for v in values if v]) if any(values) else 0
            unit = "hour" if single_day else ("month" if by_month else "day")
            self.chart_note.setText(f"Best {unit}: {full[i]} (₱{values[i]:,.0f})   ·   An average {unit} with sales: ₱{avg:,.0f}")
        else:
            self.chart_note.setText("No sales in this period yet.")

    # ══════════════════════════════════════════════════════════
    # TABLE CELL HELPER
    # ══════════════════════════════════════════════════════════
    def _c_item(self, text, color=None, align=Qt.AlignmentFlag.AlignCenter):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        if color:
            item.setForeground(QBrush(QColor(color)))
        return item

    def _table_rows(self, table):
        cols = [c for c in range(table.columnCount()) if not table.isColumnHidden(c)]
        headers = [table.horizontalHeaderItem(i).text() for i in cols]
        if table.property("empty"):
            return headers, []
        rows = [[table.item(r, c).text() if table.item(r, c) else "" for c in cols]
                for r in range(table.rowCount())]
        return headers, rows

    # ══════════════════════════════════════════════════════════
    # EXPORT — CSV
    # ══════════════════════════════════════════════════════════
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Sales Report",
            f"BakeSync_Sales_{self.report.get('period', '').replace(' ', '')}_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["BakeSync — Sales Report"])
                w.writerow([f"Period: {self.report['period']} ({self.report['period_text']})", f"Products: {self.report['category']}"])
                w.writerow([f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}"])
                w.writerow([])
                w.writerow(["KEY NUMBERS"])
                for name, value, sub, extra in self.report["numbers"]:
                    w.writerow([name, value, sub, extra])
                w.writerow([])
                w.writerow(["QUICK INSIGHTS"])
                for line in self.report["insights"]:
                    w.writerow([line])
                for title, table in (("WHAT SOLD BEST", self.tbl_top), (self.lbl_breakdown_title.text().upper(), self.tbl_breakdown)):
                    w.writerow([])
                    w.writerow([title])
                    headers, rows = self._table_rows(table)
                    w.writerow(headers)
                    w.writerows(rows)
            ToastNotification(self, f"Saved {os.path.basename(path)}", kind="success")
        except Exception as e:
            ModalDialog.show_error(self, "Export Failed", f"Could not save the file.\n\n{e}")

    # ══════════════════════════════════════════════════════════
    # EXPORT — PDF
    # ══════════════════════════════════════════════════════════
    def export_pdf(self):
        from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QMarginsF
        import html

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Sales Report as PDF",
            f"BakeSync_Sales_{self.report.get('period', '').replace(' ', '')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF Files (*.pdf)")
        if not path:
            return
        esc = html.escape

        def table_html(title, table):
            headers, rows = self._table_rows(table)
            head = "".join(f"<th>{esc(h)}</th>" for h in headers)
            body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows) \
                or f"<tr><td colspan='{len(headers)}'>No data</td></tr>"
            return f"<h3>{esc(title)}</h3><table><tr>{head}</tr>{body}</table>"

        numbers = "".join(
            f"<td class='card'><div class='t'>{esc(n)}</div><div class='v'>{esc(v)}</div>"
            f"<div class='s'>{esc(s)}</div><div class='s'>{esc(x)}</div></td>"
            for n, v, s, x in self.report["numbers"])
        doc_html = f"""
        <html><head><style>
            body {{ font-family: 'Segoe UI'; color: #0F172A; font-size: 10pt; }}
            h1 {{ color: #693903; font-size: 18pt; margin: 0; }}
            h3 {{ color: #693903; font-size: 12pt; margin-top: 16px; }}
            .meta {{ color: #64748B; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th {{ background: #6B3F27; color: white; padding: 5px; text-align: left; }}
            td {{ padding: 5px; border-bottom: 1px solid #E5E7EB; }}
            td.card {{ border: 1px solid #E2E8F0; padding: 8px; width: 25%; vertical-align: top; }}
            .t {{ color: #64748B; }} .v {{ font-size: 14pt; font-weight: bold; }} .s {{ color: #64748B; font-size: 8pt; }}
        </style></head><body>
            <h1>BakeSync — Sales Report</h1>
            <p class='meta'>{esc(self.report['period'])} ({esc(self.report['period_text'])}) · {esc(self.report['category'])}
            · Generated {datetime.now().strftime('%B %d, %Y %I:%M %p')}</p>
            <table><tr>{numbers}</tr></table>
            <h3>Quick Insights</h3><p>{'<br>'.join(esc(i) for i in self.report['insights'])}</p>
            {table_html('What Sold Best', self.tbl_top)}
            {table_html(self.lbl_breakdown_title.text(), self.tbl_breakdown)}
            <p class='meta'>Profit and waste use the cost per piece set in Pricing. Voided sales are not counted.</p>
        </body></html>"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
                                              QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter))
            doc = QTextDocument()
            doc.setHtml(doc_html)
            doc.print(printer)
            ToastNotification(self, f"Saved {os.path.basename(path)}", kind="success")
        except Exception as e:
            ModalDialog.show_error(self, "Export Failed", f"Could not save the PDF.\n\n{e}")
