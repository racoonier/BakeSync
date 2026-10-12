"""Shared look and building blocks for every BakeSync page.

- THEME:        the bakery colours (chocolate, brown, caramel, cream)
- svg_icon():   line icons (no emoji), coloured on the fly
- InfoIcon:     small (i) button; click or hover shows a short explanation
- ToggleSwitch: an ON/OFF switch that is easier to read than a checkbox
- PasswordFields: new + confirm password with a live checklist
- card(), title_row(): consistent cards and section titles
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QToolButton, QFrame,
                             QCheckBox, QLineEdit, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QByteArray, QSize, QRectF, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtSvg import QSvgRenderer

from bakesync.core.auth_utils import SPECIAL_CHARS

THEME = {
    "choc": "#3B2416", "brown": "#6B3F27", "brown_dark": "#693903", "brown_hover": "#56321F",
    "caramel": "#D9A066", "caramel_light": "#F3D9B8", "gold": "#E8B04B",
    "cream": "#FBF6F0", "cream_dark": "#F3E9DE", "line": "#EADFD3",
    "text": "#2B1D14", "mid": "#7A6A5E", "muted": "#A8998D",
    "green": "#2F7D4F", "green_bg": "#E8F4EC", "red": "#B3261E", "red_bg": "#FCEBEA",
    "amber": "#B26A00", "amber_bg": "#FFF4E0", "blue": "#2457A6", "blue_bg": "#E8EFFA",
}

_P = {
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "check_circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "x_circle": '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
    "minus": '<line x1="5" y1="12" x2="19" y2="12"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "chevron_down": '<polyline points="6 9 12 15 18 9"/>',
    "chevron_right": '<polyline points="9 18 15 12 9 6"/>',
    "chevron_left": '<polyline points="15 18 9 12 15 6"/>',
    "menu": '<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "calendar_x": '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="10" y1="14" x2="14" y2="18"/><line x1="14" y1="14" x2="10" y2="18"/>',
    "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "key": '<circle cx="7.5" cy="15.5" r="5.5"/><path d="M21 2l-9.6 9.6"/><path d="M15.5 7.5l3 3L22 7l-3-3"/>',
    "login": '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    "cart": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>',
    "undo": '<path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/>',
    "ban": '<circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>',
    "box": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "tag": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>',
    "wallet": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    "drive": '<line x1="22" y1="12" x2="2" y2="12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" y1="16" x2="6.01" y2="16"/><line x1="10" y1="16" x2="10.01" y2="16"/>',
    "restore": '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>',
    "sun": '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
    "moon": '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    "sunset": '<path d="M17 18a5 5 0 0 0-10 0"/><line x1="12" y1="9" x2="12" y2="2"/><line x1="4.22" y1="10.22" x2="5.64" y2="11.64"/><line x1="1" y1="18" x2="3" y2="18"/><line x1="21" y1="18" x2="23" y2="18"/><line x1="18.36" y1="11.64" x2="19.78" y2="10.22"/><line x1="23" y1="22" x2="1" y2="22"/><polyline points="16 5 12 9 8 5"/>',
    "store": '<path d="M3 9l1.5-5h15L21 9"/><path d="M3 9h18v1.5a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/><path d="M5 13v8h14v-8"/><path d="M10 21v-5h4v5"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    "eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "eye_off": '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "filter": '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "trend_up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "trend_down": '<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>',
    "chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "bell": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "award": '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>',
    "copy": '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "bread": '<path d="M3 12a5 5 0 0 1 5-5h8a5 5 0 0 1 5 5v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6z"/><line x1="7" y1="7" x2="7" y2="3"/><line x1="12" y1="7" x2="12" y2="2"/><line x1="17" y1="7" x2="17" y2="3"/>',
    "bag": '<path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    "dot": '<circle cx="12" cy="12" r="6" fill="currentColor"/>',
    "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/>',
}


def nice_max(value, ticks=4):
    """A round top for a chart axis, so the lines fall on easy numbers (0, 250, 500...)."""
    import math
    if value <= 0:
        return ticks
    raw = value / ticks
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag * ticks
    return 10 * mag * ticks


def svg_markup(name, color="#6B3F27", stroke=2.0):
    body = _P.get(name, _P["info"]).replace("currentColor", color)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def svg_pixmap(name, color="#6B3F27", size=20, stroke=2.0):
    ratio = 2   # render sharp on high-DPI screens
    pix = QPixmap(size * ratio, size * ratio)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    QSvgRenderer(QByteArray(svg_markup(name, color, stroke).encode("utf-8"))).render(p, QRectF(0, 0, size * ratio, size * ratio))
    p.end()
    pix.setDevicePixelRatio(ratio)
    return pix


def svg_icon(name, color="#6B3F27", size=20, stroke=2.0):
    return QIcon(svg_pixmap(name, color, size, stroke))


def icon_label(name, color="#6B3F27", size=20, bg=None, box=None, radius=None):
    """A QLabel showing an icon; with bg/box it sits in a coloured rounded square or circle."""
    lbl = QLabel()
    lbl.setPixmap(svg_pixmap(name, color, size))
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if bg:
        box = box or size + 16
        lbl.setFixedSize(box, box)
        lbl.setStyleSheet(f"background: {bg}; border-radius: {radius if radius is not None else box // 4}px; border: none;")
    else:
        lbl.setFixedSize(size, size)
        lbl.setStyleSheet("background: transparent; border: none;")
    return lbl


def initials(name):
    parts = [p for p in (name or "").replace("_", " ").split() if p]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper() if len(parts[0]) > 1 and not parts[0][1].isdigit() else parts[0][:1].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class _InfoPopup(QFrame):
    def __init__(self, title, text, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setObjectName("pop")
        self.setStyleSheet(f"QFrame#pop {{ background: #FFFFFF; border: 1px solid {THEME['line']}; border-radius: 10px; }}"
                           "QLabel { background: transparent; border: none; }")
        lay = QVBoxLayout(self); lay.setContentsMargins(14, 10, 14, 12); lay.setSpacing(4)
        if title:
            t = QLabel(title); t.setStyleSheet(f"color: {THEME['brown_dark']}; font-size: 13px; font-weight: bold;")
            lay.addWidget(t)
        b = QLabel(text); b.setWordWrap(True); b.setFixedWidth(280)
        b.setStyleSheet(f"color: {THEME['text']}; font-size: 12px; line-height: 140%;")
        lay.addWidget(b)


class InfoIcon(QToolButton):
    """Small (i). Hover shows the text as a tooltip; click opens it in a little card."""

    def __init__(self, text, title="", parent=None, size=16, color=None):
        super().__init__(parent)
        self._title, self._text = title, text
        self.setIcon(svg_icon("info", color or THEME["caramel"], size))
        self.setIconSize(QSize(size, size))
        self.setFixedSize(size + 8, size + 8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"<b>{title}</b><br>{text}" if title else text)
        self.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 6px; }"
                           f"QToolButton:hover {{ background: {THEME['cream_dark']}; }}")
        self.clicked.connect(self._show)

    def set_text(self, text):
        self._text = text
        self.setToolTip(f"<b>{self._title}</b><br>{text}" if self._title else text)

    def _show(self):
        pop = _InfoPopup(self._title, self._text, self.window())
        pop.adjustSize()
        pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        screen = self.screen().availableGeometry()
        if pos.x() + pop.width() > screen.right():
            pos.setX(screen.right() - pop.width() - 8)
        if pos.y() + pop.height() > screen.bottom():
            pos.setY(self.mapToGlobal(QPoint(0, 0)).y() - pop.height() - 4)
        pop.move(pos)
        pop.show()


def title_row(text, info=None, size=14, color=None, icon=None):
    """Section title with an optional (i) next to it. Returns (widget, layout) so callers can add buttons."""
    w = QWidget(); w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
    if icon:
        lay.addWidget(icon_label(icon, color or THEME["brown"], size + 2))
    t = QLabel(text); t.setFont(QFont("Segoe UI", size, QFont.Weight.Bold))
    t.setStyleSheet(f"color: {color or THEME['text']}; background: transparent;")
    lay.addWidget(t)
    if info:
        lay.addWidget(InfoIcon(info, text))
    lay.addStretch()
    w.title_label = t
    return w, lay


def card(radius=14, bg="#FFFFFF", border=None, name="card"):
    f = QFrame(); f.setObjectName(name)
    f.setStyleSheet(f"QFrame#{name} {{ background: {bg}; border: 1px solid {border or THEME['line']}; border-radius: {radius}px; }}"
                    "QLabel { background: transparent; border: none; }")
    return f


def button(text, kind="secondary", icon=None, h=40, icon_color=None):
    """kind: primary (brown), secondary (white), danger (red outline), ghost (text only)."""
    b = QPushButton(f"  {text}" if icon and text else text)
    b.setFixedHeight(h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    styles = {
        "primary": (f"background: {THEME['brown']}; color: white; border: none;", f"background: {THEME['brown_hover']};", "white"),
        "secondary": (f"background: white; color: {THEME['brown']}; border: 1px solid {THEME['line']};", f"background: {THEME['cream_dark']};", THEME["brown"]),
        "danger": (f"background: white; color: {THEME['red']}; border: 1px solid #F1C2BE;", f"background: {THEME['red_bg']};", THEME["red"]),
        "ghost": (f"background: transparent; color: {THEME['brown']}; border: none;", f"background: {THEME['cream_dark']};", THEME["brown"]),
        "green": (f"background: {THEME['green']}; color: white; border: none;", "background: #256541;", "white"),
    }
    base, hover, ic = styles.get(kind, styles["secondary"])
    b.setStyleSheet(f"QPushButton {{ {base} border-radius: 10px; padding: 0 16px; font-size: 13px; font-weight: 600; }}"
                    f"QPushButton:hover {{ {hover} }} QPushButton:disabled {{ background: #EEE8E2; color: #B5AAA0; border: none; }}")
    if icon:
        b.setIcon(svg_icon(icon, icon_color or ic, 16))
        b.setIconSize(QSize(16, 16))
    return b


class ToggleSwitch(QCheckBox):
    """A rounded ON/OFF switch (works like a checkbox)."""

    def __init__(self, parent=None, on_color=None):
        super().__init__(parent)
        self._on = on_color or THEME["green"]
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(46, 26)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._on if self.isChecked() else "#D8CFC6"))
        p.drawRoundedRect(QRectF(0, 0, 46, 26), 13, 13)
        p.setBrush(QColor("white"))
        x = 23 if self.isChecked() else 3
        p.drawEllipse(QRectF(x, 3, 20, 20))
        p.end()


class PasswordFields(QWidget):
    """New password + Confirm password, show/hide buttons, and a live checklist.
    `changed(bool)` says whether both boxes are valid and match."""
    changed = pyqtSignal(bool)
    RULES = [("8 characters or more", lambda p: len(p) >= 8),
             ("A capital letter (A-Z)", lambda p: any(c.isupper() for c in p)),
             ("A small letter (a-z)", lambda p: any(c.islower() for c in p)),
             ("A number (0-9)", lambda p: any(c.isdigit() for c in p)),
             ("A symbol, like ! @ # $", lambda p: any(c in SPECIAL_CHARS for c in p))]

    def __init__(self, parent=None, new_label="New password", confirm_label="Confirm new password"):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.new = self._field(lay, new_label)
        self.rules = []
        grid = QWidget(); gl = QVBoxLayout(grid); gl.setContentsMargins(4, 2, 0, 4); gl.setSpacing(2)
        for text, _ in self.RULES:
            row = QHBoxLayout(); row.setSpacing(6)
            ic = QLabel(); ic.setFixedSize(14, 14)
            tl = QLabel(text); tl.setStyleSheet(f"font-size: 12px; color: {THEME['mid']};")
            tl.setTextFormat(Qt.TextFormat.PlainText)
            row.addWidget(ic); row.addWidget(tl); row.addStretch()
            gl.addLayout(row)
            self.rules.append((ic, tl))
        lay.addWidget(grid)
        self.confirm = self._field(lay, confirm_label)
        self.match = QLabel(""); self.match.setStyleSheet("font-size: 12px;")
        lay.addWidget(self.match)
        self.new.textChanged.connect(self._check)
        self.confirm.textChanged.connect(self._check)
        self._check()

    def _field(self, lay, label):
        l = QLabel(label); l.setStyleSheet(f"color: {THEME['text']}; font-size: 13px; font-weight: 600;")
        lay.addWidget(l)
        wrap = QFrame(); wrap.setObjectName("pw")
        wrap.setStyleSheet(f"QFrame#pw {{ background: white; border: 1px solid #D6CCC2; border-radius: 9px; }}")
        h = QHBoxLayout(wrap); h.setContentsMargins(12, 0, 4, 0)
        e = QLineEdit(); e.setEchoMode(QLineEdit.EchoMode.Password); e.setFixedHeight(40)
        e.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 14px; color: {THEME['text']}; }}")
        eye = QToolButton(); eye.setIcon(svg_icon("eye", THEME["mid"], 18)); eye.setIconSize(QSize(18, 18))
        eye.setCursor(Qt.CursorShape.PointingHandCursor); eye.setToolTip("Show / hide")
        eye.setStyleSheet("QToolButton { border: none; background: transparent; padding: 6px; }")

        def toggle(_=False, ed=e, b=eye):
            show = ed.echoMode() == QLineEdit.EchoMode.Password
            ed.setEchoMode(QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password)
            b.setIcon(svg_icon("eye_off" if show else "eye", THEME["mid"], 18))
        eye.clicked.connect(toggle)
        h.addWidget(e); h.addWidget(eye)
        lay.addWidget(wrap)
        return e

    def _check(self, *_):
        p = self.new.text()
        all_ok = True
        for (ic, tl), (_, rule) in zip(self.rules, self.RULES):
            ok = rule(p)
            all_ok &= ok
            ic.setPixmap(svg_pixmap("check_circle" if ok else "x_circle", THEME["green"] if ok else "#C9BDB2", 14))
            tl.setStyleSheet(f"font-size: 12px; color: {THEME['green'] if ok else THEME['mid']};")
        c = self.confirm.text()
        if not c:
            self.match.setText("")
            same = False
        else:
            same = c == p
            self.match.setText("Both passwords match" if same else "The passwords do not match")
            self.match.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {THEME['green'] if same else THEME['red']};")
        self.changed.emit(all_ok and same)

    def is_valid(self):
        p = self.new.text()
        return all(rule(p) for _, rule in self.RULES) and p == self.confirm.text()

    def password(self):
        return self.new.text()


# ─────────────────────────────────────────────────────────────────────────────
#  Charts, stat cards, intro lines and legends shared by every page
# ─────────────────────────────────────────────────────────────────────────────
def short_money(v):
    v = float(v or 0)
    if abs(v) >= 1_000_000:
        return f"₱{v / 1_000_000:.1f}M"
    if abs(v) >= 10_000:
        return f"₱{v / 1000:.0f}k"
    if abs(v) >= 1000:
        return f"₱{v / 1000:.1f}k"
    return f"₱{v:,.0f}"


def short_num(v):
    v = float(v or 0)
    if abs(v) >= 1000:
        return f"{v / 1000:.1f}k"
    return f"{v:g}"


class BarChart(QWidget):
    """Simple, readable bar chart drawn by hand: round y-axis numbers, values on top of
    the bars when they fit, the best bar in gold, and the exact value when you point at a bar.

    set_data(labels, [(name, values, color), ...], full_labels=None)"""

    def __init__(self, parent=None, money=True, y_title="", x_title="", empty_text="No data yet", highlight=True):
        super().__init__(parent)
        self.money, self.y_title, self.x_title = money, y_title, x_title
        self.empty_text, self.highlight = empty_text, highlight
        self.labels, self.series, self.full_labels = [], [], []
        self._hover = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(140)

    def set_data(self, labels, series, full_labels=None):
        self.labels = list(labels)
        self.full_labels = list(full_labels) if full_labels else list(labels)
        self.series = [(n, [float(v or 0) for v in vals], c) for n, vals, c in series]
        self._hover = -1
        self.update()

    def _fmt(self, v):
        return short_money(v) if self.money else short_num(v)

    def _fmt_full(self, v):
        if self.money:
            return f"₱{v:,.2f}"
        return f"{v:,.1f}" if v != int(v) else f"{int(v):,}"

    def _geometry(self):
        fm = self.fontMetrics()
        top_val = max([v for _, vals, _ in self.series for v in vals] + [0])
        top = nice_max(top_val * 1.1 if top_val > 0 else (100 if self.money else 4))
        ticks = [top * i / 4 for i in range(5)]
        left = max(fm.horizontalAdvance(self._fmt(t)) for t in ticks) + 14 + (18 if self.y_title else 0)
        legend_h = 22 if len(self.series) > 1 else 0
        top_pad = 18 + legend_h
        bottom = 24 + (18 if self.x_title else 0)
        rect = QRectF(left, top_pad, max(10, self.width() - left - 10), max(10, self.height() - top_pad - bottom))
        return rect, top, ticks

    def mouseMoveEvent(self, e):
        if not self.labels:
            return
        rect, _, _ = self._geometry()
        x = e.position().x()
        idx = int((x - rect.left()) / (rect.width() / len(self.labels))) if rect.left() <= x < rect.right() else -1
        if idx != self._hover:
            self._hover = idx
            self.update()

    def leaveEvent(self, e):
        self._hover = -1
        self.update()

    def paintEvent(self, e):
        from PyQt6.QtGui import QPainterPath, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Segoe UI", 8))
        fm = p.fontMetrics()
        has_data = any(v for _, vals, _ in self.series for v in vals)
        rect, top, ticks = self._geometry()

        for t in ticks:                                            # grid + y labels
            y = rect.bottom() - (t / top) * rect.height()
            p.setPen(QPen(QColor("#EFE7DE"), 1, Qt.PenStyle.DashLine if t else Qt.PenStyle.SolidLine))
            p.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            p.setPen(QColor(THEME["mid"]))
            p.drawText(QRectF(0, y - 8, rect.left() - 8, 16),
                       int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), self._fmt(t))
        if self.y_title:
            p.save(); p.translate(10, rect.center().y()); p.rotate(-90)
            p.setPen(QColor(THEME["mid"]))
            p.drawText(QRectF(-rect.height() / 2, -8, rect.height(), 16), int(Qt.AlignmentFlag.AlignCenter), self.y_title)
            p.restore()
        if self.x_title:
            p.setPen(QColor(THEME["mid"]))
            p.drawText(QRectF(rect.left(), self.height() - 18, rect.width(), 16), int(Qt.AlignmentFlag.AlignCenter), self.x_title)

        n = len(self.labels)
        if not n or not has_data:
            p.setPen(QColor(THEME["muted"])); p.setFont(QFont("Segoe UI", 10))
            p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), self.empty_text)
            p.end()
            return

        group_w = rect.width() / n
        k = len(self.series)
        bar_area = min(group_w * (0.68 if k == 1 else 0.8), 64 * k)
        bar_w = bar_area / k
        best = -1
        if self.highlight and k == 1:
            vals = self.series[0][1]
            best = max(range(n), key=lambda i: vals[i])

        if 0 <= self._hover < n:                                   # hovered column
            p.fillRect(QRectF(rect.left() + self._hover * group_w, rect.top(), group_w, rect.height()), QColor(107, 63, 39, 16))

        for si, (name, vals, color) in enumerate(self.series):
            for i, v in enumerate(vals):
                if v <= 0:
                    continue
                h = max(2.0, (v / top) * rect.height())
                x = rect.left() + i * group_w + (group_w - bar_area) / 2 + si * bar_w
                r = QRectF(x + 1, rect.bottom() - h, max(2.0, bar_w - 2), h)
                rad = min(6.0, r.width() / 3, h / 2)
                path = QPainterPath()
                path.addRoundedRect(r, rad, rad)
                fill = QColor(THEME["gold"]) if i == best else QColor(color)
                p.fillPath(path, fill)
                p.fillRect(QRectF(r.left(), r.bottom() - rad, r.width(), rad), fill)     # flat bottom
                if k == 1 and bar_w >= 22:
                    txt = self._fmt(v)
                    if fm.horizontalAdvance(txt) <= group_w + 2:
                        p.setPen(QColor(THEME["text"]))
                        p.drawText(QRectF(x - 14, rect.bottom() - h - 16, bar_w + 28, 14), int(Qt.AlignmentFlag.AlignCenter), txt)

        step = max(1, int((max(fm.horizontalAdvance(l) for l in self.labels) + 10) / group_w) + 1)
        p.setPen(QColor(THEME["mid"]))
        for i, lab in enumerate(self.labels):                      # x labels, thinned out when crowded
            if i % step:
                continue
            p.drawText(QRectF(rect.left() + i * group_w - 14, rect.bottom() + 5, group_w + 28, 16),
                       int(Qt.AlignmentFlag.AlignCenter), lab)

        if k > 1:                                                  # legend
            x = rect.right()
            for name, _, color in reversed(self.series):
                w = fm.horizontalAdvance(name)
                x -= w
                p.setPen(QColor(THEME["text"])); p.drawText(QRectF(x, 2, w + 2, 16), int(Qt.AlignmentFlag.AlignVCenter), name)
                x -= 15
                p.setBrush(QColor(color)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(QRectF(x, 5, 10, 10), 3, 3)
                x -= 16

        if 0 <= self._hover < n:                                   # exact values for the hovered bar
            lines = [self.full_labels[self._hover]] + [
                (f"{name}: " if k > 1 else "") + self._fmt_full(vals[self._hover]) for name, vals, _ in self.series]
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            fm2 = p.fontMetrics()
            w = max(fm2.horizontalAdvance(t) for t in lines) + 22
            h = 18 * len(lines) + 10
            cx = rect.left() + (self._hover + 0.5) * group_w
            bx = min(max(rect.left(), cx - w / 2), rect.right() - w)
            p.setPen(QPen(QColor(THEME["line"]), 1)); p.setBrush(QColor("#FFFFFF"))
            p.drawRoundedRect(QRectF(bx, rect.top(), w, h), 8, 8)
            for li, t in enumerate(lines):
                p.setPen(QColor(THEME["mid"] if li == 0 else THEME["text"]))
                p.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal if li == 0 else QFont.Weight.Bold))
                p.drawText(QRectF(bx + 11, rect.top() + 5 + li * 18, w - 20, 18), int(Qt.AlignmentFlag.AlignVCenter), t)
        p.end()


class StatCard(QFrame):
    """White card: small icon + title + (i), a big value and one line under it."""

    def __init__(self, title, icon="chart", info="", accent=None, accent_bg=None):
        super().__init__()
        self.setObjectName("stat")
        self.setStyleSheet(f"QFrame#stat {{ background: white; border: 1px solid {THEME['line']}; border-radius: 14px; }}"
                           "QLabel { background: transparent; border: none; }")
        accent = accent or THEME["brown"]
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 12, 10, 12); lay.setSpacing(4)
        top = QHBoxLayout(); top.setSpacing(8)
        top.addWidget(icon_label(icon, accent, 16, bg=accent_bg or THEME["cream_dark"], box=30, radius=15))
        t = QLabel(title); t.setStyleSheet(f"color: {THEME['mid']}; font-size: 12px; font-weight: 600;")
        top.addWidget(t); top.addStretch()
        if info:
            top.addWidget(InfoIcon(info, title))
        lay.addLayout(top)
        self.value = QLabel("—"); self.value.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.value.setStyleSheet(f"color: {THEME['text']};")
        self.sub = QLabel(""); self.sub.setWordWrap(True)
        self.sub.setStyleSheet(f"color: {THEME['mid']}; font-size: 11px;")
        lay.addWidget(self.value); lay.addWidget(self.sub); lay.addStretch()

    def set(self, value, sub="", sub_color=None, value_color=None):
        self.value.setText(value)
        self.value.setStyleSheet(f"color: {value_color or THEME['text']};")
        self.sub.setText(sub)
        self.sub.setStyleSheet(f"color: {sub_color or THEME['mid']}; font-size: 11px;")


def intro_row(text, info=None, title="About this page"):
    """A muted one-line description of the page with an (i). Returns (widget, layout)."""
    w = QWidget(); w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
    l = QLabel(text); l.setStyleSheet(f"color: {THEME['mid']}; font-size: 13px;")
    lay.addWidget(l)
    if info:
        lay.addWidget(InfoIcon(info, title))
    lay.addStretch()
    w.text_label = l
    return w, lay


def legend_row(items, size=10):
    """[(color, label), ...] as small coloured dots with words."""
    w = QWidget(); w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(12)
    for color, label in items:
        d = QLabel(); d.setFixedSize(size, size)
        d.setStyleSheet(f"background: {color}; border-radius: {size // 2}px;")
        t = QLabel(label); t.setStyleSheet(f"color: {THEME['mid']}; font-size: 11px;")
        row = QHBoxLayout(); row.setSpacing(5); row.addWidget(d); row.addWidget(t)
        lay.addLayout(row)
    lay.addStretch()
    return w


def chip(text, fg, bg):
    l = QLabel(text)
    l.setStyleSheet(f"color: {fg}; background: {bg}; border-radius: 9px; padding: 2px 9px; font-size: 11px; font-weight: 600;")
    return l


class ProgressBar(QWidget):
    """Thin rounded bar: part filled in `color`, the rest in a light track."""

    def __init__(self, value=0.0, color=None, height=8):
        super().__init__()
        self._v, self._c = value, color or THEME["brown"]
        self.setFixedHeight(height)
        self.setMinimumWidth(40)

    def set_value(self, v, color=None):
        self._v = max(0.0, min(1.0, v))
        if color:
            self._c = color
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = self.height() / 2
        p.setBrush(QColor("#EFE7DE")); p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), r, r)
        if self._v > 0:
            p.setBrush(QColor(self._c)); p.drawRoundedRect(QRectF(0, 0, max(self.height(), self.width() * self._v), self.height()), r, r)
        p.end()


class RefreshButton(QPushButton):
    """'Refresh' button used on every page. After a click it shows 'Updated' with a check for a moment,
    so people can see that something happened. Connect `clicked` to the page's reload method."""

    def __init__(self, text="Refresh", h=38, parent=None):
        super().__init__(parent)
        self._text = text
        self.setFixedHeight(h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Load the newest numbers")
        self.setIconSize(QSize(16, 16))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._reset)
        self.clicked.connect(self._flash)
        self._reset()

    def _style(self, fg, bg, border):
        self.setStyleSheet(f"QPushButton {{ background: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 10px; "
                           f"padding: 0 14px; font-size: 13px; font-weight: 600; }}"
                           f"QPushButton:hover {{ background: {THEME['cream_dark']}; }}")

    def _reset(self):
        self.setText(f"  {self._text}")
        self.setIcon(svg_icon("refresh", THEME["brown"], 16))
        self._style(THEME["brown"], "white", THEME["line"])

    def _flash(self):
        self.setText("  Updated")
        self.setIcon(svg_icon("check", THEME["green"], 16))
        self._style(THEME["green"], THEME["green_bg"], "#BFE0CB")
        self._timer.start(1300)


