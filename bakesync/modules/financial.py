from bakesync.paths import IMAGES_DIR
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
                             QDoubleSpinBox, QSpinBox, QTabWidget, QHeaderView,
                             QMessageBox, QFrame, QGridLayout, QMenu, QGraphicsDropShadowEffect,
                             QScrollArea, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt, QDate, QRect, QSize, QMargins
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from datetime import date, datetime, timedelta
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import InfoIcon, title_row, nice_max, BarChart
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath
from bakesync.core.database import DatabaseManager
import json

from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix


# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN TOKENS (Minimalist Bakery Theme)
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":             "#FDFBF7",  # Cream background
    "surface":        "#FFFFFF",  # White cards/tables
    "surface2":       "#F5F2EB",  # Slight off-cream
    "border":         "#E8E2D9",
    "border2":        "#D1C7BA",
    "text_primary":   "#3D271D",  # Dark brown text
    "text_secondary": "#8A7365",  # Muted brown text
    "text_muted":     "#B0A69D",
    
    # Solid Card Colors
    "card_dark":      "#3A2318",  # Dark brown
    "card_amber":     "#9A7B4F",  # Golden brown
    "card_green":     "#1E5641",  # Deep green
    
    # Action Colors
    "blue":           "#2563EB",
    "blue_light":     "#DBEAFE",
    "green":          "#16A34A",
    "green_light":    "#DCFCE7",
    "red":            "#DC2626",
    "amber":          "#D97706",
    "slate":          "#64748B",
}

FONT_DISPLAY = "Segoe UI"
FONT_MONO = "Consolas"

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED STYLE SNIPPETS
# ─────────────────────────────────────────────────────────────────────────────
_BTN_MENU_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {C['text_secondary']};
        font-size: 18px;
        font-weight: bold;
        padding: 0px 4px;
        min-width: 32px;
        max-width: 32px;
        min-height: 28px;
        max-height: 28px;
    }}
    QPushButton:hover  {{ color: {C['text_primary']}; }}
"""

_MENU_STYLE = f"""
    QMenu {{
        background-color: {C['surface']};
        border: 1px solid {C['border']};
        border-radius: 6px;
        padding: 6px 0px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        font-size: 13px;
        font-family: {FONT_DISPLAY};
        color: {C['text_primary']};
    }}
    QMenu::item:selected {{ background-color: {C['surface2']}; }}
"""

_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {C['surface']};
        border: none;  /* 🟢 PINALITAN: Tinanggal ang outer border */
        border-radius: 8px;
        gridline-color: {C['border']};
        font-family: {FONT_DISPLAY};
        font-size: 13px;
        color: {C['text_primary']};
        selection-background-color: {C['surface2']};
        outline: none; /* 🟢 DAGDAG: Para walang blue line pag na-click */
    }}
    QTableWidget::item {{
        padding: 6px 12px;
        border-bottom: none; /* 🟢 PINALITAN: Tinanggal ang linya sa bawat row */
    }}
    QHeaderView::section {{
        background-color: {C['surface2']};
        color: {C['text_secondary']};
        font-weight: bold;
        font-size: 11px;
        font-family: {FONT_DISPLAY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 10px 12px;
        border: none;
        border-bottom: none !important;
    }}
"""

_TAB_STYLE = f"""
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {C['text_secondary']};
        padding: 10px 24px;
        font-size: 12px;
        font-weight: bold;
        font-family: {FONT_DISPLAY};
        border: none;
        border-bottom: 3px solid transparent;
        margin-right: 16px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QTabBar::tab:selected {{
        color: {C['text_primary']};
        border-bottom: 3px solid {C['card_dark']};
    }}
    QTabBar::tab:hover:!selected {{
        color: {C['text_primary']};
    }}
"""


_SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background: {C['surface2']};
        width: 6px;
        border-radius: 3px;
        margin: 0;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {C['card_dark']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: {C['surface2']};
        height: 6px;
        border-radius: 3px;
        margin: 0;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {C['card_dark']};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
        background: none;
    }}
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _shadow(widget, blur=18, offset_y=4, color="#00000010"):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, offset_y)
    fx.setColor(QColor(color))
    widget.setGraphicsEffect(fx)
    return fx

def _btn(text, bg, fg="#FFFFFF", hover=None, h=38, bold=True, radius=6, font_size=12, border=False):
    hover = hover or bg
    border_css = f"border: 1px solid {C['border']};" if border else "border: none;"
    style = f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            {border_css}
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: {'bold' if bold else 'normal'};
            font-family: {FONT_DISPLAY};
            padding: 0 16px;
        }}
        QPushButton:hover {{ background-color: {hover}; opacity: 0.9; }}
        QPushButton:pressed {{ background-color: {C['text_primary']}; color: #FFFFFF; }}
    """
    btn = QPushButton(text)
    btn.setFixedHeight(h)
    btn.setStyleSheet(style)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def _separator(horizontal=True):
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine if horizontal else QFrame.Shape.VLine)
    line.setStyleSheet(f"color: {C['border']}; background-color: {C['border']}; max-height: 1px;")
    return line

def _migrate_reconciliation(db: DatabaseManager):
    for stmt in [
        "ALTER TABLE reconciliation ADD COLUMN is_archived INTEGER DEFAULT 0",
        "ALTER TABLE reconciliation ADD COLUMN archived_by TEXT",
        "ALTER TABLE reconciliation ADD COLUMN submitted_by TEXT",
        "ALTER TABLE reconciliation ADD COLUMN actioned_by TEXT",
    ]:
        try: db.execute_query(stmt)
        except Exception: pass

    # Hiwalay ang CREATE TABLE — para hindi ma-skip kahit may ALTER error na natrigger bago ito
    try:
        db.execute_query("""CREATE TABLE IF NOT EXISTS financial_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            icon TEXT, 
            description TEXT, 
            action_by TEXT, 
            created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
        )""")
        print("[Migration] financial_audit_log table OK")
    except Exception as e:
        print(f"[Migration] FAILED to create financial_audit_log: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  STATUS BADGE WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class StatusBadge(QLabel):
    STATUS_COLORS = {
        "Submitted": (C["amber"],       C["surface2"]),
        "Verified":  (C["blue"],        C["surface2"]),
        "Closed":    (C["green"],       C["surface2"]),
        "Pending":   (C["text_muted"],  C["surface2"]),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(status, parent)
        color, bg = self.STATUS_COLORS.get(status, (C["text_muted"], C["surface2"]))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                font-family: {FONT_DISPLAY};
                padding: 4px 12px;
                min-width: 70px; /* I-lock ang width para hindi maputol ang text */
            }}
        """)
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; font-family: {FONT_DISPLAY}; }} " + _SCROLLBAR_STYLE)
        self.setFixedHeight(26)

