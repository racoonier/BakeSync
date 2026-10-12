"""Pricing page: set the selling price of each bread and retail item.

The cost per piece is already entered in Inventory, so here you only type the
selling price and the profit is worked out for you."""
import math

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
                             QDoubleSpinBox, QFrame, QAbstractSpinBox, QHeaderView,
                             QTabWidget, QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtCore import Qt, QSize, QByteArray
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap

from bakesync.core.database import DatabaseManager
from bakesync.core.audit import log_activity
from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.ui import InfoIcon

BROWN, BROWN_DARK, MID, GREEN, RED, AMBER = "#6B3F27", "#693903", "#64748B", "#047857", "#B91C1C", "#B45309"
LOW_PROFIT = 15          # % of the selling price; below this the row is flagged


def _icon(svg, color):
    pix = QPixmap()
    pix.loadFromData(QByteArray(svg.replace("currentColor", color).encode("utf-8")), "SVG")
    return QIcon(pix)


EDIT_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>'
            '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>')
ARCHIVE_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
               'stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/>'
               '<rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>')
BREAD_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a5 5 0 0 1 5-5h8a5 5 0 0 1 5 5v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6z"/>'
             '<line x1="7" y1="7" x2="7" y2="3"/><line x1="12" y1="7" x2="12" y2="2"/><line x1="17" y1="7" x2="17" y2="3"/></svg>')
BAG_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>'
           '<line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>')

TABLE_STYLE = """
    QTableWidget { border: none; font-family: 'Segoe UI'; font-size: 13px; background-color: transparent; color: #1F2937; }
    QHeaderView::section { background-color: #6B3F27; padding: 12px 15px; border: none; font-weight: 700;
                           color: #FFFFFF; font-size: 12px; }
    QTableWidget::item { padding: 10px 15px; border-bottom: 1px solid #F3F4F6; }
    QTableWidget::item:hover { background-color: #FBF6F1; }
    QScrollBar:vertical { background: transparent; width: 6px; margin: 0px; }
    QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 3px; min-height: 30px; }
"""
TAB_STYLE = """
    QTabWidget::pane { border: 1px solid #E5E7EB; background: white; border-radius: 8px; border-top-left-radius: 0px; }
    QTabBar::tab { background: #F9FAFB; color: #6B7280; font-family: 'Segoe UI'; font-size: 13px; font-weight: 600;
                   padding: 12px 25px; border: 1px solid #E5E7EB; border-bottom: none;
                   border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
    QTabBar::tab:selected { background: #6B3F27; color: #FFFFFF; }
    QTabBar::tab:hover:!selected { background: #F3F4F6; color: #4B5563; }
"""


def _profit_text(price, cost):
    """(text, color) for the Profit column."""
    if price <= 0:
        return "—", MID
    if cost <= 0:
        return "Add the puhunan", AMBER
    profit = price - cost
    if profit < 0:
        return f"Loss ₱{-profit:,.2f}", RED
    pct = profit / price * 100
    return f"+₱{profit:,.2f}", (AMBER if pct < LOW_PROFIT else GREEN)


