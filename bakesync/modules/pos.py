from bakesync.paths import IMAGES_DIR, product_image
from datetime import datetime
from bakesync.widgets.product_images import default_product_pixmap, kind_for
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QDialog, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QApplication, QSpacerItem, QGraphicsDropShadowEffect, QStackedWidget,
    QComboBox, QCompleter, QSplitter, QAbstractItemView, QButtonGroup,
)
from PyQt6.QtCore import (
    Qt, QTimer, QDate, QTime, QDateTime, pyqtSignal, QByteArray, QSize,
    QPropertyAnimation, QEasingCurve, QRect, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QBrush, QPalette, QIcon, QPixmap,
    QPainter, QPen, QLinearGradient, QRadialGradient
)


from bakesync.core.database import DatabaseManager
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import svg_icon as ui_icon, svg_pixmap as ui_pixmap, THEME as UI
import os
import re
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix

# ─────────────────────────────────────────────
#  STYLE CONSTANTS  (Python palette — brown/cream)
# ─────────────────────────────────────────────
BROWN        = "#6B3F27"
BROWN_DARK   = "#4E2D1A"
BROWN_MID    = "#8B5E3C"
BROWN_LIGHT  = "#A07050"
CREAM        = "#FAF9F7"
CREAM_MID    = "#F0E6DC"
CREAM_DARK   = "#E8D5C0"
GREEN        = "#4AAD72"
GREEN_DARK   = "#388054"
GREEN_DIM    = "rgba(74,173,114,0.15)"
RED          = "#D94A4A"
RED_DARK     = "#A83535"
RED_DIM      = "rgba(217,74,74,0.15)"
AMBER        = "#D4830A"
AMBER_DIM    = "rgba(212,131,10,0.15)"
TEXT_DARK    = "#1A1A1A"
TEXT_MID     = "#555555"
TEXT_LIGHT   = "#AAAAAA"
BORDER       = "#D7D7D7"
BORDER_MID   = "rgba(107,63,39,0.25)"
WHITE        = "#FFFFFF"

# Surface layers
SURFACE      = WHITE
SURFACE2     = CREAM
SURFACE3     = CREAM_MID

# Accent / gold-equivalent  (maps to the HTML's --gold)
GOLD         = BROWN
GOLD_DIM     = BROWN_MID
GOLD_GLOW    = "rgba(107,63,39,0.12)"


def _force_light(widget):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,      QColor(WHITE))
    pal.setColor(QPalette.ColorRole.WindowText,  QColor(TEXT_DARK))
    pal.setColor(QPalette.ColorRole.Base,        QColor(WHITE))
    pal.setColor(QPalette.ColorRole.Text,        QColor(TEXT_DARK))
    pal.setColor(QPalette.ColorRole.Button,      QColor(WHITE))
    pal.setColor(QPalette.ColorRole.ButtonText,  QColor(TEXT_DARK))
    widget.setPalette(pal)
    widget.setAutoFillBackground(True)


# ─────────────────────────────────────────────
#  SVG ICONS  (re-used throughout)
# ─────────────────────────────────────────────
SVG = {
    "bread":    '<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 11l2-2 2 2 2-2 2 2 2-2 2 2 2-2v4a5 5 0 0 1-10 0 5 5 0 0 1-4-4.9V11z"/><line x1="3" y1="11" x2="21" y2="11"/></svg>',
    "pastry":   '<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72"/></svg>',
    "beverage": '<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/></svg>',
    "others":   '<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "search":   '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "trash":    '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    "close":    '<svg fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "pay":      '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>',
    "clock":    '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "box":      '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/></svg>',
    "chart":    '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "warn":     '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "cart":     '<svg fill="none" stroke="currentColor" stroke-width="1.2" viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
    "receipt":  '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
}


def make_svg_icon(svg_str: str, size: int = 18, color: str = BROWN) -> QPixmap:
    """Render an SVG string with colour substitution to a QPixmap."""
    coloured = svg_str.replace('stroke="currentColor"', f'stroke="{color}"')
    coloured = coloured.replace('fill="currentColor"', f'fill="{color}"')
    px = QPixmap()
    px.loadFromData(QByteArray(
        f'<svg xmlns="http://www.w3.org/2000/svg" {coloured[4:]}'.encode()
        if not coloured.startswith('<svg xmlns') else coloured.encode()
    ), "SVG")
    if not px.isNull():
        px = px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
    return px


def svg_label(svg_str: str, size: int = 18, color: str = BROWN) -> QLabel:
    lbl = QLabel()
    lbl.setPixmap(make_svg_icon(svg_str, size, color))
    lbl.setFixedSize(size, size)
    lbl.setStyleSheet("border:none;background:transparent;")
    return lbl