# ─────────────────────────────────────────────────────────────────────────────
#  SOLID METRIC CARD
# ─────────────────────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, title, sub_text, bg_color, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: #FFFFFF; }}
        """)
        self.setFixedHeight(95)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setFont(QFont(FONT_DISPLAY, 10, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: rgba(255, 255, 255, 0.7); letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel("₱0.00")
        self.lbl_value.setFont(QFont(FONT_DISPLAY, 28, QFont.Weight.Bold))
        layout.addWidget(self.lbl_value)

        

        self.lbl_sub = QLabel(sub_text)
        self.lbl_sub.setFont(QFont(FONT_DISPLAY, 10))
        self.lbl_sub.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(self.lbl_sub)



from PyQt6.QtGui import QPen, QPainterPath

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM VECTOR ICONS
# ─────────────────────────────────────────────────────────────────────────────
class VectorIcon(QWidget):
    def __init__(self, icon_type, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        if icon_type == "arrow_right_flat":
            self.setFixedSize(24, 24) # Maliit lang para sa table cell
        else:
            self.setFixedSize(32, 32)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Wag lagyan ng background circle kapag flat arrow
        if self.icon_type != "arrow_right_flat":
            bg_path = QPainterPath()
            bg_path.addEllipse(0, 0, 32, 32)
            painter.fillPath(bg_path, QBrush(QColor(C["surface2"])))
        
        pen = QPen(QColor(C["text_secondary"]))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        if self.icon_type == "cash":
            painter.drawRect(8, 14, 16, 9)
            painter.drawLine(12, 14, 12, 10)
            painter.drawLine(12, 10, 20, 10)
            painter.drawLine(20, 10, 20, 14)
        elif self.icon_type == "cogs":
            painter.drawArc(8, 8, 16, 16, 45 * 16, 270 * 16)
            painter.drawLine(20, 8, 24, 12)
            painter.drawLine(24, 12, 20, 16)
        elif self.icon_type == "check":
            painter.drawLine(10, 16, 14, 20)
            painter.drawLine(14, 20, 22, 11)
        elif self.icon_type == "receipt":
            painter.drawRect(11, 8, 10, 16)
            painter.drawLine(14, 12, 18, 12)
            painter.drawLine(14, 16, 18, 16)
        elif self.icon_type == "arrow_right_flat":
            # DRAW SOTPHISTICATED VECTOR ARROW
            pen.setColor(QColor(C["text_muted"]))
            painter.setPen(pen)
            painter.drawLine(4, 12, 20, 12)
            painter.drawLine(14, 6, 20, 12)
            painter.drawLine(14, 18, 20, 12)

        painter.end()

# ─────────────────────────────────────────────────────────────────────────────
#  SOLID METRIC CARD
# ─────────────────────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, title, sub_text, bg_color, parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: #FFFFFF; }}
        """)
        self.setMinimumHeight(95) # Binawasan ang height mula 115
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12) # Hinigpitan ang margins
        layout.setSpacing(0)

        self.lbl_title = QLabel(title)
        self.lbl_title.setFont(QFont(FONT_DISPLAY, 10, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: rgba(255, 255, 255, 0.7); letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel("₱0.00")
        self.lbl_value.setFont(QFont(FONT_DISPLAY, 24, QFont.Weight.Bold)) # Pinaliit font size
        layout.addWidget(self.lbl_value)

        layout.addStretch()

        self.lbl_sub = QLabel(sub_text)
        self.lbl_sub.setFont(QFont(FONT_DISPLAY, 10))
        self.lbl_sub.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(self.lbl_sub)

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM MINIMALIST LINE CHART (QPainter)
# ─────────────────────────────────────────────────────────────────────────────
class MinimalLineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_rev = [0] * 7
        self.data_exp = [0] * 7
        self.data_mar = [0] * 7
        self.setMinimumHeight(160) # Tumaas ng konti para sa dates
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent;")

    def update_data(self, rev_list, exp_list, mar_list):
        self.data_rev = rev_list
        self.data_exp = exp_list
        self.data_mar = mar_list
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        
        # ── MARGINS (Pinalaki para pumasok ang Labels) ──
        margin_top = 35
        margin_bottom = 25 # Space para sa Dates
        margin_left = 45   # Space para sa Money values (Y-axis)
        margin_right = 15
        
        inner_width = width - margin_left - margin_right
        inner_height = height - margin_top - margin_bottom

        # Get min and max for scaling
        all_data = self.data_rev + self.data_exp + self.data_mar
        max_val = max(all_data) if all_data else 1
        min_val = min(all_data) if all_data else 0
        if max_val == min_val:
            max_val += 1 

        val_range = max_val - min_val

        # Fonts para sa labels
        axis_font = QFont(FONT_DISPLAY, 9)
        painter.setFont(axis_font)

        # ── 1. DRAW Y-AXIS (Money Values & Grid Lines) ──
        num_grid_lines = 4
        for i in range(num_grid_lines):
            y = margin_top + i * (inner_height / (num_grid_lines - 1))
            
            # Draw Dashed Grid Line
            painter.setPen(QPen(QColor(C["border"]), 1, Qt.PenStyle.DashLine))
            painter.drawLine(margin_left, int(y), width - margin_right, int(y))
            
            # Draw Money Text (e.g., ₱5.2k, ₱0)
            val = max_val - i * (val_range / (num_grid_lines - 1))
            label_text = f"₱{val/1000:.1f}k" if val >= 1000 else f"₱{int(val)}"
            painter.setPen(QColor(C["text_muted"]))
            painter.drawText(0, int(y) - 10, margin_left - 8, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)

        # ── 2. DRAW X-AXIS (Dates) ──
        from PyQt6.QtCore import QDate
        current_date = QDate.currentDate()
        num_points = len(self.data_rev) if self.data_rev else 7
        
        for i in range(num_points):
            x = margin_left + (i / max(1, num_points - 1)) * inner_width
            
            # Compute past 7 days based on current date
            days_ago = num_points - 1 - i
            point_date = current_date.addDays(-days_ago)
            date_str = point_date.toString("MMM d") # Format: e.g., "May 5"
            
            painter.setPen(QColor(C["text_muted"]))
            painter.drawText(int(x) - 20, height - margin_bottom + 8, 40, 20, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, date_str)


        # Helper function for coordinates
        def get_pt(index, value, total_points):
            x = margin_left + (index / max(1, total_points - 1)) * inner_width
            y = margin_top + (1 - ((value - min_val) / val_range)) * inner_height
            return x, y

        # Helper function to draw lines
        def draw_line(data_list, color_hex):
            if not data_list: return
            path = QPainterPath()
            points = []
            for i, val in enumerate(data_list):
                px, py = get_pt(i, val, len(data_list))
                points.append((px, py))
                if i == 0: path.moveTo(px, py)
                else: path.lineTo(px, py)
            
            # Draw Line
            pen = QPen(QColor(color_hex))
            pen.setWidth(3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
            
            # Draw Dots
            painter.setBrush(QBrush(QColor(C["surface"])))
            for px, py in points:
                painter.drawEllipse(int(px) - 4, int(py) - 4, 8, 8)

        # ── 3. DRAW THE ACTUAL LINES ──
        draw_line(self.data_rev, C["card_dark"])
        draw_line(self.data_exp, C["card_amber"])
        draw_line(self.data_mar, C["card_green"])

        # ── 4. DRAW LEGEND ──
        legend_font = QFont(FONT_DISPLAY, 9, QFont.Weight.Bold)
        painter.setFont(legend_font)
        
        legends = [("Revenue", C["card_dark"]), ("Expenses", C["card_amber"]), ("Net Margin", C["card_green"])]
        x_offset = margin_left
        for label, color in legends:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(int(x_offset), 8, 8, 8)
            
            painter.setPen(QColor(C["text_secondary"]))
            painter.drawText(int(x_offset) + 14, 17, label)
            x_offset += 80

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN FINANCIAL WIDGET
# ─────────────────────────────────────────────────────────────────────────────
EXPENSE_CATEGORIES = ["Rent", "Electricity & Water", "Supplies", "Ingredients", "Transport", "Salary", "Repairs", "Other"]
VOID_REASONS = ["Wrong item", "Wrong quantity", "Customer changed mind", "Damaged / spoiled", "Price mistake", "Sale undone", "Other"]
STATUS_WORDS = {"Submitted": "Waiting for check", "Verified": "Checked", "Closed": "Done", "Pending": "Waiting for check"}


def guess_category(name):
    """Older expenses were saved without a category; guess one from the name."""
    n = (name or "").lower()
    rules = (("Rent", ("rent",)), ("Electricity & Water", ("electric", "bill", "meralco", "internet")),
             ("Salary", ("salary", "wage", "payroll", "sahod")), ("Transport", ("transport", "fuel", "gas", "delivery", "fare")),
             ("Ingredients", ("flour", "sugar", "egg", "butter", "yeast", "ingredient", "milk")),
             ("Repairs", ("repair", "maint", "fix")),
             ("Supplies", ("clean", "suppl", "packag", "plastic", "water", "bag", "tissue")))
    for cat, words in rules:
        if any(w in n for w in words):
            return cat
    return "Other"


def period_range(name):
    """(start_date, end_date) as 'YYYY-MM-DD' strings, both inclusive."""
    today = date.today()
    if name == "Today":
        return today.isoformat(), today.isoformat()
    if name == "Yesterday":
        y = today - timedelta(days=1)
        return y.isoformat(), y.isoformat()
    if name == "This week":
        return (today - timedelta(days=today.weekday())).isoformat(), today.isoformat()
    if name == "Last 7 days":
        return (today - timedelta(days=6)).isoformat(), today.isoformat()
    if name == "This month":
        return today.replace(day=1).isoformat(), today.isoformat()
    if name == "Last month":
        last_end = today.replace(day=1) - timedelta(days=1)
        return last_end.replace(day=1).isoformat(), last_end.isoformat()
    if name == "Last 30 days":
        return (today - timedelta(days=29)).isoformat(), today.isoformat()
    return "2000-01-01", today.isoformat()   # All time


def _nice_dt(ts):
    try:
        d = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            d = datetime.strptime(str(ts)[:10], "%Y-%m-%d")
            return "Today" if d.date() == date.today() else d.strftime("%b %d, %Y")
        except ValueError:
            return str(ts)[:16]
    day = "Today" if d.date() == date.today() else ("Yesterday" if d.date() == date.today() - timedelta(days=1)
                                                     else d.strftime("%b %d, %Y"))
    return f"{day}, {d.strftime('%I:%M %p').lstrip('0')}"


class _Card(QFrame):
    """Simple number card: small title, big value, one line under it."""

    def __init__(self, title, color, info=""):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background: {color}; border-radius: 14px; }} QLabel {{ background: transparent; border: none; }}")
        self.setMinimumHeight(118)
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 14, 14, 16); lay.setSpacing(4)
        tr = QHBoxLayout(); tr.setSpacing(4)
        t = QLabel(title); t.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 600;")
        tr.addWidget(t); tr.addStretch()
        if info:
            ic = InfoIcon(info, title, color="#F3D9B8")
            ic.setStyleSheet("QToolButton { border: none; background: transparent; border-radius: 6px; }"
                             "QToolButton:hover { background: rgba(255,255,255,0.15); }")
            tr.addWidget(ic)
        self.value = QLabel("₱0.00"); self.value.setFont(QFont(FONT_DISPLAY, 24, QFont.Weight.Bold))
        self.value.setStyleSheet("color: white;")
        self.sub = QLabel(""); self.sub.setWordWrap(True); self.sub.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px;")
        lay.addLayout(tr); lay.addWidget(self.value); lay.addWidget(self.sub); lay.addStretch()