class RecipeWidget(QWidget):
    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.kind = "bread"
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_recipes()

    def init_ui(self):
        from bakesync.widgets.ui import THEME as T, StatCard, intro_row, legend_row, button as ui_button, svg_pixmap
        self.T = T
        self.setStyleSheet(f"background: {T['cream']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 16, 28, 16)

        top = QHBoxLayout(); top.setSpacing(8)
        intro, _ = intro_row("Set the puhunan and patong of each product. The selling price and tubo are worked out for you.",
                             "Puhunan = what one piece costs you.  Patong = how much you add on top.  "
                             "Selling price = puhunan + patong.  Your tubo (profit) per piece is the patong.  "
                             "Click any row to change it.", "How pricing works")
        top.addWidget(intro, 1)
        sbox = QFrame(); sbox.setObjectName("sbox"); sbox.setFixedHeight(38); sbox.setMinimumWidth(240)
        sbox.setStyleSheet(f"QFrame#sbox {{ background: white; border: 1px solid {T['line']}; border-radius: 10px; }}"
                           f"QFrame#sbox:hover {{ border-color: {T['brown']}; }}")
        sl = QHBoxLayout(sbox); sl.setContentsMargins(10, 0, 6, 0); sl.setSpacing(6)
        ic = QLabel(); ic.setPixmap(svg_pixmap("search", T["muted"], 16)); ic.setStyleSheet("background: transparent; border: none;")
        sl.addWidget(ic)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search a product...")
        self.search.setClearButtonEnabled(True)
        self.search.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 13px; color: {T['text']}; }}")
        self.search.textChanged.connect(self.load_recipes)
        sl.addWidget(self.search)
        top.addWidget(sbox)
        arch = ui_button("Archived products", "secondary", icon="box", h=38)
        arch.setToolTip("Products hidden from the POS. Open to restore one.")
        arch.clicked.connect(self.show_archived_recipes)
        self.arch_btn = arch
        top.addWidget(arch)
        layout.addLayout(top)

        cards = QHBoxLayout(); cards.setSpacing(12)
        self.c_count = StatCard("Products", "tag", "How many bread and retail products are for sale.", T["brown"], T["cream_dark"])
        self.c_avg = StatCard("Average tubo", "trend_up", "On average, how much you earn on one piece (the patong), "
                              "and what part of the selling price that is.", T["green"], T["green_bg"])
        self.c_low = StatCard("Small patong", "alert", f"Products where the tubo is under {LOW_PROFIT}% of the selling price. "
                              "Think about a bigger patong.", T["amber"], T["amber_bg"])
        self.c_missing = StatCard("Needs a price", "x_circle", "Products with no puhunan or no selling price yet. "
                                  "Click them below to set it.", T["red"], T["red_bg"])
        for c in (self.c_count, self.c_avg, self.c_low, self.c_missing):
            cards.addWidget(c)
        layout.addLayout(cards)

        box = QFrame(); box.setObjectName("pbox")
        box.setStyleSheet(f"QFrame#pbox {{ background: white; border: 1px solid {T['line']}; border-radius: 14px; }}")
        bl = QVBoxLayout(box); bl.setContentsMargins(14, 12, 14, 10); bl.setSpacing(8)
        bar = QHBoxLayout(); bar.setSpacing(6)
        self.kind_btns = {}
        for key in ("bread", "retail"):
            b = QPushButton(); b.setCheckable(True); b.setFixedHeight(34); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setIcon(_icon(BREAD_SVG if key == "bread" else BAG_SVG, T["brown"])); b.setIconSize(QSize(16, 16))
            b.setStyleSheet(f"QPushButton {{ background: white; color: {T['mid']}; border: 1px solid {T['line']}; border-radius: 17px; "
                            f"padding: 0 16px; font-size: 13px; font-weight: 600; }}"
                            f"QPushButton:checked {{ background: {T['brown']}; color: white; border-color: {T['brown']}; }}")
            b.clicked.connect(lambda _, k=key: self._set_kind(k))
            bar.addWidget(b); self.kind_btns[key] = b
        bar.addStretch()
        bar.addWidget(legend_row([(T["green"], "Good tubo"), (T["amber"], "Small patong"), (T["red"], "Loss / no puhunan")]))
        bl.addLayout(bar)
        self.table = self._make_table()
        bl.addWidget(self.table, 1)
        hint = QLabel("Click a row to change its price.")
        hint.setStyleSheet(f"color: {T['muted']}; font-size: 12px; background: transparent;")
        bl.addWidget(hint)
        layout.addWidget(box, 1)
        self._set_kind("bread", load=False)
        self.load_recipes()

    def _make_table(self):
        T = self.T
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["Product", "Puhunan (cost)", "Patong (tubo)", "Selling price", "Last changed by"])
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet(f"""
            QTableWidget {{ border: none; font-size: 13px; background: white; color: {T['text']}; gridline-color: transparent; }}
            QHeaderView::section {{ background: {T['cream_dark']}; color: {T['brown']}; padding: 9px 10px; border: none;
                                    font-weight: bold; font-size: 12px; }}
            QTableWidget::item {{ padding: 4px 10px; border-bottom: 1px solid #F3F4F6; }}
            QTableWidget::item:hover {{ background: {T['cream']}; }}
            QScrollBar:vertical {{ width: 6px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; }}
        """)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.setMouseTracking(True)
        t.setIconSize(QSize(18, 18))
        t.setCursor(Qt.CursorShape.PointingHandCursor)
        t.cellClicked.connect(lambda r, c: self._edit_row(r))
        return t

    def _set_kind(self, kind, load=True):
        self.kind = kind
        for k, b in self.kind_btns.items():
            b.setChecked(k == kind)
            b.setIcon(_icon(BREAD_SVG if k == "bread" else BAG_SVG, "#FFFFFF" if k == kind else self.T["brown"]))
        if load:
            self.load_recipes()

    def load_recipes(self):
        T = self.T
        like = f"%{self.search.text().strip()}%"
        rows = self.db.fetch_all(
            "SELECT id, name, retail_price, production_cost, product_type FROM products "
            "WHERE is_archived = 0 AND name LIKE ? ORDER BY name", (like,))
        breads = [r for r in rows if r["product_type"] == "bread"]
        retails = [r for r in rows if r["product_type"] != "bread"]
        self.kind_btns["bread"].setText(f"  Bread ({len(breads)})")
        self.kind_btns["retail"].setText(f"  Retail items ({len(retails)})")
        n_arch = self.db.fetch_one("SELECT COUNT(*) FROM products WHERE is_archived = 1")[0]
        self.arch_btn.setText(f"  Archived products ({n_arch})" if n_arch else "  Archived products")
        self._fill(breads if self.kind == "bread" else retails)

        allr = self.db.fetch_all("SELECT retail_price AS p, production_cost AS c FROM products WHERE is_archived = 0")
        priced = [r for r in allr if (r["p"] or 0) > 0 and (r["c"] or 0) > 0]
        missing = len(allr) - len(priced)
        low = sum(1 for r in priced if (r["p"] - r["c"]) / r["p"] * 100 < LOW_PROFIT)
        n_b = self.db.fetch_one("SELECT COUNT(*) FROM products WHERE is_archived = 0 AND product_type = 'bread'")[0]
        self.c_count.set(f"{len(allr)}", f"{n_b} bread  ·  {len(allr) - n_b} retail")
        if priced:
            avg = sum(r["p"] - r["c"] for r in priced) / len(priced)
            pct = sum((r["p"] - r["c"]) / r["p"] * 100 for r in priced) / len(priced)
            self.c_avg.set(f"₱{avg:,.2f}", f"per piece  ·  {pct:.0f}% of the price", value_color=T["green"])
        else:
            self.c_avg.set("—", "Set the puhunan of your products first")
        self.c_low.set(f"{low}", "All good" if not low else "Think about a bigger patong",
                       T["green"] if not low else T["amber"], T["amber"] if low else None)
        self.c_missing.set(f"{missing}", "All products have a price" if not missing else "Click them below to set it",
                           T["green"] if not missing else T["red"], T["red"] if missing else None)

    def _fill(self, products):
        T = self.T
        t = self.table
        t.clearSpans()
        t.setRowCount(len(products))
        if not products:
            t.setRowCount(1); t.setSpan(0, 0, 1, 5)
            it = QTableWidgetItem("No products found."); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setForeground(QColor(T["muted"])); it.setData(Qt.ItemDataRole.UserRole, None)
            t.setItem(0, 0, it)
            return
        icon = _icon(BREAD_SVG if self.kind == "bread" else BAG_SVG, T["caramel"])
        for row, p in enumerate(products):
            price, cost = float(p["retail_price"] or 0), float(p["production_cost"] or 0)
            name = QTableWidgetItem(icon, "  " + str(p["name"]))
            name.setData(Qt.ItemDataRole.UserRole, (p["id"], "bread" if self.kind == "bread" else "retail", p["name"]))
            name.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            cost_item = QTableWidgetItem(f"₱{cost:,.2f}" if cost > 0 else "Not set")
            cost_item.setForeground(QColor(T["mid"] if cost > 0 else T["red"]))
            text, color = _profit_text(price, cost)
            if price > 0 and cost > 0 and price >= cost:
                text += f"   ({(price - cost) / price * 100:.0f}%)"
            profit = QTableWidgetItem(text); profit.setForeground(QColor(color))
            profit.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            price_item = QTableWidgetItem(f"₱{price:,.2f}" if price > 0 else "Not set")
            price_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            price_item.setForeground(QColor(T["text"] if price > 0 else T["red"]))
            by = self.db.fetch_one(
                "SELECT action_by, created_at FROM inventory_action_log WHERE item_type=? AND item_id=? "
                "AND action IN ('price_set','recipe_set','added') ORDER BY id DESC LIMIT 1",
                ("bread" if self.kind == "bread" else "retail", p["id"]))
            by_item = QTableWidgetItem(f"{by['action_by']}  ·  {str(by['created_at'])[:10]}" if by and by["action_by"] else "—")
            by_item.setForeground(QColor(T["muted"]))
            for col, cell in enumerate((name, cost_item, profit, price_item, by_item)):
                cell.setTextAlignment((Qt.AlignmentFlag.AlignLeft if col == 0 else Qt.AlignmentFlag.AlignCenter) | Qt.AlignmentFlag.AlignVCenter)
                t.setItem(row, col, cell)
            t.setRowHeight(row, 46)

    def _edit_row(self, row):
        item = self.table.item(row, 0)
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not data:
            return
        prod_id, item_type, _ = data
        EditPriceDialog(self.db, prod_id, current_user=self.current_user, item_type=item_type, parent=self).exec()
        self.load_recipes()

    def show_archived_recipes(self):
        ArchivedRecipesDialog(self.db, current_user=self.current_user, parent=self).exec()
        self.load_recipes()