# ─────────────────────────────────────────────
#  TOAST NOTIFICATION
# ─────────────────────────────────────────────
class ToastNotification(QWidget):
    """Animated toast that slides up from the bottom-left of the parent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(44)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._start_hide)
        self._anim = None
        self._setup()

    def _setup(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 22, 0)
        layout.setSpacing(10)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet(
            f"background:{GREEN};border-radius:4px;border:none;")
        self._txt = QLabel()
        self._txt.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self._txt.setStyleSheet(f"color:{WHITE};background:transparent;border:none;")
        layout.addWidget(self._dot)
        layout.addWidget(self._txt)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(
            1, 1, self.width() - 2, self.height() - 2, 13, 13)
        painter.fillPath(path, QColor(BROWN_DARK))
        pen = QPen(QColor(BROWN_DARK))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()
        super().paintEvent(event)

    def _apply_style(self, error: bool):
        dot_color = RED if error else GREEN
        self._dot.setStyleSheet(
            f"background:{dot_color};border-radius:4px;border:none;")
        self._txt.setStyleSheet(
            f"color:{WHITE};background:transparent;border:none;")

    def show_message(self, msg: str, error: bool = False, parent_widget=None):
        self._apply_style(error)
        self._txt.setText(msg)
        self.adjustSize()

        # ── System sound ──────────────────────────────────
        try:
            import sys
            if sys.platform == "win32":
                import winsound
                if error:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                else:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        if parent_widget:
            pw = parent_widget
            self.setParent(pw)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

            # ── Start position: bottom-left, below visible area ──
            x = 20
            y_end   = pw.height() - self.height() - 24
            y_start = pw.height() + 10

            self.move(x, y_start)
            self.show()
            self.raise_()

            # ── Slide-up animation ────────────────────────────────
            self._anim = QPropertyAnimation(self, b"pos")
            self._anim.setDuration(320)
            self._anim.setStartValue(QPoint(x, y_start))
            self._anim.setEndValue(QPoint(x, y_end))
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.start()

            # ── Float bobbing after slide-in ──────────────────────
            self._float_timer = QTimer(self)
            self._float_timer.setSingleShot(True)
            self._float_pos = (x, y_end)
            self._float_timer.timeout.connect(self._float_tick)
            self._float_timer.start(340)

        self._timer.start(3000)

    def _float_tick(self):
        self._start_float(*self._float_pos)

    def _start_float(self, x: int, y_base: int):
        """Gentle up-down bob animation."""
        self._float_anim = QPropertyAnimation(self, b"pos")
        self._float_anim.setDuration(900)
        self._float_anim.setLoopCount(-1)  # infinite
        self._float_anim.setKeyValueAt(0.0,  QPoint(x, y_base))
        self._float_anim.setKeyValueAt(0.5,  QPoint(x, y_base - 5))
        self._float_anim.setKeyValueAt(1.0,  QPoint(x, y_base))
        self._float_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._float_anim.start()

    def _start_hide(self):
        """Slide down and hide."""
        # Stop float
        if hasattr(self, '_float_anim') and self._float_anim:
            self._float_anim.stop()
        if hasattr(self, '_float_timer') and self._float_timer:
            self._float_timer.stop()

        x   = self.x()
        y   = self.y()
        y_end = y + self.height() + 30

        hide_anim = QPropertyAnimation(self, b"pos")
        hide_anim.setDuration(280)
        hide_anim.setStartValue(QPoint(x, y))
        hide_anim.setEndValue(QPoint(x, y_end))
        hide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        hide_anim.finished.connect(self.hide)
        hide_anim.start()
        self._hide_anim = hide_anim


# ─────────────────────────────────────────────
#  PRODUCT CARD  (HTML-inspired style, Python palette)
# ─────────────────────────────────────────────
class ProductCard(QFrame):
    clicked_signal = pyqtSignal(int)   # emits prod_id

    def __init__(self, prod_id, name, price, stock, image_path=None, parent=None, prod_type="others"):
        super().__init__(parent)
        self.prod_id    = prod_id
        self.prod_name  = name
        self.prod_price = price
        self.prod_stock = stock
        self.prod_type  = prod_type
        self._in_cart   = False
        self._cart_qty  = 0

        self.setFixedSize(200, 250)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("pcard")
        self.setProperty("class", "pcard")
        self._build_ui(name, price, stock, image_path)
        self._update_style()

    def _build_ui(self, name, price, stock, image_path):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top image area ─────────────────────────────────
        self._img_frame = QLabel()
        self._img_frame.setFixedSize(200, 190)
        self._img_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_frame.setStyleSheet(
            f"background:{BROWN_DARK};border:none;margin:0;padding:0;"
            f"overflow:hidden;")
        self._img_frame.setContentsMargins(0, 0, 0, 0)
        self._img_frame.setClipChildren(True) if hasattr(self._img_frame, 'setClipChildren') else None

        if image_path and os.path.exists(image_path):
            px = QPixmap(image_path).scaled(
                200, 190,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            self._img_frame.setPixmap(px)
        else:
            # Walang photo: ipakita ang default na "No image yet" picture sa cream background
            self._img_frame.setStyleSheet("background:#F5ECE5;border:none;margin:0;padding:0;")
            self._img_frame.setPixmap(default_product_pixmap(200, 190, kind_for(self.prod_type)))

        # Clip container for marquee text
        self._name_clip = QWidget(self._img_frame)
        self._name_clip.setGeometry(0, 84, 168, 22)
        self._name_clip.setStyleSheet("background:transparent;border:none;")
        self._name_clip.setFixedSize(168, 22)

        # ── Name label overlaid on bottom-left of image ────
        # Madilim na strip sa likod ng pangalan para mabasa sa kahit anong larawan
        self._name_strip = QFrame(self._img_frame)
        self._name_strip.setGeometry(0, 150, 200, 32)
        self._name_strip.setStyleSheet("background: rgba(43, 22, 6, 150); border: none;")

        self._name_lbl = QLabel(name, self._img_frame)
        self._name_lbl.setWordWrap(False)
        self._name_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self._name_lbl.setStyleSheet(
            f"color:{WHITE};background:transparent;border:none;padding:0 6px;")
        self._name_lbl.setFixedWidth(168)
        self._name_lbl.setFixedHeight(22)
        self._name_lbl.move(0, 155)

        # Marquee scroll for long names
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(self._name_lbl.font())
        text_width = fm.horizontalAdvance(name)
        if text_width > 155:
            self._marquee_offset = 0
            self._marquee_direction = 1
            self._marquee_paused = 60
            self._marquee_args = (name, text_width)
            self._marquee_timer = QTimer(self)
            self._marquee_timer.timeout.connect(self._marquee_tick)
            self._marquee_timer.start(30)
        else:
            self._marquee_timer = None

        # ── Bottom info area ───────────────────────────────
        self._bottom_widget = QWidget()
        self._bottom_widget.setFixedSize(200, 55)
        self._bottom_widget.setStyleSheet(
            f"background:{WHITE};border:none;")
        bl = QHBoxLayout(self._bottom_widget)
        bl.setContentsMargins(10, 0, 10, 0)
        bl.setSpacing(0)

        self._price_lbl = QLabel(f"₱{price:.2f}")
        self._price_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._price_lbl.setStyleSheet(
            f"color:{TEXT_DARK};background:transparent;border:none;")
        bl.addWidget(self._price_lbl)

        layout.addWidget(self._img_frame)
        layout.addWidget(self._bottom_widget)

        # ── Stock label (direct child, immune to opacity) ──
        self._stock_lbl = QLabel(self)
        self._stock_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._stock_lbl.setGeometry(40, 113 + 10, 148, 195)
        self._stock_lbl.raise_()
        self._refresh_stock_label(stock)

        # ── Cart badge ─────────────────────────────────────
        self._badge = QLabel(self)
        self._badge.setFixedSize(22, 22)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(
            f"background:{BROWN};color:{WHITE};border-radius:11px;"
            f"font-size:11px;font-weight:bold;border:none;")
        self._badge.move(self.width() - 30, 10)
        self._badge.hide()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.setClipPath(path)
        super().paintEvent(event)
        painter.end()

    def _marquee_tick(self):
        self._scroll_name(*self._marquee_args)

    def _scroll_name(self, name: str, text_width: int):
        max_offset = text_width - 148

        if self._marquee_paused > 0:
            self._marquee_paused -= 1
            return

        self._marquee_offset += self._marquee_direction

        if self._marquee_offset >= max_offset:
            self._marquee_offset = max_offset
            self._marquee_direction = -1
            self._marquee_paused = 60
        elif self._marquee_offset <= 0:
            self._marquee_offset = 0
            self._marquee_direction = 1
            self._marquee_paused = 60

        # Shift label position
        self._name_lbl.move(-self._marquee_offset + 6, 155)
        self._name_lbl.setFixedWidth(text_width + 20)

    def _refresh_stock_label(self, stock):
        if stock == 0:
            self._stock_lbl.setText("Out of stock")
            self._stock_lbl.setStyleSheet(f"""
                color:{RED};
                background:transparent;
                border:none;
                font-size:10px;
                font-weight:bold;
            """)
        elif stock <= 5:
            self._stock_lbl.setText(f"Only {int(stock)} left")
            self._stock_lbl.setStyleSheet(f"""
                color:{AMBER};
                background:transparent;
                border:none;
                font-size:9px;
                font-weight:bold;
            """)
        else:
            self._stock_lbl.setText(f"{int(stock)}\nAvailable")
            self._stock_lbl.setStyleSheet(f"""
                color:{TEXT_MID};
                background:transparent;
                border:none;
                font-size:9px;
            """)

    def _update_style(self):
        if self.prod_stock == 0:
            self.setStyleSheet(f"""
                QFrame#pcard {{
                    background:transparent;
                    border:1.5px solid {BORDER};
                }}""")
            self._img_frame.setGraphicsEffect(self._make_opacity_effect(0.4))
            self._bottom_widget.setGraphicsEffect(self._make_opacity_effect(0.4))
            self._stock_lbl.setGraphicsEffect(None)
            self._stock_lbl.raise_()
            self.setEnabled(False)
        elif self._in_cart:
            self._img_frame.setGraphicsEffect(None)
            self._bottom_widget.setGraphicsEffect(None)
            self.setStyleSheet(f"""
                QFrame#pcard {{
                    background:transparent;
                    border:2px solid {BROWN};
                }}""")
        else:
            self._img_frame.setGraphicsEffect(None)
            self._bottom_widget.setGraphicsEffect(None)
            self.setStyleSheet(f"""
                QFrame#pcard {{
                    background:transparent;
                    border:1.5px solid {BORDER};
                }}
                QFrame#pcard:hover {{
                    border:2px solid {BROWN_DARK};
                }}""")
                
    def _make_opacity_effect(self, opacity: float):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(opacity)
        return effect

    def set_cart_state(self, qty: int):
        self._cart_qty = qty
        self._in_cart  = qty > 0
        if self._in_cart:
            self._badge.setText(str(qty))
            self._badge.show()
        else:
            self._badge.hide()
        remaining = max(0, self.prod_stock - qty)
        self._refresh_stock_label(remaining)
        self._update_style()

    def refresh_stock(self, new_stock):
        self.prod_stock = new_stock
        self._refresh_stock_label(new_stock)
        self._update_style()
        self.setEnabled(new_stock > 0)

    def mousePressEvent(self, e):
        if self.isEnabled():
            self.clicked_signal.emit(self.prod_id)
        super().mousePressEvent(e)


# ─────────────────────────────────────────────
#  CART ITEM  (data model)
# ─────────────────────────────────────────────
class CartItem:
    def __init__(self, prod_id, name, price, qty=1, image_path=None, prod_type=None):
        self.prod_id = prod_id
        self.prod_type = prod_type
        self.name    = name
        self.price   = price
        self.qty     = qty
        self.image_path = image_path

    @property
    def subtotal(self):
        return self.price * self.qty

class FilterPill(QPushButton):
    def __init__(self, label, value="", parent=None):
        super().__init__(label, parent)
        self.value = value
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(28)
        self._apply_style()
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, _checked):
        self._apply_style()

    def _apply_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background:{CREAM_MID};
                    border:1.5px solid {BROWN};
                    border-radius:10px;
                    padding:0px 14px;
                    color:{BROWN};
                    font-weight:bold;
                    font-size:12px;
                    font-family:'Segoe UI';
                }}""")
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;
                    border:1.5px solid {BORDER};
                    border-radius:10px;
                    padding:0px 14px;
                    color:{TEXT_MID};
                    font-size:12px;
                    font-family:'Segoe UI';
                }}
                QPushButton:hover {{
                    background:{CREAM_MID};
                    border-color:{BROWN_MID};
                    color:{BROWN_DARK};
                }}""")


# ─────────────────────────────────────────────
#  CATEGORY TAB  (UPDATED: Smaller font, bold on hover)
# ─────────────────────────────────────────────
class CategoryTab(QPushButton):
    def __init__(self, label, count=0, parent=None):
        super().__init__(parent)
        self._label = label
        self._count = count
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)
        
        # 🟢 FIX: Tinanggal natin ang naka-hardcode na QFont() na laging Bold.
        # Sa stylesheet na natin kokontrolin para pwede magbago pag naka-hover.
        
        self._update_text()
        self.toggled.connect(self._on_toggled)
        self._apply_style()

    def _on_toggled(self, _checked):
        self._apply_style()

    def set_count(self, count):
        self._count = count
        self._update_text()

    def _update_text(self):
        self.setText(f"{self._label}   ({self._count})")

    def _apply_style(self):
        # 🟢 FIX: Base font styling na ginawang 14px (mas maliit sa dati)
        base_font = "font-family: 'Segoe UI'; font-size: 14px;"
        
        if self.isChecked():
            # Kapag ito yung piniling category (Active)
            self.setStyleSheet(f"""
                QPushButton {{
                    {base_font}
                    background: transparent;
                    border: none;
                    border-bottom: 3px solid {WHITE};
                    color: {WHITE};
                    font-weight: bold; /* Bold kapag active */
                    padding: 0px 20px;
                }}""")
        else:
            # Default na hitsura (Normal at hindi bold)
            self.setStyleSheet(f"""
                QPushButton {{
                    {base_font}
                    background: transparent;
                    border: none;
                    border-bottom: 3px solid transparent;
                    color: rgba(255, 255, 255, 0.75);
                    font-weight: normal; /* Normal weight */
                    padding: 0px 20px;
                }}
                QPushButton:hover {{ 
                    background: rgba(255, 255, 255, 0.10); 
                    color: {WHITE};
                }}""")


def suggested_amounts(total):
    """Exact, then the next round amounts a customer would likely give
    (e.g. total ₱137 → Exact, ₱150, ₱200, ₱500, ₱1,000)."""
    import math
    out = [round(total, 2)]
    for step in (50, 100, 500, 1000):
        v = float(math.ceil(total / step) * step)
        if v <= total:
            v += step
        if v not in out:
            out.append(v)
    return out[:5]


# ─────────────────────────────────────────────
#  PAYMENT DIALOG  ("Other amount": type what the customer gave)
# ─────────────────────────────────────────────
class PaymentDialog(QDialog):
    def __init__(self, total: float, parent=None):
        super().__init__(parent)
        self.total    = total
        self.tendered = 0.0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(470)
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._build()
        self.adjustSize()
        self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _build(self):
        """Simple on purpose: total, one box for the cash, one row of quick amounts,
        the change, and two buttons. Enter = Confirm, Esc = Cancel."""
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        card  = QWidget(); card.setObjectName("payCard")
        card.setStyleSheet(f"""
            QWidget#payCard {{
                background:{WHITE};border:1px solid {BORDER};border-radius:18px;
            }}
            QWidget#payCard QLabel  {{ background:transparent;color:{TEXT_DARK};border:none; }}
            QWidget#payCard QWidget {{ background:{WHITE}; }}
        """)
        _force_light(card)
        cl = QVBoxLayout(card); cl.setContentsMargins(30,26,30,26); cl.setSpacing(14)

        # ── total to pay ──
        t = QLabel("Total to pay")
        t.setFont(QFont("Segoe UI", 12))
        t.setStyleSheet(f"color:{TEXT_MID};")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(t)
        due_val = QLabel(f"₱{self.total:,.2f}")
        due_val.setFont(QFont("Segoe UI", 34, QFont.Weight.Bold))
        due_val.setStyleSheet(f"color:{BROWN};")
        due_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(due_val)

        # ── cash received (cursor is here as soon as the dialog opens) ──
        lbl_cash = QLabel("Cash received")
        lbl_cash.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        lbl_cash.setStyleSheet(f"color:{TEXT_MID};")
        cl.addWidget(lbl_cash)

        self.cash_input = QLineEdit()
        self.cash_input.setPlaceholderText("Type amount  (Enter = exact)")
        self.cash_input.setFixedHeight(60)
        self.cash_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cash_input.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.cash_input.setStyleSheet(f"""
            QLineEdit {{
                background:{WHITE};color:{TEXT_DARK};
                border:2px solid {BORDER};border-radius:12px;
                padding:0 16px;
            }}
            QLineEdit:focus {{ border-color:{BROWN}; }}
        """)
        from PyQt6.QtGui import QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression
        self.cash_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,7}(\.\d{0,2})?$")))
        self.cash_input.textChanged.connect(self._update_change)
        self.cash_input.returnPressed.connect(self._confirm_if_enough)   # Enter = confirm
        cl.addWidget(self.cash_input)

        # ── one row of quick amounts: Exact, then the bills a customer most likely gives ──
        sug_row = QHBoxLayout(); sug_row.setSpacing(8)
        for val in self._suggested_amounts()[:4]:
            b = QPushButton("Exact" if abs(val - self.total) < 0.005 else f"₱{val:,.0f}")
            b.setFixedHeight(46)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # keep the cursor in the amount box
            b.setStyleSheet(f"""
                QPushButton {{
                    background:#FFF4E8;color:{TEXT_DARK};
                    border:1px solid {BORDER};border-radius:10px;
                    font-size:15px;font-weight:700;
                }}
                QPushButton:hover {{ background:{CREAM_DARK};border-color:{BROWN_MID};color:{BROWN}; }}""")
            b.clicked.connect(lambda _, v=val: self._set_cash(v))
            sug_row.addWidget(b)
        cl.addLayout(sug_row)

        # ── change / short by, big and clear ──
        self.change_frame = QFrame()
        self.change_frame.setFixedHeight(70)
        cf = QHBoxLayout(self.change_frame)
        cf.setContentsMargins(18, 0, 18, 0)
        self.change_lbl = QLabel("")
        self.change_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        self.change_val = QLabel("")
        self.change_val.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        cf.addWidget(self.change_lbl); cf.addStretch(); cf.addWidget(self.change_val)
        cl.addWidget(self.change_frame)

        # ── two buttons only ──
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(52)
        cancel.setMinimumWidth(120)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel.setToolTip("Esc")
        cancel.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE};color:{TEXT_MID};
                border:1px solid {BORDER};border-radius:12px;font-size:15px;
            }}
            QPushButton:hover {{ color:{TEXT_DARK};background:{CREAM_MID}; }}
        """)
        cancel.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setFixedHeight(52)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.confirm_btn.setToolTip("Enter")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background:{GREEN};color:{WHITE};border:none;
                border-radius:12px;font-size:16px;font-weight:bold;
            }}
            QPushButton:hover  {{ background:{GREEN_DARK}; }}
            QPushButton:disabled {{ background:{BORDER};color:{TEXT_LIGHT}; }}
        """)
        self.confirm_btn.clicked.connect(self._confirm_if_enough)

        btn_row.addWidget(cancel); btn_row.addWidget(self.confirm_btn, stretch=2)
        cl.addLayout(btn_row)

        hint = QLabel("Press Enter to confirm  ·  Esc to cancel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color:{TEXT_LIGHT};font-size:11px;")
        cl.addWidget(hint)
        outer.addWidget(card)
        for b in card.findChildren(QPushButton):   # Enter must only ever mean "Confirm"
            b.setAutoDefault(False); b.setDefault(False)
        self._update_change("")
        self.cash_input.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.cash_input.setFocus()

    def _suggested_amounts(self):
        return suggested_amounts(self.total)

    def _amount(self):
        try:
            return float(self.cash_input.text().replace(",", "") or 0)
        except ValueError:
            return 0.0

    def _set_cash(self, val):
        self.cash_input.setText(f"{val:.2f}".rstrip("0").rstrip("."))
        self.cash_input.setFocus()

    def _add_cash(self, val):
        self._set_cash(self._amount() + val)

    def _confirm_if_enough(self):
        if not self.cash_input.text().strip():
            self._set_cash(self.total)
        if self._amount() + 0.005 >= self.total:
            self.tendered = self._amount()
            self.accept()

    def _update_change(self, text):
        amt = self._amount()
        if not text.strip():
            bg, fg, label, value = CREAM_MID, TEXT_MID, "Change", "—"
            self.confirm_btn.setEnabled(True)    # empty + Confirm = exact amount
        elif amt + 0.005 < self.total:
            bg, fg, label, value = RED_DIM, RED, "Short by", f"₱{self.total - amt:,.2f}"
            self.confirm_btn.setEnabled(False)
        else:
            bg, fg, label, value = GREEN_DIM, GREEN, "Change", f"₱{amt - self.total:,.2f}"
            self.confirm_btn.setEnabled(True)
            self.tendered = amt
        self.change_frame.setStyleSheet(f"background:{bg};border:none;border-radius:12px;")
        for w in (self.change_lbl, self.change_val):
            w.setStyleSheet(f"color:{fg};background:transparent;border:none;")
        self.change_lbl.setText(label)
        self.change_val.setText(value)

# ─────────────────────────────────────────────
#  END-OF-DAY DIALOG
# ─────────────────────────────────────────────
class EndOfDayDialog(QDialog):
    def __init__(self, db, session_sales, parent=None, current_user=""):
        super().__init__(parent)
        self.db            = db
        self.session_sales = session_sales
        self.current_user  = current_user
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True); self.setMinimumWidth(540)
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._init_ui(); self.adjustSize(); self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _init_ui(self):
        # 🟢 FIX 1: Fetch sa Database imbes na RAM para safe sa App Restarts
        try:
            session = self.db.fetch_one("SELECT opened_at FROM pos_sessions WHERE status='Open' ORDER BY id DESC LIMIT 1")
            opened_at = session['opened_at'] if session else "1970-01-01"

            sales_data = self.db.fetch_all("""
                SELECT p.name, SUM(s.quantity) as qty, SUM(s.amount) as amount
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE s.created_at >= ? AND COALESCE(s.is_voided, 0) = 0
                GROUP BY p.id
            """, (opened_at,))
            
            rows = []
            session_total = 0.0
            for row in sales_data:
                rows.append({'name': row['name'], 'qty': row['qty'], 'amount': row['amount']})
                session_total += row['amount']

            txn_data = self.db.fetch_one("""
                SELECT COUNT(DISTINCT created_at) as txns
                FROM sales
                WHERE created_at >= ? AND COALESCE(is_voided, 0) = 0
            """, (opened_at,))
            session_txns = txn_data['txns'] if txn_data else 0

            db_sales = self.db.fetch_one("""
                SELECT SUM(amount) as total FROM sales 
                WHERE DATE(created_at) = DATE('now', 'localtime') 
                AND COALESCE(is_voided, 0) = 0
            """)
            db_total = db_sales['total'] if db_sales and db_sales['total'] else 0.0

        except Exception as e:
            print(f"[EOD] Data fetch error: {e}")
            rows = []
            session_total = 0.0
            session_txns = 0
            db_total = 0.0

        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        card  = QWidget(); card.setObjectName("eodCard")
        card.setStyleSheet(f"""
            QWidget#eodCard {{
                background:{WHITE};border:1px solid {BORDER};border-radius:18px;
            }}
            QWidget#eodCard QLabel  {{ background:transparent;color:{TEXT_DARK};border:none; }}
            QWidget#eodCard QWidget {{ background:{WHITE}; }}
        """)
        _force_light(card)
        cl = QVBoxLayout(card); cl.setContentsMargins(30,26,30,26); cl.setSpacing(16)

        # header
        hdr = QHBoxLayout()
        ico = QLabel(); ico.setFixedSize(44,44)
        ico.setStyleSheet(f"background:{GOLD_GLOW};border-radius:22px;border:none;")
        ico.setPixmap(make_svg_icon(SVG["clock"], 22, BROWN))
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_col = QVBoxLayout(); t_col.setSpacing(1)
        t1 = QLabel("End of Day — Session Summary")
        t1.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t2 = QLabel(f"Closed by: {self.current_user or 'Unknown'}")
        t2.setFont(QFont("Segoe UI", 9))
        t2.setStyleSheet(f"color:{TEXT_MID};")
        t_col.addWidget(t1); t_col.addWidget(t2)
        hdr.addWidget(ico); hdr.addLayout(t_col); hdr.addStretch()
        cl.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER};border:none;"); cl.addWidget(div)

        # KPI row
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(12)
        for lbl, val, color in [
            ("Session Revenue", f"₱{session_total:,.2f}", GREEN),
            ("Transactions",    str(session_txns),         BROWN),
            ("Today's Total",   f"₱{db_total:,.2f}",      "#4A90D9"),
        ]:
            kf = QFrame()
            kf.setStyleSheet(f"QFrame{{background:{CREAM_MID};border-radius:10px;border:none;}}")
            kv = QVBoxLayout(kf); kv.setContentsMargins(14,10,14,10); kv.setSpacing(2)
            la = QLabel(lbl); la.setFont(QFont("Segoe UI",9))
            la.setStyleSheet(f"color:{TEXT_MID};background:transparent;border:none;")
            lb = QLabel(val); lb.setFont(QFont("Segoe UI",16,QFont.Weight.Bold))
            lb.setStyleSheet(f"color:{color};background:transparent;border:none;")
            kv.addWidget(la); kv.addWidget(lb)
            kpi_row.addWidget(kf)
        cl.addLayout(kpi_row)

        sec_lbl = QLabel("Products Sold This Session")
        sec_lbl.setFont(QFont("Segoe UI",11,QFont.Weight.Bold)); cl.addWidget(sec_lbl)

        tbl = QTableWidget(); tbl.setColumnCount(3)
        tbl.setHorizontalHeaderLabels(["Product","Qty Sold","Revenue"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setShowGrid(False); tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setMaximumHeight(200)
        tbl.setStyleSheet(f"""
            QTableWidget {{ border:none;font-size:12px;background:white;color:{TEXT_DARK}; }}
            QHeaderView::section {{ background:{BROWN};color:white;padding:8px;
                border:none;font-size:11px;font-weight:bold; }}
            QTableWidget::item {{ padding:6px 8px;border-bottom:1px solid {BORDER}; }}
        """)
        
        # 🟢 FIX 2: List of DB records na ang gamit imbes na RAM
        tbl.setRowCount(len(rows))
        for i, v in enumerate(rows):
            for c, txt in enumerate([v['name'], str(v['qty']), f"₱{v['amount']:,.2f}"]):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setItem(i, c, it)
            tbl.setRowHeight(i, 36)
        cl.addWidget(tbl)

        note = QLabel("Session sales are saved. Count the cash in Settings > Finance > Cash Count.")
        note.setWordWrap(True); note.setFont(QFont("Segoe UI",10))
        note.setStyleSheet(
            f"color:{TEXT_MID};background:#FBF5EE;border-radius:8px;"
            f"padding:10px 12px;border:1px solid {CREAM_DARK};")
        cl.addWidget(note)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        for txt, fn, primary in [
            ("Keep Open", self.reject, False),
            ("Close Session", self.accept, True),
        ]:
            b = QPushButton(txt); b.setFixedHeight(40); b.setMinimumWidth(130)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if primary:
                b.setStyleSheet(f"""
                    QPushButton {{ background:{GREEN};color:{WHITE};border:none;
                    border-radius:10px;font-size:13px;font-weight:bold;padding:0 18px; }}
                    QPushButton:hover {{ background:{GREEN_DARK}; }}""")
            else:
                b.setStyleSheet(f"""
                    QPushButton {{ background:{WHITE};color:{TEXT_MID};
                    border:1px solid {BORDER};border-radius:10px;
                    font-size:13px;padding:0 18px; }}
                    QPushButton:hover {{ background:{CREAM_MID}; }}""")
            b.clicked.connect(fn); btn_row.addWidget(b)
        cl.addLayout(btn_row)
        outer.addWidget(card)


# ─────────────────────────────────────────────
#  STOCKS DIALOG
# ─────────────────────────────────────────────
class StocksDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(920, 620)
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._init_ui(); self.load_stocks()
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _tbl_style(self):
        return f"""
            QTableWidget {{ background:white;border:1px solid {BORDER};
                border-radius:8px;font-size:12px;color:{TEXT_DARK};outline:none; }}
            QHeaderView::section {{ background:{BROWN};color:white;padding:8px 10px;
                font-weight:bold;font-size:11px;border:none; }}
            QTableWidget::item {{ padding:5px 10px;border-bottom:1px solid {BORDER}; }}
            QTableWidget::item:selected {{ background:{CREAM_MID};color:{TEXT_DARK}; }}
        """

    def _init_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(15,15,15,20)
        card  = QWidget(); card.setObjectName("StocksCard")
        card.setStyleSheet(f"""
            QWidget#StocksCard {{ background:{WHITE};border:1px solid {BORDER};
                border-radius:14px; }}
            QLabel {{ border:none;background:transparent; }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(22); shadow.setColor(QColor(0,0,0,28)); shadow.setOffset(0,6)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card); cl.setContentsMargins(22,18,22,22); cl.setSpacing(14)

        # header
        hdr = QHBoxLayout()
        ico = QLabel(); ico.setFixedSize(28,28)
        ico.setPixmap(make_svg_icon(SVG["box"], 24, BROWN))
        ico.setStyleSheet("background:transparent;border:none;")
        t = QLabel("Stock Levels"); t.setFont(QFont("Segoe UI",15,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{TEXT_DARK};margin-left:5px;")
        close_btn = QPushButton(); close_btn.setFixedSize(30,30)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:15px;}"
            "QPushButton:hover{background:#F3F4F6;}")
        close_btn.setIcon(QIcon(make_svg_icon(SVG["close"], 16, TEXT_LIGHT)))
        close_btn.setIconSize(QSize(16,16)); close_btn.clicked.connect(self.reject)
        hdr.addWidget(ico); hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(close_btn)
        cl.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER};border:none;"); cl.addWidget(div)

        # table
        self.tbl = QTableWidget(); self.tbl.setColumnCount(4)
        self.tbl.setHorizontalHeaderLabels(["Product","Category","Stock","Status"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tbl.setColumnWidth(3, 130)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setShowGrid(False); self.tbl.setStyleSheet(self._tbl_style())
        cl.addWidget(self.tbl, stretch=1)

        close_foot = QPushButton("Close")
        close_foot.setFixedHeight(40); close_foot.setCursor(Qt.CursorShape.PointingHandCursor)
        close_foot.setStyleSheet(f"""
            QPushButton {{ background:{WHITE};color:{TEXT_MID};
            border:1px solid {BORDER};border-radius:10px;font-size:13px; }}
            QPushButton:hover {{ background:{CREAM_MID}; }}""")
        close_foot.clicked.connect(self.reject); cl.addWidget(close_foot)
        outer.addWidget(card)

    def load_stocks(self):
        try:
            products = self.db.fetch_all(
                "SELECT id,name,stock_qty,"
                "COALESCE(NULLIF(TRIM(product_type),''),'Others') as p_type "
                "FROM products WHERE is_archived=0")
        except Exception:
            return

        rows = []
        for p in products:
            try:
                er = self.db.fetch_one(
                    "SELECT COALESCE(SUM(quantity_remaining),0) AS eq "
                    "FROM product_batches WHERE product_id=? "
                    "AND quantity_remaining>0 AND expiry_date IS NOT NULL "
                    "AND expiry_date<=date('now', 'localtime')", (p['id'],))
                expired = er['eq'] if er else 0
            except Exception:
                expired = 0
            usable = max(0, (p['stock_qty'] or 0) - expired)
            rows.append((p['name'], str(p['p_type']).strip().title(), usable))

        rows.sort(key=lambda r: r[2], reverse=True)
        self.tbl.setRowCount(len(rows))
        for i, (name, cat, stock) in enumerate(rows):
            if stock > 10:   status, sc = "In Stock",     GREEN
            elif stock > 0:  status, sc = "Low Stock",    AMBER
            else:            status, sc = "Out of Stock", RED

            for c, (txt, align) in enumerate([
                (name,         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (cat,          Qt.AlignmentFlag.AlignCenter),
                (f"{int(stock)} pcs", Qt.AlignmentFlag.AlignCenter),
                (status,       Qt.AlignmentFlag.AlignCenter),
            ]):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(align)
                if c == 3:
                    it.setForeground(QBrush(QColor(sc)))
                    it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.tbl.setItem(i, c, it)
            self.tbl.setRowHeight(i, 40)


# ─────────────────────────────────────────────
#  SALES INSIGHTS DIALOG
# ─────────────────────────────────────────────
class SalesInsightsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(960, 660)
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._init_ui(); self.load_insights()
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _init_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(15,15,15,20)
        card  = QWidget(); card.setObjectName("SalesCard")
        card.setStyleSheet(f"""
            QWidget#SalesCard {{ background:{WHITE};border:1px solid {BORDER};
                border-radius:14px; }}
            QLabel {{ border:none;background:transparent; }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(22); shadow.setColor(QColor(0,0,0,28)); shadow.setOffset(0,6)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card); cl.setContentsMargins(26,22,26,26); cl.setSpacing(18)

        # header
        hdr = QHBoxLayout()
        ico = QLabel(); ico.setFixedSize(28,28)
        ico.setPixmap(make_svg_icon(SVG["chart"], 24, BROWN))
        ico.setStyleSheet("background:transparent;border:none;")
        t = QLabel("Sales Insights"); t.setFont(QFont("Segoe UI",16,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{TEXT_DARK};margin-left:6px;")
        close_btn = QPushButton(); close_btn.setFixedSize(30,30)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:15px;}"
            "QPushButton:hover{background:#F3F4F6;}")
        close_btn.setIcon(QIcon(make_svg_icon(SVG["close"], 16, TEXT_LIGHT)))
        close_btn.setIconSize(QSize(16,16)); close_btn.clicked.connect(self.reject)
        hdr.addWidget(ico); hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(close_btn)
        cl.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER};border:none;"); cl.addWidget(div)

        # KPI cards
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(14)
        self._kpi_widgets = {}
        for key, title, bg, fg in [
            ("rev",  "TODAY'S REVENUE",       "#ECFDF5", GREEN),
            ("txn",  "TODAY'S TRANSACTIONS",  "#EFF6FF", "#1E3A8A"),
            ("top",  "TOP CATEGORY",          "#FFFBEB", AMBER),
        ]:
            kf = QFrame(); kf.setFixedHeight(90)
            kf.setStyleSheet(
                f"background:{bg};border-radius:10px;border:1px solid {BORDER};")
            lyt = QVBoxLayout(kf); lyt.setContentsMargins(16,14,16,14); lyt.setSpacing(4)
            la = QLabel(title); la.setFont(QFont("Segoe UI",9,QFont.Weight.Bold))
            la.setStyleSheet(f"color:{TEXT_LIGHT};background:transparent;border:none;")
            lv = QLabel("—"); lv.setFont(QFont("Segoe UI",20,QFont.Weight.Black))
            lv.setStyleSheet(f"color:{fg};background:transparent;border:none;")
            lyt.addWidget(la); lyt.addWidget(lv)
            self._kpi_widgets[key] = lv
            kpi_row.addWidget(kf)
        cl.addLayout(kpi_row)

        rank_lbl = QLabel("All-Time Best Sellers")
        rank_lbl.setFont(QFont("Segoe UI",12,QFont.Weight.Bold))
        rank_lbl.setStyleSheet(f"color:{BROWN};")
        cl.addWidget(rank_lbl)

        self.rank_tbl = QTableWidget(); self.rank_tbl.setColumnCount(5)
        self.rank_tbl.setHorizontalHeaderLabels(
            ["#", "Product", "Category", "Total Sold", "Revenue"])
        self.rank_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.rank_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rank_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.rank_tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.rank_tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.rank_tbl.verticalHeader().setVisible(False)
        self.rank_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rank_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.rank_tbl.setShowGrid(False)
        self.rank_tbl.setStyleSheet(f"""
            QTableWidget {{ background:white;border:1px solid {BORDER};
                border-radius:8px;font-size:12px;color:{TEXT_DARK};outline:none; }}
            QHeaderView::section {{ background:{BROWN};color:white;padding:8px 10px;
                font-weight:bold;font-size:11px;border:none; }}
            QTableWidget::item {{ padding:5px 10px;border-bottom:1px solid {BORDER}; }}
        """)
        cl.addWidget(self.rank_tbl, stretch=1)

        close_foot = QPushButton("Close")
        close_foot.setFixedHeight(40); close_foot.setCursor(Qt.CursorShape.PointingHandCursor)
        close_foot.setStyleSheet(f"""
            QPushButton {{ background:{WHITE};color:{TEXT_MID};
            border:1px solid {BORDER};border-radius:10px;font-size:13px; }}
            QPushButton:hover {{ background:{CREAM_MID}; }}""")
        close_foot.clicked.connect(self.reject); cl.addWidget(close_foot)
        outer.addWidget(card)

    def load_insights(self):
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            kpi = self.db.fetch_one(
                "SELECT SUM(amount) as rev, COUNT(DISTINCT created_at) as txns "
                "FROM sales WHERE date(created_at)=? AND COALESCE(is_voided,0)=0",
                (today,))
            rev  = (kpi['rev']  or 0.0) if kpi else 0.0
            txns = (kpi['txns'] or 0)   if kpi else 0
            self._kpi_widgets["rev"].setText(f"₱{rev:,.2f}")
            self._kpi_widgets["txn"].setText(str(txns))

            cat = self.db.fetch_one(
                "SELECT COALESCE(NULLIF(TRIM(p.product_type),''),'Others') as cat,"
                "SUM(s.quantity) as qty FROM sales s "
                "JOIN products p ON s.product_id=p.id "
                "WHERE COALESCE(s.is_voided,0)=0 AND date(s.created_at)=? "
                "GROUP BY cat ORDER BY qty DESC LIMIT 1", (today,))
            self._kpi_widgets["top"].setText(
                str(cat['cat']).title() if cat else "—")

            rankings = self.db.fetch_all(
                "SELECT p.name, COALESCE(NULLIF(TRIM(p.product_type),''),'Others') as cat,"
                "SUM(s.quantity) as tq, SUM(s.amount) as tr FROM sales s "
                "JOIN products p ON s.product_id=p.id "
                "WHERE COALESCE(s.is_voided,0)=0 GROUP BY p.id ORDER BY tq DESC")
            medals = ["1st", "2nd", "3rd"]
            self.rank_tbl.setRowCount(len(rankings))
            for i, row in enumerate(rankings):
                rank = medals[i] if i < 3 else f"   {i+1}"
                for c, (txt, al) in enumerate([
                    (rank,                    Qt.AlignmentFlag.AlignCenter),
                    (row['name'],             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                    (str(row['cat']).title(), Qt.AlignmentFlag.AlignCenter),
                    (f"{row['tq']} pcs",      Qt.AlignmentFlag.AlignCenter),
                    (f"₱{row['tr']:,.2f}",    Qt.AlignmentFlag.AlignCenter),
                ]):
                    it = QTableWidgetItem(txt); it.setTextAlignment(al)
                    self.rank_tbl.setItem(i, c, it)
                self.rank_tbl.setRowHeight(i, 44)
        except Exception as e:
            print(f"[Sales] load error: {e}")


# ─────────────────────────────────────────────
#  QTY INPUT DIALOG
# ─────────────────────────────────────────────
class QtyInputDialog(QDialog):
    qty_confirmed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True); self.setFixedSize(290, 350)
        self._pending = ""
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.45);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._build(); self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        card  = QWidget(); card.setObjectName("qtyCard")
        card.setStyleSheet(f"""
            QWidget#qtyCard {{ background:{WHITE};border:1px solid {BORDER};border-radius:16px; }}
            QWidget#qtyCard QLabel {{ background:transparent;color:{TEXT_DARK};border:none; }}
        """)
        _force_light(card)
        cl = QVBoxLayout(card); cl.setContentsMargins(22,20,22,20); cl.setSpacing(12)

        t = QLabel("Enter Quantity")
        t.setFont(QFont("Segoe UI",13,QFont.Weight.Bold))
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(t)

        self.display = QLabel("0")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setFont(QFont("Segoe UI",34,QFont.Weight.Bold))
        self.display.setFixedHeight(62)
        self.display.setStyleSheet(
            f"color:{BROWN};background:{CREAM_MID};"
            f"border-radius:10px;padding:8px;border:none;")
        cl.addWidget(self.display)

        grid = QGridLayout(); grid.setSpacing(8)
        for idx, k in enumerate(["7","8","9","4","5","6","1","2","3","⌫","0","✓"]):
            b = QPushButton(k); b.setFixedHeight(44)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if k in ("✓", "⌫"):
                b.setText(""); b.setIcon(ui_icon("check" if k == "✓" else "undo", WHITE if k == "✓" else RED, 20))
            if k == "✓":
                b.setStyleSheet(f"""
                    QPushButton {{ background:{GREEN};color:white;border-radius:8px;
                    font-size:16px;font-weight:bold;border:none; }}
                    QPushButton:hover {{ background:{GREEN_DARK}; }}""")
            elif k == "⌫":
                b.setStyleSheet(f"""
                    QPushButton {{ background:#FBE9E9;color:{RED};border-radius:8px;
                    font-size:16px;font-weight:bold;border:1px solid #F0C0C0; }}
                    QPushButton:hover {{ background:#F5D0D0; }}""")
            else:
                b.setStyleSheet(f"""
                    QPushButton {{ background:{WHITE};color:{TEXT_DARK};
                    border:1px solid {BORDER};border-radius:8px;
                    font-size:17px;font-weight:bold; }}
                    QPushButton:hover {{ background:{CREAM_MID}; }}""")
            b.clicked.connect(lambda _, key=k: self._press(key))
            grid.addWidget(b, idx//3, idx%3)
        cl.addLayout(grid)

        cancel = QPushButton("Cancel"); cancel.setFixedHeight(36)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{ background:{WHITE};color:{TEXT_MID};
            border:1px solid {BORDER};border-radius:8px;font-size:12px; }}
            QPushButton:hover {{ background:{CREAM_MID}; }}""")
        cancel.clicked.connect(self.reject); cl.addWidget(cancel)
        outer.addWidget(card)

    def _press(self, key):
        if key == "⌫":
            self._pending = self._pending[:-1] or "0"
        elif key == "✓":
            q = int(self._pending) if self._pending and self._pending != "0" else 0
            if q > 0:
                self.qty_confirmed.emit(q); self.accept()
            return
        else:
            self._pending = (key if self._pending in ("", "0") else self._pending + key)
        self.display.setText(self._pending or "0")



# ─────────────────────────────────────────────
#  VOID QUANTITY SELECTOR DIALOG
# ─────────────────────────────────────────────
VOID_REASONS = ["Wrong item", "Wrong quantity", "Customer changed mind", "Damaged / spoiled", "Price mistake", "Other"]


class VoidQtyDialog(QDialog):
    def __init__(self, item_name, max_qty, parent=None):
        super().__init__(parent)
        self.max_qty = max_qty
        self.selected_qty = 1
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(400)
        
        # UI Setup
        outer = QVBoxLayout(self)
        card = QFrame(); card.setObjectName("voidCard")
        card.setStyleSheet(f"""
            QFrame#voidCard {{ background:{WHITE}; border:1px solid {BORDER}; border-radius:18px; }}
            QLabel {{ background:transparent; color:{TEXT_DARK}; border:none; }}
        """)
        cl = QVBoxLayout(card); cl.setContentsMargins(24, 24, 24, 24); cl.setSpacing(15)
        
        # Header
        t = QLabel("Select Void Quantity"); t.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        t.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(t)
        
        info = QLabel(f"How many '{item_name}' would you like to void?"); info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter); info.setStyleSheet(f"color:{TEXT_MID};")
        cl.addWidget(info)
        
        # Stepper Row
        step_row = QHBoxLayout(); step_row.setSpacing(15)
        
        btn_min = QPushButton("−"); btn_min.setFixedSize(44, 44)
        btn_min.setStyleSheet(f"QPushButton{{ background:{CREAM_MID}; border-radius:10px; font-size:18px; font-weight:bold; }} QPushButton:hover{{ background:{CREAM_DARK}; }}")
        
        self.qty_lbl = QLabel("1"); self.qty_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_plus = QPushButton("+"); btn_plus.setFixedSize(44, 44)
        btn_plus.setStyleSheet(f"QPushButton{{ background:{CREAM_MID}; border-radius:10px; font-size:18px; font-weight:bold; }} QPushButton:hover{{ background:{CREAM_DARK}; }}")
        
        step_row.addWidget(btn_min); step_row.addWidget(self.qty_lbl, 1); step_row.addWidget(btn_plus)
        cl.addLayout(step_row)
        
        # Max hint
        max_hint = QLabel(f"Max available: {max_qty}"); max_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        max_hint.setStyleSheet(f"color:{TEXT_LIGHT}; font-size:10px;")
        cl.addWidget(max_hint)

        # Why? (one click) - saved with the void so the owner can filter by reason
        why = QLabel("Why?"); why.setStyleSheet(f"color:{TEXT_DARK}; font-weight:bold;")
        cl.addWidget(why)
        self.reason = ""
        self._reason_btns = []
        grid = QGridLayout(); grid.setSpacing(6)
        for i, text in enumerate(VOID_REASONS):
            rb = QPushButton(text); rb.setFixedHeight(34); rb.setCheckable(True)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setStyleSheet(f"QPushButton{{ background:{WHITE}; color:{TEXT_DARK}; border:1px solid {BORDER}; border-radius:8px; font-size:12px; }}"
                             f"QPushButton:hover{{ border-color:{BROWN_MID}; }}"
                             f"QPushButton:checked{{ background:{BROWN}; color:white; border-color:{BROWN}; font-weight:bold; }}")
            rb.clicked.connect(lambda _, t=text, b=rb: self._pick_reason(t, b))
            grid.addWidget(rb, i // 2, i % 2)
            self._reason_btns.append(rb)
        cl.addLayout(grid)
        
        # Action Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setFixedHeight(40)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"QPushButton{{ background:{WHITE}; color:{TEXT_DARK}; border:1px solid {BORDER}; border-radius:10px; }}"
                             f"QPushButton:hover{{ background:{CREAM_MID}; }}")
        cancel.clicked.connect(self.reject)
        
        self.confirm = QPushButton(f"Void 1 Item"); self.confirm.setFixedHeight(40)
        self.confirm.setStyleSheet(f"QPushButton{{ background:{RED}; color:white; border-radius:10px; font-weight:bold; }} QPushButton:hover{{ background:{RED_DARK}; }}"
                                   f"QPushButton:disabled{{ background:{BORDER}; color:{TEXT_LIGHT}; }}")
        self.confirm.setEnabled(False)   # pick a reason first
        self.confirm.setToolTip("Choose why first")
        self.confirm.clicked.connect(self.accept)
        
        btn_row.addWidget(cancel); btn_row.addWidget(self.confirm)
        cl.addLayout(btn_row)
        
        outer.addWidget(card)
        
        # Logic
        btn_min.clicked.connect(lambda: self._update_qty(-1))
        btn_plus.clicked.connect(lambda: self._update_qty(1))
        
    def _pick_reason(self, text, btn):
        self.reason = text
        for b in self._reason_btns:
            b.setChecked(b is btn)
        self.confirm.setEnabled(True)

    def _update_qty(self, delta):
        new_val = max(1, min(self.max_qty, self.selected_qty + delta))
        self.selected_qty = new_val
        self.qty_lbl.setText(str(new_val))
        self.confirm.setText(f"Void {new_val} Item{'s' if new_val > 1 else ''}")


# ─────────────────────────────────────────────
#  VOID TRANSACTION DIALOG  (ported from original)
# ─────────────────────────────────────────────
class VoidTransactionDialog(QDialog):
    def __init__(self, db, parent=None, current_user=""):
        super().__init__(parent)
        self.db           = db
        self.current_user = current_user
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(1200, 560)
        self.selected_txn_time = None
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show(); self._overlay.raise_()
        self._init_ui(); self.load_transactions()
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-self.width())//2, (s.height()-self.height())//2)

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide(); self._overlay.deleteLater(); self._overlay = None

    def accept(self):   self._close_overlay(); super().accept()
    def reject(self):   self._close_overlay(); super().reject()
    def closeEvent(self, e): self._close_overlay(); super().closeEvent(e)

    def _tbl_style(self):
        return f"""
            QTableWidget {{ background:white;border:1px solid {BORDER};
                border-radius:8px;font-size:12px;color:{TEXT_DARK};outline:none; }}
            QHeaderView::section {{ background:{BROWN};color:white;padding:8px 10px;
                font-weight:bold;font-size:11px;border:none; }}
            QTableWidget::item {{ padding:4px 10px;border-bottom:1px solid {BORDER}; }}
            QTableWidget::item:selected {{ background:{CREAM_MID};color:{TEXT_DARK}; }}
        """

    def _init_ui(self):
        main = QVBoxLayout(self); main.setContentsMargins(15,15,15,20)
        card = QWidget(); card.setObjectName("VoidCard")
        card.setStyleSheet(f"""
            QWidget#VoidCard {{ background:{WHITE};border:1px solid {BORDER};
                border-radius:14px; }}
            QLabel {{ border:none;background:transparent; }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(22); shadow.setColor(QColor(0,0,0,28)); shadow.setOffset(0,6)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card); cl.setContentsMargins(22,18,22,18); cl.setSpacing(14)

        # header
        hdr = QHBoxLayout()
        ico = QLabel(); ico.setFixedSize(26,26)
        ico.setPixmap(make_svg_icon(SVG["receipt"], 22, BROWN))
        ico.setStyleSheet("background:transparent;border:none;")
        t = QLabel("Transaction History"); t.setFont(QFont("Segoe UI",15,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{TEXT_DARK};margin-left:5px;")
        close_btn = QPushButton(); close_btn.setFixedSize(30,30)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:15px;}"
            "QPushButton:hover{background:#F3F4F6;}")
        close_btn.setIcon(QIcon(make_svg_icon(SVG["close"], 16, TEXT_LIGHT)))
        close_btn.setIconSize(QSize(16,16)); close_btn.clicked.connect(self.reject)
        hdr.addWidget(ico); hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(close_btn)
        cl.addLayout(hdr)

        div = QFrame(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER};border:none;"); cl.addWidget(div)

        tables = QHBoxLayout(); tables.setSpacing(24)

        # left — transactions
        lw = QWidget(); ll = QVBoxLayout(lw); ll.setContentsMargins(0,0,0,0); ll.setSpacing(8)
        lt = QLabel("Recent Sales"); lt.setFont(QFont("Segoe UI",12,QFont.Weight.Bold))
        lt.setStyleSheet(f"color:{BROWN};")
        ll.addWidget(lt)
        self.txn_table = QTableWidget(); self.txn_table.setColumnCount(4)
        self.txn_table.setHorizontalHeaderLabels(["Time","Total","Items","Cashier"])
        self.txn_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.txn_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.txn_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.txn_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.txn_table.verticalHeader().setVisible(False)
        self.txn_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.txn_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.txn_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.txn_table.setShowGrid(False); self.txn_table.setStyleSheet(self._tbl_style())
        self.txn_table.itemSelectionChanged.connect(self._on_txn_selected)
        ll.addWidget(self.txn_table)
        tables.addWidget(lw, stretch=1)

        # right — items
        rw = QWidget(); rl = QVBoxLayout(rw); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
        rt = QLabel("Purchased Items"); rt.setFont(QFont("Segoe UI",12,QFont.Weight.Bold))
        rt.setStyleSheet(f"color:{BROWN};")
        rl.addWidget(rt)
        self.items_table = QTableWidget(); self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Item Name","Qty","Price","Action"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.items_table.setColumnWidth(1, 60)
        self.items_table.setColumnWidth(2, 90)
        self.items_table.setColumnWidth(3, 180)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.items_table.setShowGrid(False); self.items_table.setStyleSheet(self._tbl_style())
        rl.addWidget(self.items_table)
        tables.addWidget(rw, stretch=1)

        cl.addLayout(tables, stretch=1)
        main.addWidget(card)

    def load_transactions(self):
        try:
            txns = self.db.fetch_all(
                "SELECT created_at, SUM(amount) as total_amount, SUM(quantity) as qty,"
                " MAX(cashier) as cashier FROM sales GROUP BY created_at "
                "ORDER BY created_at DESC LIMIT 50")
            self.txn_table.setRowCount(len(txns))
            for row, t in enumerate(txns):
                raw = str(t['created_at'])
                ts  = raw[5:16] if len(raw) >= 16 else raw
                ti  = QTableWidgetItem(ts)
                ti.setData(Qt.ItemDataRole.UserRole, t['created_at'])
                for c, txt in enumerate([ts, f"₱{t['total_amount']:.2f}",
                                          str(t['qty']), str(t['cashier'] or "")]):
                    it = (ti if c == 0 else QTableWidgetItem(txt))
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.txn_table.setItem(row, c, it)
                self.txn_table.setRowHeight(row, 40)
        except Exception as e:
            print(f"[Void] load_transactions: {e}")

    def _on_txn_selected(self):
        sel = self.txn_table.selectedItems()
        if not sel:
            self.items_table.setRowCount(0); self.selected_txn_time = None; return
        row = sel[0].row()
        self.selected_txn_time = self.txn_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.load_items(self.selected_txn_time)

    def load_items(self, txn_time):
        try:
            # 1. Fetch all items (Active and Voided) for this transaction
            raw_items = self.db.fetch_all(
                "SELECT s.id, p.id as product_id, p.name, s.quantity, s.amount, "
                "COALESCE(s.is_voided, 0) as is_voided, s.voided_by "
                "FROM sales s JOIN products p ON s.product_id = p.id "
                "WHERE s.created_at = ?", (txn_time,))
            
            # 2. Group items by Product ID to merge them visually
            grouped = {}
            for row in raw_items:
                pid = row['product_id']
                if pid not in grouped:
                    grouped[pid] = {
                        'active_id': None, 
                        'name': row['name'], 
                        'active_qty': 0, 
                        'active_amt': 0.0,
                        'voided_qty': 0, 
                        'voided_by': None
                    }
                
                if row['is_voided']:
                    grouped[pid]['voided_qty'] += row['quantity']
                    # Keep track of the last person who performed a void on this item
                    if row['voided_by']: grouped[pid]['voided_by'] = row['voided_by']
                else:
                    # Store the ID of the 'Active' row so the Void button knows which record to subtract from
                    grouped[pid]['active_id'] = row['id']
                    grouped[pid]['active_qty'] += row['quantity']
                    grouped[pid]['active_amt'] += row['amount']

            # 3. Build the table based on grouped data
            self.items_table.setRowCount(len(grouped))
            for i, (pid, data) in enumerate(grouped.items()):
                # ── Column 0: Item Name + Aggregate History Label ──────
                container = QWidget()
                container.setStyleSheet("background:transparent;")
                layout = QVBoxLayout(container)
                layout.setContentsMargins(10, 4, 10, 4); layout.setSpacing(0)
                
                name_lbl = QLabel(data['name'])
                name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
                name_lbl.setStyleSheet("background:transparent; border:none;")
                layout.addWidget(name_lbl)
                
                # Show the history label if any units were voided
                if data['voided_qty'] > 0:
                    status_text = f"({data['voided_qty']} unit(s) already voided by {data['voided_by'] or 'Admin'})"
                    mini_label = QLabel(status_text)
                    mini_label.setFont(QFont("Segoe UI", 9))
                    mini_label.setStyleSheet(f"color:{RED}; font-style: italic; background:transparent; border:none;")
                    layout.addWidget(mini_label)
                
                if data['active_qty'] == 0:
                    name_lbl.setStyleSheet(f"color:{TEXT_LIGHT}; background:transparent; border:none;")

                self.items_table.setCellWidget(i, 0, container)

                # ── Column 1 & 2: Remaining Qty and Price ──────────────
                q_txt = str(data['active_qty'])
                p_txt = f"₱{data['active_amt']:.2f}"
                
                for col_idx, txt in enumerate([q_txt, p_txt]):
                    it = QTableWidgetItem(txt)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if data['active_qty'] == 0:
                        it.setForeground(QBrush(QColor(TEXT_LIGHT)))
                    self.items_table.setItem(i, col_idx + 1, it)

                # ── Column 3: Intelligent Void Button ──────────────────
                ac_w = QWidget(); 
                al = QHBoxLayout(ac_w)
                ac_w.setStyleSheet("background:transparent;")
                al.setContentsMargins(4,4,4,4); al.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Only show the Void button if there are still active items left
                if data['active_qty'] > 0:
                    vb = QPushButton("Void")
                    vb.setCursor(Qt.CursorShape.PointingHandCursor)
                    vb.setStyleSheet(f"""
                        QPushButton {{ background:transparent; color:{RED}; border:1px solid #FECACA;
                        border-radius:6px; padding:5px 14px; font-size:12px; font-weight:600; }}
                        QPushButton:hover {{ background:{RED_DIM}; border-color:{RED}; }}""")
                    
                    # Connect to your void_specific_item method from the previous turn
                    # 🟢 FIX: I-capture ang 'pid' as 'p=pid' para hindi ma-late bind sa last item!
                    vb.clicked.connect(lambda _, d=data, p=pid: self.void_specific_item(
                        d['active_id'], p, d['name'], d['active_qty'], d['active_amt']))
                    al.addWidget(vb)
                else:
                    lbl = QLabel("FULLY VOIDED")
                    lbl.setStyleSheet(f"color:{RED}; font-size:10px; font-weight:bold;")
                    al.addWidget(lbl)
                
                self.items_table.setCellWidget(i, 3, ac_w)
                self.items_table.setRowHeight(i, 65)

        except Exception as e:
            print(f"[Void] aggregated load_items error: {e}")

    def void_specific_item(self, item_row_id, product_id, product_name, total_qty, total_amount):
        # 1. Open the new Quantity Selector Dialog
        v_dlg = VoidQtyDialog(product_name, total_qty, self)
        if v_dlg.exec() != QDialog.DialogCode.Accepted:
            return
            
        void_qty = v_dlg.selected_qty
        unit_price = total_amount / total_qty
        u = self.current_user or "Unknown"
        
        try:
            # Lahat ng void steps ay isang transaction: walang half-applied na void
            with self.db.transaction():
                # Case A: Voiding EVERYTHING in that line
                if void_qty == total_qty:
                    self.db.execute_query(
                        "UPDATE sales SET is_voided=1, voided_by=? WHERE id=?", 
                        (u, item_row_id))
            
                # Case B: PARTIAL VOID
                else:
                    new_qty = total_qty - void_qty
                    new_amt = unit_price * new_qty
                    # Reduce the original order
                    self.db.execute_query(
                        "UPDATE sales SET quantity=?, amount=? WHERE id=?", 
                        (new_qty, new_amt, item_row_id))
                    # Create a new record for the voided portion (for logs/reports)
                    self.db.execute_query(
                        "INSERT INTO sales (product_id, quantity, amount, cashier, created_at, is_voided, voided_by) "
                        "VALUES (?, ?, ?, ?, datetime('now','localtime'), 1, ?)",
                        (product_id, void_qty, unit_price * void_qty, u, u))

                # 2. Return stock to inventory
                self.db.execute_query(
                    "UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", 
                    (void_qty, product_id))
            
                # 3. Log the action
                try:
                    reason = v_dlg.reason or "Not given"
                    self.db.execute_query(
                        "INSERT INTO void_logs (product_id, quantity, amount, reason, voided_by) VALUES (?,?,?,?,?)",
                        (product_id, void_qty, unit_price * void_qty, reason, u))
                
                    # 🟢 BAGONG DAGDAG: I-sync ito sa Finance Recent Activity
                    self.db.execute_query(
                        "INSERT INTO financial_audit_log (icon, description, action_by) VALUES (?, ?, ?)",
                        ("receipt", f"Voided {void_qty}x {product_name} (-₱{unit_price * void_qty:,.2f})", u)
                    )

                    # 🟢 FIX: I-sync din ito sa inventory_action_log para lumabas sa System Audit Logs (audit_logs.py)
                    self.db.execute_query(
                        "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?, ?, ?, ?, ?)",
                        ("product", product_id, product_name, "voided", u)
                    )
                except Exception as e:
                    print(f"[Void] audit log error: {e}")

            log_activity(self.db, u, "sale voided", "void",
                         f"{void_qty} x {product_name} (-₱{unit_price * void_qty:,.2f}) - reason: {v_dlg.reason or 'not given'}")

            # 4. Refresh UI
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            BakeSyncAlert.show_success(self, "Success", f"Voided {void_qty} unit(s) of {product_name}.")
            
            self.load_transactions()
            if self.selected_txn_time:
                self.load_items(self.selected_txn_time)
            if hasattr(self.parent(), 'load_products'):
                self.parent().load_products()
                
        except Exception as e:
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            BakeSyncAlert.show_error(self, "Void Error", str(e))


# ─────────────────────────────────────────────
#  MAIN POS WIDGET  ← the big integration
# ─────────────────────────────────────────────
class POSWidget(QWidget):
    sale_completed = pyqtSignal()

    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db            = db
        self.current_user  = current_user
        self.cart: list[CartItem]  = []
        self._undo_stack: list[tuple[int, int]] = []   # (prod_id, qty added) for Undo
        self.session_sales: list[CartItem] = []
        self._pending_qty: int    = 1
        self._qty_mode: bool      = False
        self._stock_filter: str   = ""      # "in" | "low" | "out" | ""
        self._active_cat: str     = ""      # lowercase category name
        self._all_cards: list[ProductCard] = []
        self._toast               = ToastNotification(self)
        self._held_orders: dict = {}
        self._discount_pct: float = 0.0

        # DB migrations (safe)
        for ddl in [
            "ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'bread'",
            "ALTER TABLE products ADD COLUMN image_path TEXT",
            "ALTER TABLE sales    ADD COLUMN voided_by TEXT",
        ]:
            try: self.db.execute_query(ddl)
            except Exception: pass

        self._build_ui()
        self.load_products()
        self._start_clock()
        self._install_extra_shortcuts()

    # ──────────────────────────────────────────
    #  showEvent  (re-detect logged-in user)
    # ──────────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        for w in QApplication.topLevelWidgets():
            for attr in ('current_user', 'logged_in_user', 'username'):
                v = getattr(w, attr, None)
                if v:
                    self.current_user = v; break
        self.load_products()
        self._refresh_cart()

    def _build_ui(self):
        # 🟢 GINAWANG HORIZONTAL LAYOUT ANG ROOT (Left and Right Split)
        root = QHBoxLayout(self) 
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"""
            QWidget {{ background:{CREAM}; }}
            QScrollBar:vertical {{
                background:{CREAM_MID};
                width:6px;
                border-radius:3px;
                margin:0;
            }}
            QScrollBar::handle:vertical {{
                background:{BROWN_MID};
                border-radius:3px;
                min-height:30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background:{BROWN_DARK};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height:0;
                background:none;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background:none;
            }}
            QScrollBar:horizontal {{
                background:{CREAM_MID};
                height:6px;
                border-radius:3px;
                margin:0;
            }}
            QScrollBar::handle:horizontal {{
                background:{BROWN_MID};
                border-radius:3px;
                min-width:30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background:{BROWN_DARK};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width:0;
                background:none;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background:none;
            }}
        """)

        # ── LEFT PANEL (Header, Tabs, Filters, Grid) ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 1. Header (Hotkeys, EOD, etc.)
        header = self._make_header()
        left_layout.addWidget(header)

        # 2. Tabs (Categories)
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(48)
        self._tab_bar.setStyleSheet(
            f"background:{BROWN_DARK};"
            f"border-bottom:1px solid rgba(255,255,255,0.1);")
        self._tab_layout = QHBoxLayout(self._tab_bar)
        self._tab_layout.setContentsMargins(18, 0, 18, 0)
        self._tab_layout.setSpacing(0)
        left_layout.addWidget(self._tab_bar)

        # 3. Filter bar (In stock, Low stock, etc.)
        filter_bar = self._make_filter_bar()
        left_layout.addWidget(filter_bar)

        # 3b. Mabenta Ngayon: one click for the best sellers
        self._best_bar = QWidget()
        self._best_bar.setFixedHeight(54)
        self._best_bar.setStyleSheet(f"background:{CREAM};border-bottom:1px solid {BORDER};")
        bb = QHBoxLayout(self._best_bar)
        bb.setContentsMargins(18, 0, 18, 0); bb.setSpacing(8)
        self._best_title = QLabel("Best sellers today:")
        self._best_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._best_title.setStyleSheet(f"color:{BROWN};background:transparent;border:none;")
        bb.addWidget(self._best_title)
        self._best_btns_layout = QHBoxLayout(); self._best_btns_layout.setSpacing(8)
        bb.addLayout(self._best_btns_layout)
        bb.addStretch()
        self._best_bar.hide()
        left_layout.addWidget(self._best_bar)

        # 4. Grid Stack (Mismong mga tinapay)
        self._grid_stack = QStackedWidget()
        self._cat_grids: dict[str, QGridLayout] = {}
        left_layout.addWidget(self._grid_stack, stretch=1)

        root.addWidget(left_panel, stretch=1)

        # ── RIGHT PANEL (Search Bar + Current Order) ──
        right_border = QWidget()
        right_border.setFixedWidth(372)
        right_border.setStyleSheet(
            f"background:transparent;"
            f"border-left:2px solid {BROWN_DARK};"
        )
        right_border_layout = QHBoxLayout(right_border)
        right_border_layout.setContentsMargins(2, 0, 0, 0)
        right_border_layout.setSpacing(0)

        # Inner panel — holds all the actual content
        right_panel = QWidget()
        right_panel.setFixedWidth(370)
        right_panel.setStyleSheet(f"background:{WHITE};border:none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_border_layout.addWidget(right_panel)

        # 1. Search Bar (Nasa taas agad ng Current Order)
        op_top = QWidget()
        op_top.setFixedHeight(56)
        op_top.setStyleSheet(f"""
            background:white;
            border-bottom:1px solid {BORDER_MID};
        """)
        ot = QHBoxLayout(op_top)
        ot.setContentsMargins(14, 0, 14, 0)
        ot.setSpacing(8)
        
        s_ico = svg_label(SVG["search"], 15, BROWN_MID)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search, then Enter to add  ·  e.g. 30 pan")
        self._search_input.setFrame(False)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background:transparent;
                color:{BROWN_DARK};
                font-size:13px;
                font-family:'Segoe UI';
                border:none;
                outline:none;
                selection-background-color:{BROWN_MID};
                selection-color:{WHITE};
            }}
            QLineEdit::placeholder {{
                color:{BROWN_LIGHT};
            }}
        """)
        self._search_input.textChanged.connect(self._apply_filters)
        self._search_input.returnPressed.connect(self._add_from_search)

        ot.addWidget(s_ico)
        ot.addWidget(self._search_input)
        
        right_layout.addWidget(op_top)

        # 2. Current Order Panel Body (Direktang nakadikit sa ilalim ng Search Bar)
        order_body = self._make_order_panel_body()
        right_layout.addWidget(order_body, stretch=1)

        root.addWidget(right_border)

        self._clock_lbl = QLabel(self)
        self._clock_lbl.hide()

    # ── HEADER ────────────────────────────────
    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet(
            f"background:#3D1F0D;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(0)

        # ── HOTKEYS label ─────────────────────────────────
        hotkey_lbl = QLabel("HOTKEYS:")
        hotkey_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        hotkey_lbl.setStyleSheet(f"color:rgba(255,255,255,0.6);background:transparent;border:none;")
        hl.addWidget(hotkey_lbl)
        hl.addSpacing(20)

        # ── F9 / F10 / F11 pill buttons ───────────────────
        hotkey_specs = [
            ("F9 CLEAR",  RED_DARK),
            ("F10 VOID",  AMBER),
            ("F11 PAY",   GREEN_DARK),
        ]
        for label, color in hotkey_specs:
            b = QLabel(label)
            b.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            b.setStyleSheet(f"""
                color:{color};
                background:transparent;
                border:none;
                font-size:10px;
                font-weight:demibold;
                letter-spacing:0.05em;
            """)
            hl.addWidget(b)
            hl.addSpacing(20)

        hl.addStretch()

        # ── STOCKS / SALES / EOD ──────────────────────────
        for label, callback in [
            ("STOCKS", self._show_stocks),
            ("SALES",  self._show_sales),
            ("EOD",    self._end_of_day),
        ]:
            b = QPushButton(label)
            b.setFixedHeight(56)
            b.setMinimumWidth(80)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;color:{WHITE};
                    border:none;
                    font-size:12px;font-weight:600;padding:0 18px;
                    letter-spacing:0.05em;
                }}
                QPushButton:hover {{ background:rgba(255,255,255,0.08); }}
            """)
            b.clicked.connect(callback)
            hl.addWidget(b)

        # ── keyboard shortcuts ────────────────────────────
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("F9"),  self, self._confirm_clear_cart)
        QShortcut(QKeySequence("F10"), self, self._void_action)
        QShortcut(QKeySequence("F11"), self, self._process_payment)

        # ── hidden clock label (kept for _tick compatibility) ──
        self._clock_hdr = QLabel()
        self._clock_hdr.hide()

        return hdr

    # ── FILTER BAR ────────────────────────────
    def _make_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(50)
        bar.setStyleSheet(
            f"background:{WHITE};border-bottom:1px solid {BORDER};")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(18, 0, 18, 0); bl.setSpacing(20)

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)

        for label, value in [("All",""),("In Stock","in"),
                              ("Low Stock","low"),("Out of Stock","out")]:
            p = FilterPill(label, value)
            if value == "":
                p.setChecked(True)
            self._filter_group.addButton(p)
            p.clicked.connect(lambda checked, v=value, btn=p: self._set_stock_filter(v, btn))
            bl.addWidget(p)

        bl.addStretch()

        # sort
        self._sort_cb = QComboBox()
        self._sort_cb.addItems(
            ["Default", "Name A→Z", "Price: Low→High", "Price: High→Low"])
        self._sort_cb.setFixedHeight(34)
        
        # 🟢 AUTO-CREATE ICON SCRIPT 🟢
        import os
        # Hanapin ang 'images' folder (kung saan nakalagay ang poplogo mo)
        script_dir = os.path.dirname(__file__)
        img_dir = IMAGES_DIR
        os.makedirs(img_dir, exist_ok=True) # Siguraduhing may images folder
        
        arrow_path = os.path.join(img_dir, "dropdown_arrow.svg")
        
        # Isulat ang SVG file sa folder kung wala pa ito
        if not os.path.exists(arrow_path):
            svg_content = "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#8B5E3C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>"
            with open(arrow_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
        
        # Ayusin ang path format para mabasa ng PyQt CSS (palitan ang \ ng /)
        css_arrow_path = arrow_path.replace("\\", "/")

        self._sort_cb.setStyleSheet(f"""
            QComboBox {{
                background: {CREAM};
                border: 1.5px solid {BORDER};
                border-radius: 8px;
                padding: 4px 30px 4px 14px;
                color: {TEXT_DARK};
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{ 
                border-color: {BROWN_MID}; 
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: none;
            }}
            
            /* 🟢 Ginamit na natin yung local file na ginawa ng system natin! */
            QComboBox::down-arrow {{
                image: url("{css_arrow_path}");
                width: 16px;
                height: 16px;
            }}
            
            QComboBox::down-arrow:on {{
                top: 1px;
                left: 1px;
            }}
            
            QComboBox QAbstractItemView {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                selection-background-color: {CREAM_MID};
                selection-color: {TEXT_DARK};
                outline: none;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                height: 32px;
                border-radius: 6px;
                padding-left: 8px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {CREAM};
            }}
        """)
        self._sort_cb.currentIndexChanged.connect(self._apply_filters)
        bl.addWidget(self._sort_cb)
        return bar

    # ── ORDER PANEL ───────────────────────────
    def _make_order_panel(self) -> QWidget:
        return self._make_order_panel_body()
    
    def _make_order_panel_body(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(370)
        panel.setObjectName("orderPanelContainer")
        panel.setStyleSheet(f"""
            QWidget#orderPanelContainer {{
                background:{WHITE};
                border:none;
            }}
            QWidget#orderPanelHdr {{
                background:{WHITE};
                border:none;
                border-bottom:1px solid {BORDER};
            }}
        """)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # ── Order panel header ────────────────
        op_hdr = QWidget()
        op_hdr.setFixedHeight(48)
        op_hdr.setObjectName("orderPanelHdr")
        op_hdr.setStyleSheet(
            f"QWidget#orderPanelHdr {{ background:{WHITE};border-bottom:1px solid {BORDER}; }}")
        oh = QHBoxLayout(op_hdr)
        oh.setContentsMargins(16, 0, 16, 0)
        oh.setSpacing(8)
        order_title = QLabel("CURRENT ORDER")
        order_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        order_title.setStyleSheet(
            f"color:{TEXT_DARK};background:transparent;border:none;letter-spacing:0.05em;")
        self._order_badge = QLabel("0 items")
        self._order_badge.setFixedHeight(24)
        self._order_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._order_badge.setStyleSheet(
            f"background:{BROWN};color:{WHITE};"
            f"border-radius:12px;padding:0px 12px;border:none;"
            f"font-size:11px;font-weight:bold;")
        oh.addWidget(order_title)
        oh.addStretch()
        oh.addWidget(self._order_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        pl.addWidget(op_hdr)

        # ── Change banner (shown right after a sale, instead of a receipt popup) ──
        self._change_banner = QFrame(); self._change_banner.setObjectName("chg")
        self._change_banner.setStyleSheet(f"QFrame#chg {{ background:{UI['green_bg']}; border:2px solid #9FD3B1; border-radius:16px; }}"
                                          "QLabel { background:transparent; border:none; }")
        cb = QVBoxLayout(self._change_banner); cb.setContentsMargins(18, 16, 18, 16); cb.setSpacing(4)
        top = QHBoxLayout(); top.setSpacing(8)
        ok_ic = QLabel(); ok_ic.setPixmap(ui_pixmap("check_circle", UI["green"], 22))
        top.addWidget(ok_ic)
        ok_t = QLabel("Paid. Give change:"); ok_t.setStyleSheet(f"color:{UI['green']};font-size:15px;font-weight:bold;")
        top.addWidget(ok_t); top.addStretch()
        cb.addLayout(top)
        self._chg_amount = QLabel("₱0.00")
        self._chg_amount.setFont(QFont("Segoe UI", 34, QFont.Weight.Bold))
        self._chg_amount.setStyleSheet(f"color:{UI['green']};")
        cb.addWidget(self._chg_amount)
        self._chg_detail = QLabel(""); self._chg_detail.setStyleSheet(f"color:{TEXT_MID};font-size:13px;")
        cb.addWidget(self._chg_detail)
        self._undo_sale_btn = QPushButton()
        self._undo_sale_btn.setIcon(ui_icon("undo", UI["red"], 16))
        self._undo_sale_btn.setFixedHeight(36)
        self._undo_sale_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._undo_sale_btn.setToolTip("Wrong button? Cancel this sale and put the items back")
        self._undo_sale_btn.setStyleSheet(f"QPushButton {{ background:white; color:{UI['red']}; border:1px solid #F1C2BE; border-radius:9px; "
                                          f"font-size:13px; font-weight:600; padding:0 12px; }} QPushButton:hover {{ background:{UI['red_bg']}; }}")
        self._undo_sale_btn.clicked.connect(self._undo_last_sale)
        cb.addSpacing(6)
        cb.addWidget(self._undo_sale_btn)
        self._change_banner.hide()
        banner_wrap = QWidget(); bw = QVBoxLayout(banner_wrap); bw.setContentsMargins(12, 12, 12, 0)
        bw.addWidget(self._change_banner)
        pl.addWidget(banner_wrap)
        self._banner_wrap = banner_wrap
        self._last_sale = None
        self._undo_timer = QTimer(self); self._undo_timer.timeout.connect(self._tick_undo)
        self._banner_timer = QTimer(self); self._banner_timer.setSingleShot(True)
        self._banner_timer.timeout.connect(self._hide_change_banner)

        # ── Empty state ───────────────────────
        self._empty_widget = QWidget()
        el = QVBoxLayout(self._empty_widget)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(10)
        cart_ico = svg_label(SVG["cart"], 54, BORDER)
        empty_lbl = QLabel("Select products from\nthe left to begin")
        empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_lbl.setFont(QFont("Segoe UI", 12))
        empty_lbl.setStyleSheet(
            f"color:{TEXT_LIGHT};background:;border:none;")
        el.addWidget(cart_ico, alignment=Qt.AlignmentFlag.AlignCenter)
        el.addWidget(empty_lbl)
        pl.addWidget(self._empty_widget, stretch=1)

        # ── Cart scroll area ──────────────────
        self._cart_scroll = QScrollArea()
        self._cart_scroll.setWidgetResizable(True)
        self._cart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._cart_scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollArea > QWidget > QWidget{{background:transparent;}}"
            "QScrollBar:vertical{width:3px;background:transparent;}"
            "QScrollBar::handle:vertical{background:#D0C0B0;border-radius:2px;}")
        self._cart_container = QWidget()
        self._cart_container.setStyleSheet("background:transparent;border:none;")
        self._cart_vbox = QVBoxLayout(self._cart_container)
        self._cart_vbox.setContentsMargins(10, 10, 10, 10)
        self._cart_vbox.setSpacing(10)
        self._cart_vbox.addStretch()
        self._cart_scroll.setWidget(self._cart_container)
        pl.addWidget(self._cart_scroll, stretch=1)
        self._cart_scroll.hide()

        # ── Hold + Clear All row ──────────────
        action_row_widget = QWidget()
        action_row_widget.setStyleSheet(
            f"QWidget {{ background:{WHITE}; }} "
            f"QWidget {{ border-top:1px solid {BORDER}; }}")
        action_row_widget.setFixedHeight(52)
        ar = QHBoxLayout(action_row_widget)
        ar.setContentsMargins(12, 8, 12, 8)
        ar.setSpacing(8)

        self._held_btn = QPushButton("Hold")
        self._held_btn.setFixedHeight(36)
        self._held_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._held_btn.setStyleSheet(f"""
            QPushButton {{
                background:white;color:black;
                border:1px solid {BROWN_DARK};border-radius:8px;
                font-size:12px;font-weight:600;
            }}
            QPushButton:hover {{ background:{BROWN_DARK};color:{WHITE}; }}
            """)
        self._held_btn.clicked.connect(self._hold_cart)

        self._recall_btn = QPushButton("Held (0)")
        self._recall_btn.setFixedHeight(36)
        self._recall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._recall_btn.clicked.connect(self._recall_held)
        self._recall_btn.hide()

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(36)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background:white;color:black;
                border:1px solid {BROWN_DARK};border-radius:8px;
                font-size:12px;font-weight:600;
            }}
            QPushButton:hover {{ background:{RED_DARK};color:{WHITE}; }}
            """)
        clear_btn.clicked.connect(self._confirm_clear_cart)

        self._undo_btn = QPushButton("  Undo")
        self._undo_btn.setIcon(ui_icon("undo", BROWN_DARK, 15))
        self._undo_btn.setFixedHeight(36)
        self._undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._undo_btn.setToolTip("Take back the last item you added (Ctrl+Z)")
        self._undo_btn.setStyleSheet(self._held_btn.styleSheet())
        self._undo_btn.clicked.connect(self._undo_last_add)
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_last_add)

        ar.addWidget(self._undo_btn)
        ar.addWidget(self._held_btn)
        ar.addWidget(self._recall_btn)
        ar.addWidget(clear_btn)
        pl.addWidget(action_row_widget)

        # ── Totals ────────────────────────────
        totals_frame = QFrame()
        totals_frame.setStyleSheet(f"""
            QFrame {{
                background:{WHITE};
                border:none;
                border-top:1px solid {BORDER};
            }}
            QFrame QLabel {{
                background:transparent;
                border:none;
            }}
        """)
        tf = QVBoxLayout(totals_frame)
        tf.setContentsMargins(18, 12, 18, 0)
        tf.setSpacing(4)

        for attr, lbl_txt in [("_tot_sub", "Subtotal"), ("_tot_items", "Items")]:
            row = QHBoxLayout()
            la = QLabel(lbl_txt)
            la.setFont(QFont("Segoe UI", 11))
            la.setStyleSheet(f"color:{TEXT_MID};background:transparent;border:none;")
            lv = QLabel("₱0.00" if "sub" in attr else "0 pcs")
            lv.setFont(QFont("Segoe UI", 11))
            lv.setAlignment(Qt.AlignmentFlag.AlignRight)
            lv.setStyleSheet(f"color:{TEXT_MID};background:transparent;border:none;")
            setattr(self, attr, lv)
            row.addWidget(la)
            row.addWidget(lv)
            tf.addLayout(row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{BORDER};border:none;margin:4px 0;")
        tf.addWidget(sep)

        grand_row = QHBoxLayout()
        gl = QLabel("Total")
        gl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        gl.setStyleSheet(f"color:{TEXT_DARK};background:transparent;border:none;")
        self._tot_grand = QLabel("₱0.00")
        self._tot_grand.setFont(QFont("Georgia", 26, QFont.Weight.Bold))
        self._tot_grand.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._tot_grand.setStyleSheet(f"color:{BROWN};background:transparent;border:none;")
        grand_row.addWidget(gl)
        grand_row.addWidget(self._tot_grand)
        tf.addLayout(grand_row)
        pl.addWidget(totals_frame)

        # ── Fast pay: one click = paid ─────────
        pay = QWidget(); pay.setObjectName("payArea")
        pay.setStyleSheet(f"QWidget#payArea {{ background:{WHITE}; }} QLabel {{ background:transparent; border:none; }}")
        pv = QVBoxLayout(pay); pv.setContentsMargins(16, 6, 16, 16); pv.setSpacing(8)
        hint = QLabel("Customer paid:  (one click)")
        hint.setStyleSheet(f"color:{TEXT_MID};font-size:12px;")
        pv.addWidget(hint)
        self._exact_btn = QPushButton()
        self._exact_btn.setFixedHeight(54)
        self._exact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._exact_btn.setToolTip("The customer gave the exact amount")
        self._exact_btn.clicked.connect(lambda: self._quick_pay(None))
        pv.addWidget(self._exact_btn)
        bills = QHBoxLayout(); bills.setSpacing(8)
        self._bill_btns = []
        for _ in range(3):
            b = QPushButton(); b.setFixedHeight(46); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(self._on_bill_clicked)
            bills.addWidget(b); self._bill_btns.append(b)
        pv.addLayout(bills)
        self._other_btn = QPushButton("  Other amount  (F11)")
        self._other_btn.setIcon(ui_icon("edit", BROWN, 16))
        self._other_btn.setFixedHeight(40)
        self._other_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._other_btn.setToolTip("Type the exact cash the customer gave, e.g. ₱1,050")
        self._other_btn.clicked.connect(self._process_payment)
        pv.addWidget(self._other_btn)
        pl.addWidget(pay)
        self._update_pay_btn(0.0)
        return panel

        

    def _update_pay_btn(self, total: float):
        enabled = total > 0
        self._exact_btn.setEnabled(enabled)
        self._other_btn.setEnabled(enabled)
        self._exact_btn.setText(f"  Exact   ₱{total:,.2f}" if enabled else "  Exact amount")
        self._exact_btn.setIcon(ui_icon("check", WHITE if enabled else TEXT_LIGHT, 20))
        self._exact_btn.setStyleSheet(f"""
            QPushButton {{ background:{GREEN}; color:{WHITE}; border:none; border-radius:12px; font-size:17px; font-weight:bold; }}
            QPushButton:hover {{ background:{GREEN_DARK}; }}
            QPushButton:disabled {{ background:{CREAM_MID}; color:{TEXT_LIGHT}; }}""")
        bills = [v for v in suggested_amounts(total)[1:]] if enabled else []
        for i, b in enumerate(self._bill_btns):
            if i < len(bills):
                b.setText(f"₱{bills[i]:,.0f}"); b.setProperty("amount", bills[i]); b.setEnabled(True)
            else:
                b.setText("—"); b.setProperty("amount", None); b.setEnabled(False)
            b.setStyleSheet(f"""
                QPushButton {{ background:#FFF4E8; color:{TEXT_DARK}; border:1px solid {BORDER}; border-radius:10px; font-size:16px; font-weight:bold; }}
                QPushButton:hover {{ background:{CREAM_DARK}; border-color:{BROWN_MID}; color:{BROWN}; }}
                QPushButton:disabled {{ background:{CREAM_MID}; color:{TEXT_LIGHT}; border:none; }}""")
        self._other_btn.setStyleSheet(f"""
            QPushButton {{ background:white; color:{BROWN}; border:1px solid {BORDER}; border-radius:10px; font-size:13px; font-weight:600; }}
            QPushButton:hover {{ background:{CREAM_MID}; }}
            QPushButton:disabled {{ color:{TEXT_LIGHT}; }}""")

    # ══════════════════════════════════════════
    #  CLOCK
    # ══════════════════════════════════════════
    def _start_clock(self):
        self._tick()
        t = QTimer(self); t.timeout.connect(self._tick); t.start(10000)

    def _tick(self):
        now = QDateTime.currentDateTime()
        txt = now.toString("ddd  MMM d  ·  h:mm AP")
        self._clock_hdr.setText(txt)

    # ══════════════════════════════════════════
    #  PRODUCT LOADING
    # ══════════════════════════════════════════
    def _build_category_tabs(self, cat_names: list[str]):
        # clear old tabs. Take them out of their (exclusive) button group and silence them first:
        # otherwise the group re-checks a tab that is being deleted and its restyle slot runs on
        # a half-destroyed widget, which crashes the app.
        old_group = getattr(self, "_cat_tab_group", None)
        while self._tab_layout.count():
            item = self._tab_layout.takeAt(0)
            w = item.widget()
            if w:
                w.blockSignals(True)
                if old_group is not None:
                    old_group.removeButton(w)
                w.hide()
                w.deleteLater()
        if old_group is not None:
            old_group.deleteLater()
        # clear old stacked pages
        while self._grid_stack.count():
            w = self._grid_stack.widget(0)
            self._grid_stack.removeWidget(w)
            w.deleteLater()
        self._cat_grids.clear()

        self._cat_tabs: list[CategoryTab] = []
        self._cat_tab_group = QButtonGroup(self)
        self._cat_tab_group.setExclusive(True)

        for i, cat in enumerate(cat_names):
            tab = CategoryTab(cat, 0)
            self._cat_tabs.append(tab)
            self._cat_tab_group.addButton(tab)
            if i == 0:
                tab.setChecked(True)
                self._active_cat = cat.lower()
            tab._cat_index, tab._cat_name = i, cat
            tab.clicked.connect(self._on_cat_tab_clicked)
            self._tab_layout.addWidget(tab)

            # scrollable page
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet(
                "QScrollArea{background:transparent;border:none;}"
                "QScrollBar:vertical{width:4px;background:transparent;}"
                "QScrollBar::handle:vertical{background:#C0B0A0;border-radius:2px;}")
            container = QWidget()
            container.setStyleSheet("background:transparent;")
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            grid = QGridLayout(container)
            grid.setContentsMargins(18, 16, 18, 16); grid.setSpacing(14)
            grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            scroll.setWidget(container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._grid_stack.addWidget(scroll)
            self._cat_grids[cat.lower()] = grid

        self._tab_layout.addStretch()

    def load_products(self):
        if not hasattr(self, '_cat_grids'):
            return

        # 1. KUNIN ANG CATEGORIES (Ligtas at may Fallback)
        cat_names = ["Bread"]
        try:
            cats = self.db.fetch_all(
                "SELECT DISTINCT COALESCE(NULLIF(TRIM(product_type),''),'Others') as pt FROM products WHERE is_archived=0 ORDER BY pt ASC"
            )
            if cats:
                fetched = []
                for c in cats:
                    # I-convert ang row sa dictionary para safe ang paghugot
                    c_dict = dict(c) if hasattr(c, 'keys') else c
                    val = c_dict.get('pt') if isinstance(c_dict, dict) else c[0]
                    fetched.append(str(val).strip().title())
                
                if "Bread" in fetched:
                    fetched.remove("Bread")
                cat_names = ["Bread"] + fetched
        except Exception as e:
            print("Category fetch error:", e)

        self._build_category_tabs(cat_names)

        # 2. KUNIN ANG PRODUCTS (May Fallback Queries)
        products = []
        try:
            products = self.db.fetch_all(
                "SELECT id, name, retail_price, stock_qty, product_type, image_path FROM products WHERE is_archived=0 ORDER BY name ASC"
            )
        except Exception:
            try:
                products = self.db.fetch_all(
                    "SELECT id, name, retail_price, stock_qty FROM products WHERE is_archived=0 ORDER BY name ASC"
                )
            except Exception as e:
                print("Product fetch error:", e)
                return

        self._all_cards.clear()
        
        # Ihanda ang counters para sa Grid
        grid_idx = {c.lower(): 0 for c in cat_names}
        all_names = []
        cols = 3

        for p in products:
            try:
                # 🟢 SAFE DICTIONARY CONVERSION (Para iwas crash)
                p_dict = dict(p) if hasattr(p, 'keys') else p
                
                prod_id = p_dict.get('id')
                name = p_dict.get('name', 'Unknown')
                price = float(p_dict.get('retail_price') or 0.0)
                
                total_stock = p_dict.get('stock_qty')
                total_stock = int(total_stock) if total_stock is not None else 0
                
                ptype_raw = p_dict.get('product_type', 'bread')
                ptype = str(ptype_raw if ptype_raw else 'bread').strip().lower()
                
                img = product_image(p_dict.get('image_path'))

                # Check Expiry
                try:
                    er = self.db.fetch_one(
                        "SELECT COALESCE(SUM(quantity_remaining),0) AS eq "
                        "FROM product_batches WHERE product_id=? "
                        "AND quantity_remaining>0 AND expiry_date IS NOT NULL "
                        "AND expiry_date<=date('now', 'localtime')", (prod_id,)
                    )
                    er_dict = dict(er) if hasattr(er, 'keys') else er
                    expired = int(er_dict.get('eq', 0)) if isinstance(er_dict, dict) else int(er[0])
                except Exception:
                    expired = 0
                    
                stock = max(0, total_stock - expired)

                card = ProductCard(prod_id, name, price, stock, img, prod_type=ptype)
                card.prod_image_path = img
                card.clicked_signal.connect(self._add_to_cart_by_id)
                self._all_cards.append(card)
                all_names.append(name)

                # Ilagay sa tamang Category Grid
                matched_cat = cat_names[0].lower() # Fallback (Bread)
                for cat_key in self._cat_grids:
                    if cat_key == ptype or ptype in cat_key:
                        matched_cat = cat_key
                        break
                
                grid = self._cat_grids[matched_cat]
                card._current_grid = grid
                
                idx = grid_idx[matched_cat]
                grid.addWidget(card, idx // cols, idx % cols)
                grid_idx[matched_cat] += 1
                
            except Exception as e:
                print(f"Error loading product: {e}")

        # Update Tabs Count
        for tab in self._cat_tabs:
            c = sum(1 for cd in self._all_cards if cd.prod_type == tab._label.lower())
            tab.set_count(c) # Ito na ang tatawagin imbes na tab._cnt.setText()

        # Setup Search Completer
        comp = QCompleter(all_names, self)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)

        popup = comp.popup()
        popup.setStyleSheet(f"""
            QListView {{
                background:{WHITE};
                border:1.5px solid {BORDER_MID};
                padding:2px;
                font-family:'Segoe UI';
                font-size:10px;
                color:{BROWN_DARK};
                outline:none;
            }}
            QListView::item {{
                height:30px;
                border-radius:6px;
                padding-left:10px;
                color:{BROWN_DARK};
            }}
            QListView::item:hover {{
                background:{CREAM_MID};
                color:{BROWN_DARK};
            }}
            QListView::item:selected {{
                background:{CREAM_DARK};
                color:{BROWN_DARK};
                font-weight:bold;
            }}
            QScrollBar:vertical {{
                background:{CREAM_MID};
                width:6px;
                border-radius:3px;
                margin:0;
            }}
            QScrollBar::handle:vertical {{
                background:{BROWN_MID};
                border-radius:3px;
                min-height:30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background:{BROWN_DARK};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height:0;
                background:none;
            }}
        """)

        self._search_input.setCompleter(comp)

        self._apply_filters()
        self._refresh_best_sellers()

    def _refresh_best_sellers(self):
        """Best sellers today (or the last 7 days if today is still quiet) as one-click buttons."""
        while self._best_btns_layout.count():
            w = self._best_btns_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        rows, title = [], "Best sellers today:"
        for days, label in (("-0 days", "Best sellers today:"), ("-6 days", "Best sellers this week:")):
            try:
                rows = self.db.fetch_all(
                    "SELECT s.product_id AS pid, SUM(s.quantity) AS q FROM sales s "
                    "JOIN products p ON p.id = s.product_id "
                    "WHERE COALESCE(s.is_voided, 0) = 0 AND p.is_archived = 0 "
                    "AND date(s.created_at) >= date('now', 'localtime', ?) "
                    "GROUP BY s.product_id ORDER BY q DESC LIMIT 8", (days,))
            except Exception as e:
                print(f"[POS] best sellers error: {e}")
                rows = []
            title = label
            if len(rows) >= 3:
                break
        cards = {c.prod_id: c for c in self._all_cards}
        shown = 0
        for r in rows:
            card = cards.get(r["pid"])
            if not card:
                continue
            b = QPushButton(f"{card.prod_name}  ₱{card.prod_price:g}")
            b.setFixedHeight(34)
            b.setMaximumWidth(190)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(f"Add 1 {card.prod_name}  ({int(card.prod_stock)} left)")
            b.setEnabled(card.prod_stock > 0)
            b.setStyleSheet(f"""
                QPushButton {{ background:{WHITE};color:{BROWN_DARK};border:1.5px solid {BROWN_MID};
                               border-radius:17px;padding:0 14px;font-size:12px;font-weight:600; }}
                QPushButton:hover {{ background:{BROWN};color:{WHITE};border-color:{BROWN}; }}
                QPushButton:disabled {{ color:{TEXT_LIGHT};border-color:{BORDER}; }}
            """)
            b.clicked.connect(lambda _, pid=card.prod_id: self._add_to_cart_by_id(pid))
            self._best_btns_layout.addWidget(b)
            shown += 1
        self._best_title.setText(title)
        self._best_bar.setVisible(shown > 0)


    def _parse_search(self):
        """'30 pan' / '30x pan' -> (30, 'pan'); 'pan' -> (1, 'pan').
        A space or x is required after the number so names like '3-in-1 Coffee' still work."""
        text = self._search_input.text().strip().lower()
        m = re.match(r"^(\d{1,4})\s*(?:[x×*]\s*|\s+)(.+)$", text)
        if m and int(m.group(1)) > 0:
            return int(m.group(1)), m.group(2).strip()
        return 1, text

    def _add_from_search(self):
        """Enter in the search box adds the best-matching product (any category)."""
        qty, name = self._parse_search()
        if not name:
            return
        matches = [c for c in self._all_cards if name in c.prod_name.lower()]
        if not matches:
            self._toast.show_message(f"No product matches \"{name}\"", error=True, parent_widget=self)
            return
        matches.sort(key=lambda c: (c.prod_name.lower() != name,            # exact name first
                                    not c.prod_name.lower().startswith(name),  # then "starts with"
                                    c.prod_stock <= 0,                          # in-stock before sold out
                                    c.prod_name.lower()))
        card = matches[0]
        if card.prod_stock <= 0 or not card.isEnabled():
            self._toast.show_message(f"{card.prod_name} is out of stock", error=True, parent_widget=self)
            return
        before = sum(i.qty for i in self.cart if i.prod_id == card.prod_id)
        self._pending_qty = qty
        self._add_to_cart_by_id(card.prod_id)
        if sum(i.qty for i in self.cart if i.prod_id == card.prod_id) > before:
            self._search_input.clear()
            self._toast.show_message(f"Added {qty} × {card.prod_name}", parent_widget=self)

    def _apply_filters(self, *_):
        q     = self._parse_search()[1]
        sf    = self._stock_filter
        sort  = self._sort_cb.currentIndex()
        ac    = self._active_cat.lower()

        current_grid = self._cat_grids.get(ac)
        if not current_grid:
            return
        
        # 1. 🟢 SAFE GRID CLEANUP: Tanggalin lang ang "No products found" text
        widgets_to_remove = []
        for i in range(current_grid.count()):
            item = current_grid.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if not isinstance(w, ProductCard):
                    widgets_to_remove.append(w)
                    
        for w in widgets_to_remove:
            w.hide()
            current_grid.removeWidget(w)
            w.deleteLater()

        # 2. 🟢 BULLETPROOF FILTERING: Gamitin ang internal grid reference
        matching = []
        for card in self._all_cards:
            # Tignan kung naka-assign ba talaga ang card na ito sa current tab
            # (Iniiwasan nito ang error kung hindi eksakto ang spelling ng category sa database)
            if getattr(card, '_current_grid', None) != current_grid:
                card.hide()
                continue
                
            m_q = (q == "" or q in card.prod_name.lower())
            m_sf = (sf == ""
                    or (sf == "in"  and card.prod_stock > 5)
                    or (sf == "low" and 0 < card.prod_stock <= 5)
                    or (sf == "out" and card.prod_stock == 0))
            
            if m_q and m_sf:
                matching.append(card)
                card.show()
            else:
                card.hide()
                current_grid.removeWidget(card) # Alisin muna sa grid para walang blank spaces

        # 3. I-sort ang mga cards
        if sort > 0:
            if sort == 1:  matching.sort(key=lambda c: c.prod_name.lower())
            elif sort == 2: matching.sort(key=lambda c: c.prod_price)
            elif sort == 3: matching.sort(key=lambda c: -c.prod_price)

        # 4. 🟢 DYNAMIC COLUMNS (Auto-Fit Logic)
        if matching:
            RIGHT_PANEL_WIDTH = 374
            CARD_SPACING = 14
            GRID_PADDING = 36

            available_total = self.width() - RIGHT_PANEL_WIDTH - GRID_PADDING
            aw = max(100, available_total)

            # Determine column count based on minimum card width
            MIN_CARD = 200
            cols = max(1, (aw + CARD_SPACING) // (MIN_CARD + CARD_SPACING))
            self._last_cols = cols

            # Stretch card width to fill available space evenly
            card_width = (aw - CARD_SPACING * (cols - 1)) // cols

            # Fixed heights — same regardless of sidebar state
            IMG_H   = 190
            CARD_H  = 250  # IMG_H + 55 bottom + 5 padding

            for card in matching:
                card.setFixedSize(card_width, CARD_H)
                card._img_frame.setFixedSize(card_width, IMG_H)
                card._bottom_widget.setFixedSize(card_width, 55)

                # Name label: pinned to bottom of image
                card._name_lbl.move(0, IMG_H - 27)
                card._name_lbl.setFixedWidth(card_width - 32)
                card._name_strip.setGeometry(0, IMG_H - 32, card_width, 32)   # dark strip follows the card width

                # Stock label: upper-right of image
                card._stock_lbl.setGeometry(
                    card_width // 2, IMG_H - 77,
                    card_width // 2 - 15, 215)

                # Badge: top-right corner
                card._badge.move(card_width - 30, 10)

            for i, card in enumerate(matching):
                current_grid.addWidget(card, i // cols, i % cols)
        else:
            empty_lbl = QLabel("No products found")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color:#AAAAAA;font-size:16px;padding:40px;")
            current_grid.addWidget(empty_lbl, 0, 0, 1, 3)
            empty_lbl.show()

    # ── IBA PANG FILTER AT CATEGORY METHODS (I-paste sa ilalim ng _apply_filters) ──
    def _on_cat_tab_clicked(self, _checked=False):
        tab = self.sender()
        if tab is not None and hasattr(tab, "_cat_index"):
            self._switch_cat(tab._cat_index, tab._cat_name, tab)

    def _switch_cat(self, idx: int, cat: str, btn):
        # 1. I-uncheck ang lahat ng tabs
        for t in self._cat_tabs:
            t.setChecked(False)
            
        # 2. I-check ang pinindot mong tab at i-set bilang active
        btn.setChecked(True)
        self._active_cat = cat.lower()
        
        # 3. Palitan ang view ng Grid papunta sa napiling category
        self._grid_stack.setCurrentIndex(idx)
        
        # 4. I-reset ang search at stock filters
        self._search_input.clear()
        self._stock_filter = "" 
        
        if hasattr(self, '_filter_group'):
            for b in self._filter_group.buttons():
                b.setChecked(b.value == "")
                
        # 5. I-apply ang bagong display
        self._apply_filters()

    def _set_stock_filter(self, value: str, btn):
        self._stock_filter = value
        if hasattr(self, '_filter_group'):
            for b in self._filter_group.buttons():
                b.setChecked(b is btn)
        self._apply_filters()
    # ══════════════════════════════════════════
    #  CART  LOGIC
    # ══════════════════════════════════════════
    def _add_to_cart_by_id(self, prod_id: int):
        card = next((c for c in self._all_cards if c.prod_id == prod_id), None)
        if not card or not card.isEnabled():
            return
        in_cart = sum(i.qty for i in self.cart if i.prod_id == prod_id)
        if in_cart + self._pending_qty > card.prod_stock:
            self._toast.show_message(
                f"Max stock reached for {card.prod_name}", error=True,
                parent_widget=self)
            self._pending_qty = 1; return

        existing = next((i for i in self.cart if i.prod_id == prod_id), None)
        self._undo_stack.append((prod_id, self._pending_qty))
        if existing:
            existing.qty += self._pending_qty
        else:
            self.cart.append(CartItem(prod_id, card.prod_name,
                                      card.prod_price, self._pending_qty,
                                      image_path=getattr(card, 'prod_image_path', None),
                                      prod_type=getattr(card, 'prod_type', None)))
        self._pending_qty = 1
        self._refresh_cart_panel()
        self._apply_filters()

    def _refresh_cart_panel(self):
        # remove all old rows
        while self._cart_vbox.count() > 1:
            item = self._cart_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.cart:
            self._empty_widget.setVisible(self._change_banner.isHidden())
            self._cart_scroll.hide()
            self._order_badge.setText("0 items")
            self._order_badge.setStyleSheet(
                f"background:{BROWN};color:{WHITE};"
                f"border-radius:12px;padding:0px 12px;border:none;"
                f"font-size:11px;font-weight:bold;")
            self._update_totals(0, 0)
            for card in self._all_cards:
                card.set_cart_state(0)
            return

        self._empty_widget.hide()
        self._cart_scroll.show()
        if not self._change_banner.isHidden():      # next customer: the change was already given
            self._hide_change_banner()

        subtotal = 0.0; total_qty = 0
        for item in self.cart:
            row = self._make_cart_row(item)
            self._cart_vbox.insertWidget(self._cart_vbox.count() - 1, row)
            subtotal   += item.subtotal
            total_qty  += item.qty

        self._update_totals(subtotal, total_qty)

        # update card badges
        cart_counts = {i.prod_id: i.qty for i in self.cart}
        for card in self._all_cards:
            card.set_cart_state(cart_counts.get(card.prod_id, 0))
            if card.prod_id not in cart_counts:
                card.set_cart_state(0)

    def _make_cart_row(self, item: CartItem) -> QWidget:
        w = _CartRowWidget(item)
        w.qty_changed.connect(self._change_qty)
        w.remove.connect(self._remove_item)
        return w

    def _change_qty(self, prod_id: int, delta: int):
        item = next((i for i in self.cart if i.prod_id == prod_id), None)
        if not item: return
        card = next((c for c in self._all_cards if c.prod_id == prod_id), None)
        new_qty = item.qty + delta
        if new_qty <= 0:
            self.cart = [i for i in self.cart if i.prod_id != prod_id]
        elif card and new_qty > card.prod_stock:
            if item.qty >= card.prod_stock:
                self._toast.show_message("Max stock reached", error=True, parent_widget=self)
                return
            self._undo_stack.append((prod_id, int(card.prod_stock) - item.qty))
            item.qty = int(card.prod_stock)
            self._toast.show_message(f"Only {int(card.prod_stock)} left — quantity set to {int(card.prod_stock)}",
                                     error=True, parent_widget=self)
        else:
            if delta > 0:
                self._undo_stack.append((prod_id, delta))
            item.qty = new_qty
        self._refresh_cart_panel()
        self._apply_filters()

    def _undo_last_add(self):
        """Take back the most recent addition (product click, +, +5, +10 or typed quantity)."""
        while self._undo_stack:
            prod_id, added = self._undo_stack.pop()
            item = next((i for i in self.cart if i.prod_id == prod_id), None)
            if not item:
                continue   # already removed by hand
            item.qty -= added
            if item.qty <= 0:
                self.cart = [i for i in self.cart if i.prod_id != prod_id]
            self._toast.show_message(f"Undone: {added} × {item.name}", parent_widget=self)
            self._refresh_cart_panel()
            self._apply_filters()
            return
        self._toast.show_message("Nothing to undo", error=True, parent_widget=self)

    def _remove_item(self, prod_id: int):
        self.cart = [i for i in self.cart if i.prod_id != prod_id]
        self._apply_filters()
        self._refresh_cart_panel()

    def _clear_cart(self):
        self.cart.clear()
        self._undo_stack.clear()
        self._refresh_cart_panel()
        self._apply_filters()

    def _update_totals(self, sub: float, qty: int):
        self._tot_sub.setText(f"₱{sub:,.2f}")
        self._tot_items.setText(f"{qty} pcs")
        disc = self._get_discount_amount()
        net  = max(0.0, sub - disc)
        self._tot_grand.setText(f"₱{net:,.2f}")
        self._update_pay_btn(net)
        
        if qty > 0:
            n = len(self.cart)
            self._order_badge.setText(f"{n} item{'s' if n != 1 else ''}  ·  {qty} pcs")
            self._order_badge.setStyleSheet(
                f"background:{BROWN};color:{WHITE};"
                f"border-radius:12px;padding:0px 12px;border:none;"
                f"font-size:11px;font-weight:bold;")
        else:
            self._order_badge.setText("0 items")
            self._order_badge.setStyleSheet(
                f"background:{BROWN};color:{WHITE};"
                f"border-radius:12px;padding:0px 12px;border:none;"
                f"font-size:11px;font-weight:bold;")

    # ── CLEAR / VOID (UPDATED with BakeSyncAlert) ──
    def _confirm_clear_cart(self):
        # 1. Check if the cart is empty first
        if not self.cart:
            try:
                # 🟢 FIX: Use the themed alert for "Already Empty" status
                from bakesync.widgets.custom_alerts import BakeSyncAlert
                BakeSyncAlert.show_error(
                    self.window(), 
                    "Empty Cart", 
                    "The cart is already empty. There is nothing to clear!"
                )
            except ImportError:
                # Fallback to toast if custom_alerts is missing
                self._toast.show_message("Cart is already empty", error=True, parent_widget=self)
            return

        # 2. If not empty, ask for confirmation to clear
        try:
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            if BakeSyncAlert.ask_yes_no(
                self.window(), "Clear Cart?",
                "Are you sure you want to remove all items from the current order?",
                yes_text="Clear All", no_text="Cancel"):
                self._clear_cart()
                self._toast.show_message("Cart cleared", parent_widget=self)
        except ImportError:
            self._clear_cart()
            self._toast.show_message("Cart cleared", parent_widget=self)

    def _void_action(self):
        dlg = VoidTransactionDialog(self.db, self, self.current_user)
        dlg.exec()
        self.load_products()
        self._refresh_cart_panel()

    # ══════════════════════════════════════════
    #  PAYMENT
    # ══════════════════════════════════════════
    def _ready_to_pay(self):
        """Cart not empty and every item still in stock (expired pieces do not count)."""
        if not self.cart:
            self._toast.show_message("Cart is empty — add items first", parent_widget=self)
            return False
        for item in self.cart:
            try:
                row = self.db.fetch_one("SELECT COALESCE(stock_qty,0) AS ts FROM products WHERE id=?", (item.prod_id,))
                ts = row['ts'] if row else 0
                er = self.db.fetch_one(
                    "SELECT COALESCE(SUM(quantity_remaining),0) AS eq FROM product_batches WHERE product_id=? "
                    "AND quantity_remaining>0 AND expiry_date IS NOT NULL AND expiry_date<=date('now', 'localtime')",
                    (item.prod_id,))
                if item.qty > max(0, ts - (er['eq'] if er else 0)):
                    self._toast.show_message(f"Not enough stock: {item.name}", error=True, parent_widget=self)
                    return False
            except Exception as e:
                print(f"[POS] stock check: {e}")
        return True

    def _process_payment(self):
        """'Other amount' (F11): type what the customer gave."""
        if not self._ready_to_pay():
            return
        total = self._discounted_total()
        dlg = PaymentDialog(total, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._complete_sale(getattr(dlg, 'tendered', total) or total)

    def _on_bill_clicked(self, _checked=False):
        b = self.sender()
        if b is not None and b.property("amount") is not None:
            self._quick_pay(b.property("amount"))

    def _quick_pay(self, amount):
        """One click: Exact (amount None) or a bill button."""
        if not self._ready_to_pay():
            return
        total = self._discounted_total()
        self._complete_sale(total if amount is None else float(amount))

    def _complete_sale(self, tendered):
        total = self._discounted_total()
        tendered = max(tendered, total)
        change = tendered - total
        # one transaction: every item is saved, or none (no half-saved sale);
        # one timestamp for the whole sale so End of Day counts transactions right
        sale_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ids = []
        try:
            with self.db.transaction():
                for item in self.cart:
                    cur = self.db.execute_query(
                        "INSERT INTO sales (product_id,quantity,amount,tendered,change_given,cashier,created_at) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (item.prod_id, item.qty, item.subtotal, tendered, change, self.current_user or "Unknown", sale_time))
                    ids.append(cur.lastrowid)
                    self.db.execute_query("UPDATE products SET stock_qty=MAX(0,stock_qty-?) WHERE id=?", (item.qty, item.prod_id))
        except Exception as e:
            self._toast.show_message(f"Sale not saved: {e}", error=True, parent_widget=self)
            return
        pcs = sum(i.qty for i in self.cart)
        log_activity(self.db, self.current_user, "sale completed", "sale",
                     f"₱{total:,.2f} - {pcs:g} pcs - cash ₱{tendered:,.2f}, change ₱{change:,.2f}")
        for item in self.cart:
            self.session_sales.append(CartItem(item.prod_id, item.name, item.price, item.qty))
        self._last_sale = {"ids": ids, "items": [(i.prod_id, i.name, i.qty, i.subtotal) for i in self.cart],
                           "total": total, "time": sale_time}
        self._discount_pct = 0.0
        self._clear_cart()
        self.load_products()
        self.sale_completed.emit()
        self._show_change_banner(total, tendered, change)

    # ── change banner + undo ────────────────────────────────
    def _show_change_banner(self, total, tendered, change):
        self._chg_amount.setText(f"₱{change:,.2f}" if change > 0.004 else "No change")
        self._chg_detail.setText(f"Paid ₱{tendered:,.2f}   ·   Total ₱{total:,.2f}")
        self._undo_left = 10
        self._undo_sale_btn.setVisible(True)
        self._undo_sale_btn.setText(f"  Undo this sale ({self._undo_left})")
        self._change_banner.show()
        self._empty_widget.hide()
        self._undo_timer.start(1000)
        self._banner_timer.start(30000)

    def _tick_undo(self):
        self._undo_left -= 1
        if self._undo_left <= 0:
            self._undo_timer.stop()
            self._undo_sale_btn.setVisible(False)
            self._last_sale = None
        else:
            self._undo_sale_btn.setText(f"  Undo this sale ({self._undo_left})")

    def _hide_change_banner(self):
        self._undo_timer.stop()
        self._change_banner.hide()
        self._last_sale = None
        if not self.cart:
            self._empty_widget.show()

    def _undo_last_sale(self):
        sale = self._last_sale
        if not sale:
            return
        u = self.current_user or "Unknown"
        try:
            with self.db.transaction():
                for sid, (pid, name, qty, amount) in zip(sale["ids"], sale["items"]):
                    self.db.execute_query("UPDATE sales SET is_voided=1, voided_by=? WHERE id=?", (u, sid))
                    self.db.execute_query("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?", (qty, pid))
                    self.db.execute_query("INSERT INTO void_logs (product_id, quantity, amount, reason, voided_by) VALUES (?,?,?,?,?)",
                                          (pid, qty, amount, "Sale undone", u))
        except Exception as e:
            self._toast.show_message(f"Could not undo: {e}", error=True, parent_widget=self)
            return
        log_activity(self.db, u, "sale voided", "void", f"Undid the sale of ₱{sale['total']:,.2f} right after payment")
        for pid, name, qty, amount in sale["items"]:           # put the items back in the cart
            self.cart.append(CartItem(pid, name, amount / qty if qty else 0, qty))
        self._hide_change_banner()
        self._refresh_cart_panel()
        self.load_products()
        self.sale_completed.emit()
        self._toast.show_message("Sale undone. The items are back in the cart.", parent_widget=self)

    # ══════════════════════════════════════════
    #  MODALS — stocks, sales, EOD
    # ══════════════════════════════════════════
    def _show_stocks(self):
        StocksDialog(self.db, self).exec()

    def _show_sales(self):
        SalesInsightsDialog(self.db, self).exec()

    def _end_of_day(self):
        try:
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            if not BakeSyncAlert.ask_yes_no(
                self.window(), "End of Day?",
                "Close this POS session and finalize today's sales?",
                yes_text="Close Session", no_text="Cancel"):
                return
        except ImportError:
            pass

        # 🟢 I-open ang dialog muna. Mag-u-update LANG ang DB kapag kinlick ang "Close Session"
        dlg = EndOfDayDialog(self.db, self.session_sales, self, self.current_user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                # Isara ang session at magbukas ng bago nang sabay (all-or-nothing)
                with self.db.transaction():
                    session = self.db.fetch_one("SELECT id, opened_at FROM pos_sessions WHERE status='Open' ORDER BY id DESC LIMIT 1")
                    if session:
                        opened_at = session['opened_at']
                        sales_data = self.db.fetch_one(
                            "SELECT SUM(amount) as total_amt, COUNT(DISTINCT created_at) as txns "
                            "FROM sales WHERE created_at >= ? AND COALESCE(is_voided, 0) = 0", (opened_at,))

                        total = sales_data['total_amt'] or 0.0
                        txns = sales_data['txns'] or 0

                        self.db.execute_query(
                            "UPDATE pos_sessions SET closed_at=datetime('now', 'localtime'),"
                            "total_sales=?, total_txns=?, closed_by=?, status='Closed' "
                            "WHERE id=?",
                            (total, txns, self.current_user or "Unknown", session['id']))

                    # Magbukas agad ng bagong session
                    self.db.execute_query("INSERT INTO pos_sessions (status, opened_at) VALUES ('Open', datetime('now', 'localtime'))")

            except Exception as e:
                print(f"[POS] EOD update error: {e}")

            log_activity(self.db, self.current_user, "POS day closed", "sale", "Closed the POS session (End of Day)")
            self.session_sales.clear()
            self._toast.show_message("Session closed — have a great day!", parent_widget=self)

    # ══════════════════════════════════════════
    #  Public helpers kept for compatibility
    # ══════════════════════════════════════════
    def show_void_history(self):   self._void_action()
    def show_stocks_dialog(self):  self._show_stocks()
    def show_sales_dialog(self):   self._show_sales()
    def _refresh_products(self):   self.load_products()
    def _refresh_cart(self):       self._refresh_cart_panel()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_grid_stack') and hasattr(self, '_apply_filters'):
            QTimer.singleShot(0, self._apply_filters)

# ─────────────────────────────────────────────
#  RECEIPT DIALOG  (extended — print-ready)

# ─────────────────────────────────────────────
class _CartRowWidget(QWidget):
    """
    A single animated row in the order panel.
    Signals: qty_changed(prod_id, new_qty)  remove(prod_id)
    """
    qty_changed = pyqtSignal(int, int)   # prod_id, new_qty
    remove      = pyqtSignal(int)        # prod_id

    def __init__(self, item: "CartItem", parent=None):
        super().__init__(parent)
        self._item = item
        self.setFixedHeight(66)
        self.setObjectName("cartRowWidget") # 🟢 FIX: Nilagyan ng ID
        self.setStyleSheet(
            f"QWidget#cartRowWidget {{" # 🟢 FIX: Scoped ang bottom border
            f"background:{WHITE};"
            f"border-bottom:1px solid rgba(0,0,0,0.04);"
            f"}}"
        )
        self._build()

    def _build(self):
        self.setFixedHeight(100)
        self.setObjectName("cartRowWidget")
        self.setStyleSheet(f"""
            QWidget#cartRowWidget {{
                background:{WHITE};
                border:1.5px solid #D0C8C0;
                border-radius:12px;
            }}
            QWidget#cartRowWidget QLabel {{
                background:transparent;
                border:none;
            }}
            QWidget#cartRowWidget QWidget {{
                background:transparent;
                border:none;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(4)

        # ── Top row: icon + name/price + X ────
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.setContentsMargins(0, 0, 0, 0)

        # icon
        ico = QLabel()
        ico.setFixedSize(48, 48)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet(
            f"background:{BROWN_DARK};border-radius:8px;border:1.5px solid #D0C8C0;"
            f"overflow:hidden;")

        img_path = getattr(self._item, 'image_path', None)
        if img_path and os.path.exists(img_path):
            px = QPixmap(img_path).scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            ico.setPixmap(px)
        else:
            ico.setStyleSheet("background:#F5ECE5;border-radius:8px;border:1.5px solid #D0C8C0;")
            ico.setPixmap(default_product_pixmap(48, 48, kind_for(getattr(self._item, 'prod_type', None))))

        # name + unit price col
        info = QWidget()
        info.setStyleSheet("background:transparent;border:none;")
        il = QVBoxLayout(info)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(1)
        il.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        from PyQt6.QtGui import QFontMetrics
        nm = QLabel(self._item.name)
        nm.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        nm.setStyleSheet(f"color:{TEXT_DARK};background:transparent;border:none;")
        nm.setMaximumWidth(160)
        fm = QFontMetrics(nm.font())
        nm.setText(fm.elidedText(self._item.name, Qt.TextElideMode.ElideRight, 160))

        pr = QLabel(f"₱{self._item.price:.2f} each")
        pr.setFont(QFont("Segoe UI", 9))
        pr.setStyleSheet(f"color:{BROWN_LIGHT};background:transparent;border:none;")

        il.addWidget(nm)
        il.addWidget(pr)

        # X delete button
        del_btn = QPushButton("X")
        del_btn.setFixedSize(20, 20)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent;border:none;
                color:{RED};font-size:11px;font-weight:bold;
            }}
            QPushButton:hover {{ color:{RED_DARK}; }}
        """)
        del_btn.clicked.connect(lambda: self.remove.emit(self._item.prod_id))

        top_row.addWidget(ico)
        top_row.addWidget(info, stretch=1)
        top_row.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # ── Bottom row: subtotal + stepper ─────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.setContentsMargins(0, 0, 0, 0)

        self._sub_lbl = QLabel(f"₱{self._item.subtotal:,.2f}")
        self._sub_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._sub_lbl.setStyleSheet(f"color:{TEXT_DARK};background:transparent;border:none;")

        # stepper
        ctrl = QWidget()
        ctrl.setStyleSheet("background:transparent;border:none;")
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        btn_minus = QPushButton("−")
        btn_minus.setFixedSize(26, 26)
        btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minus.setStyleSheet(f"""
            QPushButton {{
                background:{CREAM_MID};border:1px solid {BORDER};
                border-radius:6px;color:{TEXT_DARK};
                font-size:15px;font-weight:bold;
            }}
            QPushButton:hover {{ background:{CREAM_DARK};border-color:{BROWN_MID}; }}
        """)
        btn_minus.clicked.connect(self._dec)

        self._qty_lbl = QPushButton(str(self._item.qty))
        self._qty_lbl.setFixedSize(44, 28)
        self._qty_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._qty_lbl.setToolTip("Click to type the quantity")
        self._qty_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._qty_lbl.setStyleSheet(f"""
            QPushButton {{
                color:#1A1A1A; background:{WHITE};
                border:1.5px solid {BROWN_MID}; border-radius:6px;
                font-size:13px; font-weight:bold;
            }}
            QPushButton:hover {{ background:{CREAM_MID}; }}
        """)
        self._qty_lbl.clicked.connect(self._open_qty_editor)

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(26, 26)
        btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plus.setStyleSheet(f"""
            QPushButton {{
                background:{CREAM_MID};border:1px solid {BORDER};
                border-radius:6px;color:{TEXT_DARK};
                font-size:15px;font-weight:bold;
            }}
            QPushButton:hover {{ background:{CREAM_DARK};border-color:{BROWN_MID}; }}
        """)
        btn_plus.clicked.connect(self._inc)

        cl.addWidget(btn_minus)
        cl.addWidget(self._qty_lbl)
        cl.addWidget(btn_plus)
        for step in (5, 10):   # bread is usually bought by fives and tens
            b = QPushButton(f"+{step}")
            b.setFixedSize(36, 26)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(f"Add {step} more")
            b.setStyleSheet(f"""
                QPushButton {{
                    background:{CREAM_MID};border:1px solid {BORDER};
                    border-radius:6px;color:{BROWN};font-size:11px;font-weight:bold;
                }}
                QPushButton:hover {{ background:{CREAM_DARK};border-color:{BROWN_MID}; }}
            """)
            b.clicked.connect(lambda _, n=step: self.qty_changed.emit(self._item.prod_id, n))
            cl.addWidget(b)

        bottom_row.addWidget(self._sub_lbl, stretch=1)
        bottom_row.addWidget(ctrl)

        outer.addLayout(top_row)
        outer.addLayout(bottom_row)

    # ── qty helpers ───────────────────────────
    def _inc(self):
        self.qty_changed.emit(self._item.prod_id, +1)

    def _dec(self):
        self.qty_changed.emit(self._item.prod_id, -1)

    def _open_qty_editor(self):
        """Show an inline overlay with a text input for direct qty entry."""
        # Find the top-level POS window to attach the overlay to
        top = self.window()

        # ── Semi-transparent full overlay ─────────────────────
        overlay = QWidget(top)
        overlay.setGeometry(top.rect())
        overlay.setStyleSheet("background:rgba(0,0,0,0.55);")
        overlay.show()
        overlay.raise_()

        # ── Centered card ──────────────────────────────────────
        card = QWidget(overlay)
        card.setFixedSize(260, 130)
        card.setObjectName("qtyCard")
        card.setStyleSheet(f"""
            QWidget#qtyCard {{
                background:transparent;
            }}
        """)
        card.setObjectName("qtyCard")

        # Center card on overlay
        card.move(
            (overlay.width()  - card.width())  // 2,
            (overlay.height() - card.height()) // 2,
        )

        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        lbl = QLabel("How many pieces?")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{CREAM_MID};background:transparent;border:none;")
        cl.addWidget(lbl)

        inp = QLineEdit(str(self._item.qty))
        inp.selectAll()   # typing replaces the current number
        inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inp.setFixedHeight(46)
        inp.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        inp.setStyleSheet(f"""
            QLineEdit {{
                background:transparent;
                color:{CREAM_MID};
                border:1px solid transparent;
            }}
        """)

        # Only allow digits
        from PyQt6.QtGui import QIntValidator
        inp.setValidator(QIntValidator(1, 9999))

        cl.addWidget(inp)
        card.show()
        inp.setFocus()

        # Store original qty in case of cancel
        original_qty = self._item.qty

        def _commit():
            text = inp.text().strip()
            if not text:
                overlay.deleteLater()
                return

            try:
                new_qty = int(text)
                if new_qty < 1:
                    new_qty = 1
            except ValueError:
                overlay.deleteLater()
                return

            overlay.deleteLater()

            if new_qty != original_qty:
                delta = new_qty - original_qty
                self.qty_changed.emit(self._item.prod_id, delta)

        def _cancel():
            overlay.deleteLater()

        # Click on overlay background = cancel
        overlay.mousePressEvent = lambda e: _cancel()

        # Block clicks on card from bubbling to overlay
        card.mousePressEvent = lambda e: e.accept()

        # Enter key = commit, Esc = cancel
        inp.returnPressed.connect(_commit)
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Escape"), overlay, _cancel)

    def refresh_qty(self, qty: int):
        self._item.qty = qty
        self._qty_lbl.setText(str(qty))
        self._sub_lbl.setText(f"₱{self._item.subtotal:,.2f}")


# ─────────────────────────────────────────────
#  NUMERIC KEYPAD DIALOG  (standalone — F-key qty entry)
# ─────────────────────────────────────────────
class NumpadDialog(QDialog):
    """
    Pop-up numpad for entering a cash amount or quantity.
    Emits value_confirmed(float) on accept.
    """
    value_confirmed = pyqtSignal(float)

    def __init__(
        self,
        title: str = "Enter Amount",
        prefix: str = "₱",
        integer_only: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._prefix       = prefix
        self._integer_only = integer_only
        self._raw          = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(310, 400)

        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.45);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._build(title)
        self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move(
            (s.width() - self.width()) // 2,
            (s.height() - self.height()) // 2,
        )

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    def accept(self):
        self._close_overlay()
        super().accept()

    def reject(self):
        self._close_overlay()
        super().reject()

    def closeEvent(self, e):
        self._close_overlay()
        super().closeEvent(e)

    def _build(self, title):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("numCard")
        card.setStyleSheet(f"""
            QWidget#numCard {{
                background:{WHITE};
                border:1px solid {BORDER};
                border-radius:16px;
            }}
            QWidget#numCard QLabel {{
                background:transparent;
                color:{TEXT_DARK};
                border:none;
            }}
        """)
        _force_light(card)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 20, 22, 20)
        cl.setSpacing(12)

        # title
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(t)

        # display
        self._display = QLabel(f"{self._prefix}0")
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self._display.setFixedHeight(64)
        self._display.setStyleSheet(
            f"color:{BROWN};background:{CREAM_MID};"
            f"border-radius:10px;padding:8px;border:none;"
        )
        cl.addWidget(self._display)

        # numpad grid
        grid = QGridLayout()
        grid.setSpacing(8)
        if self._integer_only:
            keys = ["7","8","9","4","5","6","1","2","3","⌫","0","✓"]
        else:
        # 12 keys: last row is ⌫  .  ✓  (clean 4×3 grid)
            keys = ["7","8","9","4","5","6","1","2","3","⌫",".","✓"]

        for idx, k in enumerate(keys):
            b = QPushButton(k)
            b.setFixedHeight(46)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if k in ("✓", "⌫"):
                b.setText(""); b.setIcon(ui_icon("check" if k == "✓" else "undo", WHITE if k == "✓" else RED, 20))

            if k == "✓":
                b.setStyleSheet(f"""
                    QPushButton {{
                        background:{GREEN};color:{WHITE};
                        border-radius:8px;font-size:17px;
                        font-weight:bold;border:none;
                    }}
                    QPushButton:hover {{ background:{GREEN_DARK}; }}
                """)
            elif k == "⌫":
                b.setStyleSheet(f"""
                    QPushButton {{
                        background:#FBE9E9;color:{RED};
                        border-radius:8px;font-size:17px;
                        font-weight:bold;border:1px solid #F0C0C0;
                    }}
                    QPushButton:hover {{ background:#F5D0D0; }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        background:{WHITE};color:{TEXT_DARK};
                        border:1px solid {BORDER};border-radius:8px;
                        font-size:18px;font-weight:bold;
                    }}
                    QPushButton:hover {{ background:{CREAM_MID}; }}
                """)

            b.clicked.connect(lambda _, key=k: self._press(key))
            grid.addWidget(b, idx // 3, idx % 3)

        cl.addLayout(grid)

        # cancel
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(36)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE};color:{TEXT_MID};
                border:1px solid {BORDER};border-radius:8px;font-size:12px;
            }}
            QPushButton:hover {{ background:{CREAM_MID}; }}
        """)
        cancel.clicked.connect(self.reject)
        cl.addWidget(cancel)

        outer.addWidget(card)

    def _press(self, key):
        if key == "⌫":
            self._raw = self._raw[:-1]
        elif key == "✓":
            try:
                v = float(self._raw) if self._raw else 0.0
                if v > 0:
                    self.value_confirmed.emit(v)
                    self.accept()
            except ValueError:
                pass
            return
        elif key == ".":
            if "." not in self._raw:
                self._raw += "."
        else:
            if self._raw == "0":
                self._raw = key
            else:
                self._raw += key

        display = f"{self._prefix}{self._raw or '0'}"
        self._display.setText(display)