class FinancialWidget(QWidget):
    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db = db
        self.current_user = current_user or "Unknown"
        _migrate_reconciliation(db)
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; font-family: {FONT_DISPLAY}; }}")
        self.init_ui()
        from PyQt6.QtCore import QTimer
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_realtime_data)
        self.auto_refresh_timer.start(30000)

    # ── timers / refresh ──────────────────────────────────────────────────
    def stop_timers(self):
        try:
            self.auto_refresh_timer.stop()
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_realtime_data()

    def refresh_realtime_data(self):
        if not self.isVisible() or self.db.is_closed():
            return
        [self.load_summary_cards, self.load_recon_data, self.load_expenses, self.load_void_data][self.tabs.currentIndex()]()

    def on_tab_changed(self, index=None):
        self.refresh_realtime_data()

    # ── UI ────────────────────────────────────────────────────────────────
    def _combo(self, items, width=170):
        cb = QComboBox()
        cb.addItems(items)
        cb.setFixedHeight(38)
        cb.setMinimumWidth(width)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        return cb

    def _panel(self):
        f = QFrame()
        f.setObjectName("panel")
        f.setStyleSheet(f"QFrame#panel {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 12px; }}"
                        "QLabel { background: transparent; border: none; }")
        return f

    def _hint(self, text):
        l = QLabel(text); l.setWordWrap(False)
        l.setStyleSheet(f"color: {C['text_secondary']}; font-size: 13px; background: transparent;")
        return l

    def _summary_line(self):
        l = QLabel(""); l.setWordWrap(True)
        l.setStyleSheet(f"color: {C['text_primary']}; background: {C['surface2']}; border-radius: 8px; padding: 9px 14px; font-size: 13px;")
        return l

    def init_ui(self):
        root = QVBoxLayout(self); root.setContentsMargins(32, 18, 32, 18); root.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_TAB_STYLE.replace("text-transform: uppercase;", ""))

        # 1) SUMMARY ─────────────────────────────────────────────
        ov = QWidget(); ovl = QVBoxLayout(ov); ovl.setContentsMargins(0, 16, 0, 0); ovl.setSpacing(14)
        top = QHBoxLayout()
        top.addWidget(self._hint("Money in and money out for the period you pick."))
        top.addStretch()
        self._period_btns = {}
        for name in ("Today", "This week", "This month"):
            b = QPushButton(name); b.setCheckable(True); b.setFixedHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ background: white; color: {C['text_secondary']}; border: 1px solid {C['border']}; "
                            f"border-radius: 18px; padding: 0 18px; font-size: 13px; font-weight: 600; }}"
                            f"QPushButton:checked {{ background: {C['card_dark']}; color: white; border-color: {C['card_dark']}; }}")
            b.clicked.connect(lambda _, n=name: self._set_period(n))
            top.addWidget(b)
            self._period_btns[name] = b
        self._period = "Today"
        self._period_btns["Today"].setChecked(True)
        ovl.addLayout(top)

        cards = QHBoxLayout(); cards.setSpacing(14)
        self.card_sales = _Card("Sales", C["card_dark"], "All the money from the POS for this period. Voided sales are not counted.")
        self.card_cost = _Card("Cost of what was sold", C["card_amber"],
                               "What the bread and items you sold cost you (the puhunan in Pricing times the pieces sold).")
        self.card_exp = _Card("Expenses", "#7C5A3A", "Money you paid out: rent, bills, supplies and others. Add them in the Expenses tab.")
        self.card_profit = _Card("Profit", C["card_green"], "What is left for you: Sales minus the cost of what was sold minus Expenses. "
                                 "Red means you spent more than you earned.")
        for c in (self.card_sales, self.card_cost, self.card_exp, self.card_profit):
            cards.addWidget(c)
        ovl.addLayout(cards)
        self.money_note = self._summary_line()
        ovl.addWidget(self.money_note)

        row = QHBoxLayout(); row.setSpacing(14)
        chart_panel = self._panel()
        cpl = QVBoxLayout(chart_panel); cpl.setContentsMargins(16, 14, 16, 10)
        ct, _ = title_row("Money in and out — last 14 days", size=13, icon="chart",
                          info="Each day has two bars. Dark brown = sales (money in). Light brown = expenses (money out). "
                               "A taller dark bar is a better day. Days with no bars had no sales.")
        cpl.addWidget(ct)
        self.chart_note = QLabel(""); self.chart_note.setWordWrap(True)
        self.chart_note.setStyleSheet(f"color: {C['text_secondary']}; font-size: 12px;")
        cpl.addWidget(self.chart_note)
        self.chart_view = BarChart(money=True, empty_text="No sales or expenses in the last 14 days")
        self.chart_view.setMinimumHeight(240)
        cpl.addWidget(self.chart_view, 1)
        row.addWidget(chart_panel, 6)

        side = QVBoxLayout(); side.setSpacing(14)
        cat_panel = self._panel()
        self.cat_layout = QVBoxLayout(cat_panel); self.cat_layout.setContentsMargins(16, 14, 16, 14); self.cat_layout.setSpacing(6)
        side.addWidget(cat_panel)
        act_panel = self._panel()
        al = QVBoxLayout(act_panel); al.setContentsMargins(16, 14, 16, 14); al.setSpacing(6)
        at, _ = title_row("Recent money activity", size=13, icon="activity",
                          info="The last cash counts, expenses and voids, newest first.")
        al.addWidget(at)
        self.activity_list_layout = QVBoxLayout(); self.activity_list_layout.setSpacing(4)
        al.addLayout(self.activity_list_layout); al.addStretch()
        side.addWidget(act_panel, 1)
        row.addLayout(side, 4)
        ovl.addLayout(row, 1)
        self.tabs.addTab(ov, "Summary")

        # 2) CASH COUNT ──────────────────────────────────────────
        rc = QWidget(); rcl = QVBoxLayout(rc); rcl.setContentsMargins(0, 16, 0, 0); rcl.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(self._hint("Count the cash in the drawer at closing."))
        head.addWidget(InfoIcon("BakeSync compares the cash you counted with the POS sales. "
                                "Exact = they match. Short = cash is missing. Over = there is extra cash. "
                                "A manager then marks each count as Checked, then Done.", "Cash Count"))
        head.addStretch()
        arch = _btn("Archived counts", C["surface"], C["text_primary"], border=True, h=38, font_size=13)
        arch.clicked.connect(self.open_archived_eod_dialog)
        head.addWidget(arch)
        count = _btn("Count Cash Now", C["card_dark"], h=38, font_size=13)
        count.clicked.connect(self.open_eod_dialog)
        head.addWidget(count)
        rcl.addLayout(head)
        rf = QHBoxLayout(); rf.setSpacing(8)
        self.rc_period = self._combo(["Last 30 days", "This week", "This month", "Last month", "All time"], 150)
        self.rc_result = self._combo(["All results", "Exact", "Short", "Over"], 140)
        self.rc_status = self._combo(["Any status", "Waiting for check", "Checked", "Done"], 170)
        self.rc_person = self._combo(["Everyone"], 150)
        rf.addWidget(QLabel("Show:"))
        for w in (self.rc_period, self.rc_result, self.rc_status, self.rc_person):
            w.currentTextChanged.connect(self.load_recon_data)
            rf.addWidget(w)
        rf.addStretch()
        rcl.addLayout(rf)
        self.recon_summary = self._summary_line()
        rcl.addWidget(self.recon_summary)
        self.recon_table = self._make_table(["Date", "POS sales", "Cash counted", "Difference", "Status", "Counted / checked by", ""])
        hdr = self.recon_table.horizontalHeader()
        for c in range(6):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.recon_table.setColumnWidth(6, 110)
        rcl.addWidget(self.recon_table, 1)
        self.tabs.addTab(rc, "Cash Count")

        # 3) EXPENSES ────────────────────────────────────────────
        ex = QWidget(); exl = QVBoxLayout(ex); exl.setContentsMargins(0, 16, 0, 0); exl.setSpacing(12)
        f = QHBoxLayout(); f.setSpacing(8)
        self.exp_period = self._combo(["This month", "Last month", "This week", "Today", "Last 30 days", "All time"], 150)
        self.exp_cat = self._combo(["All categories"] + EXPENSE_CATEGORIES, 190)
        self.exp_search = QLineEdit(); self.exp_search.setPlaceholderText("Search expense...")
        self.exp_search.setFixedSize(200, 38); self.exp_search.setClearButtonEnabled(True)
        self.exp_search.setStyleSheet(f"QLineEdit {{ background: white; border: 1px solid {C['border']}; border-radius: 8px; "
                                      f"padding: 0 12px; font-size: 13px; color: {C['text_primary']}; }}")
        for w in (self.exp_period, self.exp_cat):
            w.currentTextChanged.connect(self.load_expenses)
        self.exp_search.textChanged.connect(self.load_expenses)
        f.addWidget(self.exp_period); f.addWidget(self.exp_cat); f.addWidget(self.exp_search)
        f.addWidget(InfoIcon("Money you paid for the store: rent, bills, supplies, salary and more. "
                             "Pick a period and a kind to see only those. Expenses lower your profit.", "Expenses"))
        f.addStretch()
        add = _btn("+ Add Expense", C["card_dark"], h=38, font_size=13)
        add.clicked.connect(self.log_opex)
        f.addWidget(add)
        exl.addLayout(f)
        self.exp_summary = self._summary_line()
        exl.addWidget(self.exp_summary)
        self.exp_table = self._make_table(["Date", "What", "Category", "Amount", "Added by"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        exl.addWidget(self.exp_table, 1)
        self.tabs.addTab(ex, "Expenses")

        # 4) VOIDS & REFUNDS ─────────────────────────────────────
        vd = QWidget(); vdl = QVBoxLayout(vd); vdl.setContentsMargins(0, 16, 0, 0); vdl.setSpacing(12)
        f2 = QHBoxLayout(); f2.setSpacing(8)
        self.void_reason = self._combo(["All reasons"] + VOID_REASONS + ["Not given"], 200)
        self.void_period = self._combo(["This month", "Last month", "This week", "Today", "Last 30 days", "All time"], 150)
        self.void_cashier = self._combo(["All cashiers"], 160)
        for w in (self.void_reason, self.void_period, self.void_cashier):
            w.currentTextChanged.connect(self.load_void_data)
        f2.addWidget(QLabel("Show:")); f2.addWidget(self.void_reason); f2.addWidget(self.void_period); f2.addWidget(self.void_cashier)
        f2.addWidget(InfoIcon("A void cancels a sale and returns the money. The cashier picks the reason. "
                              "Many voids from one person, or many 'Not given' reasons, are worth asking about.", "Voids & Refunds"))
        f2.addStretch()
        vdl.addLayout(f2)
        self.void_summary = self._summary_line()
        vdl.addWidget(self.void_summary)
        self.void_table = self._make_table(["When", "Product", "Qty", "Money returned", "Reason", "Voided by"])
        self.void_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vdl.addWidget(self.void_table, 1)
        self.tabs.addTab(vd, "Voids && Refunds")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        root.addWidget(self.tabs)
        self.load_summary_cards()

    def _make_table(self, headers):
        t = QTableWidget()
        t.setFrameShape(QFrame.Shape.NoFrame)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(_TABLE_STYLE.replace("text-transform: uppercase;", "") +
                        f"QTableWidget {{ alternate-background-color: {C['surface2']}; }}" + _SCROLLBAR_STYLE)
        return t

    def _cell(self, table, row, col, text, color=None, bold=False, align=Qt.AlignmentFlag.AlignCenter):
        it = QTableWidgetItem(text)
        it.setTextAlignment(align)
        if color:
            it.setForeground(QColor(color))
        if bold:
            it.setFont(QFont(FONT_DISPLAY, 10, QFont.Weight.Bold))
        table.setItem(row, col, it)
        return it

    def _empty(self, table, text):
        table.setRowCount(1)
        it = self._cell(table, 0, 0, text, C["text_muted"])
        table.setSpan(0, 0, 1, table.columnCount())
        return it

    # ── SUMMARY ───────────────────────────────────────────────────────────
    def _set_period(self, name):
        self._period = name
        for n, b in self._period_btns.items():
            b.setChecked(n == name)
        self.load_summary_cards()

    def _money(self, start, end):
        s = self.db.fetch_one("""
            SELECT COALESCE(SUM(s.amount), 0) AS sales, COALESCE(SUM(s.quantity), 0) AS pcs,
                   COALESCE(SUM(s.quantity * COALESCE(p.production_cost, 0)), 0) AS cost,
                   COUNT(DISTINCT s.created_at) AS customers
            FROM sales s LEFT JOIN products p ON p.id = s.product_id
            WHERE COALESCE(s.is_voided, 0) = 0 AND date(s.created_at) BETWEEN ? AND ?""", (start, end))
        e = self.db.fetch_one("SELECT COALESCE(SUM(amount), 0) AS e, COUNT(*) AS n FROM operating_expenses "
                              "WHERE date(expense_date) BETWEEN ? AND ?", (start, end))
        return dict(s), e["e"], e["n"]

    def load_summary_cards(self):
        try:
            start, end = period_range(self._period)
            m, exp, n_exp = self._money(start, end)
            profit = m["sales"] - m["cost"] - exp
            self.card_sales.value.setText(f"₱{m['sales']:,.2f}")
            self.card_sales.sub.setText(f"{m['customers']:,} customers  ·  {m['pcs']:,.0f} pcs sold")
            self.card_cost.value.setText(f"₱{m['cost']:,.2f}")
            self.card_cost.sub.setText("What the sold bread and items cost you")
            self.card_exp.value.setText(f"₱{exp:,.2f}")
            self.card_exp.sub.setText(f"{n_exp} expense{'s' if n_exp != 1 else ''} recorded")
            self.card_profit.value.setText(f"₱{profit:,.2f}" if profit >= 0 else f"-₱{-profit:,.2f}")
            self.card_profit.sub.setText("You earned money" if profit > 0 else ("Break even" if profit == 0 else "Expenses are higher than earnings"))
            pc = C["card_green"] if profit >= 0 else "#B91C1C"
            self.card_profit.setStyleSheet(f"QFrame {{ background: {pc}; border-radius: 14px; }} "
                                           "QLabel { background: transparent; border: none; }")

            # compare with the same length of time just before
            d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
            span = (d1 - d0).days + 1
            p_end = d0 - timedelta(days=1)
            p_start = p_end - timedelta(days=span - 1)
            if self._period == "Today":
                # yesterday up to this same time, so the comparison is fair during the day
                prev = self.db.fetch_one("SELECT COALESCE(SUM(amount), 0) AS s FROM sales WHERE COALESCE(is_voided,0) = 0 "
                                         "AND created_at BETWEEN datetime('now','localtime','-1 day','start of day') "
                                         "AND datetime('now','localtime','-1 day')")["s"]
                label = "yesterday at this time"
            else:
                prev = self._money(p_start.isoformat(), p_end.isoformat())[0]["sales"]
                label = "last week (same days)" if self._period == "This week" else "last month (same days)"
            if prev > 0:
                diff = (m["sales"] - prev) / prev * 100
                word = "more" if diff >= 0 else "less"
                color = "#047857" if diff >= 0 else "#B91C1C"
                note = (f"Sales are <b style='color:{color}'>{abs(diff):.0f}% {word}</b> than {label} (₱{prev:,.2f}).")
            else:
                note = f"No sales {label} to compare with."
            if m["customers"]:
                note += f"  Each customer spends about <b>₱{m['sales'] / m['customers']:,.2f}</b>."
            self.money_note.setText(note)

            self._load_chart()
            self._load_categories(start, end)
            self.load_recent_activities()
        except Exception as e:
            print(f"[Financial] load_summary_cards error: {e}")

    def _load_chart(self):
        days = [date.today() - timedelta(days=i) for i in range(13, -1, -1)]
        sales = {r["d"]: r["t"] for r in self.db.fetch_all(
            "SELECT date(created_at) AS d, SUM(amount) AS t FROM sales WHERE COALESCE(is_voided,0) = 0 "
            "AND date(created_at) >= ? GROUP BY d", (days[0].isoformat(),))}
        exps = {r["d"]: r["t"] for r in self.db.fetch_all(
            "SELECT date(expense_date) AS d, SUM(amount) AS t FROM operating_expenses WHERE date(expense_date) >= ? GROUP BY d",
            (days[0].isoformat(),))}
        self.chart_view.set_data([d.strftime("%d").lstrip("0") if d != date.today() else "Today" for d in days],
                                 [("Sales (money in)", [sales.get(d.isoformat(), 0) for d in days], C["card_dark"]),
                                  ("Expenses (money out)", [exps.get(d.isoformat(), 0) for d in days], "#D9A86C")],
                                 full_labels=[d.strftime("%A, %b %d") for d in days])
        tot_s, tot_e = sum(sales.values()), sum(exps.values())
        if tot_s:
            best = max(sales.items(), key=lambda x: x[1])
            self.chart_note.setText(f"In 14 days: <b>₱{tot_s:,.0f}</b> sales and <b>₱{tot_e:,.0f}</b> expenses.  "
                                    f"Best day: <b>{date.fromisoformat(best[0]).strftime('%A, %b %d')}</b> (₱{best[1]:,.0f}).")
        else:
            self.chart_note.setText("No sales in the last 14 days yet.")

    def _load_categories(self, start, end):
        while self.cat_layout.count():
            it = self.cat_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        t, _ = title_row("Where the money went", size=13, icon="wallet",
                         info="Your expenses for this period, grouped by kind. The longest bar is where most of your money went.")
        self.cat_layout.addWidget(t)
        totals = {}
        for r in self.db.fetch_all("SELECT expense_name, category, amount FROM operating_expenses "
                                   "WHERE date(expense_date) BETWEEN ? AND ?", (start, end)):
            cat = r["category"] or guess_category(r["expense_name"])
            totals[cat] = totals.get(cat, 0) + (r["amount"] or 0)
        if not totals:
            l = QLabel("No expenses recorded for this period."); l.setStyleSheet(f"color: {C['text_muted']}; font-size: 12px;")
            self.cat_layout.addWidget(l)
            return
        biggest = max(totals.values())
        for cat, amt in sorted(totals.items(), key=lambda x: -x[1])[:5]:
            line = QHBoxLayout(); line.setSpacing(8)
            n = QLabel(cat); n.setFixedWidth(130); n.setStyleSheet(f"color: {C['text_primary']}; font-size: 12px;")
            bar = QFrame(); bar.setFixedHeight(10)
            bar.setFixedWidth(max(4, int(150 * amt / biggest)))
            bar.setStyleSheet(f"background: {C['card_amber']}; border-radius: 5px;")
            v = QLabel(f"₱{amt:,.0f}"); v.setStyleSheet(f"color: {C['text_primary']}; font-size: 12px; font-weight: bold;")
            line.addWidget(n); line.addWidget(bar); line.addStretch(); line.addWidget(v)
            w = QWidget(); w.setStyleSheet("background: transparent;"); w.setLayout(line)
            self.cat_layout.addWidget(w)

    def load_recent_activities(self):
        while self.activity_list_layout.count():
            it = self.activity_list_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        logs = self.db.fetch_all("SELECT description, action_by, created_at FROM financial_audit_log ORDER BY id DESC LIMIT 5")
        if not logs:
            l = QLabel("No recent activity."); l.setStyleSheet(f"color: {C['text_muted']}; font-size: 12px;")
            self.activity_list_layout.addWidget(l)
        for log in logs:
            l = QLabel(f"<b>{log['description']}</b><br><span style='color:{C['text_secondary']}'>"
                       f"{_nice_dt(log['created_at'])} · {log['action_by'] or '—'}</span>")
            l.setWordWrap(True); l.setStyleSheet(f"color: {C['text_primary']}; font-size: 12px; padding: 3px 0;")
            self.activity_list_layout.addWidget(l)

    # ── CASH COUNT ────────────────────────────────────────────────────────
    def open_eod_dialog(self):
        if EODCashCountDialog(self.db, current_user=self.current_user).exec():
            self.load_recon_data()

    def open_archived_eod_dialog(self):
        ArchivedEODDialog(self.db, parent=self, current_user=self.current_user).exec()
        self.load_recon_data()

    def load_recon_data(self):
        try:
            start, end = period_range(self.rc_period.currentText())
            data = self.db.fetch_all("SELECT * FROM reconciliation WHERE COALESCE(is_archived, 0) = 0 "
                                     "AND date(created_at) BETWEEN ? AND ? ORDER BY created_at DESC", (start, end))
            people = sorted({r["submitted_by"] for r in data if "submitted_by" in r.keys() and r["submitted_by"]})
            cur = self.rc_person.currentText()
            if [self.rc_person.itemText(i) for i in range(1, self.rc_person.count())] != people:
                self.rc_person.blockSignals(True)
                self.rc_person.clear(); self.rc_person.addItems(["Everyone"] + people)
                self.rc_person.setCurrentText(cur if cur in people else "Everyone")
                self.rc_person.blockSignals(False)

            def result(r):
                v = r["variance"] or 0
                return "Exact" if abs(v) < 0.01 else ("Short" if v < 0 else "Over")
            want_res, want_st, want_p = self.rc_result.currentText(), self.rc_status.currentText(), self.rc_person.currentText()
            data = [r for r in data
                    if (want_res == "All results" or result(r) == want_res)
                    and (want_st == "Any status" or STATUS_WORDS.get(r["status"] or "Pending", r["status"]) == want_st)
                    and (want_p == "Everyone" or ("submitted_by" in r.keys() and r["submitted_by"] == want_p))]
            self.recon_table.clearSpans()
            short = [r for r in data if (r["variance"] or 0) < -0.009]
            over = [r for r in data if (r["variance"] or 0) > 0.009]
            exact = len(data) - len(short) - len(over)
            waiting = sum(1 for r in data if (r["status"] or "Pending") in ("Submitted", "Pending"))
            if data:
                txt = (f"{len(data)} count{'s' if len(data) != 1 else ''}:  <b style='color:#047857'>{exact} exact</b>  ·  "
                       f"<b style='color:#B91C1C'>{len(short)} short</b> (₱{-sum(r['variance'] for r in short):,.2f} total)  ·  "
                       f"<b style='color:#B45309'>{len(over)} over</b> (₱{sum(r['variance'] for r in over):,.2f})")
                if waiting:
                    txt += f"  ·  {waiting} waiting for a manager to check"
                self.recon_summary.setText(txt)
            else:
                self.recon_summary.setText("No cash counts for this choice. Click 'Count Cash Now' at closing time.")
            if not data:
                self._empty(self.recon_table, "No cash counts yet.")
                return
            self.recon_table.setRowCount(len(data))
            keys = data[0].keys()
            for row, item in enumerate(data):
                sys_val, act_val, var = item["system_sales"] or 0.0, item["actual_cash"] or 0.0, item["variance"] or 0.0
                self._cell(self.recon_table, row, 0, _nice_dt(item["created_at"]))
                self._cell(self.recon_table, row, 1, f"₱{sys_val:,.2f}", C["text_secondary"])
                self._cell(self.recon_table, row, 2, f"₱{act_val:,.2f}", bold=True)
                if abs(var) < 0.01:
                    self._cell(self.recon_table, row, 3, "Exact", C["green"], True)
                elif var < 0:
                    self._cell(self.recon_table, row, 3, f"Short ₱{-var:,.2f}", C["red"], True)
                else:
                    self._cell(self.recon_table, row, 3, f"Over ₱{var:,.2f}", C["amber"], True)
                status = item["status"] or "Pending"
                self._cell(self.recon_table, row, 4, STATUS_WORDS.get(status, status),
                           {"Submitted": C["amber"], "Verified": C["blue"], "Closed": C["green"]}.get(status, C["text_muted"]), True)
                who = [item[k] for k in ("submitted_by", "verified_by") if k in keys and item[k]]
                self._cell(self.recon_table, row, 5, " / ".join(dict.fromkeys(who)) or "—")
                b = QPushButton("Check" if status == "Submitted" else ("Mark done" if status == "Verified" else "More"))
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setStyleSheet(f"QPushButton {{ background: white; color: {C['card_dark']}; border: 1px solid {C['border2']}; "
                                f"border-radius: 7px; font-size: 12px; font-weight: bold; padding: 4px 10px; }}"
                                f"QPushButton:hover {{ background: {C['surface2']}; }}")
                b.clicked.connect(lambda _, r=item["id"], s=status, btn=b: self._show_recon_menu(btn, r, s))
                w = QWidget(); w.setStyleSheet("background: transparent;")
                h = QHBoxLayout(w); h.setContentsMargins(6, 4, 6, 4); h.addWidget(b)
                self.recon_table.setCellWidget(row, 6, w)
                self.recon_table.setRowHeight(row, 46)
        except Exception as e:
            print(f"[Financial] load_recon_data error: {e}")

    def _show_recon_menu(self, btn, recon_id, status):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_STYLE)
        if status == "Submitted":
            menu.addAction("Mark as checked").triggered.connect(lambda: self.update_recon_status(recon_id, "Verified"))
        elif status == "Verified":
            menu.addAction("Mark as done").triggered.connect(lambda: self.update_recon_status(recon_id, "Closed"))
        menu.addAction("Show bills counted").triggered.connect(lambda: self._show_denoms(recon_id))
        menu.addSeparator()
        menu.addAction("Archive").triggered.connect(lambda: self.archive_recon(recon_id))
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _show_denoms(self, recon_id):
        r = self.db.fetch_one("SELECT denominations, actual_cash, created_at FROM reconciliation WHERE id = ?", (recon_id,))
        try:
            d = json.loads(r["denominations"] or "{}")
        except (ValueError, TypeError):
            d = {}
        details = {f"₱{float(k):,.0f}" if float(k) >= 1 else f"{float(k) * 100:.0f}¢": f"x {v}"
                   for k, v in sorted(d.items(), key=lambda x: -float(x[0]))} if d else {"Bills": "not recorded"}
        details["Total"] = f"₱{(r['actual_cash'] or 0):,.2f}"
        BakeSyncAlert.show_info(self, "Bills and coins counted", _nice_dt(r["created_at"]), details=details)

    def update_recon_status(self, recon_id, new_status):
        word = "checked" if new_status == "Verified" else "done"
        if not BakeSyncAlert.ask_yes_no(self, "Confirm", f"Mark this cash count as {word}?",
                                        yes_text=f"YES, {word.upper()}", no_text="CANCEL"):
            return
        try:
            self.db.execute_query("UPDATE reconciliation SET status = ?, actioned_by = ?, verified_by = ? WHERE id = ?",
                                  (new_status, self.current_user, self.current_user, recon_id))
            log_activity(self.db, self.current_user, f"cash count {word}", "money", f"Cash count #{recon_id}")
            self.load_recon_data()
        except Exception as e:
            BakeSyncAlert.show_error(self, "Update Error", "Could not update the cash count.", details={"Error": str(e)})

    def archive_recon(self, recon_id):
        if not BakeSyncAlert.ask_yes_no(self, "Archive this cash count?",
                                        "It will be moved to 'Archived counts'. You can bring it back later.",
                                        yes_text="ARCHIVE", no_text="CANCEL"):
            return
        try:
            self.db.execute_query("UPDATE reconciliation SET is_archived = 1, archived_by = ? WHERE id = ?",
                                  (self.current_user, recon_id))
            log_activity(self.db, self.current_user, "cash count archived", "money", f"Cash count #{recon_id}")
            self.load_recon_data()
        except Exception as e:
            BakeSyncAlert.show_error(self, "Archive Error", "Could not archive the cash count.", details={"Error": str(e)})

    # ── EXPENSES ──────────────────────────────────────────────────────────
    def log_opex(self):
        if OpExDialog(self.db, current_user=self.current_user).exec():
            self.load_expenses()

    def load_expenses(self):
        try:
            start, end = period_range(self.exp_period.currentText())
            cat_f = self.exp_cat.currentText()
            q = self.exp_search.text().strip().lower()
            rows = self.db.fetch_all("SELECT expense_name, category, amount, expense_date, logged_by FROM operating_expenses "
                                     "WHERE date(expense_date) BETWEEN ? AND ? ORDER BY expense_date DESC, id DESC", (start, end))
            shown = []
            for r in rows:
                cat = r["category"] or guess_category(r["expense_name"])
                if cat_f != "All categories" and cat != cat_f:
                    continue
                if q and q not in (r["expense_name"] or "").lower():
                    continue
                shown.append((r, cat))
            self.exp_table.clearSpans()
            total = sum(r["amount"] or 0 for r, _ in shown)
            if shown:
                big_r, big_c = max(shown, key=lambda x: x[0]["amount"] or 0)
                self.exp_summary.setText(f"Total: <b>₱{total:,.2f}</b>  ·  {len(shown)} expense{'s' if len(shown) != 1 else ''}  ·  "
                                         f"Biggest: {big_r['expense_name']} (₱{big_r['amount']:,.2f})")
            else:
                self.exp_summary.setText("No expenses for this choice.")
                self._empty(self.exp_table, "No expenses found.")
                return
            self.exp_table.setRowCount(len(shown))
            for row, (r, cat) in enumerate(shown):
                self._cell(self.exp_table, row, 0, _nice_dt(r["expense_date"]))
                self._cell(self.exp_table, row, 1, r["expense_name"] or "—", bold=True)
                self._cell(self.exp_table, row, 2, cat, C["text_secondary"])
                self._cell(self.exp_table, row, 3, f"₱{(r['amount'] or 0):,.2f}", C["red"], True)
                self._cell(self.exp_table, row, 4, r["logged_by"] or "—")
                self.exp_table.setRowHeight(row, 42)
        except Exception as e:
            print(f"[Financial] load_expenses error: {e}")

    # ── VOIDS ─────────────────────────────────────────────────────────────
    def load_void_data(self):
        try:
            cashiers = [r["voided_by"] for r in self.db.fetch_all(
                "SELECT DISTINCT voided_by FROM void_logs WHERE voided_by IS NOT NULL ORDER BY voided_by")]
            current = self.void_cashier.currentText()
            if [self.void_cashier.itemText(i) for i in range(1, self.void_cashier.count())] != cashiers:
                self.void_cashier.blockSignals(True)
                self.void_cashier.clear(); self.void_cashier.addItems(["All cashiers"] + cashiers)
                self.void_cashier.setCurrentText(current if current in cashiers else "All cashiers")
                self.void_cashier.blockSignals(False)

            start, end = period_range(self.void_period.currentText())
            sql = ("SELECT v.created_at, p.name, v.quantity, v.amount, v.reason, v.voided_by FROM void_logs v "
                   "LEFT JOIN products p ON p.id = v.product_id WHERE date(v.created_at) BETWEEN ? AND ?")
            params = [start, end]
            if self.void_cashier.currentText() != "All cashiers":
                sql += " AND v.voided_by = ?"; params.append(self.void_cashier.currentText())
            reason_f = self.void_reason.currentText()
            if reason_f == "Not given":
                sql += f" AND COALESCE(v.reason, '') NOT IN ({','.join('?' * len(VOID_REASONS))})"; params += VOID_REASONS
            elif reason_f != "All reasons":
                sql += " AND v.reason = ?"; params.append(reason_f)
            data = self.db.fetch_all(sql + " ORDER BY v.created_at DESC LIMIT 300", params)

            self.void_table.clearSpans()
            if not data:
                self.void_summary.setText("No voids for this choice.")
                self._empty(self.void_table, "No voids found.")
                return
            counts = {}
            for d in data:
                key = d["reason"] if d["reason"] in VOID_REASONS else "Not given"
                counts[key] = counts.get(key, 0) + 1
            top = max(counts.items(), key=lambda x: x[1])
            self.void_summary.setText(
                f"<b>{len(data)}</b> void{'s' if len(data) != 1 else ''}  ·  <b style='color:#B91C1C'>₱{sum(d['amount'] or 0 for d in data):,.2f}</b> "
                f"returned  ·  {sum(d['quantity'] or 0 for d in data):g} pcs  ·  Most common reason: <b>{top[0]}</b> ({top[1]})")
            self.void_table.setRowCount(len(data))
            for row, d in enumerate(data):
                self._cell(self.void_table, row, 0, _nice_dt(d["created_at"]))
                self._cell(self.void_table, row, 1, d["name"] or "(deleted product)", bold=True)
                self._cell(self.void_table, row, 2, f"{d['quantity']:g}")
                self._cell(self.void_table, row, 3, f"-₱{(d['amount'] or 0):,.2f}", C["red"], True)
                reason = d["reason"] if d["reason"] in VOID_REASONS else "Not given"
                self._cell(self.void_table, row, 4, reason, C["text_muted"] if reason == "Not given" else None)
                self._cell(self.void_table, row, 5, d["voided_by"] or "—")
                self.void_table.setRowHeight(row, 42)
        except Exception as e:
            print(f"[Financial] load_void_data error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  DIALOG CLASSES
# ─────────────────────────────────────────────────────────────────────────────
_DIALOG_STYLE = f"""
    QDialog {{ background-color: {C['surface']}; font-family: {FONT_DISPLAY}; }}
    QLabel {{ color: {C['text_primary']}; }}
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background-color: {C['surface2']}; border: 1px solid {C['border']};
        border-radius: 6px; padding: 8px 12px; font-size: 13px; color: {C['text_primary']};
    }}
"""

# ─────────────────────────────────────────────────────────────────────────────
#  ARCHIVED EOD DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class ArchivedEODDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None, current_user: str = ""):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(1020, 560)
        self._drag_pos = None
        self._init_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _create_vector_icon(self, svg_string, color):
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QByteArray
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode('utf-8')), "SVG")
        return QIcon(pixmap)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        # ── MAIN CARD ──
        card = QFrame()
        card.setObjectName("ArchiveCard")
        card.setStyleSheet(f"""
            QFrame#ArchiveCard {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: {C['text_primary']}; }}
        """)
        _shadow(card, blur=20, offset_y=4, color="#00000015")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(16)

        # ── HEADER ──
        header = QHBoxLayout()
        title = QLabel("Archived EOD Records")
        title.setFont(QFont(FONT_DISPLAY, 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C['text_primary']};")

        close_btn = QPushButton(""); close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ border: none; font-size: 16px; color: {C['text_muted']}; background: transparent; }}
            QPushButton:hover {{ color: {C['red']}; }}
        """)
        close_btn.clicked.connect(self.accept)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        card_layout.addLayout(header)

        card_layout.addWidget(_separator())

        # ── TABLE ──
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Date", "System", "Actual", "Variance", "Final Status", "Submitted By", "Archived By", "⋮"]
        )
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(_TABLE_STYLE + f"QTableWidget {{ alternate-background-color: {C['surface2']}; }}" + _SCROLLBAR_STYLE)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 70)

        card_layout.addWidget(self.table)

        outer.addWidget(card)
        self._load_data()

    def _load_data(self):
        data = self.db.fetch_all("SELECT * FROM reconciliation WHERE COALESCE(is_archived, 0) = 1 ORDER BY created_at DESC")
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            keys = item.keys()

            date_item = QTableWidgetItem(str(item['created_at'])[:10])
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, date_item)

            sys_val = item['system_sales'] if item['system_sales'] else 0.0
            act_val = item['actual_cash'] if item['actual_cash'] else 0.0

            sys_widget = QWidget()
            sys_widget.setStyleSheet("background: transparent;")
            sys_layout = QHBoxLayout(sys_widget)
            sys_layout.setContentsMargins(12, 0, 12, 0)
            sys_lbl = QLabel(f"₱{sys_val:,.2f}")
            sys_lbl.setStyleSheet(f"color: {C['text_secondary']};")
            sys_lbl.setFont(QFont(FONT_DISPLAY, 12))
            sys_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sys_layout.addWidget(sys_lbl, 1)
            sys_layout.addWidget(VectorIcon("arrow_right_flat"))
            self.table.setCellWidget(row, 1, sys_widget)

            act_item = QTableWidgetItem(f"₱{act_val:,.2f}")
            act_item.setFont(QFont(FONT_DISPLAY, 12, QFont.Weight.Bold))
            act_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, act_item)

            variance = item['variance'] if item['variance'] else 0.0
            var_item = QTableWidgetItem(f"₱{variance:,.2f}")
            var_item.setFont(QFont(FONT_DISPLAY, 12, QFont.Weight.Bold))
            var_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            var_item.setForeground(QColor(C["red"] if variance < 0 else C["amber"] if variance > 0 else C["green"]))
            self.table.setItem(row, 3, var_item)

            status = item['status'] if item['status'] else "—"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setFont(QFont(FONT_DISPLAY, 11, QFont.Weight.Bold))
            if status == "Submitted": status_color = C["amber"]
            elif status == "Verified": status_color = C["blue"]
            elif status == "Closed": status_color = C["green"]
            else: status_color = C["text_muted"]
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 4, status_item)

            submitted_by = item['submitted_by'] if 'submitted_by' in keys and item['submitted_by'] else "—"
            sub_item = QTableWidgetItem(submitted_by)
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, sub_item)

            archived_by = item['archived_by'] if 'archived_by' in keys and item['archived_by'] else "—"
            arc_item = QTableWidgetItem(archived_by)
            arc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, arc_item)

            # ── MENU BUTTON ──
            MENU_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>"""
            menu_btn = QPushButton()
            menu_btn.setIcon(self._create_vector_icon(MENU_SVG, "#FFFFFF"))
            menu_btn.setIconSize(QSize(16, 16))
            menu_btn.setFixedSize(30, 30)
            menu_btn.setToolTip("More Actions")
            menu_btn.setStyleSheet("""
                QPushButton { border: none; background-color: #693903; border-radius: 6px; }
                QPushButton:hover { background-color: #452803; }
            """)
            menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            menu_btn.clicked.connect(lambda _, r=item['id'], b=menu_btn: self._show_archive_menu(b, r))
            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wl = QHBoxLayout(wrapper)
            wl.setContentsMargins(4, 2, 4, 2)
            wl.addWidget(menu_btn)
            self.table.setCellWidget(row, 7, wrapper)

            self.table.setRowHeight(row, 46)

    def _show_archive_menu(self, btn: QPushButton, recon_id: int):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_STYLE)
        act = menu.addAction("Restore to Active")
        act.triggered.connect(lambda: self._restore_record(recon_id))
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _restore_record(self, recon_id: int):
        confirm = BakeSyncAlert.ask_yes_no(
            self,
            title="Restore EOD Record",
            message="Are you sure you want to restore this record back to the active reconciliation table?",
            yes_text="RESTORE",
            no_text="CANCEL"
        )
        if not confirm:
            return
        try:
            self.db.execute_query(
                "UPDATE reconciliation SET is_archived = 0, archived_by = NULL WHERE id = ?",
                (recon_id,)
            )
            self._load_data()
            BakeSyncAlert.show_success(
                self,
                title="Restored Successfully",
                message="The EOD record has been restored to the active table.",
                details={"Record ID": f"#{recon_id}"}
            )
        except Exception as e:
            BakeSyncAlert.show_error(self, "Restore Error", "Failed to restore the record.", details={"Error": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
#  EOD CASH COUNT DIALOG (Compact, No Emojis, No Payouts)
# ─────────────────────────────────────────────────────────────────────────────
class EODCashCountDialog(QDialog):
    def __init__(self, db: DatabaseManager, current_user: str = "Admin"):
        super().__init__()
        self.db = db
        self.current_user = current_user
        
        # Frameless Window Setup (Pinaliit na Width)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(600)
        
        self._drag_pos = None
        self._init_ui()
        self._load_initial_sales()
        self._recalc() # Initial compute

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _create_svg_icon(self, svg_string, color):
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QByteArray
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode('utf-8')), "SVG")
        return QIcon(pixmap)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── MAIN CARD ──
        card = QFrame()
        card.setObjectName("MainCard")
        card.setStyleSheet(f"""
            QFrame#MainCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }}
            QLabel {{ border: none; background: transparent; color: #0F172A; }}
        """)
        _shadow(card, blur=20, offset_y=4, color="#00000015")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # ── HEADER ──
        header_layout = QHBoxLayout()
        title_icon = QLabel()
        calc_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16.01" y2="14"></line><line x1="12" y1="14" x2="12.01" y2="14"></line><line x1="8" y1="14" x2="8.01" y2="14"></line><line x1="16" y1="18" x2="16.01" y2="18"></line><line x1="12" y1="18" x2="12.01" y2="18"></line><line x1="8" y1="18" x2="8.01" y2="18"></line><line x1="16" y1="10" x2="16.01" y2="10"></line><line x1="12" y1="10" x2="12.01" y2="10"></line><line x1="8" y1="10" x2="8.01" y2="10"></line></svg>"""
        title_icon.setPixmap(self._create_svg_icon(calc_svg, "#1E293B").pixmap(20, 20))
        
        title_text = QVBoxLayout()
        title_text.setSpacing(2)
        lbl_title = QLabel("Count the Cash")
        lbl_title.setFont(QFont(FONT_DISPLAY, 14, QFont.Weight.Bold))
        lbl_sub = QLabel("Type how many of each bill and coin is in the drawer.")
        lbl_sub.setStyleSheet("color: #64748B; font-size: 11px;")
        title_text.addWidget(lbl_title)
        title_text.addWidget(lbl_sub)
        
        close_btn = QPushButton(""); close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { border: none; font-size: 16px; color: #9CA3AF; } QPushButton:hover { color: #DC2626; }")
        close_btn.clicked.connect(self.reject)

        header_layout.addWidget(title_icon, alignment=Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(title_text)
        header_layout.addStretch()
        header_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(header_layout)

        # ── SECTION 1: SYSTEM EXPECTED ──
        sys_frame = QFrame()
        sys_frame.setStyleSheet("""
            QFrame { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }
            QLabel { border: none; background: transparent; }
            QLineEdit, QDoubleSpinBox {
                background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;
                padding: 8px 12px; font-size: 14px; font-weight: bold; color: #0F172A;
            }
            QDoubleSpinBox:focus { border: 1px solid #B45309; }
        """)
        sys_layout = QHBoxLayout(sys_frame)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(20)

        # Vector SVGs para sa Fields
        cal_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>"""
        money_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"></rect><circle cx="12" cy="12" r="2"></circle><path d="M6 12h.01M18 12h.01"></path></svg>"""

        # Date Field
        date_col = QVBoxLayout()
        date_col.setSpacing(6)
        
        date_header = QHBoxLayout()
        date_icon = QLabel()
        date_icon.setPixmap(self._create_svg_icon(cal_svg, "#64748B").pixmap(16, 16))
        date_lbl = QLabel("Date")
        date_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #475569;")
        date_header.addWidget(date_icon)
        date_header.addWidget(date_lbl)
        date_header.addStretch()
        
        self.date_input = QLineEdit(QDate.currentDate().toString("MM/dd/yyyy"))
        self.date_input.setReadOnly(True)
        self.date_input.setStyleSheet("color: #64748B; background-color: #F1F5F9; border: 1px solid #E2E8F0;")
        
        date_sub = QLabel("Today")
        date_sub.setStyleSheet("color: #94A3B8; font-size: 11px;")

        date_col.addLayout(date_header)
        date_col.addWidget(self.date_input)
        date_col.addWidget(date_sub)
        sys_layout.addLayout(date_col, 1)

        # POS Sales Field
        pos_col = QVBoxLayout()
        pos_col.setSpacing(6)
        
        pos_header = QHBoxLayout()
        pos_icon = QLabel()
        pos_icon.setPixmap(self._create_svg_icon(money_svg, "#16A34A").pixmap(16, 16))
        pos_lbl = QLabel("POS sales today")
        pos_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #0F172A;")
        pos_header.addWidget(pos_icon)
        pos_header.addWidget(pos_lbl)
        pos_header.addStretch()
        
        self.pos_input = QDoubleSpinBox()
        self.pos_input.setRange(0, 9999999.99); self.pos_input.setDecimals(2)
        self.pos_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.pos_input.setStyleSheet("border: 2px solid #16A34A; color: #16A34A;")
        self.pos_input.valueChanged.connect(self._recalc)
        
        pos_sub = QLabel("The cash that should be in the drawer.")
        pos_sub.setStyleSheet("color: #94A3B8; font-size: 11px;")
        
        pos_col.addLayout(pos_header)
        pos_col.addWidget(self.pos_input)
        pos_col.addWidget(pos_sub)
        sys_layout.addLayout(pos_col, 1)

        card_layout.addWidget(sys_frame)
        card_layout.addWidget(_separator())

        # ── SECTION 2: PHYSICAL CASH COUNT ──
        count_title_layout = QHBoxLayout()
        coin_icon = QLabel()
        coin_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"></path><line x1="12" y1="18" x2="12" y2="22"></line><line x1="12" y1="2" x2="12" y2="6"></line></svg>"""
        coin_icon.setPixmap(self._create_svg_icon(coin_svg, "#1E293B").pixmap(18, 18))
        
        count_lbl = QLabel("Bills and coins in the drawer"); count_lbl.setFont(QFont(FONT_DISPLAY, 12, QFont.Weight.Bold))
        count_title_layout.addWidget(coin_icon); count_title_layout.addWidget(count_lbl); count_title_layout.addStretch()
        card_layout.addLayout(count_title_layout)

        # Denominations Grid
        grid = QGridLayout()
        grid.setSpacing(8)
        self.denoms = {}
        denom_values = [1000, 500, 200, 100, 50, 20, 10, 5, 1]
        
        for i, val in enumerate(denom_values):
            box = QFrame()
            box.setStyleSheet("QFrame { border: 1px solid #E2E8F0; border-radius: 6px; background: #FFFFFF; }")
            bl = QVBoxLayout(box); bl.setContentsMargins(6, 6, 6, 6); bl.setSpacing(4)
            
            lbl = QLabel(f"₱{val:,}"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #B45309; font-weight: bold; font-size: 12px; border: none;")
            
            spin = QSpinBox(); spin.setRange(0, 9999); spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setStyleSheet("""
                QSpinBox { border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px; font-size: 13px; font-weight: bold; background: #F8FAFC; color: #0F172A; }
                QSpinBox:focus { border: 1px solid #B45309; background: #FFFFFF; }
            """)
            spin.valueChanged.connect(self._recalc)
            self.denoms[val] = spin
            
            bl.addWidget(lbl); bl.addWidget(spin)
            grid.addWidget(box, i // 5, i % 5)

        card_layout.addLayout(grid)

        # ── SECTION 3: SUMMARY & VARIANCE ──
        self.summary_box = QFrame()
        self.summary_layout = QVBoxLayout(self.summary_box)
        self.summary_layout.setContentsMargins(15, 15, 15, 15)
        
        # Totals Row
        totals_row = QHBoxLayout()
        
        sys_tot_col = QVBoxLayout()
        stl = QLabel("SHOULD BE"); stl.setStyleSheet("color: #475569; font-size: 10px; font-weight: bold;")
        self.lbl_sys_total = QLabel("₱0.00"); self.lbl_sys_total.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A;")
        sys_tot_col.addWidget(stl, alignment=Qt.AlignmentFlag.AlignCenter); sys_tot_col.addWidget(self.lbl_sys_total, alignment=Qt.AlignmentFlag.AlignCenter)
        
        act_tot_col = QVBoxLayout()
        atl = QLabel("COUNTED"); atl.setStyleSheet("color: #475569; font-size: 10px; font-weight: bold;")
        self.lbl_act_total = QLabel("₱0.00"); self.lbl_act_total.setStyleSheet("font-size: 18px; font-weight: 900; color: #0F172A;")
        act_tot_col.addWidget(atl, alignment=Qt.AlignmentFlag.AlignCenter); act_tot_col.addWidget(self.lbl_act_total, alignment=Qt.AlignmentFlag.AlignCenter)
        
        totals_row.addLayout(sys_tot_col); totals_row.addStretch(); totals_row.addLayout(act_tot_col)
        self.summary_layout.addLayout(totals_row)
        
        # Dashed Line
        dash = QFrame(); dash.setFixedHeight(1); dash.setStyleSheet("border-top: 1px dashed #A7F3D0; background: transparent;")
        self.summary_layout.addWidget(dash)
        
        # Variance Result
        var_col = QVBoxLayout(); var_col.setSpacing(2)
        self.lbl_variance = QLabel("Difference: ₱0.00 (Exact)")
        self.lbl_variance.setStyleSheet("font-size: 18px; font-weight: 900;")
        self.lbl_feedback = QLabel("Perfect! Physical count matches.")
        self.lbl_feedback.setStyleSheet("font-size: 11px;")
        var_col.addWidget(self.lbl_variance, alignment=Qt.AlignmentFlag.AlignCenter)
        var_col.addWidget(self.lbl_feedback, alignment=Qt.AlignmentFlag.AlignCenter)
        self.summary_layout.addLayout(var_col)

        card_layout.addWidget(self.summary_box)

        # ── FOOTER BUTTONS ──
        footer = QHBoxLayout()
        
        self.btn_submit = QPushButton(" Submit Final EOD")
        chk_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>"""
        self.btn_submit.setIcon(self._create_svg_icon(chk_svg, "#FFFFFF"))
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.setStyleSheet("""
            QPushButton { background-color: #8B4513; color: white; border-radius: 6px; padding: 10px 18px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #6B3E11; }
        """)
        self.btn_submit.clicked.connect(self._submit)

        btn_reset = QPushButton(" Reset")
        rst_svg = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><polyline points="23 20 23 14 17 14"></polyline><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path></svg>"""
        btn_reset.setIcon(self._create_svg_icon(rst_svg, "#0F172A"))
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton { background-color: #E2E8F0; color: #0F172A; border-radius: 6px; padding: 10px 18px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        btn_reset.clicked.connect(self._reset)

        footer.addWidget(self.btn_submit)
        footer.addWidget(btn_reset)
        footer.addStretch()
        card_layout.addLayout(footer)

        layout.addWidget(card)

    def _load_initial_sales(self):
        try:
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            res = self.db.fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS t FROM sales 
                WHERE (date(created_at) = ? OR date(created_at) = ?) 
                AND (is_voided IS NULL OR is_voided = 0)
            """, (today_str, today_str))
            sales = res['t'] if res else 0.0
            self.pos_input.setValue(sales)
        except Exception as e:
            print(f"Error loading sales: {e}")

    def _recalc(self):
        # Computations (Wala nang Payouts)
        sys_expected = self.pos_input.value()
        actual_cash = sum(val * spin.value() for val, spin in self.denoms.items())
        variance = actual_cash - sys_expected

        # Update Labels
        self.lbl_sys_total.setText(f"₱{sys_expected:,.2f}")
        self.lbl_act_total.setText(f"₱{actual_cash:,.2f}")

        # Dynamic Styling
        if abs(variance) < 0.01: # Balanced
            self.summary_box.setStyleSheet("QFrame { background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; } QLabel { border: none; background: transparent; }")
            self.lbl_variance.setStyleSheet("font-size: 18px; font-weight: 900; color: #D97706;")
            self.lbl_variance.setText("Exact — the cash matches")
            self.lbl_feedback.setStyleSheet("font-size: 11px; color: #D97706;")
            self.lbl_feedback.setText("The drawer has exactly the right amount.")
        elif variance > 0: # Over
            self.summary_box.setStyleSheet("QFrame { background-color: #FFF7ED; border: 1px solid #FDE68A; border-radius: 8px; } QLabel { border: none; background: transparent; }")
            self.lbl_variance.setStyleSheet("font-size: 18px; font-weight: 900; color: #D97706;")
            self.lbl_variance.setText(f"Over by ₱{variance:,.2f}")
            self.lbl_feedback.setStyleSheet("font-size: 11px; color: #B45309;")
            self.lbl_feedback.setText("There is more cash than the POS sales. Count again to be sure.")
        else: # Short
            self.summary_box.setStyleSheet("QFrame { background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; } QLabel { border: none; background: transparent; }")
            self.lbl_variance.setStyleSheet("font-size: 18px; font-weight: 900; color: #DC2626;")
            self.lbl_variance.setText(f"Short by ₱{abs(variance):,.2f}")
            self.lbl_feedback.setStyleSheet("font-size: 11px; color: #B91C1C;")
            self.lbl_feedback.setText("There is less cash than the POS sales. Count again to be sure.")

    def _reset(self):
        for spin in self.denoms.values():
            spin.setValue(0)
        self._load_initial_sales()
        self._recalc()

    def _submit(self):
        sys_expected = self.pos_input.value()
        actual_cash = sum(val * spin.value() for val, spin in self.denoms.items())
        variance = actual_cash - sys_expected

        if sys_expected == 0.0 and actual_cash == 0.0:
            confirm = BakeSyncAlert.ask_yes_no(
                self, "Zero Count", 
                "Both expected and actual cash are 0.00.\nAre you sure you want to submit an empty EOD?",
                yes_text="SUBMIT", no_text="CANCEL"
            )
            if not confirm: return

        confirm_sub = BakeSyncAlert.ask_yes_no(
            self, "Confirm EOD Record",
            f"Save this cash count?\n\nPOS sales: ₱{sys_expected:,.2f}\nCash counted: ₱{actual_cash:,.2f}",
            yes_text="SAVE", no_text="CANCEL"
        )
        
        if not confirm_sub: return

        deno_data = {str(k): s.value() for k, s in self.denoms.items() if s.value() > 0}
        
        try:
            self.db.execute_query(
                "INSERT INTO reconciliation (system_sales, actual_cash, variance, status, denominations, submitted_by) VALUES (?, ?, ?, 'Submitted', ?, ?)",
                (sys_expected, actual_cash, variance, json.dumps(deno_data), self.current_user)
            )
            
            # 🟢 ITO ANG NAG-AADD SA RECENT ACTIVITY:
            self.db.execute_query(
                "INSERT INTO financial_audit_log (icon, description, action_by) VALUES (?, ?, ?)",
                ("cash", f"Cash counted: ₱{actual_cash:,.2f} (POS ₱{sys_expected:,.2f})", self.current_user)
            )
            if variance < -0.009:
                log_activity(self.db, self.current_user, "cash short", "money",
                             f"Counted ₱{actual_cash:,.2f}, POS says ₱{sys_expected:,.2f} - short ₱{-variance:,.2f}")
            else:
                log_activity(self.db, self.current_user, "cash counted", "money",
                             f"Counted ₱{actual_cash:,.2f}, POS says ₱{sys_expected:,.2f}"
                             + (f" - over ₱{variance:,.2f}" if variance > 0.009 else " - exact"))
            
            self.accept()
            
            BakeSyncAlert.show_success(
                self.parent(),
                "EOD Submitted",
                "Your End of Day cash count has been recorded successfully.\nIt is now pending for Manager verification.",
                details={
                    "Expected": f"₱{sys_expected:,.2f}",
                    "Actual": f"₱{actual_cash:,.2f}",
                    "Variance": f"₱{variance:,.2f}"
                }
            )
        except Exception as e:
            BakeSyncAlert.show_error(self, "Submission Failed", "There was an error saving the EOD record.", details={"Error": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
#  OPEX DIALOG (Minimalist & Custom Alerts)
# ─────────────────────────────────────────────────────────────────────────────
class OpExDialog(QDialog):
    """Add an expense: pick a category (one click), say what it was, type the amount."""

    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db = db
        self.current_user = current_user or "Unknown"
        self.category = ""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(470)
        self._drag_pos = None
        self._init_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10)
        card = QFrame(); card.setObjectName("OpExCard")
        card.setStyleSheet(f"""
            QFrame#OpExCard {{ background-color: {C['surface']}; border-radius: 14px; }}
            QLabel {{ color: {C['text_primary']}; border: none; background: transparent; }}
            QLineEdit, QDoubleSpinBox {{ background-color: white; border: 1px solid {C['border2']}; border-radius: 8px;
                                         padding: 8px 12px; font-size: 14px; color: {C['text_primary']}; }}
            QLineEdit:focus, QDoubleSpinBox:focus {{ border: 1.5px solid {C['card_dark']}; }}
        """)
        _shadow(card, blur=24, color="#00000025")
        cl = QVBoxLayout(card); cl.setContentsMargins(26, 22, 26, 22); cl.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Add Expense"); title.setFont(QFont(FONT_DISPLAY, 16, QFont.Weight.Bold))
        close_btn = QPushButton(""); close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16)); close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { border: none; font-size: 16px; color: #9CA3AF; } QPushButton:hover { color: #DC2626; }")
        close_btn.clicked.connect(self.reject)
        header.addWidget(title); header.addStretch(); header.addWidget(close_btn)
        cl.addLayout(header)

        cl.addWidget(QLabel("<b>1.</b> What kind of expense?"))
        grid = QGridLayout(); grid.setSpacing(6)
        self._cat_btns = []
        for i, cat in enumerate(EXPENSE_CATEGORIES):
            b = QPushButton(cat.replace("&", "&&")); b.setCheckable(True); b.setFixedHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton {{ background: white; color: {C['text_primary']}; border: 1px solid {C['border2']}; "
                            f"border-radius: 8px; font-size: 12px; }} QPushButton:hover {{ border-color: {C['card_dark']}; }}"
                            f"QPushButton:checked {{ background: {C['card_dark']}; color: white; border-color: {C['card_dark']}; font-weight: bold; }}")
            b.clicked.connect(lambda _, c=cat, btn=b: self._pick(c, btn))
            grid.addWidget(b, i // 4, i % 4)
            self._cat_btns.append(b)
        cl.addLayout(grid)

        cl.addWidget(QLabel("<b>2.</b> What was it for?"))
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("e.g. October rent, Meralco bill, flour 25kg")
        self.name_input.setFixedHeight(40)
        cl.addWidget(self.name_input)

        cl.addWidget(QLabel("<b>3.</b> How much?"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 9999999.99); self.amount_input.setDecimals(2); self.amount_input.setPrefix("₱ ")
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.amount_input.setFixedHeight(48)
        self.amount_input.setFont(QFont(FONT_DISPLAY, 16, QFont.Weight.Bold))
        cl.addWidget(self.amount_input)

        self.err = QLabel(""); self.err.setStyleSheet("color: #B91C1C; font-size: 12px;"); self.err.hide()
        cl.addWidget(self.err)

        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = _btn("Cancel", "white", C["text_secondary"], border=True, h=44, font_size=14)
        cancel.clicked.connect(self.reject)
        self.save_btn = _btn("Save Expense", C["card_dark"], h=44, font_size=14)
        self.save_btn.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(self.save_btn, stretch=2)
        cl.addLayout(btns)
        layout.addWidget(card)

    def _pick(self, cat, btn):
        self.category = cat
        for b in self._cat_btns:
            b.setChecked(b is btn)
        if not self.name_input.text().strip():
            self.name_input.setPlaceholderText(f"e.g. {cat}")
        self.name_input.setFocus()

    def _save(self):
        name = self.name_input.text().strip() or self.category
        amount = self.amount_input.value()
        problem = ("Please choose what kind of expense it is." if not self.category else
                   "Please type the amount." if amount <= 0 else None)
        if problem:
            self.err.setText(problem); self.err.show()
            return
        try:
            self.db.execute_query(
                "INSERT INTO operating_expenses (expense_name, amount, logged_by, category) VALUES (?, ?, ?, ?)",
                (name, amount, self.current_user, self.category))
            self.db.execute_query(
                "INSERT INTO financial_audit_log (icon, description, action_by) VALUES (?, ?, ?)",
                ("receipt", f"Expense: {name} (₱{amount:,.2f})", self.current_user))
            log_activity(self.db, self.current_user, "expense added", "money", f"{self.category}: {name} - ₱{amount:,.2f}")
            self.accept()
        except Exception as e:
            BakeSyncAlert.show_error(self, "Save Error", "Could not save the expense.", details={"Error": str(e)})


if __name__ == "__main__":
    import sys; from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    try:
        main_window = FinancialWidget(db=DatabaseManager(), current_user="Admin"); main_window.resize(1100, 800); main_window.show()
        sys.exit(app.exec())
    except Exception as e: print(e); sys.exit(1)