_TONES = {
    "green": ("green", "green_bg"), "red": ("red", "red_bg"), "amber": ("amber", "amber_bg"),
    "blue": ("blue", "blue_bg"), "brown": ("brown", "cream_dark"), "gold": ("amber", "#FDF0D5"),
}


class Highlights(QFrame):
    """White card with a short list of key facts. Each fact is one row:
    coloured icon, a small label ("Best seller"), the answer in bold, and one muted line under it."""

    def __init__(self, title="Highlights", info="", max_rows=6):
        super().__init__()
        self.setObjectName("hl")
        self.setStyleSheet(f"QFrame#hl {{ background: white; border: 1px solid {THEME['line']}; border-radius: 14px; }}"
                           "QLabel { background: transparent; border: none; }")
        self.max_rows = max_rows
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 12, 16, 10); lay.setSpacing(4)
        head, _ = title_row(title, info=info, size=13, icon="award")
        lay.addWidget(head)
        self.rows = QVBoxLayout(); self.rows.setSpacing(0); self.rows.setContentsMargins(0, 2, 0, 0)
        lay.addLayout(self.rows)
        lay.addStretch()

    def set_items(self, items):
        """items: [(icon, tone, label, value, sub), ...]  tone = green/red/amber/blue/brown/gold."""
        while self.rows.count():
            w = self.rows.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not items:
            empty = QWidget(); el = QVBoxLayout(empty); el.setContentsMargins(0, 30, 0, 0); el.setSpacing(8)
            empty.setObjectName("hlempty"); empty.setStyleSheet("QWidget#hlempty { background: transparent; }")
            el.addWidget(icon_label("chart", THEME["caramel"], 22, bg=THEME["cream_dark"], box=48, radius=24), 0, Qt.AlignmentFlag.AlignHCenter)
            msg = QLabel("Nothing to show yet.\nHighlights appear once there are sales in this period.")
            msg.setWordWrap(True); msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet(f"color: {THEME['muted']}; font-size: 12px;")
            el.addWidget(msg)
            self.rows.addWidget(empty)
            return
        items = items[:self.max_rows]
        for i, (icon, tone, label, value, sub) in enumerate(items):
            fg, bg = _TONES.get(tone, _TONES["brown"])
            row = QFrame(); row.setObjectName("hlrow")
            row.setStyleSheet("QFrame#hlrow { background: transparent; border: none; " +
                              (f"border-bottom: 1px solid {THEME['cream_dark']}; }}" if i < len(items) - 1 else "}"))
            h = QHBoxLayout(row); h.setContentsMargins(0, 8, 0, 8); h.setSpacing(12)
            h.addWidget(icon_label(icon, THEME[fg], 18, bg=THEME.get(bg, bg), box=38, radius=10), 0, Qt.AlignmentFlag.AlignTop)
            col = QVBoxLayout(); col.setSpacing(1)
            l = QLabel(label.upper()); l.setStyleSheet(f"color: {THEME['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
            v = QLabel(value); v.setWordWrap(True)
            v.setStyleSheet(f"color: {THEME['text']}; font-size: 13px; font-weight: 700;")
            col.addWidget(l); col.addWidget(v)
            if sub:
                s = QLabel(sub); s.setWordWrap(True)
                s.setStyleSheet(f"color: {THEME[fg] if tone in ('red', 'amber') else THEME['mid']}; font-size: 11px;")
                col.addWidget(s)
            h.addLayout(col, 1)
            self.rows.addWidget(row)