# ─────────────────────────────────────────────
#  QUICK-ADD DIALOG  (scan / name lookup)
# ─────────────────────────────────────────────
class QuickAddDialog(QDialog):
    """
    Lets the cashier type a partial product name and pick from a list.
    Emits product_selected(prod_id, qty).
    """
    product_selected = pyqtSignal(int, int)

    def __init__(self, products: list, parent=None):
        """products: list of dicts with keys id, name, price, stock"""
        super().__init__(parent)
        self._products = products
        self._qty      = 1

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(480, 520)

        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.50);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._build()
        self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move(
            (s.width() - self.width()) // 2,
            (s.height() - self.height()) // 2,
        )

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    def accept(self):
        self._close_overlay()
        super().accept()

    def reject(self):
        self._close_overlay()
        super().reject()

    def closeEvent(self, e):
        self._close_overlay()
        super().closeEvent(e)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("qaCard")
        card.setStyleSheet(f"""
            QWidget#qaCard {{
                background:{WHITE};
                border:1px solid {BORDER};
                border-radius:16px;
            }}
            QWidget#qaCard QLabel {{
                background:transparent;
                color:{TEXT_DARK};
                border:none;
            }}
        """)
        _force_light(card)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 20, 22, 20)
        cl.setSpacing(12)

        # ── header ────────────────────────────
        hdr = QHBoxLayout()
        t = QLabel("Quick Add Product")
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{BROWN};")
        close_b = QPushButton()
        close_b.setFixedSize(28, 28)
        close_b.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:14px;}"
            "QPushButton:hover{background:#F3F4F6;}"
        )
        close_b.setIcon(QIcon(make_svg_icon(SVG["close"], 14, TEXT_LIGHT)))
        close_b.setIconSize(QSize(14, 14))
        close_b.clicked.connect(self.reject)
        hdr.addWidget(t)
        hdr.addStretch()
        hdr.addWidget(close_b)
        cl.addLayout(hdr)

        # ── search ────────────────────────────
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type product name…")
        self._search.setFixedHeight(42)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background:{WHITE};color:{TEXT_DARK};
                border:1.5px solid {BORDER};border-radius:10px;
                padding:0 12px;font-size:13px;
            }}
            QLineEdit:focus {{ border-color:{BROWN}; }}
        """)
        self._search.textChanged.connect(self._filter)
        cl.addWidget(self._search)

        # ── product table ─────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(3)
        self._tbl.setHorizontalHeaderLabels(["Product", "Price", "Stock"])
        self._tbl.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self._tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._tbl.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._tbl.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)
        self._tbl.setShowGrid(False)
        self._tbl.setStyleSheet(f"""
            QTableWidget {{
                border:1px solid {BORDER};border-radius:8px;
                font-size:12px;color:{TEXT_DARK};outline:none;
            }}
            QHeaderView::section {{
                background:{BROWN};color:{WHITE};
                padding:8px 10px;font-weight:bold;
                font-size:11px;border:none;
            }}
            QTableWidget::item {{
                padding:5px 10px;
                border-bottom:1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background:{CREAM_MID};color:{TEXT_DARK};
            }}
        """)
        self._tbl.doubleClicked.connect(self._confirm_selection)
        cl.addWidget(self._tbl, stretch=1)

        # ── qty + confirm row ─────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        qty_lbl = QLabel("Qty:")
        qty_lbl.setFont(QFont("Segoe UI", 11))

        self._qty_spin = QLineEdit("1")
        self._qty_spin.setFixedSize(60, 36)
        self._qty_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qty_spin.setStyleSheet(f"""
            QLineEdit {{
                background:{WHITE};color:{TEXT_DARK};
                border:1.5px solid {BORDER};border-radius:8px;
                font-size:14px;font-weight:bold;
            }}
            QLineEdit:focus {{ border-color:{BROWN}; }}
        """)

        add_btn = QPushButton("Add to Order")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BROWN};color:{WHITE};border:none;
                border-radius:8px;font-size:13px;font-weight:bold;
                padding:0 18px;
            }}
            QPushButton:hover {{ background:{BROWN_DARK}; }}
        """)
        add_btn.clicked.connect(self._confirm_selection)

        bottom.addWidget(qty_lbl)
        bottom.addWidget(self._qty_spin)
        bottom.addStretch()
        bottom.addWidget(add_btn)
        cl.addLayout(bottom)

        outer.addWidget(card)
        self._load_all()

    def _load_all(self, query=""):
        q = query.lower()
        rows = [
            p for p in self._products
            if q in p["name"].lower()
        ]
        self._tbl.setRowCount(len(rows))
        for i, p in enumerate(rows):
            # stash prod_id
            name_it = QTableWidgetItem(p["name"])
            name_it.setData(Qt.ItemDataRole.UserRole, p["id"])
            for c, (txt, al) in enumerate([
                (p["name"], Qt.AlignmentFlag.AlignLeft  | Qt.AlignmentFlag.AlignVCenter),
                (f"₱{p['price']:.2f}", Qt.AlignmentFlag.AlignCenter),
                (str(int(p["stock"])),  Qt.AlignmentFlag.AlignCenter),
            ]):
                it = (name_it if c == 0 else QTableWidgetItem(txt))
                it.setTextAlignment(al)
                self._tbl.setItem(i, c, it)
                if c == 2 and p["stock"] == 0:
                    it.setForeground(QBrush(QColor(RED)))
            self._tbl.setRowHeight(i, 38)

    def _filter(self, text):
        self._load_all(text)

    def _confirm_selection(self):
        sel = self._tbl.selectedItems()
        if not sel:
            return
        prod_id = self._tbl.item(sel[0].row(), 0).data(
            Qt.ItemDataRole.UserRole)
        try:
            qty = max(1, int(self._qty_spin.text()))
        except ValueError:
            qty = 1
        self.product_selected.emit(prod_id, qty)
        self.accept()


