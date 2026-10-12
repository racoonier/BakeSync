"""The panel that opens from the bell: alerts grouped by kind, each with a button
that goes straight to the page where you fix it."""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor

from bakesync.widgets.ui import THEME as T, icon_label, chip, button

SECTIONS = [
    ("expired", "Expired — remove in Waste", "trash", T["red"], T["red_bg"], "Waste Control",
     "These have passed their sell-by date and must not be sold."),
    ("expiring", "Last day to sell", "calendar", T["amber"], T["amber_bg"], "Inventory",
     "Sell these today. Tomorrow they expire."),
    ("low", "Low or out of stock", "box", T["blue"], T["blue_bg"], "Inventory",
     "Bake or order more of these soon."),
]


class AlertsPopup(QFrame):
    def __init__(self, alerts, go, allowed, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._go, self._allowed = go, allowed
        outer = QVBoxLayout(self); outer.setContentsMargins(6, 6, 6, 6)
        box = QFrame(); box.setObjectName("box")
        box.setStyleSheet(f"QFrame#box {{ background: white; border: 1px solid {T['line']}; border-radius: 14px; }}"
                          "QLabel { background: transparent; border: none; }")
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(24); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 50))
        box.setGraphicsEffect(sh)
        outer.addWidget(box)
        lay = QVBoxLayout(box); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.setFixedWidth(400)

        total = sum(len(alerts.get(k, [])) for k, *_ in SECTIONS)
        head = QWidget(); hl = QHBoxLayout(head); hl.setContentsMargins(16, 14, 16, 10); hl.setSpacing(8)
        hl.addWidget(icon_label("bell", T["brown"], 18, bg=T["cream_dark"], box=34, radius=17))
        col = QVBoxLayout(); col.setSpacing(0)
        t = QLabel("Alerts"); t.setStyleSheet(f"color: {T['text']}; font-size: 15px; font-weight: bold;")
        s = QLabel("Things to look at in your stock" if total else "Everything looks fine")
        s.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
        col.addWidget(t); col.addWidget(s)
        hl.addLayout(col, 1)
        if total:
            hl.addWidget(chip(f"{total} alert{'s' if total != 1 else ''}", T["red"], T["red_bg"]))
        lay.addWidget(head)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background: {T['line']};")
        lay.addWidget(line)

        if not total:
            e = QWidget(); el = QVBoxLayout(e); el.setContentsMargins(0, 26, 0, 26); el.setSpacing(8)
            el.addWidget(icon_label("check_circle", T["green"], 36), alignment=Qt.AlignmentFlag.AlignCenter)
            m = QLabel("No alerts. All good!"); m.setStyleSheet(f"color: {T['green']}; font-size: 13px; font-weight: 600;")
            el.addWidget(m, alignment=Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(e)
            return

        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                         f"QScrollBar:vertical {{ width: 6px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; }}")
        holder = QWidget(); holder.setObjectName("holder"); holder.setStyleSheet("QWidget#holder { background: white; }")
        hlay = QVBoxLayout(holder); hlay.setContentsMargins(12, 10, 12, 10); hlay.setSpacing(10)
        rows = 0
        for key, title, icon, fg, bg, page, hint in SECTIONS:
            items = alerts.get(key, [])
            if not items:
                continue
            sec = QFrame(); sec.setObjectName("sec")
            sec.setStyleSheet(f"QFrame#sec {{ background: {T['cream']}; border-radius: 10px; }}")
            sl = QVBoxLayout(sec); sl.setContentsMargins(10, 8, 10, 8); sl.setSpacing(4)
            top = QHBoxLayout(); top.setSpacing(8)
            top.addWidget(icon_label(icon, fg, 14, bg=bg, box=26, radius=13))
            st = QLabel(f"{title}  ({len(items)})"); st.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: bold;")
            top.addWidget(st, 1)
            if allowed(page):
                b = button("Open", "secondary", h=26)
                b.setProperty("page", page)
                b.clicked.connect(self._open)
                top.addWidget(b)
            sl.addLayout(top)
            h = QLabel(hint); h.setStyleSheet(f"color: {T['mid']}; font-size: 11px;"); h.setWordWrap(True)
            sl.addWidget(h)
            for name, detail in items[:6]:
                r = QHBoxLayout(); r.setContentsMargins(34, 0, 0, 0)
                n = QLabel(name); n.setStyleSheet(f"color: {T['text']}; font-size: 12px;")
                d = QLabel(detail); d.setStyleSheet(f"color: {fg}; font-size: 12px; font-weight: 600;")
                r.addWidget(n); r.addStretch(); r.addWidget(d)
                sl.addLayout(r)
                rows += 1
            if len(items) > 6:
                more = QLabel(f"…and {len(items) - 6} more"); more.setStyleSheet(f"color: {T['mid']}; font-size: 11px; padding-left: 34px;")
                sl.addWidget(more)
            hlay.addWidget(sec)
        hlay.addStretch()
        sc.setWidget(holder)
        holder.adjustSize()
        sc.setFixedHeight(min(440, holder.sizeHint().height() + 4))
        lay.addWidget(sc)
        foot = QLabel("Alerts update every minute.")
        foot.setStyleSheet(f"color: {T['muted']}; font-size: 11px; padding: 8px 16px 10px 16px;")
        lay.addWidget(foot)

    def _open(self):
        page = self.sender().property("page")
        self.close()
        self._go(page)

    def show_under(self, widget):
        self.adjustSize()
        pos = widget.mapToGlobal(QPoint(widget.width() - self.width() + 6, widget.height() + 2))
        scr = widget.screen().availableGeometry()
        pos.setX(max(scr.left() + 6, min(pos.x(), scr.right() - self.width() - 6)))
        self.move(pos)
        self.show()