class EditPriceDialog(QDialog):
    """Puhunan (cost) + Patong (markup, in ₱ or %) = Selling price. Tubo = patong."""

    def __init__(self, db, prod_id, current_user="", item_type="retail", parent=None):
        super().__init__(parent)
        self.db = db
        self.prod_id = prod_id
        self.current_user = current_user
        self.item_type = item_type
        self.mode = "peso"
        self.setWindowTitle("Set Price")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(480)
        self.prod = self.db.fetch_one("SELECT name, retail_price, production_cost FROM products WHERE id = ?", (prod_id,))
        avg = self.db.fetch_one(
            "SELECT COALESCE(SUM(quantity), 0) / 7.0 AS a FROM sales WHERE product_id = ? AND COALESCE(is_voided, 0) = 0 "
            "AND date(created_at) > date('now', 'localtime', '-7 days')", (prod_id,))
        self.avg_daily = float(avg["a"] or 0) if avg else 0.0
        self._build()

    def _spin(self, big=False):
        sp = QDoubleSpinBox()
        sp.setRange(0, 99999); sp.setDecimals(2)
        sp.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sp.setFixedHeight(50 if big else 44)
        sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sp.setFont(QFont("Segoe UI", 16 if big else 14, QFont.Weight.Bold))
        sp.setStyleSheet("QDoubleSpinBox { border: 2px solid #D6CCC2; border-radius: 10px; padding: 0 12px; color: #1F2937; background: white; "
                         "selection-background-color: #E8D5C4; selection-color: #1F2937; } QDoubleSpinBox:focus { border-color: #6B3F27; }")
        return sp

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame(); card.setObjectName("c")
        card.setStyleSheet("QFrame#c { background: white; border-radius: 16px; } QLabel { background: transparent; border: none; }")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)
        lay = QVBoxLayout(card); lay.setContentsMargins(28, 22, 28, 22); lay.setSpacing(10)
        if not self.prod:
            lay.addWidget(QLabel("This product could not be found."))
            return

        head = QHBoxLayout()
        title = QLabel(self.prod["name"])
        title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold)); title.setStyleSheet(f"color: {BROWN_DARK};")
        head.addWidget(title); head.addStretch()
        from bakesync.widgets.ui import button as ui_button
        arch = ui_button("Archive", "danger", icon="trash", h=32)
        arch.setToolTip("Hide this product from the POS and the lists")
        arch.clicked.connect(self._archive)
        head.addWidget(arch)
        head.addWidget(InfoIcon("Puhunan is what one piece costs you. Patong is how much you add on top. "
                                "Selling price = puhunan + patong, and your tubo (profit) is the patong.", "How pricing works"))
        lay.addLayout(head)

        # 1. Puhunan
        l1 = QLabel("1.  Puhunan (cost) per piece"); l1.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold;")
        lay.addWidget(l1)
        self.cost_input = self._spin(); self.cost_input.setPrefix("₱ ")
        self.cost_input.setValue(float(self.prod["production_cost"] or 0))
        lay.addWidget(self.cost_input)

        # 2. Patong, in pesos or percent
        prow = QHBoxLayout()
        l2 = QLabel("2.  Patong (how much you add)"); l2.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold;")
        prow.addWidget(l2); prow.addStretch()
        self.mode_btns = {}
        for key, text in (("peso", "₱ Pesos"), ("pct", "% Percent")):
            b = QPushButton(text); b.setCheckable(True); b.setFixedHeight(30); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("QPushButton { background: white; color: #7A6A5E; border: 1px solid #E8D5C4; padding: 0 12px; font-size: 12px; font-weight: 600; }"
                            "QPushButton:checked { background: #6B3F27; color: white; border-color: #6B3F27; }")
            b.clicked.connect(lambda _, k=key: self._set_mode(k))
            prow.addWidget(b); self.mode_btns[key] = b
        self.mode_btns["peso"].setStyleSheet(self.mode_btns["peso"].styleSheet() + "QPushButton { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }")
        self.mode_btns["pct"].setStyleSheet(self.mode_btns["pct"].styleSheet() + "QPushButton { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }")
        lay.addLayout(prow)
        self.patong_input = self._spin(); self.patong_input.setPrefix("₱ ")
        lay.addWidget(self.patong_input)
        self.quick_row = QHBoxLayout(); self.quick_row.setSpacing(8)
        self.quick_btns = []
        for _ in range(4):
            b = QPushButton(); b.setFixedHeight(36); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("QPushButton { background: #FFF4E8; color: #1F2937; border: 1px solid #E8D5C4; border-radius: 9px; "
                            "font-size: 13px; font-weight: bold; } QPushButton:hover { background: #F5ECE5; border-color: #6B3F27; }")
            b.clicked.connect(lambda _, btn=b: self.patong_input.setValue(btn.property("v")))
            self.quick_row.addWidget(b); self.quick_btns.append(b)
        lay.addLayout(self.quick_row)

        # result: selling price and tubo, big
        self.result = QFrame(); self.result.setObjectName("res")
        rl = QHBoxLayout(self.result); rl.setContentsMargins(16, 12, 16, 12); rl.setSpacing(10)
        c1 = QVBoxLayout(); c1.setSpacing(0)
        t1 = QLabel("Selling price"); t1.setStyleSheet("color: #7A6A5E; font-size: 12px;")
        self.price_lbl = QLabel("₱0.00"); self.price_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        c1.addWidget(t1); c1.addWidget(self.price_lbl)
        c2 = QVBoxLayout(); c2.setSpacing(0)
        t2 = QLabel("Tubo per piece"); t2.setStyleSheet("color: #7A6A5E; font-size: 12px;"); t2.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.tubo_lbl = QLabel("₱0.00"); self.tubo_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.tubo_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        c2.addWidget(t2); c2.addWidget(self.tubo_lbl)
        rl.addLayout(c1); rl.addStretch(); rl.addLayout(c2)
        lay.addWidget(self.result)
        self.daily = QLabel(""); self.daily.setStyleSheet("color: #475569; font-size: 12px;"); self.daily.setWordWrap(True)
        lay.addWidget(self.daily)

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setMinimumWidth(120)
        save = QPushButton("Save Price")
        for b, style in ((cancel, "background: white; color: #64748B; border: 1px solid #E2E8F0;"),
                         (save, f"background: {BROWN_DARK}; color: white; border: none; font-weight: bold;")):
            b.setFixedHeight(46); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setAutoDefault(False)
            b.setStyleSheet(f"QPushButton {{ {style} border-radius: 10px; font-size: 14px; }}")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save_pricing)
        btns.addWidget(cancel); btns.addWidget(save, stretch=2)
        lay.addLayout(btns)

        # start in pesos with the current patong (price - cost)
        cur_patong = max(0.0, float(self.prod["retail_price"] or 0) - float(self.prod["production_cost"] or 0))
        self._set_mode("peso")
        self.patong_input.setValue(cur_patong)
        self.cost_input.valueChanged.connect(self._update)
        self.patong_input.valueChanged.connect(self._update)
        self._update()
        self.cost_input.setFocus(); self.cost_input.selectAll()

    def _set_mode(self, mode):
        old_amount = self._patong_pesos() if hasattr(self, "patong_input") and self.mode else 0
        self.mode = mode
        for k, b in self.mode_btns.items():
            b.setChecked(k == mode)
        self.patong_input.blockSignals(True)
        if mode == "pct":
            self.patong_input.setPrefix(""); self.patong_input.setSuffix(" %")
            cost = self.cost_input.value()
            self.patong_input.setValue(round(old_amount / cost * 100, 2) if cost > 0 else 0)
            values = [10, 20, 30, 50]
            for b, v in zip(self.quick_btns, values):
                b.setText(f"{v}%"); b.setProperty("v", float(v))
        else:
            self.patong_input.setSuffix(""); self.patong_input.setPrefix("₱ ")
            self.patong_input.setValue(round(old_amount, 2))
            for b, v in zip(self.quick_btns, (1, 2, 5, 10)):
                b.setText(f"+₱{v}"); b.setProperty("v", float(v))
        self.patong_input.blockSignals(False)
        self._update()

    def _patong_pesos(self):
        v = self.patong_input.value()
        return self.cost_input.value() * v / 100 if self.mode == "pct" else v

    def selling_price(self):
        return round(self.cost_input.value() + self._patong_pesos(), 2)

    def _update(self, *_):
        cost, tubo, price = self.cost_input.value(), self._patong_pesos(), self.selling_price()
        self.price_lbl.setText(f"₱{price:,.2f}")
        self.tubo_lbl.setText(f"₱{tubo:,.2f}")
        pct = tubo / price * 100 if price > 0 else 0
        low = price > 0 and pct < LOW_PROFIT
        bg, fg, border = ("#FFF7ED", AMBER, "#FED7AA") if low else ("#ECFDF5", GREEN, "#A7F3D0")
        if price <= 0:
            bg, fg, border = "#F8FAFC", MID, "#E2E8F0"
        self.result.setStyleSheet(f"QFrame#res {{ background: {bg}; border: 1px solid {border}; border-radius: 12px; }}"
                                  "QLabel { background: transparent; border: none; }")
        self.price_lbl.setStyleSheet("color: #1F2937;")
        self.tubo_lbl.setStyleSheet(f"color: {fg};")
        text = ""
        if cost <= 0:
            text = "Type the puhunan first."
        elif tubo <= 0:
            text = "Add a patong, or you will not earn anything."
        elif low:
            text = f"The tubo is small: only {pct:.0f}% of the selling price."
        if self.avg_daily >= 1 and tubo > 0:
            text += (" " if text else "") + (f"You sell about {self.avg_daily:.0f} a day, so that is about "
                                             f"₱{tubo * self.avg_daily:,.0f} tubo a day.")
        self.daily.setText(text)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.save_pricing()
        elif e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _archive(self):
        name = self.prod["name"]
        if not BakeSyncAlert.ask_yes_no(self, "Archive this product?",
                                        f"'{name}' will be hidden from the POS and the lists. "
                                        "You can bring it back any time from 'Archived products'.",
                                        yes_text="ARCHIVE", no_text="CANCEL"):
            return
        self.db.execute_query("UPDATE products SET is_archived = 1 WHERE id = ?", (self.prod_id,))
        self.db.execute_query(
            "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
            (self.item_type, self.prod_id, name, "archived", self.current_user))
        log_activity(self.db, self.current_user, "product archived", "price", f"{name} hidden from the POS")
        self.accept()

    def save_pricing(self):
        cost, price = self.cost_input.value(), self.selling_price()
        if cost <= 0:
            BakeSyncAlert.show_warning(self, "No Puhunan", "Please type how much one piece costs you (puhunan).")
            return
        if price <= cost and not BakeSyncAlert.ask_yes_no(
                self, "No Patong",
                f"The selling price is the same as the puhunan (₱{cost:,.2f}), so you will not earn anything.\n\nSave anyway?",
                yes_text="SAVE ANYWAY", no_text="GO BACK"):
            return
        old_price, old_cost = float(self.prod["retail_price"] or 0), float(self.prod["production_cost"] or 0)
        with self.db.transaction():
            self.db.execute_query("UPDATE products SET retail_price = ?, production_cost = ? WHERE id = ?",
                                  (price, cost, self.prod_id))
            self.db.execute_query(
                "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                (self.item_type, self.prod_id, self.prod["name"], "price_set", self.current_user))
        details = (f"{self.prod['name']}: price ₱{old_price:,.2f} -> ₱{price:,.2f} "
                   f"(puhunan ₱{cost:,.2f} + patong ₱{price - cost:,.2f})")
        if abs(old_cost - cost) > 0.001:
            details += f", puhunan was ₱{old_cost:,.2f}"
        log_activity(self.db, self.current_user, "price changed", "price", details)
        self.accept()


class ArchivedRecipesDialog(QDialog):
    """Hidden (archived) products, bread and retail, each on its own row with a clear Restore button."""

    def __init__(self, db, current_user="", parent=None):
        super().__init__(parent)
        from bakesync.widgets.ui import THEME as T, svg_icon, button as ui_button, svg_pixmap
        self.T = T
        self.db = db
        self.current_user = current_user
        self.setWindowTitle("Archived Products")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(580, 520)
        outer = QVBoxLayout(self); outer.setContentsMargins(10, 10, 10, 10)
        card = QFrame(); card.setObjectName("c")
        card.setStyleSheet("QFrame#c { background: white; border-radius: 16px; } QLabel { background: transparent; border: none; }")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)
        lay = QVBoxLayout(card); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)

        head = QHBoxLayout(); head.setSpacing(8)
        tcol = QVBoxLayout(); tcol.setSpacing(2)
        title = QLabel("Archived products")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); title.setStyleSheet(f"color: {T['brown_dark']};")
        sub = QLabel("These are hidden from the POS. Click Restore to sell one again.")
        sub.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
        tcol.addWidget(title); tcol.addWidget(sub)
        head.addLayout(tcol, 1)
        x = QPushButton(); x.setIcon(svg_icon("x", T["mid"], 18)); x.setFixedSize(34, 34)
        x.setCursor(Qt.CursorShape.PointingHandCursor); x.setToolTip("Close")
        x.setStyleSheet(f"QPushButton {{ border: none; border-radius: 17px; background: transparent; }}"
                        f"QPushButton:hover {{ background: {T['cream_dark']}; }}")
        x.clicked.connect(self.accept)
        head.addWidget(x, 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(head)

        sbox = QFrame(); sbox.setObjectName("sbox"); sbox.setFixedHeight(38)
        sbox.setStyleSheet(f"QFrame#sbox {{ background: white; border: 1px solid {T['line']}; border-radius: 10px; }}"
                           f"QFrame#sbox:hover {{ border-color: {T['brown']}; }}")
        sl = QHBoxLayout(sbox); sl.setContentsMargins(10, 0, 6, 0); sl.setSpacing(6)
        ic = QLabel(); ic.setPixmap(svg_pixmap("search", T["muted"], 16))
        sl.addWidget(ic)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search archived products...")
        self.search.setClearButtonEnabled(True)
        self.search.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 13px; color: {T['text']}; }}")
        self.search.textChanged.connect(self.load_data)
        sl.addWidget(self.search)
        lay.addWidget(sbox)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {T['mid']}; font-size: 12px; font-weight: 600;")
        lay.addWidget(self.count_lbl)

        from PyQt6.QtWidgets import QScrollArea
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}"
                         f"QScrollBar:vertical {{ width: 6px; background: transparent; }}"
                         f"QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; min-height: 30px; }}"
                         "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
                         "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }")
        holder = QWidget(); holder.setObjectName("holder"); holder.setStyleSheet("QWidget#holder { background: white; }")
        self.list_lay = QVBoxLayout(holder); self.list_lay.setContentsMargins(0, 0, 4, 0); self.list_lay.setSpacing(8)
        sc.setWidget(holder)
        lay.addWidget(sc, 1)

        close = ui_button("Close", "secondary", h=40)
        close.clicked.connect(self.accept)
        lay.addWidget(close)
        self.load_data()

    def load_data(self):
        T = self.T
        from bakesync.widgets.ui import icon_label, svg_icon, chip
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        like = f"%{self.search.text().strip()}%"
        items = self.db.fetch_all("SELECT id, name, product_type FROM products WHERE is_archived = 1 AND name LIKE ? ORDER BY name", (like,))
        total = self.db.fetch_one("SELECT COUNT(*) FROM products WHERE is_archived = 1")[0]
        self.count_lbl.setText(f"{total} archived product{'s' if total != 1 else ''}"
                               + (f"  ·  {len(items)} shown" if self.search.text().strip() else ""))
        if not items:
            empty = QFrame(); empty.setObjectName("empty")
            empty.setStyleSheet(f"QFrame#empty {{ background: {T['cream']}; border: 1px dashed {T['line']}; border-radius: 12px; }}")
            el = QVBoxLayout(empty); el.setContentsMargins(16, 28, 16, 28); el.setSpacing(8)
            el.addWidget(icon_label("box", T["muted"], 28), 0, Qt.AlignmentFlag.AlignHCenter)
            msg = QLabel("No archived products." if not self.search.text().strip() else "No archived product matches your search.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter); msg.setStyleSheet(f"color: {T['mid']}; font-size: 13px;")
            el.addWidget(msg)
            self.list_lay.addWidget(empty)
            self.list_lay.addStretch()
            return
        for it in items:
            is_bread = it["product_type"] == "bread"
            row = QFrame(); row.setObjectName("arow")
            row.setStyleSheet(f"QFrame#arow {{ background: white; border: 1px solid {T['line']}; border-radius: 12px; }}"
                              f"QFrame#arow:hover {{ border-color: {T['caramel']}; }}")
            h = QHBoxLayout(row); h.setContentsMargins(12, 10, 12, 10); h.setSpacing(12)
            h.addWidget(icon_label("bread" if is_bread else "bag", T["caramel"], 18, bg=T["cream_dark"], box=38, radius=10))
            col = QVBoxLayout(); col.setSpacing(2)
            name = QLabel(it["name"]); name.setStyleSheet(f"color: {T['text']}; font-size: 14px; font-weight: 700;")
            who = self.db.fetch_one(
                "SELECT action_by, created_at FROM inventory_action_log WHERE item_id = ? AND item_type = ? AND action = 'archived' "
                "ORDER BY id DESC LIMIT 1", (it["id"], "bread" if is_bread else "retail"))
            line = "Bread" if is_bread else "Retail item"
            if who and who["created_at"]:
                line += f"  ·  archived {str(who['created_at'])[:10]}" + (f" by {who['action_by']}" if who["action_by"] else "")
            info = QLabel(line); info.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
            col.addWidget(name); col.addWidget(info)
            h.addLayout(col, 1)
            b = QPushButton("  Restore"); b.setFixedHeight(36); b.setMinimumWidth(110)
            b.setIcon(svg_icon("restore", "#FFFFFF", 16)); b.setIconSize(QSize(16, 16))
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.setToolTip(f"Put {it['name']} back on the POS")
            b.setStyleSheet(f"QPushButton {{ background: {T['green']}; color: white; border: none; border-radius: 10px; "
                            f"padding: 0 14px; font-size: 13px; font-weight: 700; }} QPushButton:hover {{ background: #256541; }}")
            b.setProperty("prod", (it["id"], it["name"], it["product_type"]))
            b.clicked.connect(self._on_restore_clicked)
            h.addWidget(b)
            self.list_lay.addWidget(row)
        self.list_lay.addStretch()

    def _on_restore_clicked(self):
        btn = self.sender()
        data = btn.property("prod") if btn else None
        if data:
            self.restore_item(*data)

    def restore_item(self, prod_id, name, ptype):
        self.db.execute_query("UPDATE products SET is_archived = 0 WHERE id = ?", (prod_id,))
        self.db.execute_query(
            "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
            ("bread" if ptype == "bread" else "retail", prod_id, name, "restored", self.current_user))
        log_activity(self.db, self.current_user, "product restored", "price", f"{name} is back on the POS")
        self.load_data()