# ─────────────────────────────────────────────
#  DAILY SUMMARY WIDGET  (embeddable, no dialog)
# ─────────────────────────────────────────────
class DailySummaryCard(QFrame):
    """
    A compact summary card that can be embedded anywhere.
    Shows today's revenue, transaction count, and top product.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("dsc")
        self.setStyleSheet(f"""
            QFrame#dsc {{
                background:{WHITE};
                border:1.5px solid {BORDER};
                border-radius:14px;
            }}
        """)
        self._build()
        self.refresh()

    def _build(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 14)
        self._layout.setSpacing(10)

        title = QLabel("Today at a Glance")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{BROWN};")
        self._layout.addWidget(title)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        self._rev_val  = self._kpi_card(kpi_row, "Revenue",      "₱0.00",  GREEN)
        self._txn_val  = self._kpi_card(kpi_row, "Transactions", "0",      BROWN)
        self._top_val  = self._kpi_card(kpi_row, "Top Product",  "—",      AMBER)
        self._layout.addLayout(kpi_row)

    def _kpi_card(self, parent_layout, label, init_val, color):
        f = QFrame()
        f.setStyleSheet(
            f"QFrame{{background:{CREAM_MID};"
            f"border-radius:8px;border:none;}}"
        )
        fv = QVBoxLayout(f)
        fv.setContentsMargins(12, 8, 12, 8)
        fv.setSpacing(2)
        la = QLabel(label)
        la.setFont(QFont("Segoe UI", 9))
        la.setStyleSheet(f"color:{TEXT_MID};background:transparent;border:none;")
        lv = QLabel(init_val)
        lv.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lv.setStyleSheet(
            f"color:{color};background:transparent;border:none;")
        fv.addWidget(la)
        fv.addWidget(lv)
        parent_layout.addWidget(f)
        return lv

    def refresh(self):
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            kpi = self.db.fetch_one(
                "SELECT SUM(amount) as rev, COUNT(DISTINCT created_at) as txns "
                "FROM sales "
                "WHERE date(created_at)=? "
                "  AND COALESCE(is_voided,0)=0",
                (today,),
            )
            rev  = (kpi["rev"]  or 0.0) if kpi else 0.0
            txns = (kpi["txns"] or 0)   if kpi else 0
            self._rev_val.setText(f"₱{rev:,.2f}")
            self._txn_val.setText(str(txns))

            top = self.db.fetch_one(
                "SELECT p.name FROM sales s "
                "JOIN products p ON s.product_id=p.id "
                "WHERE date(s.created_at)=? "
                "  AND COALESCE(s.is_voided,0)=0 "
                "GROUP BY p.id ORDER BY SUM(s.quantity) DESC LIMIT 1",
                (today,),
            )
            self._top_val.setText(top["name"] if top else "—")
        except Exception as e:
            print(f"[DailySummaryCard] refresh error: {e}")

class HoldOrderDialog(QDialog):
    """
    Lets the cashier give a label (e.g. table number / customer name)
    to a held order so it can be recalled later.
    """
    label_confirmed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(380, 240)

        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.45);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._build()
        self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move(
            (s.width() - self.width()) // 2,
            (s.height() - self.height()) // 2,
        )

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    def accept(self):
        self._close_overlay()
        super().accept()

    def reject(self):
        self._close_overlay()
        super().reject()

    def closeEvent(self, e):
        self._close_overlay()
        super().closeEvent(e)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("holdCard")
        card.setStyleSheet(f"""
            QWidget#holdCard {{
                background:{WHITE};
                border:1px solid {BORDER};
                border-radius:16px;
            }}
            QWidget#holdCard QLabel {{
                background:transparent;
                color:{TEXT_DARK};
                border:none;
            }}
        """)
        _force_light(card)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 22, 24, 22)
        cl.setSpacing(14)

        t = QLabel("Hold This Order")
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{BROWN};")
        cl.addWidget(t)

        sub = QLabel(
            "Give this order a label so you can recall it later.\n"
            "e.g. Table 3, or a customer name."
        )
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet(f"color:{TEXT_MID};")
        sub.setWordWrap(True)
        cl.addWidget(sub)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Order label…")
        self._inp.setFixedHeight(44)
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background:{WHITE};color:{TEXT_DARK};
                border:1.5px solid {BORDER};border-radius:10px;
                padding:0 12px;font-size:14px;
            }}
            QLineEdit:focus {{ border-color:{BROWN}; }}
        """)
        self._inp.returnPressed.connect(self._confirm)
        cl.addWidget(self._inp)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(40)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE};color:{TEXT_MID};
                border:1px solid {BORDER};border-radius:10px;
                font-size:13px;
            }}
            QPushButton:hover {{ background:{CREAM_MID}; }}
        """)
        cancel.clicked.connect(self.reject)

        hold = QPushButton("Hold Order")
        hold.setFixedHeight(40)
        hold.setCursor(Qt.CursorShape.PointingHandCursor)
        hold.setStyleSheet(f"""
            QPushButton {{
                background:{BROWN};color:{WHITE};border:none;
                border-radius:10px;font-size:13px;font-weight:bold;
            }}
            QPushButton:hover {{ background:{BROWN_DARK}; }}
        """)
        hold.clicked.connect(self._confirm)

        btn_row.addWidget(cancel)
        btn_row.addWidget(hold)
        cl.addLayout(btn_row)

        outer.addWidget(card)

    def _confirm(self):
        lbl = self._inp.text().strip() or "Order"
        self.label_confirmed.emit(lbl)
        self.accept()

class HeldOrdersDialog(QDialog):
    """
    Shows all held orders.  Selecting one emits order_recalled(list[CartItem]).
    """
    order_recalled = pyqtSignal(list)

    def __init__(self, held: dict, parent=None):
        """held: {label: [CartItem, ...]}"""
        super().__init__(parent)
        self._held = held

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(520, 440)

        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background:rgba(0,0,0,0.50);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._build()
        self._center()

    def _center(self):
        s = QApplication.primaryScreen().geometry()
        self.move(
            (s.width() - self.width()) // 2,
            (s.height() - self.height()) // 2,
        )

    def _close_overlay(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None

    def accept(self):
        self._close_overlay()
        super().accept()

    def reject(self):
        self._close_overlay()
        super().reject()

    def closeEvent(self, e):
        self._close_overlay()
        super().closeEvent(e)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("heldCard")
        card.setStyleSheet(f"""
            QWidget#heldCard {{
                background:{WHITE};
                border:1px solid {BORDER};
                border-radius:16px;
            }}
            QWidget#heldCard QLabel {{
                background:transparent;
                color:{TEXT_DARK};
                border:none;
            }}
        """)
        _force_light(card)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 22, 24, 22)
        cl.setSpacing(14)

        # ── header ────────────────────────────
        hdr = QHBoxLayout()
        t = QLabel("Held Orders")
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{BROWN};")
        close_b = QPushButton()
        close_b.setFixedSize(28, 28)
        close_b.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:14px;}"
            "QPushButton:hover{background:#F3F4F6;}"
        )
        close_b.setIcon(QIcon(make_svg_icon(SVG["close"], 14, TEXT_LIGHT)))
        close_b.setIconSize(QSize(14, 14))
        close_b.clicked.connect(self.reject)
        hdr.addWidget(t)
        hdr.addStretch()
        hdr.addWidget(close_b)
        cl.addLayout(hdr)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{BORDER};border:none;")
        cl.addWidget(div)

        # ── held order list ───────────────────
        if not self._held:
            empty = QLabel("No orders are currently on hold.")
            empty.setFont(QFont("Segoe UI", 12))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{TEXT_LIGHT};margin:30px 0;")
            cl.addWidget(empty, stretch=1)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet(
                "QScrollArea{background:transparent;border:none;}"
            )
            inner = QWidget()
            il = QVBoxLayout(inner)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(8)

            for label, items in self._held.items():
                row_w = QFrame()
                row_w.setStyleSheet(
                    f"QFrame{{background:{WHITE};border:none;"
                    f"border-bottom:1px solid {BORDER};}}"
                )
                row_l = QVBoxLayout(row_w)
                row_l.setContentsMargins(0, 12, 0, 12)
                row_l.setSpacing(8)

                # ── Top row: label + action buttons ──
                top_row = QHBoxLayout()
                top_row.setSpacing(8)

                lbl_name = QLabel(label)
                lbl_name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
                lbl_name.setStyleSheet(
                    f"color:{BROWN};background:transparent;border:none;")
                top_row.addWidget(lbl_name, stretch=1)

                delete_btn = QPushButton("Delete")
                delete_btn.setFixedHeight(30)
                delete_btn.setMinimumWidth(64)
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background:transparent;color:{RED};
                        border:1px solid #FECACA;
                        border-radius:6px;font-size:11px;font-weight:600;
                        padding:0 10px;
                    }}
                    QPushButton:hover {{ background:{RED_DIM};border-color:{RED}; }}
                """)
                delete_btn.clicked.connect(
                    lambda _, lbl=label: self._delete_held(lbl))

                recall_btn = QPushButton("Recall")
                recall_btn.setFixedHeight(30)
                recall_btn.setMinimumWidth(64)
                recall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                recall_btn.setStyleSheet(f"""
                    QPushButton {{
                        background:{BROWN};color:{WHITE};border:none;
                        border-radius:6px;font-size:11px;font-weight:bold;
                        padding:0 10px;
                    }}
                    QPushButton:hover {{ background:{BROWN_DARK}; }}
                """)
                recall_btn.clicked.connect(
                    lambda _, lbl=label, its=items: self._recall(lbl, its))

                top_row.addWidget(delete_btn)
                top_row.addWidget(recall_btn)
                row_l.addLayout(top_row)

                # ── Item breakdown table ──────────────
                for ci in items:
                    item_row = QHBoxLayout()
                    item_row.setSpacing(0)

                    dot = QLabel("•")
                    dot.setFixedWidth(16)
                    dot.setStyleSheet(
                        f"color:{TEXT_LIGHT};background:transparent;border:none;")

                    item_name = QLabel(ci.name)
                    item_name.setFont(QFont("Segoe UI", 10))
                    item_name.setStyleSheet(
                        f"color:{TEXT_DARK};background:transparent;border:none;")

                    qty_lbl = QLabel(f"× {ci.qty}")
                    qty_lbl.setFont(QFont("Segoe UI", 10))
                    qty_lbl.setStyleSheet(
                        f"color:{TEXT_MID};background:transparent;border:none;")
                    qty_lbl.setFixedWidth(36)
                    qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    unit_lbl = QLabel(f"₱{ci.price:.2f} ea.")
                    unit_lbl.setFont(QFont("Segoe UI", 9))
                    unit_lbl.setStyleSheet(
                        f"color:{TEXT_LIGHT};background:transparent;border:none;")
                    unit_lbl.setFixedWidth(72)
                    unit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                                          Qt.AlignmentFlag.AlignVCenter)

                    sub_lbl = QLabel(f"₱{ci.subtotal:,.2f}")
                    sub_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                    sub_lbl.setStyleSheet(
                        f"color:{TEXT_DARK};background:transparent;border:none;")
                    sub_lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                                         Qt.AlignmentFlag.AlignVCenter)

                    item_row.addWidget(dot)
                    item_row.addWidget(item_name, stretch=1)
                    item_row.addWidget(qty_lbl)
                    item_row.addWidget(unit_lbl)
                    item_row.addSpacing(20)
                    item_row.addWidget(sub_lbl)
                    item_row.addSpacing(10)
                    row_l.addLayout(item_row)

                # ── Divider + total ───────────────────
                div_line = QFrame()
                div_line.setFixedHeight(1)
                div_line.setStyleSheet(
                    f"background:{BORDER};border:none;margin:2px 0;")
                row_l.addWidget(div_line)

                total = sum(i.subtotal for i in items)
                total_row = QHBoxLayout()
                total_lbl = QLabel("Order Total")
                total_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                total_lbl.setStyleSheet(
                    f"color:{TEXT_MID};background:transparent;border:none;")
                total_val = QLabel(f"₱{total:,.2f}")
                total_val.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                total_val.setStyleSheet(
                    f"color:{GREEN};background:transparent;border:none;")
                total_val.setAlignment(Qt.AlignmentFlag.AlignRight)
                total_row.addWidget(total_lbl)
                total_row.addWidget(total_val)
                row_l.addLayout(total_row)

                il.addWidget(row_w)

            il.addStretch()
            scroll.setWidget(inner)
            cl.addWidget(scroll, stretch=1)

        # ── close button ──────────────────────
        close_foot = QPushButton("Close")
        close_foot.setFixedHeight(40)
        close_foot.setCursor(Qt.CursorShape.PointingHandCursor)
        close_foot.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE};color:{TEXT_MID};
                border:1px solid {BORDER};border-radius:10px;font-size:13px;
            }}
            QPushButton:hover {{ background:{CREAM_MID}; }}
        """)
        close_foot.clicked.connect(self.reject)
        cl.addWidget(close_foot)

        outer.addWidget(card)

    def _recall(self, label: str, items: list):
        self.order_recalled.emit(items)
        self._held.pop(label, None)
        self.accept()

    def _delete_held(self, label: str):
        try:
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            if not BakeSyncAlert.ask_yes_no(
                self, "Delete Held Order?",
                f"Are you sure you want to permanently delete \"{label}\"?\n"
                f"This cannot be undone.",
                yes_text="Delete", no_text="Cancel"):
                return
        except ImportError:
            pass

        self._held.pop(label, None)

        # Re-open fresh with updated held orders
        new_dlg = HeldOrdersDialog(self._held, self.parent())
        new_dlg.order_recalled.connect(
            lambda items: self.order_recalled.emit(items))
        self._close_overlay()
        super().reject()
        new_dlg.exec()

def _extend_pos_widget(cls):
    """
    Attaches the new feature-set methods to an already-defined POSWidget class.
    Call once after the class is defined:  _extend_pos_widget(POSWidget)
    """

    # ── Hold current cart (UPDATED with BakeSyncAlert) ──
    def _hold_cart(self):
        if not self.cart:
            try:
                # 🟢 FIX: Using the custom alert theme for the error dialog
                from bakesync.widgets.custom_alerts import BakeSyncAlert
                BakeSyncAlert.show_error(
                    self.window(), 
                    "Empty Cart", 
                    "Your cart is empty. Please add items before attempting to hold an order."
                )
            except ImportError:
                # Fallback to toast if the custom_alerts file isn't found
                self._toast.show_message(
                    "Cart is empty — nothing to hold.",
                    error=True, parent_widget=self)
            return
            
        dlg = HoldOrderDialog(self)
        dlg.label_confirmed.connect(self._do_hold)
        dlg.exec()

    def _do_hold(self, label: str):
        self._held_orders[label] = list(self.cart)
        n = len(self._held_orders)
        self._clear_cart()
        self._toast.show_message(
            f"Order \"{label}\" held  ({n} held total)",
            parent_widget=self)
        self._update_held_btn()

    # ── Recall held order ─────────────────────
    def _recall_held(self):
        dlg = HeldOrdersDialog(self._held_orders, self)
        dlg.order_recalled.connect(self._restore_held)
        dlg.exec()
        self._update_held_btn()

    def _restore_held(self, items: list):
        if self.cart:
            try:
                from bakesync.widgets.custom_alerts import BakeSyncAlert
                choice = BakeSyncAlert.ask_yes_no(
                    self.window(),
                    "Cart Not Empty",
                    "You still have items in your current order.\n"
                    "What would you like to do?\n\n"
                    "• YES — Hold current order first, then recall.\n"
                    "• NO  — Discard current order and recall.",
                    yes_text="Hold Current First",
                    no_text="Discard & Recall",
                )
            except ImportError:
                choice = False

            if choice:
                # Auto-hold the current cart with a generated label
                import datetime
                auto_label = f"Auto-hold {datetime.datetime.now().strftime('%H:%M:%S')}"
                self._held_orders[auto_label] = list(self.cart)
                self._toast.show_message(
                    f"Current order saved as \"{auto_label}\"",
                    parent_widget=self)
                self._update_held_btn()

        self.cart = items
        self._refresh_cart_panel()
        self._apply_filters()
        self._toast.show_message("Order recalled.", parent_widget=self)

    # ── Update held-orders badge on button ────
    def _update_held_btn(self):
        n = len(self._held_orders)
        if hasattr(self, "_recall_btn") and self._recall_btn:
            if n > 0:
                self._recall_btn.setText(f"Held ({n})")
                self._recall_btn.setStyleSheet(f"""
                    QPushButton {{
                        background:white;color:black;
                        border:1px solid {BROWN_DARK};border-radius:8px;
                        font-size:12px;font-weight:600;
                    }}
                    QPushButton:hover {{ background:{BROWN_DARK};color:{WHITE}; }}
                """)
                self._recall_btn.show()
            else:
                self._recall_btn.hide()

    # ── Quick-add dialog ──────────────────────
    def _open_quick_add(self):
        products = []
        for card in self._all_cards:
            products.append({
                "id":    card.prod_id,
                "name":  card.prod_name,
                "price": card.prod_price,
                "stock": card.prod_stock,
            })
        dlg = QuickAddDialog(products, self)
        dlg.product_selected.connect(self._quick_add_to_cart)
        dlg.exec()

    def _quick_add_to_cart(self, prod_id: int, qty: int):
        self._pending_qty = qty
        self._add_to_cart_by_id(prod_id)

    # ── Discount on cart total ────────────────
    def _apply_discount(self, pct: float):
        """Apply a percentage discount to the current order total."""
        if not self.cart:
            return
        # Store discount on the widget for use in payment
        self._discount_pct = max(0.0, min(100.0, pct))
        self._refresh_cart_panel()
        self._toast.show_message(
            f"{pct:.0f}% discount applied.",
            parent_widget=self)

    def _get_discount_amount(self) -> float:
        pct = getattr(self, "_discount_pct", 0.0)
        gross = sum(i.subtotal for i in self.cart)
        return gross * pct / 100.0

    def _discounted_total(self) -> float:
        gross = sum(i.subtotal for i in self.cart)
        return max(0.0, gross - self._get_discount_amount())

    # ── Keyboard shortcut: open quick-add ─────
    def _install_extra_shortcuts(self):
        from PyQt6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("F1"), self, self._open_quick_add)
        QShortcut(QKeySequence("F2"), self, self._hold_cart)
        QShortcut(QKeySequence("F3"), self, self._recall_held)

    # ── Attach everything ─────────────────────
    cls._hold_cart            = _hold_cart
    cls._do_hold              = _do_hold
    cls._recall_held          = _recall_held
    cls._restore_held         = _restore_held
    cls._update_held_btn      = _update_held_btn
    cls._open_quick_add       = _open_quick_add
    cls._quick_add_to_cart    = _quick_add_to_cart
    cls._apply_discount       = _apply_discount
    cls._get_discount_amount  = _get_discount_amount
    cls._discounted_total     = _discounted_total
    cls._install_extra_shortcuts = _install_extra_shortcuts
    return cls

_extend_pos_widget(POSWidget)

if __name__ == "__main__":
    import sys

    class _MockDB:
        """Minimal in-memory DB shim for running the POS without the full app."""

        def __init__(self):
            import sqlite3
            self._conn = sqlite3.connect(":memory:")
            self._conn.row_factory = sqlite3.Row
            c = self._conn.cursor()
            c.executescript("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name TEXT, retail_price REAL,
                    stock_qty INTEGER,
                    product_type TEXT DEFAULT 'Bread',
                    image_path TEXT,
                    is_archived INTEGER DEFAULT 0
                );
                CREATE TABLE sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER, quantity INTEGER,
                    amount REAL, tendered REAL, change_given REAL,
                    cashier TEXT, created_at TEXT,
                    is_voided INTEGER DEFAULT 0, voided_by TEXT
                );
                CREATE TABLE product_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER, quantity_remaining INTEGER,
                    expiry_date TEXT
                );
                CREATE TABLE void_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER, quantity INTEGER,
                    amount REAL, reason TEXT, voided_by TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );
                CREATE TABLE pos_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT DEFAULT 'Open',
                    total_sales REAL DEFAULT 0,
                    total_txns INTEGER DEFAULT 0,
                    closed_by TEXT,
                    closed_at TEXT
                );
                INSERT INTO pos_sessions (status) VALUES ('Open');
                INSERT INTO products (name, retail_price, stock_qty, product_type)
                    VALUES
                    ('Sourdough Loaf',    120.00, 24, 'Bread'),
                    ('Croissant',          55.00, 40, 'Pastry'),
                    ('Pandesal (6 pcs)',   30.00,  5, 'Bread'),
                    ('Chocolate Eclair',   65.00,  0, 'Pastry'),
                    ('Iced Americano',     90.00, 18, 'Beverage'),
                    ('Caramel Latte',     110.00, 12, 'Beverage'),
                    ('Cheese Roll',        45.00, 30, 'Bread'),
                    ('Almond Croissant',   75.00,  3, 'Pastry');
            """)
            self._conn.commit()

        def fetch_all(self, query, params=()):
            c = self._conn.cursor()
            c.execute(query, params)
            return c.fetchall()

        def fetch_one(self, query, params=()):
            c = self._conn.cursor()
            c.execute(query, params)
            return c.fetchone()

        def execute_query(self, query, params=()):
            c = self._conn.cursor()
            c.execute(query, params)
            self._conn.commit()
            return c.lastrowid

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db  = _MockDB()
    pos = POSWidget(db, current_user="Demo Cashier")
    pos.setWindowTitle("La Farine POS — Standalone Test")
    pos.resize(1280, 800)
    pos.show()

    sys.exit(app.exec())