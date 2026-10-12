"""End of Day: decide what happens to leftover bread (sell now, sell tomorrow, throw away)."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush

from bakesync.core.leftovers import leftover_bread, apply_leftover_decisions, SELL_NOW, SELL_TOMORROW, THROW
from bakesync.widgets.custom_alerts import BakeSyncAlert

CHOICES = [("Sell tomorrow", SELL_TOMORROW), ("Throw away", THROW), ("Keep selling today", SELL_NOW)]
BROWN, MID, RED, GREEN = "#693903", "#64748B", "#B91C1C", "#047857"


class LeftoverDialog(QDialog):
    def __init__(self, db, current_user="", parent=None):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.rows = [dict(r) for r in leftover_bread(db)]
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumSize(720, 520)
        self._build()
        self._update_summary()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet("QFrame { background: white; border-radius: 16px; } QLabel { background: transparent; }")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)
        lay = QVBoxLayout(card); lay.setContentsMargins(26, 22, 26, 20); lay.setSpacing(12)

        title = QLabel("Leftover Bread (End of Day)")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); title.setStyleSheet(f"color: {BROWN};")
        lay.addWidget(title)
        total_pcs = sum(r["left_qty"] for r in self.rows)
        total_val = sum(r["left_qty"] * r["price"] for r in self.rows)
        head = QLabel(
            f"<b>{len(self.rows)} kind{'s' if len(self.rows) != 1 else ''}</b> of bread {'are' if len(self.rows) != 1 else 'is'} left: <b>{total_pcs:g} pcs</b>, "
            f"worth ₱{total_val:,.2f} if all are sold. Choose what to do with each one."
            if self.rows else "No bread left. Everything sold today!")
        head.setWordWrap(True)
        head.setStyleSheet("color: #7C2D12; background: #FFF7ED; border-radius: 8px; padding: 10px 14px; font-size: 13px;")
        lay.addWidget(head)

        # bulk actions for checked rows
        bulk = QHBoxLayout(); bulk.setSpacing(8)
        self.chk_all = QCheckBox("Select all")
        self.chk_all.setStyleSheet("font-size: 13px; color: #1F2937;")
        self.chk_all.toggled.connect(self._toggle_all)
        bulk.addWidget(self.chk_all)
        bulk.addStretch()
        lbl = QLabel("For selected:"); lbl.setStyleSheet(f"color: {MID}; font-size: 12px;")
        bulk.addWidget(lbl)
        for text, value in CHOICES:
            b = QPushButton(text)
            b.setFixedHeight(32); b.setCursor(Qt.CursorShape.PointingHandCursor)
            color = RED if value == THROW else BROWN
            b.setStyleSheet(f"QPushButton {{ background: white; color: {color}; border: 1.5px solid {color}; border-radius: 8px; "
                            f"padding: 0 12px; font-size: 12px; font-weight: bold; }} QPushButton:hover {{ background: #F5ECE5; }}")
            b.clicked.connect(lambda _, v=value: self._apply_to_checked(v))
            bulk.addWidget(b)
        lay.addLayout(bulk)

        self.table = QTableWidget(len(self.rows), 5)
        self.table.setHorizontalHeaderLabels(["", "Bread", "Left", "Value", "Action"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; font-size: 13px; color: #1F2937; }
            QHeaderView::section { background: #6B3F27; color: white; border: none; padding: 8px; font-weight: bold; }
            QTableWidget::item { padding: 4px 8px; border-bottom: 1px solid #F3F4F6; }
        """)
        self.combos = []
        for r, row in enumerate(self.rows):
            chk = QTableWidgetItem(); chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(r, 0, chk)
            last_day = row["last_day_qty"] > 0
            name = QTableWidgetItem(row["name"] + ("   (last day today)" if last_day else ""))
            if last_day:
                name.setForeground(QBrush(QColor(RED)))
            self.table.setItem(r, 1, name)
            for c, text in ((2, f"{row['left_qty']:g} pcs"), (3, f"₱{row['left_qty'] * row['price']:,.2f}")):
                it = QTableWidgetItem(text); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.table.setItem(r, c, it)
            combo = QComboBox()
            for text, value in CHOICES:
                combo.addItem(text, value)
            combo.setCurrentIndex(1 if last_day else 0)   # suggestion: throw if today is its last day, else sell tomorrow
            combo.currentIndexChanged.connect(self._update_summary)
            self.table.setCellWidget(r, 4, combo)
            self.combos.append(combo)
            self.table.setRowHeight(r, 44)
        lay.addWidget(self.table, stretch=1)

        self.summary = QLabel("")
        self.summary.setStyleSheet("font-size: 13px; color: #1F2937;")
        lay.addWidget(self.summary)

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setMinimumWidth(130)
        save = QPushButton("Save")
        save.setEnabled(bool(self.rows))
        for b, style in ((cancel, "background: white; color: #64748B; border: 1px solid #E2E8F0;"),
                         (save, f"background: {BROWN}; color: white; border: none; font-weight: bold;")):
            b.setFixedHeight(46); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ {style} border-radius: 10px; font-size: 14px; }} "
                            "QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, stretch=2)
        lay.addLayout(btns)

    def _toggle_all(self, on):
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)

    def _apply_to_checked(self, value):
        checked = [r for r in range(self.table.rowCount()) if self.table.item(r, 0).checkState() == Qt.CheckState.Checked]
        if not checked:
            BakeSyncAlert.show_info(self, "Nothing selected", "Check the boxes on the left first, or click 'Select all'.")
            return
        for r in checked:
            self.combos[r].setCurrentIndex(next(i for i, (_, v) in enumerate(CHOICES) if v == value))

    def decisions(self):
        return {row["id"]: self.combos[r].currentData() for r, row in enumerate(self.rows)}

    def _update_summary(self, *_):
        tot = {SELL_TOMORROW: 0, THROW: 0, SELL_NOW: 0}
        loss = 0.0
        for r, row in enumerate(self.rows):
            choice = self.combos[r].currentData()
            tot[choice] += row["left_qty"]
            if choice == THROW:
                loss += row["left_qty"] * row["cost"]
        self.summary.setText(
            f"Sell tomorrow: <b>{tot[SELL_TOMORROW]:g} pcs</b>  ·  Keep selling today: <b>{tot[SELL_NOW]:g} pcs</b>  ·  "
            f"<span style='color:{RED}'>Throw away: <b>{tot[THROW]:g} pcs</b> (₱{loss:,.2f} cost)</span>")

    def _save(self):
        dec = self.decisions()
        throw_pcs = sum(row["left_qty"] for r, row in enumerate(self.rows) if dec[row["id"]] == THROW)
        if throw_pcs and not BakeSyncAlert.ask_yes_no(
                self, "Throw away bread?",
                f"{throw_pcs:g} pcs will be recorded as waste and removed from stock. Are you sure?",
                yes_text="YES, THROW AWAY", no_text="GO BACK"):
            return
        result = apply_leftover_decisions(self.db, dec, self.current_user)
        self.accept()
        BakeSyncAlert.show_success(self.parent(), "Saved",
                                   f"Sell tomorrow: {result['tomorrow']:g} pcs\nThrown away: {result['waste']:g} pcs")
