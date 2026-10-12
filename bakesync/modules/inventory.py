from bakesync.paths import IMAGES_DIR, PRODUCT_IMAGES_DIR, product_image
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QFrame,
                             QLineEdit, QSpinBox, QComboBox, QHeaderView,
                             QMenu, QDoubleSpinBox, QTabWidget, QCalendarWidget)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QColor, QBrush, QIcon
from PyQt6.QtWidgets import QSizePolicy
from bakesync.core.database import DatabaseManager

from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.product_images import default_product_pixmap
from bakesync.core.leftovers import expire_old_batches
from datetime import date as _date, timedelta as _timedelta
from PyQt6.QtGui import QPixmap
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix


def _calendar_popup(parent_dialog, expiry_line_edit, anchor_widget,
                    arrow_down_path, arrow_left_path, arrow_right_path):
    """
    Build and show a calendar popup anchored below `anchor_widget`.
    Writes the selected date (yyyy-MM-dd) into `expiry_line_edit`.
    Attach the returned open_calendar function to your cal_btn.clicked signal.
    """
    def open_calendar():
        if parent_dialog._cal_popup and parent_dialog._cal_popup.isVisible():
            popup = parent_dialog._cal_popup
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
            ao = QPropertyAnimation(popup, b"windowOpacity")
            ao.setDuration(180); ao.setStartValue(1.0); ao.setEndValue(0.0)
            ao.setEasingCurve(QEasingCurve.Type.InQuad)
            sg = popup.geometry()
            ag = QPropertyAnimation(popup, b"geometry")
            ag.setDuration(180); ag.setStartValue(sg)
            ag.setEndValue(QRect(sg.x(), sg.y() - 10, sg.width(), sg.height()))
            ag.setEasingCurve(QEasingCurve.Type.InQuad)
            ag.finished.connect(popup.hide)
            ao.start(); ag.start(); popup._anims = [ao, ag]
            return

        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect

        popup = QFrame(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint |
                       Qt.WindowType.NoDropShadowWindowHint)
        popup.setStyleSheet("QFrame { background-color: white; border: 1px solid #D1D5DB; border-radius: 10px; }")
        popup.setFixedWidth(anchor_widget.width())
        popup.setFixedHeight(240)
        parent_dialog._cal_popup = popup

        pop_layout = QVBoxLayout(popup)
        pop_layout.setContentsMargins(4, 6, 4, 6)
        pop_layout.setSpacing(2)

        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        calendar.setNavigationBarVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        current = QDate.fromString(expiry_line_edit.text(), "yyyy-MM-dd")
        if current.isValid():
            calendar.setSelectedDate(current)
        calendar.setFixedHeight(185)
        calendar.setStyleSheet("""
            QCalendarWidget { background-color: white; border: none; }
            QCalendarWidget QAbstractItemView { background-color: white; color: #0F172A;
                selection-background-color: #693903; selection-color: white;
                border: none; outline: none; font-size: 10px; }
            QCalendarWidget QTableView::item:hover { background-color: #F3E8DC; color: #693903; }
            QCalendarWidget QAbstractItemView:enabled { color: #0F172A; }
            QCalendarWidget QAbstractItemView:disabled { color: #CBD5E1; }
            QCalendarWidget QHeaderView::section { background-color: white; color: #94A3B8;
                font-size: 9px; font-weight: normal; border: none; padding: 1px 0px; }
            QCalendarWidget QHeaderView::section:hover { background-color: white; color: #94A3B8; }
        """)

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: white; border: none;")
        nav_h = QHBoxLayout(nav_widget)
        nav_h.setContentsMargins(8, 0, 8, 4)
        nav_h.setSpacing(4)

        nav_label = QPushButton()
        nav_label.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_label.setStyleSheet("""
            QPushButton { font-size: 12px; font-weight: normal; color: #0F172A;
                background: transparent; border: none; padding: 0px; text-align: left; }
            QPushButton:hover { color: #693903; }
        """)

        def update_nav_label():
            try:
                d = QDate(calendar.yearShown(), calendar.monthShown(), 1)
                nav_label.setText(d.toString("MMMM yyyy"))
                nav_label.setIcon(QIcon(arrow_down_path))
                nav_label.setIconSize(QSize(8, 8))
                nav_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            except Exception:
                pass

        update_nav_label()
        calendar.currentPageChanged.connect(lambda y, m: update_nav_label())

        def open_month_year_picker():
            picker = QFrame(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.NoDropShadowWindowHint)
            picker.setStyleSheet("QFrame { background-color: white; border: 1px solid #D1D5DB; border-radius: 8px; }")
            picker.setFixedWidth(anchor_widget.width())
            pl = QVBoxLayout(picker)
            pl.setContentsMargins(8, 8, 8, 8)
            pl.setSpacing(6)

            sy = [calendar.yearShown()]
            sm = [calendar.monthShown()]

            yr = QHBoxLayout(); yr.setSpacing(8)
            yp = QPushButton(); yp.setIcon(QIcon(arrow_left_path)); yp.setIconSize(QSize(12, 12))
            yp.setFixedSize(26, 26); yp.setCursor(Qt.CursorShape.PointingHandCursor)
            yp.setStyleSheet("QPushButton { border: 1px solid #E2E8F0; border-radius: 5px; background: white; } QPushButton:hover { background: #F1F5F9; }")
            yl = QLabel(str(sy[0])); yl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            yl.setStyleSheet("font-size: 12px; font-weight: bold; color: #0F172A; border: none; background: transparent;")
            yl.setFixedWidth(60)
            yn = QPushButton(); yn.setIcon(QIcon(arrow_right_path)); yn.setIconSize(QSize(12, 12))
            yn.setFixedSize(26, 26); yn.setCursor(Qt.CursorShape.PointingHandCursor)
            yn.setStyleSheet("QPushButton { border: 1px solid #E2E8F0; border-radius: 5px; background: white; } QPushButton:hover { background: #F1F5F9; }")
            yr.addStretch(); yr.addWidget(yp); yr.addWidget(yl); yr.addWidget(yn); yr.addStretch()
            pl.addLayout(yr)

            months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            from PyQt6.QtWidgets import QGridLayout
            mgw = QWidget(); mgw.setStyleSheet("background: transparent; border: none;")
            mg = QGridLayout(mgw); mg.setSpacing(4); mg.setContentsMargins(0, 0, 0, 0)
            mbs = []

            def mmb(i, label):
                mb = QPushButton(label); mb.setFixedHeight(28); mb.setCursor(Qt.CursorShape.PointingHandCursor)
                isel = (i + 1 == sm[0])
                mb.setStyleSheet(f"QPushButton {{ border-radius: 5px; font-size: 11px; border: none; "
                                 f"background-color: {'#693903' if isel else 'transparent'}; "
                                 f"color: {'white' if isel else '#0F172A'}; }} "
                                 f"QPushButton:hover {{ background-color: {'#693903' if isel else '#F1F5F9'}; }}")
                def oc(checked=False, month=i + 1):
                    calendar.setCurrentPage(sy[0], month); update_nav_label(); picker.hide()
                mb.clicked.connect(oc)
                return mb

            for i, label in enumerate(months):
                b = mmb(i, label); mbs.append(b); mg.addWidget(b, i // 4, i % 4)
            pl.addWidget(mgw)

            def cy(delta):
                sy[0] += delta; yl.setText(str(sy[0]))
                for i in range(len(mbs)):
                    isel = (i + 1 == sm[0]) and (sy[0] == calendar.yearShown())
                    mbs[i].setStyleSheet(f"QPushButton {{ border-radius: 5px; font-size: 11px; border: none; "
                                         f"background-color: {'#693903' if isel else 'transparent'}; "
                                         f"color: {'white' if isel else '#0F172A'}; }} "
                                         f"QPushButton:hover {{ background-color: {'#693903' if isel else '#F1F5F9'}; }}")

            yp.clicked.connect(lambda: cy(-1)); yn.clicked.connect(lambda: cy(1))
            gp = nav_label.mapToGlobal(nav_label.rect().bottomLeft())
            picker.move(gp.x(), gp.y() + 4); picker.adjustSize(); picker.show()

        nav_label.clicked.connect(open_month_year_picker)

        pbc = QPushButton(); pbc.setFixedSize(24, 24); pbc.setIcon(QIcon(arrow_left_path)); pbc.setIconSize(QSize(14, 14))
        pbc.setCursor(Qt.CursorShape.PointingHandCursor)
        pbc.setStyleSheet("QPushButton { border: 1px solid #E2E8F0; border-radius: 6px; background: white; } QPushButton:hover { background-color: #F1F5F9; }")
        nbc = QPushButton(); nbc.setFixedSize(24, 24); nbc.setIcon(QIcon(arrow_right_path)); nbc.setIconSize(QSize(14, 14))
        nbc.setCursor(Qt.CursorShape.PointingHandCursor)
        nbc.setStyleSheet("QPushButton { border: 1px solid #E2E8F0; border-radius: 6px; background: white; } QPushButton:hover { background-color: #F1F5F9; }")

        def go_prev():
            y, m = calendar.yearShown(), calendar.monthShown(); m -= 1
            if m < 1: m = 12; y -= 1
            calendar.setCurrentPage(y, m); update_nav_label()

        def go_next():
            y, m = calendar.yearShown(), calendar.monthShown(); m += 1
            if m > 12: m = 1; y += 1
            calendar.setCurrentPage(y, m); update_nav_label()

        pbc.clicked.connect(go_prev); nbc.clicked.connect(go_next)
        nav_h.addWidget(nav_label); nav_h.addStretch(); nav_h.addWidget(pbc); nav_h.addWidget(nbc)
        pop_layout.addWidget(nav_widget); pop_layout.addWidget(calendar)

        gpos = anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft())
        sy2 = gpos.y() - 10; ey = gpos.y() + 4
        popup.move(gpos.x(), sy2); popup.setWindowOpacity(0.0); popup.show()

        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        ao = QPropertyAnimation(popup, b"windowOpacity")
        ao.setDuration(200); ao.setStartValue(0.0); ao.setEndValue(1.0); ao.setEasingCurve(QEasingCurve.Type.OutQuad)
        ag = QPropertyAnimation(popup, b"geometry")
        ag.setDuration(200)
        ag.setStartValue(QRect(gpos.x(), sy2, popup.width(), popup.height()))
        ag.setEndValue(QRect(gpos.x(), ey, popup.width(), popup.height()))
        ag.setEasingCurve(QEasingCurve.Type.OutQuad)
        ao.start(); ag.start(); popup._anims = [ao, ag]

        def on_date_clicked(date):
            expiry_line_edit.setText(date.toString("yyyy-MM-dd"))
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
            ao2 = QPropertyAnimation(popup, b"windowOpacity")
            ao2.setDuration(180); ao2.setStartValue(1.0); ao2.setEndValue(0.0); ao2.setEasingCurve(QEasingCurve.Type.InQuad)
            cg = popup.geometry()
            ag2 = QPropertyAnimation(popup, b"geometry")
            ag2.setDuration(180); ag2.setStartValue(cg)
            ag2.setEndValue(QRect(cg.x(), cg.y() - 10, cg.width(), cg.height()))
            ag2.setEasingCurve(QEasingCurve.Type.InQuad)
            ag2.finished.connect(popup.hide); ao2.start(); ag2.start(); popup._anims = [ao2, ag2]

        calendar.clicked.connect(on_date_clicked)

    return open_calendar


def _make_expiry_row(parent_dialog, default_date_str=None):
    """
    Returns (expiry_container, expiry_line_edit) with a calendar button wired up.
    Call after setting ARROW_*_PATH attributes on parent_dialog.
    """
    CALENDAR_PATH = os.path.join(IMAGES_DIR, "calendar.png").replace("\\", "/")
    ARROW_DOWN_PATH  = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
    ARROW_LEFT_PATH  = os.path.join(IMAGES_DIR, "arrowleft.png").replace("\\", "/")
    ARROW_RIGHT_PATH = os.path.join(IMAGES_DIR, "arrowright.png").replace("\\", "/")

    expiry_container = QWidget()
    expiry_container.setFixedHeight(38)
    expiry_container.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 4px; background: white;")
    expiry_h = QHBoxLayout(expiry_container)
    expiry_h.setContentsMargins(0, 0, 0, 0)
    expiry_h.setSpacing(0)

    expiry_input = QLineEdit()
    expiry_input.setPlaceholderText("yyyy-MM-dd")
    expiry_input.setText(default_date_str or QDate.currentDate().addMonths(6).toString("yyyy-MM-dd"))
    expiry_input.setStyleSheet("border: none; padding: 8px 12px; font-size: 13px; color: #0F172A; background: transparent;")
    expiry_h.addWidget(expiry_input)

    cal_btn = QPushButton()
    cal_btn.setFixedSize(36, 38)
    cal_btn.setIcon(QIcon(CALENDAR_PATH))
    cal_btn.setIconSize(QSize(16, 16))
    cal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cal_btn.setStyleSheet("""
        QPushButton { border: none; background: transparent; padding: 0px;
            border-top-right-radius: 4px; border-bottom-right-radius: 4px; }
        QPushButton:hover { background-color: #F3F4F6; }
    """)
    expiry_h.addWidget(cal_btn)

    parent_dialog._cal_popup = None
    cal_btn.clicked.connect(_calendar_popup(
        parent_dialog, expiry_input, expiry_container,
        ARROW_DOWN_PATH, ARROW_LEFT_PATH, ARROW_RIGHT_PATH
    ))

    return expiry_container, expiry_input


def _make_draggable(dialog):
    """Mixin-style: patch drag-move and center-on-show onto a QDialog."""
    def mousePressEvent(event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog._drag_pos = event.globalPosition().toPoint() - dialog.frameGeometry().topLeft()
    def mouseMoveEvent(event):
        if event.buttons() == Qt.MouseButton.LeftButton and getattr(dialog, '_drag_pos', None):
            dialog.move(event.globalPosition().toPoint() - dialog._drag_pos)
    def mouseReleaseEvent(event):
        dialog._drag_pos = None
    def showEvent(event):
        QDialog.showEvent(dialog, event)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        dialog.move((screen.width() - dialog.width()) // 2,
                    (screen.height() - dialog.height()) // 2)
    dialog.mousePressEvent  = mousePressEvent
    dialog.mouseMoveEvent   = mouseMoveEvent
    dialog.mouseReleaseEvent= mouseReleaseEvent
    dialog.showEvent        = showEvent


def _close_btn():
    btn = QPushButton(""); btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedSize(28, 28)
    btn.setStyleSheet("""
        QPushButton { background-color: transparent; color: #475569; font-size: 14px; border: none; border-radius: 4px; }
        QPushButton:hover { background-color: #FEE2E2; color: #B91C1C; }
    """)
    return btn


LABEL_STYLE = "font-size: 12px; color: #475569; font-weight: normal; background: transparent; border: none; padding: 0px;"

DIALOG_WRAPPER_STYLE = """
    QFrame { background-color: white; border: 1px solid #303030; border-radius: 7px; }
    QLabel { border: none; background: transparent; padding: 0px; color: #0F172A; }
    QWidget { background-color: white; color: #0F172A; }
    QLineEdit { background-color: white; color: #0F172A; }
    QDoubleSpinBox { background-color: white; color: #0F172A; }
    QSpinBox { background-color: white; color: #0F172A; }
    QComboBox { background-color: white; color: #0F172A; }
"""

TABLE_STYLE_SUMMARY = """
    QTableWidget { background-color: white; gridline-color: #E5E7EB; border: none; font-size: 13px; color: #0F172A; }
    QHeaderView::section { background-color: #693903; color: white; font-weight: normal; font-size: 12px; padding: 8px; border: none; }
    QTableWidget::item { padding: 8px; }
    QTableWidget::item:selected { background-color: #cbd5e1; color: black; }
    QScrollBar:vertical { background: transparent; width: 6px; margin: 0px; }
    QScrollBar::handle:vertical { background: #D0D0D0; border-radius: 3px; min-height: 30px; }
    QScrollBar::handle:vertical:hover { background: #AAAAAA; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""

TAB_STYLE = """
    QTabWidget::pane { border: none; background: white; margin: 0px; padding: 0px;
        margin-left: -1px; margin-right: -1px; margin-bottom: -1px; }
    QTabBar::tab { background: transparent; color: #555555; font-size: 13px; font-weight: normal;
        padding: 10px 15px; border: none; border-bottom: 2px solid transparent; }
    QTabBar::tab QLabel { margin-right: 4px; }
    QTabBar::tab:selected { background: #e8cfc4; color: #2b2b2b;
        border-top: 1px solid #2b2b2b; border-bottom: 2px solid #e8cfc4; }
    QTabBar::tab:!selected:hover { color: #2b2b2b; background: #E0E0E0; }
"""


def _make_spin_container(spin_widget, arrow_down_path, arrow_up_path, height=38):
    """Wrap a QSpinBox/QDoubleSpinBox with up/down arrow buttons."""
    container = QWidget()
    container.setFixedHeight(height)
    container.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 4px; background: white;")
    h = QHBoxLayout(container)
    h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
    h.addWidget(spin_widget)

    dn = QPushButton(); dn.setFixedSize(28, height); dn.setIcon(QIcon(arrow_down_path)); dn.setIconSize(QSize(12, 12))
    dn.setCursor(Qt.CursorShape.PointingHandCursor)
    dn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: #F3F4F6; }")
    dn.clicked.connect(spin_widget.stepDown)

    up = QPushButton(); up.setFixedSize(28, height); up.setIcon(QIcon(arrow_up_path)); up.setIconSize(QSize(12, 12))
    up.setCursor(Qt.CursorShape.PointingHandCursor)
    up.setStyleSheet("QPushButton { border: none; background: transparent; border-top-right-radius: 4px; border-bottom-right-radius: 4px; } QPushButton:hover { background-color: #F3F4F6; }")
    up.clicked.connect(spin_widget.stepUp)

    h.addWidget(dn); h.addWidget(up)
    return container

class InventoryWidget(QWidget):
    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.init_ui()

    def _create_vector_icon(self, svg_string, color):
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QByteArray
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode('utf-8')), "SVG")
        return QIcon(pixmap)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_bread_data()
        self.load_retail_data()

    def init_ui(self):
        BROWN_DARK  = "#693903"
        BROWN_MID   = "#735F48"
        BROWN_LIGHT = "#948778"
        CREAM       = "#F1F5F9"
        CREAM_LIGHT = "#FFFFFF"
        TEXT_DARK   = "#0F172A"
        TEXT_MID    = "#475569"
        ARROW_PATH  = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(CREAM))
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(40, 10, 40, 10)

        top_bar_container = QWidget()
        top_bar_container.setStyleSheet("background-color: transparent;")
        top_bar_container_layout = QVBoxLayout(top_bar_container)
        top_bar_container_layout.setSpacing(0)
        top_bar_container_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(0)
        top_bar.setContentsMargins(0, 0, 0, 0)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #EADFD3; border: none;")

        top_bar_container_layout.addLayout(top_bar)
        top_bar_container_layout.addWidget(separator)

        TAB_BTN_STYLE = f"QPushButton {{ background: white; color: #7A6A5E; border: 1px solid #EADFD3; border-radius: 17px; padding: 7px 18px; font-size: 13px; font-weight: 600; margin: 8px 6px 8px 0; }} QPushButton:hover {{ background: #F5ECE5; }}"
        TAB_BTN_ACTIVE_STYLE = f"QPushButton {{ background: #6B3F27; color: white; border: 1px solid #6B3F27; border-radius: 17px; padding: 7px 18px; font-size: 13px; font-weight: 600; margin: 8px 6px 8px 0; }}"

        def make_tab_wrapper(btn, active=False):
            wrapper = QFrame()
            wrapper.setStyleSheet("QFrame { border: none; background: transparent; }")
            wl = QVBoxLayout(wrapper)
            wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(0)
            wl.addWidget(btn)
            return wrapper


        self.tab_bread_btn = QPushButton("Bread Products")
        self.tab_bread_btn.setStyleSheet(TAB_BTN_ACTIVE_STYLE)
        self.tab_bread_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_bread_btn.clicked.connect(lambda: self.switch_tab("bread"))
        self.tab_bread_wrapper = make_tab_wrapper(self.tab_bread_btn, active=True)
        top_bar.addWidget(self.tab_bread_wrapper)

        self.tab_retail_btn = QPushButton("Retail Products")
        self.tab_retail_btn.setStyleSheet(TAB_BTN_STYLE)
        self.tab_retail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_retail_btn.clicked.connect(lambda: self.switch_tab("retail"))
        self.tab_retail_wrapper = make_tab_wrapper(self.tab_retail_btn, active=False)
        top_bar.addWidget(self.tab_retail_wrapper)

        top_bar.addStretch()

        self.add_bread_btn = QPushButton("+ Bread")
        self.add_bread_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_bread_btn.setStyleSheet("""
            QPushButton { 
                background-color: #693903; 
                color: white; 
                border: 1px solid #693903; 
                border-radius: 6px; 
                padding: 8px 16px; 
                font-size: 13px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #452803; 
                border: 1px solid #452803;
            }
        """)
        self.add_bread_btn.clicked.connect(self.add_new_bread)

        self.add_retail_btn = QPushButton("+ Retail Item")
        self.add_retail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_retail_btn.setStyleSheet("""
            QPushButton { 
                background-color: #FFFFFF; 
                color: #693903; 
                border: 2px solid #693903; 
                border-radius: 6px; 
                padding: 7px 16px; 
                font-size: 13px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #F3E8DC; 
            }
        """)
        self.add_retail_btn.setVisible(False)
        self.add_retail_btn.clicked.connect(self.add_new_retail)

        self.archive_inv_btn = QPushButton("Archived Items")
        self.archive_inv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.archive_inv_btn.setStyleSheet("""
            QPushButton { 
                background-color: #E8D5C4; 
                color: #452803; 
                border: none; 
                border-radius: 6px; 
                padding: 8px 16px; 
                font-size: 13px;
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #D4B89F; 
            }
        """)
        self.archive_inv_btn.clicked.connect(self.show_archived_items)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.bulk_stock_btn = QPushButton("+ Add Stock (all bread)")
        self.bulk_stock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bulk_stock_btn.setToolTip("Enter how many came out of the oven, for all bread at once")
        self.bulk_stock_btn.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #693903; border: 2px solid #693903; border-radius: 6px;
                          padding: 7px 16px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #F3E8DC; }
        """)
        self.bulk_stock_btn.clicked.connect(self.open_bulk_bread_stock)
        btn_layout.addWidget(self.bulk_stock_btn)
        btn_layout.addWidget(self.add_bread_btn)
        btn_layout.addWidget(self.add_retail_btn)
        btn_layout.addWidget(self.archive_inv_btn)
        top_bar.addLayout(btn_layout)

        layout.addWidget(top_bar_container)
        from bakesync.widgets.ui import intro_row, legend_row, InfoIcon, svg_pixmap
        intro, _ = intro_row("Your bread and retail items: how many are ready to sell, and until when.",
                             "Items that need attention (out of stock, low, last day to sell) are listed first. "
                             "Click any row to see the details and to add stock, change the price or archive it.", "Inventory")
        intro.setContentsMargins(0, 10, 0, 6)
        layout.addWidget(intro)

        card = QFrame()
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setObjectName("card")
        card.setStyleSheet(f"QFrame#card {{ background-color: {CREAM_LIGHT}; border: none; }}")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(0, 16, 0, 16)

        card_top = QHBoxLayout()
        card_top.setContentsMargins(16, 8, 16, 8)
        card_top.setSpacing(10)

        self.card_title = QLabel("Bread Inventory")
        self.card_title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {TEXT_DARK}; background-color: transparent; padding-right: 8px;")
        card_top.addWidget(self.card_title)

        search_box = QFrame(); search_box.setObjectName("sbox")
        search_box.setFixedHeight(36); search_box.setMinimumWidth(240)
        search_box.setStyleSheet("QFrame#sbox { background: white; border: 1px solid #D6CCC2; border-radius: 9px; }"
                                 "QFrame#sbox:hover { border-color: #6B3F27; }")
        sbl = QHBoxLayout(search_box); sbl.setContentsMargins(10, 0, 6, 0); sbl.setSpacing(6)
        s_ic = QLabel(); s_ic.setPixmap(svg_pixmap("search", "#A8998D", 16)); s_ic.setStyleSheet("border: none; background: transparent;")
        sbl.addWidget(s_ic)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search an item...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(f"QLineEdit {{ background: transparent; border: none; font-size: 13px; color: {TEXT_DARK}; }}")
        self.search_input.textChanged.connect(self.load_bread_data)
        self.search_input.textChanged.connect(self.load_retail_data)
        sbl.addWidget(self.search_input)
        card_top.addWidget(search_box)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Low", "Out of stock", "Expiring"])
        self.filter_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_combo.setMinimumWidth(150)
        self.filter_combo.setFixedHeight(36)
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{ background-color: white; border: 1px solid #D6CCC2; border-radius: 9px; padding: 4px 34px 4px 12px; font-size: 13px; color: {TEXT_DARK}; min-width: 130px; }}
            QComboBox:hover {{ border: 1px solid {BROWN_MID}; }}
            QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border: none; border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
            QComboBox::down-arrow {{ image: url({ARROW_PATH}); width: 12px; height: 12px; }}
            QComboBox QAbstractItemView {{ background-color: white; border: 1px solid {BROWN_LIGHT}; outline: none; padding: 0px; }}
            QComboBox QAbstractItemView::item {{ padding: 0px 12px; color: {TEXT_DARK}; border: none; margin: 0px; min-width: 150px; }}
            QComboBox QAbstractItemView::item:hover {{ background-color: #6B3F27; color: white; }}
            QComboBox QAbstractItemView::item:selected {{ background-color: #6B3F27; color: white; }}
        """)
        self.filter_combo.currentTextChanged.connect(self.load_bread_data)
        self.filter_combo.currentTextChanged.connect(self.load_retail_data)
        card_top.addWidget(self.filter_combo)
        # 🟢 NEW: CATEGORY FILTER PARA SA RETAIL
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All Categories", "Beverage", "Spread/Jam", "Merchandise", "Packaging", "Others"])
        self.category_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.category_combo.setMinimumWidth(190)
        self.category_combo.setFixedHeight(36)
        self.category_combo.setStyleSheet(self.filter_combo.styleSheet()) # Kopyahin ang style ng filter
        self.category_combo.currentTextChanged.connect(self.load_retail_data)
        self.category_combo.setVisible(False) # Nakatago by default (lalabas lang sa Retail tab)
        card_top.addWidget(self.category_combo)

        card_top.addStretch()
        card_top.addWidget(legend_row([("#B91C1C", "Out"), ("#D97706", "Low"), ("#059669", "OK"), ("#2563EB", "Plenty")]))
        card_top.addWidget(InfoIcon("Out = none left to sell.  Low = fewer than 10 bread or 5 retail pieces.  "
                                    "OK = enough for now.  Plenty = 50 or more.  'Sell by' is the last day the oldest pieces can be sold.",
                                    "What the colours mean"))
        card_layout.addLayout(card_top)
        hint = QLabel("Click a row to see details and actions.")
        hint.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent; padding-left: 16px;")
        card_layout.addWidget(hint)

        TABLE_STYLE = f"""
            QTableWidget {{ background-color: transparent; gridline-color: transparent; border: none; font-size: 13px; color: #0F172A; }}
            QHeaderView::section {{ background-color: #693903; color: white; font-weight: normal; font-size: 12px; padding: 10px 8px; border: none; }}
            QTableWidget::item:selected {{ background-color: #cbd5e1; color: black; }}
            QToolTip {{ background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #444444; padding: 4px 8px; font-size: 12px; border-radius: 4px; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: #D0D0D0; border-radius: 3px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: #AAAAAA; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """

        def _make_table(columns):
            t = QTableWidget()
            t.setColumnCount(len(columns))
            t.setHorizontalHeaderLabels(columns)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            t.verticalHeader().setVisible(False)
            t.setShowGrid(False)
            t.setStyleSheet(TABLE_STYLE)
            t.setAlternatingRowColors(False)
            t.viewport().setStyleSheet("")
            return t


        self.bread_table = _make_table(["Item Name", "Ready to sell", "Status", "Sell by"])
        self.bread_table.cellClicked.connect(lambda r, c: self._open_summary(self.bread_table, r))
        self.bread_table.setCursor(Qt.CursorShape.PointingHandCursor)
        card_layout.addWidget(self.bread_table)

        self.retail_table = _make_table(["Item Name", "Category", "Ready to sell", "Status", "Sell by"])
        self.retail_table.cellClicked.connect(lambda r, c: self._open_summary(self.retail_table, r))
        self.retail_table.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retail_table.setVisible(False)
        card_layout.addWidget(self.retail_table)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 16)
        outer.addWidget(card, stretch=1)
        layout.addLayout(outer, stretch=1)

        self.current_tab = "bread"
        self._ensure_product_type_column()
        self.check_and_auto_expire_items()
        self.load_bread_data()
        self.load_retail_data()

    def _make_action_btn(self, row, menu_handler, view_handler, bg_color=None, stock_handler=None):
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        from PyQt6.QtCore import Qt, QSize
        from PyQt6.QtGui import QColor

        if bg_color is None:
            bg_color = QColor("#FFFFFF")
        bg_hex = bg_color.name(QColor.NameFormat.HexRgb)

        container = QWidget()
        container.setStyleSheet(f"background-color: {bg_hex}; border: none; margin: 0px; padding: 0px;")

        # 🟢 TRUE VECTOR SVGS
        VIEW_SVG = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        """

        MENU_SVG = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="1"></circle>
            <circle cx="12" cy="5" r="1"></circle>
            <circle cx="12" cy="19" r="1"></circle>
        </svg>
        """

        # 🟢 VIEW BUTTON (EYE) - White Background, Brown Icon
        view_btn = QPushButton()
        view_btn.setIcon(self._create_vector_icon(VIEW_SVG, "#693903"))
        view_btn.setIconSize(QSize(16, 16))
        view_btn.setFixedSize(30, 30)
        view_btn.setToolTip("View Overview")
        view_btn.setStyleSheet("""
            QPushButton { border: 1px solid #693903; background-color: #FFFFFF; border-radius: 6px; }
            QPushButton:hover { background-color: #F3E8DC; }
        """)
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.clicked.connect(lambda checked=False, r=row: view_handler(r))

        # 🟢 MENU BUTTON (3-DOTS) - Brown Background, White Icon
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
        menu_btn.clicked.connect(lambda checked=False, r=row: menu_handler(r))

        cl = QHBoxLayout(container)
        cl.setContentsMargins(4, 2, 4, 2)
        cl.setSpacing(8)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if stock_handler is not None:
            stock_btn = QPushButton("+ Stock")
            stock_btn.setFixedHeight(30)
            stock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            stock_btn.setToolTip("Add stock")
            stock_btn.setStyleSheet("""
                QPushButton { background-color: #693903; color: white; border: none; border-radius: 6px;
                              padding: 0 12px; font-size: 12px; font-weight: bold; }
                QPushButton:hover { background-color: #452803; }
            """)
            stock_btn.clicked.connect(lambda checked=False, r=row: stock_handler(r))
            cl.addWidget(stock_btn)
        # Standard Order: View muna, bago yung Menu
        cl.addWidget(view_btn)
        cl.addWidget(menu_btn)
        
        return container

    def _menu_style(self):
        return """
            QMenu { background-color: white; border: 1px solid #948778; padding: 0px; }
            QMenu::item { padding: 4px 24px; color: #0F172A; font-size: 13px; margin: 0px; }
            QMenu::item:selected { background-color: #693903; color: white; }
        """

    def switch_tab(self, tab):
        BROWN_DARK = "#693903"; TEXT_MID = "#475569"
        AW = IW = "QFrame { border: none; background: transparent; }"
        AB = f"QPushButton {{ background: #6B3F27; color: white; border: 1px solid #6B3F27; border-radius: 17px; padding: 7px 18px; font-size: 13px; font-weight: 600; margin: 8px 6px 8px 0; }}"
        IB = f"QPushButton {{ background: white; color: #7A6A5E; border: 1px solid #EADFD3; border-radius: 17px; padding: 7px 18px; font-size: 13px; font-weight: 600; margin: 8px 6px 8px 0; }} QPushButton:hover {{ background: #F5ECE5; }}"
        self.current_tab = tab
        for wrapper, btn, active in [
            (self.tab_bread_wrapper,  self.tab_bread_btn,  tab == "bread"),
            (self.tab_retail_wrapper, self.tab_retail_btn, tab == "retail"),
        ]:
            wrapper.setStyleSheet(AW if active else IW)
            btn.setStyleSheet(AB if active else IB)
        self.bread_table.setVisible(tab == "bread")
        self.retail_table.setVisible(tab == "retail")
        if hasattr(self, 'category_combo'):
            self.category_combo.setVisible(tab == "retail")

        title_map = {"bread": "Bread Inventory", "retail": "Retail Inventory"}
        self.card_title.setText(title_map.get(tab, "Inventory"))
        if hasattr(self, 'add_bread_btn'):  self.add_bread_btn.setVisible(tab == "bread")
        if hasattr(self, 'bulk_stock_btn'): self.bulk_stock_btn.setVisible(tab == "bread")
        if hasattr(self, 'add_retail_btn'): self.add_retail_btn.setVisible(tab == "retail")
        for tbl in [self.bread_table, self.retail_table]:
            tbl.viewport().update()
        self.update()

    def _get_status(self, stock, usage, expiry_date, today):
        if stock <= 0:
            return "Out of Stock", QColor("#FEE2E2")
        if usage > 0:
            if stock < (usage * 3):    return "Low Stock",  QColor("#FEF9C3")
            elif stock >= (usage * 14): return "High Stock", QColor("#DCFCE7")
        else:
            if stock < 10:   return "Low Stock",  QColor("#FEF9C3")
            elif stock >= 50: return "High Stock", QColor("#DCFCE7")
        return "Good", QColor("#D1FAE5")

    def _ensure_product_type_column(self):
        try:
            self.db.execute_query("ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'beverage'")
        except Exception:
            pass
        try:
            self.db.execute_query("ALTER TABLE product_batches ADD COLUMN stocked_by TEXT DEFAULT ''")
        except Exception:
            pass

    def load_bread_data(self, *_):
        self._load_table(self.bread_table, "bread")

    def _load_table(self, table, kind):
        """Fill the Bread or Retail table. Items needing attention (out, low, last day) come first."""
        search = self.search_input.text().strip()
        flt = self.filter_combo.currentText()
        is_bread = kind == "bread"
        query = ("SELECT id, name, stock_qty, product_type FROM products WHERE is_archived = 0 AND "
                 + ("product_type = 'bread'" if is_bread else "COALESCE(product_type, '') != 'bread'"))
        params = []
        if search:
            query += " AND name LIKE ?"; params.append(f"%{search}%")
        if not is_bread and hasattr(self, 'category_combo') and self.category_combo.currentText() != "All Categories":
            query += " AND product_type = ?"; params.append(self.category_combo.currentText())
        try:
            rows = self.db.fetch_all(query, params)
        except Exception as e:
            print(f"[Inventory] load error: {e}")
            rows = []

        today = _date.today()
        STATUS = {"out": ("Out", "#B91C1C", "#FEE2E2"), "low": ("Low", "#B45309", "#FEF3C7"),
                  "ok": ("OK", "#047857", "#D1FAE5"), "many": ("Plenty", "#1D4ED8", "#DBEAFE")}
        items = []
        for r in rows:
            stock = r['stock_qty'] or 0
            b = self.db.fetch_one(
                "SELECT COALESCE(SUM(CASE WHEN expiry_date <= ? THEN quantity_remaining END), 0) AS expired, "
                "MIN(CASE WHEN expiry_date > ? THEN expiry_date END) AS next_exp "
                "FROM product_batches WHERE product_id = ? AND quantity_remaining > 0", (today.isoformat(), today.isoformat(), r['id']))
            usable = max(0, stock - (b['expired'] or 0))
            low_limit = 10 if is_bread else 5
            if usable <= 0:
                state = "out"
            elif (is_bread and usable < low_limit) or (not is_bread and usable <= low_limit):
                state = "low"
            elif is_bread and usable >= 50:
                state = "many"
            else:
                state = "ok"
            last_day = None   # last day it can be sold = the day before its expiry date
            if usable > 0 and b['next_exp']:
                try:
                    last_day = _date.fromisoformat(b['next_exp'][:10]) - _timedelta(days=1)
                except ValueError:
                    last_day = None
            soon = last_day is not None and last_day <= today + _timedelta(days=1)
            if flt == "Low" and state != "low": continue
            if flt == "Out of stock" and state != "out": continue
            if flt == "Expiring" and not soon: continue
            priority = {"out": 0, "low": 1}.get(state, 3 if not soon else 2)
            items.append((priority, r['name'].lower(), r, usable, state, last_day))
        items.sort(key=lambda x: (x[0], x[1]))

        table.setRowCount(len(items))
        WHITE = QColor("#FFFFFF")
        for row, (_, _, r, usable, state, last_day) in enumerate(items):
            cells = []
            name_item = QTableWidgetItem(str(r['name']))
            name_item.setData(Qt.ItemDataRole.UserRole, r['id'])
            cells.append(name_item)
            if not is_bread:
                cells.append(QTableWidgetItem(str(r['product_type'] or "—").title()))
            cells.append(QTableWidgetItem(f"{usable:g}"))
            label, fg, bg = STATUS[state]
            status_item = QTableWidgetItem(label)
            status_item.setBackground(QBrush(QColor(bg))); status_item.setForeground(QBrush(QColor(fg)))
            f = status_item.font(); f.setBold(True); status_item.setFont(f)
            cells.append(status_item)
            if last_day is None:
                exp_text, exp_color = "—", "#94A3B8"
            elif last_day <= today:
                exp_text, exp_color = "Today", "#B91C1C"
            elif last_day == today + _timedelta(days=1):
                exp_text, exp_color = "Tomorrow", "#92400E"
            else:
                exp_text, exp_color = last_day.strftime("%b %d").replace(" 0", " "), "#475569"
            exp_item = QTableWidgetItem(exp_text); exp_item.setForeground(QBrush(QColor(exp_color)))
            cells.append(exp_item)
            for col, cell in enumerate(cells):
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if cell is not status_item:
                    cell.setBackground(QBrush(WHITE))
                    if cell is not exp_item:
                        cell.setForeground(QBrush(QColor("#0F172A")))
                table.setItem(row, col, cell)
            table.setRowHeight(row, 46)

    def _open_summary(self, table, row):
        item = table.item(row, 0)
        if not item:
            return
        dlg = ProductSummaryDialog(self.db, item.data(Qt.ItemDataRole.UserRole), current_user=self.current_user, parent=self)
        dlg.exec()
        if dlg.changed:
            self.load_bread_data()
            self.load_retail_data()

    def _stock_bread_row(self, row):
        pid = self.bread_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if UpdateBreadStockDialog(self.db, pid, current_user=self.current_user).exec():
            self.load_bread_data()

    def _stock_retail_row(self, row):
        pid = self.retail_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if UpdateRetailBatchDialog(self.db, pid, current_user=self.current_user).exec():
            self.load_retail_data()

    def open_bulk_bread_stock(self):
        if BulkBreadStockDialog(self.db, self, current_user=self.current_user).exec():
            self.load_bread_data()

    def load_retail_data(self, *_):
        self._load_table(self.retail_table, "retail")

    def check_and_auto_expire_items(self):
        """Once a day: write off stock whose expiry date has arrived (same rule as the POS)."""
        today_str = _date.today().isoformat()
        if getattr(self, '_last_expire_check', None) == today_str:
            return
        self._last_expire_check = today_str
        try:
            expire_old_batches(self.db, self.current_user or "System")
        except Exception as e:
            print(f"[Inventory] auto-expire error: {e}")

    def show_bread_action_menu(self, row):
        item = self.bread_table.item(row, 0)
        if not item: return
        prod_id = item.data(Qt.ItemDataRole.UserRole)
        prod_name = item.text()
        menu = QMenu(self); menu.setStyleSheet(self._menu_style())
        stock_action   = menu.addAction("Add/Update Stock")
        archive_action = menu.addAction("Archive Item")
        btn = self.bread_table.cellWidget(row, 4).findChild(QPushButton)
        action = menu.exec(btn.mapToGlobal(btn.rect().center()))
        if action == stock_action:
            if UpdateBreadStockDialog(self.db, prod_id, current_user=self.current_user).exec():
                self.load_bread_data()
        elif action == archive_action:
            self.db.execute_query("UPDATE products SET is_archived = 1 WHERE id = ?", (prod_id,))
            self.db.execute_query(
                "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                ('bread', prod_id, prod_name, 'archived', self.current_user))
            self.load_bread_data()

    def show_retail_action_menu(self, row):
        item = self.retail_table.item(row, 0)
        if not item: return
        prod_id = item.data(Qt.ItemDataRole.UserRole)
        prod_name = item.text()
        menu = QMenu(self); menu.setStyleSheet(self._menu_style())
        edit_action    = menu.addAction("Edit Details")
        stock_action   = menu.addAction("Add/Update Stock")
        archive_action = menu.addAction("Archive Item")
        btn = self.retail_table.cellWidget(row, 5).findChild(QPushButton)
        action = menu.exec(btn.mapToGlobal(btn.rect().center()))
        if action == edit_action:
            if EditRetailDialog(self.db, prod_id).exec(): self.load_retail_data()
        elif action == stock_action:
            if UpdateRetailBatchDialog(self.db, prod_id, current_user=self.current_user).exec(): self.load_retail_data()
        elif action == archive_action:
            self.db.execute_query("UPDATE products SET is_archived = 1 WHERE id = ?", (prod_id,))
            self.db.execute_query(
                "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                ('retail', prod_id, prod_name, 'archived', self.current_user))
            self.load_retail_data()

    def add_new_bread(self):
        if AddBreadDialog(self.db, self, current_user=self.current_user).exec():
            self.load_bread_data()

    def add_new_retail(self):
        if AddRetailDialog(self.db, current_user=self.current_user).exec(): self.load_retail_data()

    def show_archived_items(self):
        from bakesync.modules.recipe import ArchivedRecipesDialog
        ArchivedRecipesDialog(self.db, current_user=self.current_user, parent=self).exec()
        self.load_bread_data(); self.load_retail_data()

class _BaseDialog(QDialog):
    """Provides drag-to-move and center-on-show. All inventory dialogs inherit this."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def showEvent(self, event):
        super().showEvent(event)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)
    
    def _create_vector_icon(self, svg_string, color):
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import QByteArray
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode('utf-8')), "SVG")
        return QIcon(pixmap)

    def _build_wrapper(self, width=None, height=None):
        """Set up FramelessWindowHint + TranslucentBackground + outer wrapper frame."""
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QDialog { background-color: transparent; }")
        if width:  self.setFixedWidth(width)
        if height: self.setFixedHeight(height)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        wrapper = QFrame()
        wrapper.setStyleSheet(DIALOG_WRAPPER_STYLE)
        from PyQt6.QtGui import QPalette, QColor
        pal = wrapper.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#0F172A"))
        pal.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#0F172A"))
        wrapper.setPalette(pal)
        wrapper.setAutoFillBackground(True)
        outer.addWidget(wrapper)


        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(32, 25, 32, 38)
        layout.setSpacing(16)
        return layout

    def _title_row(self, text, layout):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 15)
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 20px; font-weight: normal; color: #0F172A;")
        row.addWidget(lbl); row.addStretch()
        cb = _close_btn(); cb.clicked.connect(self.reject)
        row.addWidget(cb)
        layout.addLayout(row)

    def _save_btn(self, text, color_bg, color_border, color_hover, layout):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color_bg}; color: white; border: 1px solid {color_border};
                border-radius: 4px; font-size: 14px; font-weight: normal; }}
            QPushButton:hover {{ background-color: {color_hover}; }}
        """)
        layout.addWidget(btn)
        return btn

class AddRetailDialog(_BaseDialog):
    def __init__(self, db, parent=None, current_user=""):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.setWindowTitle("Add Retail Item")
        layout = self._build_wrapper(width=520) # 🟢 Pinalaki para sa 2-column layout
        self._title_row("Add Retail Item", layout)

        ARROW_DOWN_PATH = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
        ARROW_UP_PATH   = os.path.join(IMAGES_DIR, "arrowup.png").replace("\\", "/")

        FIELD_STYLE = f"""
            QLineEdit, QDoubleSpinBox, QSpinBox {{ border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #0F172A; background-color: white; }}
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox {{ border: 1px solid #693903; }}
            QComboBox {{ border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #0F172A; background-color: white; }}
            QComboBox:focus {{ border: 1px solid #693903; }}
            QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border: none; }}
            QComboBox::down-arrow {{ image: url({ARROW_DOWN_PATH}); width: 12px; height: 12px; }}
            QComboBox QAbstractItemView {{ background-color: white; border: 1px solid #948778; outline: none; padding: 0px; }}
            QComboBox QAbstractItemView::item {{ padding: 6px 12px; color: #0F172A; border: none; }}
            QComboBox QAbstractItemView::item:hover {{ background-color: #693903; color: white; }}
        """

        # 🟢 BAGONG IMAGE UPLOAD UI
        self.selected_image_path = None
        row_img = QHBoxLayout(); row_img.setSpacing(16)
        
        self.lbl_img_preview = QLabel()
        self.lbl_img_preview.setFixedSize(100, 80)
        self.lbl_img_preview.setStyleSheet("border: 1px dashed #D1D5DB; border-radius: 5px; background-color: #F8FAFC;")
        self.lbl_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_preview.setScaledContents(True)

        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        self.lbl_img_preview.setScaledContents(False)
        self.lbl_img_preview.setPixmap(default_product_pixmap(100, 80, "retail"))

        self.btn_upload = QPushButton(" Select Image")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.setStyleSheet("QPushButton { background: #E8D5C4; color: #4A2C1C; border-radius: 4px; padding: 6px 12px; font-weight: bold; } QPushButton:hover { background: #D4BFA9; }")
        self.btn_upload.clicked.connect(self._choose_image)

        img_col = QVBoxLayout()
        lbl_img_title = QLabel("Product Image (For POS):"); lbl_img_title.setStyleSheet(LABEL_STYLE)
        
        img_row_inner = QHBoxLayout()
        img_row_inner.addWidget(self.lbl_img_preview)
        img_row_inner.addWidget(self.btn_upload)
        img_row_inner.addStretch()
        
        img_col.addWidget(lbl_img_title)
        img_col.addLayout(img_row_inner)
        row_img.addLayout(img_col)
        
        layout.addLayout(row_img)

        # --- ROW 1: Name & Category ---
        row1 = QHBoxLayout(); row1.setSpacing(16)
        
        col_name = QVBoxLayout(); col_name.setSpacing(6)
        lbl_name = QLabel("Product Name:"); lbl_name.setStyleSheet(LABEL_STYLE)
        self.name_input = QLineEdit(); self.name_input.setFixedHeight(38); self.name_input.setStyleSheet(FIELD_STYLE)
        col_name.addWidget(lbl_name); col_name.addWidget(self.name_input)
        row1.addLayout(col_name, stretch=2)

        col_cat = QVBoxLayout(); col_cat.setSpacing(6)
        lbl_cat = QLabel("Category:"); lbl_cat.setStyleSheet(LABEL_STYLE)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Beverage", "Spread/Jam", "Merchandise", "Packaging", "Others"])
        self.cat_combo.setFixedHeight(38)
        self.cat_combo.setStyleSheet(FIELD_STYLE)
        self.cat_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        col_cat.addWidget(lbl_cat); col_cat.addWidget(self.cat_combo)
        row1.addLayout(col_cat, stretch=1)
        
        layout.addLayout(row1)

        # ── Puhunan + Patong = Selling price (worked out for you) ──
        row2 = QHBoxLayout(); row2.setSpacing(16)
        self.cost_spin = QDoubleSpinBox(); self.patong_spin = QDoubleSpinBox()
        self.price_spin = QDoubleSpinBox(); self.price_spin.setRange(0, 199998); self.price_spin.setDecimals(2)
        for title, spin in (("Puhunan / cost per piece (₱):", self.cost_spin), ("Patong per piece (₱):", self.patong_spin)):
            col = QVBoxLayout(); col.setSpacing(6)
            lbl = QLabel(title); lbl.setStyleSheet(LABEL_STYLE)
            spin.setRange(0, 99999); spin.setDecimals(2); spin.setFixedHeight(38)
            spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            spin.setStyleSheet(FIELD_STYLE)
            col.addWidget(lbl); col.addWidget(spin)
            row2.addLayout(col)
        layout.addLayout(row2)
        self.price_preview = QLabel()
        self.price_preview.setStyleSheet("background: #F3F9F5; color: #2F7D4F; border: 1px solid #CBE7D5; border-radius: 8px; "
                                         "padding: 8px 12px; font-size: 13px;")
        layout.addWidget(self.price_preview)

        def _update_price(*_):
            price = round(self.cost_spin.value() + self.patong_spin.value(), 2)
            self.price_spin.setValue(price)
            self.price_preview.setText(f"Selling price: <b>₱{price:,.2f}</b>   ·   Tubo per piece: <b>₱{self.patong_spin.value():,.2f}</b>")
        self.cost_spin.valueChanged.connect(_update_price)
        self.patong_spin.valueChanged.connect(_update_price)
        _update_price()

        # --- ROW 3: Stock & Expiry ---
        row3 = QHBoxLayout(); row3.setSpacing(16)

        col_stock = QVBoxLayout(); col_stock.setSpacing(6)
        lbl_stock = QLabel("Initial Stock Quantity:"); lbl_stock.setStyleSheet(LABEL_STYLE)
        self.stock_spin = QSpinBox(); self.stock_spin.setRange(0, 99999); self.stock_spin.setFixedHeight(38)
        self.stock_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.stock_spin.setStyleSheet("border: none; padding: 8px 12px; font-size: 13px; color: #0F172A; background: transparent;")
        col_stock.addWidget(lbl_stock)
        col_stock.addWidget(_make_spin_container(self.stock_spin, ARROW_DOWN_PATH, ARROW_UP_PATH))
        row3.addLayout(col_stock)

        col_expiry = QVBoxLayout(); col_expiry.setSpacing(6)
        lbl_expiry = QLabel("Expiry Date:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        expiry_container, self.expiry_date = _make_expiry_row(self)
        col_expiry.addWidget(lbl_expiry); col_expiry.addWidget(expiry_container)
        row3.addLayout(col_expiry)

        layout.addLayout(row3)

        layout.addSpacing(8)
        btn = self._save_btn("Register Retail Item", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_data)

    def _choose_image(self):
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilters(["Images (*.png *.jpg *.jpeg)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_image_path = selected_files[0]
                self.lbl_img_preview.setPixmap(QPixmap(self.selected_image_path))
                self.lbl_img_preview.setText("")

    def save_data(self):
        # --- 0. ANTI-DOUBLE CLICK PROTECTION ---
        # Pipigilan nito ang system na mag-run ulit kung nagpo-proseso na siya
        if getattr(self, '_is_processing', False):
            return
        self._is_processing = True

        try:
            name = self.name_input.text().strip()
            category = self.cat_combo.currentText()
            cost = self.cost_spin.value()
            price = self.price_spin.value()
            stock = self.stock_spin.value()
            expiry = self.expiry_date.text().strip() or QDate.currentDate().toString("yyyy-MM-dd")
            
            # --- BASIC VALIDATIONS ---
            if not name or stock <= 0: 
                BakeSyncAlert.show_warning(self, "Incomplete Form", "Please provide a valid item name and stock quantity greater than 0.")
                return

            if any(char.isdigit() for char in name):
                if not BakeSyncAlert.ask_yes_no(
                    self, "Unusual Name Detected", 
                    f"The retail item name '{name}' contains numbers.\nAre you sure this is correct?"
                ):
                    return

            if stock > 50:
                if not BakeSyncAlert.ask_yes_no(
                    self, "High Quantity Warning", 
                    f"You are entering a large initial stock quantity ({stock} pcs).\n\nIs this amount correct?"
                ):
                    return

            from PyQt6.QtCore import QDate
            expiry_qdate = QDate.fromString(expiry, "yyyy-MM-dd")
            today = QDate.currentDate()
            
            if expiry_qdate <= today:
                BakeSyncAlert.show_error(
                    self, "Expired Date Detected", 
                    "You cannot register an item that is already expired or expiring today. Please input a valid future date."
                )
                return
            elif today.daysTo(expiry_qdate) <= 7:
                if not BakeSyncAlert.ask_yes_no(
                    self, "Short Shelf Life", 
                    f"Warning: This item will expire in {today.daysTo(expiry_qdate)} days.\n\nDo you want to proceed?"
                ):
                    return
            
            # --- DATABASE LOGIC ---
            existing = self.db.fetch_one("SELECT * FROM products WHERE name COLLATE NOCASE = ?", (name,))
            
            if existing:
                current_stock = existing['stock_qty'] if existing['stock_qty'] else 0
                existing_price = existing['retail_price'] if existing['retail_price'] else 0.0
                
                existing_details = {
                    "Matched Item": existing['name'].upper(),
                    "Category": existing['product_type'] if existing['product_type'] else "Unknown",
                    "Current Stock": f"{current_stock} pcs",
                    "Current Price": f"₱{existing_price:,.0f}",
                    "Your New Batch": f"{stock} pcs"
                }
                
                if BakeSyncAlert.ask_yes_no(
                    self, "Retail Item Already Exists", 
                    "We found an exact match in your system! Do you mean this item?\nDo you want to add your new entry as another batch for it?",
                    details=existing_details
                ):
                    self.db.execute_query("UPDATE products SET stock_qty = stock_qty + ?, is_archived = 0 WHERE id = ?", (stock, existing['id']))
                    try:
                        self.db.execute_query("INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date) VALUES (?, ?, ?, ?)", (existing['id'], stock, stock, expiry))
                    except Exception as e:
                        print(f"[Inventory] product batch insert error: {e}")
                    self.db.execute_query(
                        "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                        ('retail', existing['id'], name, 'restocked', self.current_user))
                else:
                    return # I-cancel ang proseso
            else:
                # --- SAFE INSERT NA MAY ERROR CATCHER ---
                try:
                    self.db.execute_query(
                        "INSERT INTO products (name, retail_price, production_cost, stock_qty, unit, avg_daily_usage, expiry_date, is_archived, product_type) VALUES (?, ?, ?, ?, 'Pieces', 0, ?, 0, ?)",
                        (name, price, cost, stock, expiry, category))
                    prod_id = self.db.fetch_one("SELECT last_insert_rowid() as id")['id']
                    
                    # 🟢 IMAGE SAVING LOGIC PARA SA RETAIL
                    if getattr(self, 'selected_image_path', None):
                        try:
                            import os, shutil
                            images_dir = PRODUCT_IMAGES_DIR
                            if not os.path.exists(images_dir):
                                os.makedirs(images_dir)
                            
                            _, ext = os.path.splitext(self.selected_image_path)
                            new_filename = f"prod_{prod_id}{ext}"
                            final_path = os.path.join(images_dir, new_filename).replace("\\", "/")
                            
                            shutil.copy(self.selected_image_path, final_path)
                            self.db.execute_query("UPDATE products SET image_path = ? WHERE id = ?", (os.path.basename(final_path), prod_id))
                        except Exception as e:
                            print("Image save error:", e)

                    try:
                        self.db.execute_query("INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date, stocked_by) VALUES (?, ?, ?, ?, ?)", (prod_id, stock, stock, expiry, self.current_user))
                    except Exception as e:
                        print(f"[Inventory] product batch insert error: {e}")
                    self.db.execute_query(
                        "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                        ('retail', prod_id, name, 'added', self.current_user))
                except Exception as e:
                    # Kung makalusot pa rin at sumigaw ang database, sasaluhin natin dito!
                    if "UNIQUE constraint" in str(e):
                        BakeSyncAlert.show_error(self, "Conflict Detected", f"The item '{name}' is already in the database but could not be updated. Please try searching for it first.")
                        return
                    else:
                        print(f"Database error: {e}")
                        return
            
            # --- DISPOSE & SHOW SUCCESS ALERT ---
            info_details = {
                "Item Name": name.upper(),
                "Category": category,
                "Added Stock": f"{stock} pcs",
                "Selling Price": f"₱{price:,.0f}",
                "Unit Cost": f"₱{cost:,.0f}"
            }

            self.accept() # Isara muna ang window

            BakeSyncAlert.show_success(
                self.parent(), 
                "Retail Item Registered", 
                "The retail item has been successfully saved to the inventory.", 
                details=info_details
            )

        finally:
            # Laging i-release ang lock kahit magka-error man, para pwede ulit mag-click
            self._is_processing = False



class AddBreadDialog(_BaseDialog):
    """Same layout as Add Retail Item: image, name, cost & price, initial stock & expiry.
    Without a photo the product shows the default 'No image yet' picture in POS."""
    def __init__(self, db, parent=None, current_user=""):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.setWindowTitle("Add Bread Item")
        layout = self._build_wrapper(width=520)
        self._title_row("Add Bread Item", layout)

        ARROW_DOWN_PATH = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
        ARROW_UP_PATH   = os.path.join(IMAGES_DIR, "arrowup.png").replace("\\", "/")
        FIELD_STYLE = """
            QLineEdit, QDoubleSpinBox, QSpinBox { border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #0F172A; background-color: white; }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #693903; }
        """

        # ── Image (same as retail) ──
        self.selected_image_path = None
        self.lbl_img_preview = QLabel()
        self.lbl_img_preview.setFixedSize(100, 80)
        self.lbl_img_preview.setStyleSheet("border: 1px dashed #D1D5DB; border-radius: 5px; background-color: #F8FAFC;")
        self.lbl_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_preview.setPixmap(default_product_pixmap(100, 80, "bread"))
        self.btn_upload = QPushButton(" Select Image")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.setStyleSheet("QPushButton { background: #E8D5C4; color: #4A2C1C; border-radius: 4px; padding: 6px 12px; font-weight: bold; } QPushButton:hover { background: #D4BFA9; }")
        self.btn_upload.clicked.connect(self._choose_image)
        img_col = QVBoxLayout()
        lbl_img_title = QLabel("Product Image (For POS):"); lbl_img_title.setStyleSheet(LABEL_STYLE)
        img_row_inner = QHBoxLayout()
        img_row_inner.addWidget(self.lbl_img_preview)
        img_row_inner.addWidget(self.btn_upload)
        img_hint = QLabel("Optional. Without a photo, POS shows the default picture.")
        img_hint.setWordWrap(True)
        img_hint.setStyleSheet("font-size: 11px; color: #94A3B8; background: transparent; border: none;")
        img_row_inner.addWidget(img_hint, stretch=1)
        img_col.addWidget(lbl_img_title)
        img_col.addLayout(img_row_inner)
        layout.addLayout(img_col)

        # ── Row 1: Name ──
        col_name = QVBoxLayout(); col_name.setSpacing(6)
        lbl_name = QLabel("Bread Name:"); lbl_name.setStyleSheet(LABEL_STYLE)
        self.name_input = QLineEdit(); self.name_input.setFixedHeight(38); self.name_input.setStyleSheet(FIELD_STYLE)
        self.name_input.setPlaceholderText("e.g. Pandesal, Ensaymada, Tasty Bread")
        col_name.addWidget(lbl_name); col_name.addWidget(self.name_input)
        layout.addLayout(col_name)

        # ── Puhunan + Patong = Selling price (worked out for you) ──
        row2 = QHBoxLayout(); row2.setSpacing(16)
        self.cost_spin = QDoubleSpinBox(); self.patong_spin = QDoubleSpinBox()
        self.price_spin = QDoubleSpinBox(); self.price_spin.setRange(0, 199998); self.price_spin.setDecimals(2)
        for title, spin in (("Puhunan / cost per piece (₱):", self.cost_spin), ("Patong per piece (₱):", self.patong_spin)):
            col = QVBoxLayout(); col.setSpacing(6)
            lbl = QLabel(title); lbl.setStyleSheet(LABEL_STYLE)
            spin.setRange(0, 99999); spin.setDecimals(2); spin.setFixedHeight(38)
            spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            spin.setStyleSheet(FIELD_STYLE)
            col.addWidget(lbl); col.addWidget(spin)
            row2.addLayout(col)
        layout.addLayout(row2)
        self.price_preview = QLabel()
        self.price_preview.setStyleSheet("background: #F3F9F5; color: #2F7D4F; border: 1px solid #CBE7D5; border-radius: 8px; "
                                         "padding: 8px 12px; font-size: 13px;")
        layout.addWidget(self.price_preview)

        def _update_price(*_):
            price = round(self.cost_spin.value() + self.patong_spin.value(), 2)
            self.price_spin.setValue(price)
            self.price_preview.setText(f"Selling price: <b>₱{price:,.2f}</b>   ·   Tubo per piece: <b>₱{self.patong_spin.value():,.2f}</b>")
        self.cost_spin.valueChanged.connect(_update_price)
        self.patong_spin.valueChanged.connect(_update_price)
        _update_price()

        # ── Row 3: Initial stock & Expiry ──
        row3 = QHBoxLayout(); row3.setSpacing(16)
        col_stock = QVBoxLayout(); col_stock.setSpacing(6)
        lbl_stock = QLabel("Initial Stock (pcs baked, can be 0):"); lbl_stock.setStyleSheet(LABEL_STYLE)
        self.stock_spin = QSpinBox(); self.stock_spin.setRange(0, 99999); self.stock_spin.setFixedHeight(38)
        self.stock_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.stock_spin.setStyleSheet("border: none; padding: 8px 12px; font-size: 13px; color: #0F172A; background: transparent;")
        col_stock.addWidget(lbl_stock)
        col_stock.addWidget(_make_spin_container(self.stock_spin, ARROW_DOWN_PATH, ARROW_UP_PATH))
        row3.addLayout(col_stock)
        col_expiry = QVBoxLayout(); col_expiry.setSpacing(6)
        lbl_expiry = QLabel("Expiry Date:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        expiry_container, self.expiry_date = _make_expiry_row(self, QDate.currentDate().addDays(2).toString("yyyy-MM-dd"))
        col_expiry.addWidget(lbl_expiry); col_expiry.addWidget(expiry_container)
        row3.addLayout(col_expiry)
        layout.addLayout(row3)

        layout.addSpacing(8)
        btn = self._save_btn("Register Bread Item", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_bread)

    def _choose_image(self):
        from PyQt6.QtWidgets import QFileDialog
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilters(["Images (*.png *.jpg *.jpeg)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_image_path = selected_files[0]
                self.lbl_img_preview.setPixmap(QPixmap(self.selected_image_path).scaled(
                    100, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def save_bread(self):
        if getattr(self, '_is_processing', False):
            return
        self._is_processing = True
        try:
            name = self.name_input.text().strip()
            cost = self.cost_spin.value()
            price = self.price_spin.value()
            stock = self.stock_spin.value()
            expiry = self.expiry_date.text().strip() or QDate.currentDate().addDays(2).toString("yyyy-MM-dd")

            if not name:
                BakeSyncAlert.show_warning(self, "Empty Name", "Please enter a bread name.")
                return
            if price <= 0:
                BakeSyncAlert.show_warning(self, "No Price", "Please type the puhunan (cost) and the patong per piece.")
                return
            if price < cost and not BakeSyncAlert.ask_yes_no(
                    self, "Selling Below Cost",
                    f"The selling price (₱{price:,.2f}) is lower than the cost (₱{cost:,.2f}).\n\nSave anyway?"):
                return
            if stock > 0 and QDate.fromString(expiry, "yyyy-MM-dd") < QDate.currentDate():
                BakeSyncAlert.show_error(self, "Expired Date", "The expiry date is already in the past. Please pick today or a later date.")
                return

            existing = self.db.fetch_one("SELECT id, is_archived FROM products WHERE name COLLATE NOCASE = ?", (name,))
            if existing:
                if existing['is_archived']:
                    BakeSyncAlert.show_warning(self, "Archived Item",
                        f"'{name}' already exists but is archived. Restore it from the archive instead.")
                else:
                    BakeSyncAlert.show_warning(self, "Already Exists",
                        f"An item named '{name}' already exists. Use 'Add/Update Stock' to add more pieces.")
                return

            with self.db.transaction():
                self.db.execute_query(
                    "INSERT INTO products (name, retail_price, production_cost, stock_qty, unit, avg_daily_usage, is_archived, product_type) "
                    "VALUES (?, ?, ?, ?, 'Pieces', 0, 0, 'bread')",
                    (name, price, cost, stock))
                prod_id = self.db.fetch_one("SELECT last_insert_rowid() as id")['id']
                if stock > 0:
                    self.db.execute_query(
                        "INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date, stocked_by) VALUES (?, ?, ?, ?, ?)",
                        (prod_id, stock, stock, expiry, self.current_user))
                self.db.execute_query(
                    "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                    ('bread', prod_id, name, 'added', self.current_user))

            if self.selected_image_path:
                try:
                    import shutil
                    os.makedirs(PRODUCT_IMAGES_DIR, exist_ok=True)
                    new_filename = f"prod_{prod_id}{os.path.splitext(self.selected_image_path)[1]}"
                    shutil.copy(self.selected_image_path, os.path.join(PRODUCT_IMAGES_DIR, new_filename))
                    self.db.execute_query("UPDATE products SET image_path = ? WHERE id = ?", (new_filename, prod_id))
                except Exception as e:
                    print("Image save error:", e)

            self.accept()
            BakeSyncAlert.show_success(
                self.parent(), "Bread Item Registered",
                "The bread item has been successfully saved to the inventory.",
                details={"Bread Name": name.upper(), "Selling Price": f"₱{price:,.2f}",
                         "Cost per piece": f"₱{cost:,.2f}", "Initial Stock": f"{stock} pcs",
                         "Photo": "Uploaded" if self.selected_image_path else "Default picture"})
        finally:
            self._is_processing = False

class UpdateBreadStockDialog(_BaseDialog):
    """Log a freshly baked batch: adds pieces to stock with an expiry date."""
    def __init__(self, db, prod_id, parent=None, current_user=""):
        super().__init__(parent)
        self.db = db; self.prod_id = prod_id; self.current_user = current_user
        self.setWindowTitle("Add Bread Stock Batch")
        layout = self._build_wrapper(width=460)

        self.prod = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.prod_id,))
        if not self.prod: self.reject(); return

        # ── Title row ─────────────────────────────────────────────
        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 15)
        title = QLabel(f"Log Baked Batch: {self.prod['name']}")
        title.setStyleSheet("font-size: 16px; font-weight: normal; color: #0F172A;")
        title_row.addWidget(title); title_row.addStretch()
        cb = _close_btn(); cb.clicked.connect(self.reject); title_row.addWidget(cb)
        layout.addLayout(title_row)

        # ── Current stock (read-only) ─────────────────────────────
        lbl_current = QLabel("Current Stock:"); lbl_current.setStyleSheet(LABEL_STYLE)
        current_display = QLineEdit(str(int(self.prod['stock_qty'] or 0)))
        current_display.setReadOnly(True); current_display.setFixedHeight(38)
        current_display.setStyleSheet(
            "border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; "
            "font-size: 13px; color: #94A3B8; background-color: #F9FAFB;")
        layout.addWidget(lbl_current); layout.addWidget(current_display)

        # ── Quick-pick quantity buttons ───────────────────────────
        lbl_qty = QLabel("Quantity Baked (pieces):"); lbl_qty.setStyleSheet(LABEL_STYLE)
        layout.addWidget(lbl_qty)

        QUICK_PICKS = [20, 40, 60]
        BTN_BASE = ("QPushButton { border: 1px solid #D1D5DB; border-radius: 6px; "
                    "font-size: 14px; font-weight: bold; color: #693903; "
                    "background-color: white; padding: 6px 0px; }"
                    "QPushButton:hover { background-color: #F3E8DC; border-color: #693903; }")
        BTN_ACTIVE = ("QPushButton { border: 2px solid #693903; border-radius: 6px; "
                      "font-size: 14px; font-weight: bold; color: white; "
                      "background-color: #693903; padding: 6px 0px; }")

        quick_row = QHBoxLayout(); quick_row.setSpacing(8)
        self._quick_btns = []
        for val in QUICK_PICKS:
            b = QPushButton(f"{val} pcs")
            b.setFixedHeight(38); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(BTN_BASE)
            b.clicked.connect(lambda ch=False, v=val: self._set_qty(v))
            quick_row.addWidget(b)
            self._quick_btns.append((b, val))
        layout.addLayout(quick_row)

        # ── Custom quantity input ─────────────────────────────────
        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText("Or enter custom quantity...")
        self._custom_input.setFixedHeight(38)
        self._custom_input.setStyleSheet(
            "border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; "
            "font-size: 13px; color: #0F172A; background-color: white;")
        self._custom_input.textChanged.connect(self._on_custom_changed)
        layout.addWidget(self._custom_input)

        self._btn_base_style  = BTN_BASE
        self._btn_active_style = BTN_ACTIVE
        self._selected_qty = 0   # will be set when user picks

        # ── Expiry date ───────────────────────────────────────────
        lbl_expiry = QLabel("Batch Expiry Date:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        expiry_container, self.expiry_input = _make_expiry_row(
            self, QDate.currentDate().addDays(2).toString("yyyy-MM-dd"))
        layout.addWidget(lbl_expiry); layout.addWidget(expiry_container)

        note = QLabel("Bread batches expire in 2 days by default (from production).")
        note.setStyleSheet("font-size: 11px; color: #94A3B8; background: transparent; border: none;")
        note.setWordWrap(True); layout.addWidget(note)

        btn = self._save_btn("Add to Stock", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_batch)

    # ── Helpers ──────────────────────────────────────────────────────

    def _set_qty(self, value):
        """Called when a quick-pick button is pressed."""
        self._selected_qty = value
        self._custom_input.blockSignals(True)
        self._custom_input.clear()
        self._custom_input.blockSignals(False)
        for btn, v in self._quick_btns:
            btn.setStyleSheet(self._btn_active_style if v == value else self._btn_base_style)

    def _on_custom_changed(self, text):
        """Called when the user types in the custom input."""
        for btn, _ in self._quick_btns:
            btn.setStyleSheet(self._btn_base_style)   # deselect all quick-picks
        try:
            self._selected_qty = int(text)
        except ValueError:
            self._selected_qty = 0

    def save_batch(self):
        qty_baked = self._selected_qty
        expiry = self.expiry_input.text().strip() or QDate.currentDate().addDays(2).toString("yyyy-MM-dd")

        if qty_baked <= 0:
            BakeSyncAlert.show_warning(self, "No Quantity", "Please select 20, 40, 60 pcs or enter a custom quantity before saving.")
            return

        # Stock at batch ay sabay na mase-save (all-or-nothing)
        with self.db.transaction():
            self.db.execute_query("UPDATE products SET stock_qty = COALESCE(stock_qty, 0) + ? WHERE id = ?", (qty_baked, self.prod_id))
            self.db.execute_query(
                "INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date, stocked_by) VALUES (?, ?, ?, ?, ?)",
                (self.prod_id, qty_baked, qty_baked, expiry, self.current_user))

        info_details = {
            "Product Baked": self.prod['name'].upper(),
            "Quantity Added": f"{qty_baked} pcs",
            "Batch Expiry": expiry,
        }

        self.accept() # Close the form first

        BakeSyncAlert.show_success(
            self.parent(),
            "Stock Added",
            f"{qty_baked} pcs of {self.prod['name']} added to stock.",
            details=info_details
        )


class BulkBreadStockDialog(_BaseDialog):
    """Add today's baked pieces for many breads at once: one box per bread, one Save."""
    def __init__(self, db, parent=None, current_user=""):
        super().__init__(parent)
        self.db = db
        self.current_user = current_user
        self.setWindowTitle("Add Bread Stock")
        layout = self._build_wrapper(width=560)
        self._title_row("Add Bread Stock", layout)

        hint = QLabel("Enter how many pieces came out of the oven. Leave 0 for bread you did not bake.")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 12px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(hint)

        self.breads = self.db.fetch_all(
            "SELECT id, name, COALESCE(stock_qty, 0) AS stock FROM products "
            "WHERE product_type = 'bread' AND is_archived = 0 ORDER BY name")
        self.table = QTableWidget(len(self.breads), 3)
        self.table.setHorizontalHeaderLabels(["Bread", "Current stock", "Add (pcs)"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setMinimumHeight(min(60 + 46 * len(self.breads), 380))
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; color: #0F172A; background: white; }
            QHeaderView::section { background-color: #693903; color: white; font-size: 12px; padding: 8px; border: none; }
            QTableWidget::item { padding: 4px 8px; border-bottom: 1px solid #F3F4F6; }
        """)
        self.spins = []
        for r, b in enumerate(self.breads):
            name = QTableWidgetItem(b['name'])
            cur = QTableWidgetItem(f"{b['stock']:g}"); cur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 0, name); self.table.setItem(r, 1, cur)
            spin = QSpinBox()
            spin.setRange(0, 9999)
            spin.setFixedSize(110, 34)
            spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setStyleSheet("QSpinBox { border: 1px solid #D1D5DB; border-radius: 6px; font-size: 14px; font-weight: bold; "
                               "color: #0F172A; background: white; } QSpinBox:focus { border: 1.5px solid #693903; }")
            box = QWidget(); bl = QHBoxLayout(box); bl.setContentsMargins(6, 4, 6, 4); bl.addWidget(spin)
            self.table.setCellWidget(r, 2, box)
            self.table.setRowHeight(r, 46)
            self.spins.append(spin)
        layout.addWidget(self.table)

        lbl_expiry = QLabel("Expiry date of the new batch:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        expiry_container, self.expiry_input = _make_expiry_row(
            self, QDate.currentDate().addDays(2).toString("yyyy-MM-dd"))
        layout.addWidget(lbl_expiry); layout.addWidget(expiry_container)

        btn = self._save_btn("Save All", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_all)
        if self.spins:
            self.spins[0].setFocus()

    def save_all(self):
        entries = [(b, s.value()) for b, s in zip(self.breads, self.spins) if s.value() > 0]
        if not entries:
            BakeSyncAlert.show_warning(self, "Nothing entered", "Enter a number for at least one bread.")
            return
        expiry = self.expiry_input.text().strip() or QDate.currentDate().addDays(2).toString("yyyy-MM-dd")
        if QDate.fromString(expiry, "yyyy-MM-dd") <= QDate.currentDate():
            BakeSyncAlert.show_error(self, "Wrong expiry date", "The expiry date must be tomorrow or later.")
            return
        with self.db.transaction():
            for b, qty in entries:
                self.db.execute_query("UPDATE products SET stock_qty = COALESCE(stock_qty, 0) + ? WHERE id = ?", (qty, b['id']))
                self.db.execute_query(
                    "INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date, stocked_by) VALUES (?, ?, ?, ?, ?)",
                    (b['id'], qty, qty, expiry, self.current_user))
                self.db.execute_query(
                    "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
                    ('bread', b['id'], b['name'], 'restocked', self.current_user))
        self.accept()
        BakeSyncAlert.show_success(
            self.parent(), "Stock Added",
            f"Stock added for {len(entries)} bread items ({sum(q for _, q in entries):g} pcs).",
            details={b['name']: f"+{q:g} pcs" for b, q in entries})


class UpdateRetailBatchDialog(_BaseDialog):
    def __init__(self, db, prod_id, parent=None, current_user=""):
        super().__init__(parent)
        self.db = db; self.prod_id = prod_id; self.current_user = current_user
        self.setWindowTitle("Add Retail Stock Batch")
        layout = self._build_wrapper(width=350)

        self.prod = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.prod_id,))
        if not self.prod: self.reject(); return

        ARROW_DOWN_PATH = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
        ARROW_UP_PATH   = os.path.join(IMAGES_DIR, "arrowup.png").replace("\\", "/")

        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 15)
        title = QLabel(f"Add Retail Batch: {self.prod['name']}"); title.setStyleSheet("font-size: 16px; font-weight: normal; color: #0F172A;")
        title_row.addWidget(title); title_row.addStretch()
        cb = _close_btn(); cb.clicked.connect(self.reject); title_row.addWidget(cb)
        layout.addLayout(title_row)

        lbl_current = QLabel("Current Stock:"); lbl_current.setStyleSheet(LABEL_STYLE)
        current_display = QLineEdit(str(int(self.prod['stock_qty'] or 0))); current_display.setReadOnly(True); current_display.setFixedHeight(38)
        current_display.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #94A3B8; background-color: #F9FAFB;")
        layout.addWidget(lbl_current); layout.addWidget(current_display)

        lbl_qty = QLabel("Quantity to Add:"); lbl_qty.setStyleSheet(LABEL_STYLE)
        self.qty_spin = QSpinBox(); self.qty_spin.setRange(1, 99999); self.qty_spin.setFixedHeight(38)
        self.qty_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.qty_spin.setStyleSheet("border: none; padding: 8px 12px; font-size: 13px; color: #0F172A; background: transparent;")
        layout.addWidget(lbl_qty)
        layout.addWidget(_make_spin_container(self.qty_spin, ARROW_DOWN_PATH, ARROW_UP_PATH))

        lbl_expiry = QLabel("Batch Expiry Date:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        expiry_container, self.expiry_input = _make_expiry_row(self)
        layout.addWidget(lbl_expiry); layout.addWidget(expiry_container)

        btn = self._save_btn("Save Retail Batch", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_batch)

    def save_batch(self):
        qty = self.qty_spin.value()
        expiry = self.expiry_input.text().strip() or QDate.currentDate().addMonths(6).toString("yyyy-MM-dd")
        self.db.execute_query("UPDATE products SET stock_qty = COALESCE(stock_qty, 0) + ? WHERE id = ?", (qty, self.prod_id))
        try:
            self.db.execute_query("INSERT INTO product_batches (product_id, quantity_remaining, initial_qty, expiry_date, stocked_by) VALUES (?, ?, ?, ?, ?)", (self.prod_id, qty, qty, expiry, self.current_user))
        except Exception as e:
            print(f"[Inventory] product batch insert error: {e}")
        self.accept()


class EditRetailDialog(_BaseDialog):
    def __init__(self, db, prod_id, parent=None):
        super().__init__(parent)
        self.db = db; self.prod_id = prod_id
        self.setWindowTitle("Edit Retail Item")
        # 🟢 Pinalaki natin ang width from 350 to 450 para kasya ang mga buttons!
        layout = self._build_wrapper(width=450) 
        self._title_row("Edit Retail Item", layout)

        self.prod = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.prod_id,))
        if not self.prod: self.reject(); return

        # ==========================================
        # 🟢 IMAGE UPLOAD UI SECTION
        # ==========================================
        self.selected_image_path = None
        row_img = QHBoxLayout(); row_img.setSpacing(16)
        
        self.lbl_img_preview = QLabel()
        self.lbl_img_preview.setFixedSize(100, 80)
        self.lbl_img_preview.setStyleSheet("border: 1px dashed #D1D5DB; border-radius: 5px; background-color: #F8FAFC;")
        self.lbl_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_preview.setScaledContents(True)

        import os
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#F9FAFB" stroke="#D1D5DB" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>"""
        
        # I-load ang existing image kung meron sa database
        if 'image_path' in self.prod.keys() and product_image(self.prod['image_path']):
            self.lbl_img_preview.setPixmap(QPixmap(product_image(self.prod['image_path'])))
        else:
            self.lbl_img_preview.setScaledContents(False)
            self.lbl_img_preview.setPixmap(default_product_pixmap(100, 80, "retail"))

        self.btn_upload = QPushButton("Change Image")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.setStyleSheet("QPushButton { background: #E8D5C4; color: #4A2C1C; border-radius: 4px; padding: 5px 10px; font-weight: bold; } QPushButton:hover { background: #D4BFA9; }")
        self.btn_upload.clicked.connect(self._choose_image)

        self.btn_remove = QPushButton("Remove Image")
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.setStyleSheet("QPushButton { background: #FBE9E9; color: #DC2626; border-radius: 4px; padding: 5px 10px; font-weight: bold; } QPushButton:hover { background: #FCA5A5; }")
        self.btn_remove.clicked.connect(self._remove_image)

        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(5)
        btn_vbox.addWidget(self.btn_upload)
        btn_vbox.addWidget(self.btn_remove)

        img_col = QVBoxLayout()
        lbl_img_title = QLabel("Product Image (For POS):"); lbl_img_title.setStyleSheet(LABEL_STYLE)
        
        img_row_inner = QHBoxLayout()
        img_row_inner.addWidget(self.lbl_img_preview)
        img_row_inner.addLayout(btn_vbox)
        img_row_inner.addStretch()
        
        img_col.addWidget(lbl_img_title)
        img_col.addLayout(img_row_inner)
        row_img.addLayout(img_col)
        
        layout.addLayout(row_img)

        # ==========================================
        # 🟢 EXISTING RETAIL FIELDS
        # ==========================================
        FIELD_STYLE = """
            QLineEdit { border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #0F172A; background-color: white; }
            QLineEdit:focus { border: 1px solid #693903; }
        """
        lbl_name = QLabel("Item Name:"); lbl_name.setStyleSheet(LABEL_STYLE)
        self.name_input = QLineEdit(self.prod['name']); self.name_input.setFixedHeight(38); self.name_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(lbl_name); layout.addWidget(self.name_input)

        lbl_expiry = QLabel("Expiry Date:"); lbl_expiry.setStyleSheet(LABEL_STYLE)
        existing = QDate.fromString(str(self.prod['expiry_date']), "yyyy-MM-dd") if self.prod['expiry_date'] else QDate.currentDate().addMonths(6)
        expiry_container, self.expiry_date = _make_expiry_row(self, existing.toString("yyyy-MM-dd"))
        layout.addWidget(lbl_expiry); layout.addWidget(expiry_container)

        layout.addSpacing(8)
        btn = self._save_btn("Save Changes", "#693903", "#693903", "#452803", layout)
        btn.clicked.connect(self.save_changes)

    # ──────────────────────────────────────────
    #  SMART IMAGE BUTTONS (With Alerts)
    # ──────────────────────────────────────────
    def _choose_image(self):
        from bakesync.widgets.custom_alerts import BakeSyncAlert
        import os
        
        has_image = False
        if getattr(self, 'selected_image_path', None) not in [None, "REMOVE"]:
            has_image = True 
        elif getattr(self, 'selected_image_path', None) != "REMOVE":
            if 'image_path' in self.prod.keys() and product_image(self.prod['image_path']):
                has_image = True

        if has_image:
            if not BakeSyncAlert.ask_yes_no(
                self.window(),
                "Change Image?",
                "Are you sure you want to change the current retail item image?",
                yes_text="YES, CHANGE IT",
                no_text="CANCEL"
            ):
                return
        else:
            if not BakeSyncAlert.ask_yes_no(
                self.window(),
                "No Image Found",
                "This item has no photo yet (it uses the default icon). Do you want to choose a photo now?",
                yes_text="PROCEED",
                no_text="CANCEL"
            ):
                return

        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilters(["Images (*.png *.jpg *.jpeg)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_image_path = selected_files[0]
                self.lbl_img_preview.setPixmap(QPixmap(self.selected_image_path))
                self.lbl_img_preview.setText("")
                
                BakeSyncAlert.show_success(
                    self.window(), 
                    "Image Selected", 
                    "Successfully loaded the new image! Click 'Save Changes' to apply."
                )

    def _remove_image(self):
        from bakesync.widgets.custom_alerts import BakeSyncAlert
        import os
        
        has_image = False
        if getattr(self, 'selected_image_path', None) not in [None, "REMOVE"]:
            has_image = True
        elif getattr(self, 'selected_image_path', None) != "REMOVE":
            if 'image_path' in self.prod.keys() and product_image(self.prod['image_path']):
                has_image = True

        if not has_image:
            if BakeSyncAlert.ask_yes_no(
                self.window(),
                "Cannot Remove",
                "This item already uses the default icon, so there is nothing to remove. Do you want to add a photo instead?",
                yes_text="YES, ADD IMAGE",
                no_text="CANCEL"
            ):
                self._choose_image()
            return

        if not BakeSyncAlert.ask_yes_no(
            self.window(),
            "Remove Image?",
            "Are you sure you want to remove this photo? The item will use the default icon.",
            yes_text="YES, REMOVE IT",
            no_text="CANCEL"
        ):
            return

        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        
        self.selected_image_path = "REMOVE"
        
        self.lbl_img_preview.setScaledContents(False)
        self.lbl_img_preview.setPixmap(default_product_pixmap(100, 80, "retail"))
        
        BakeSyncAlert.show_success(
            self.window(), 
            "Image Removed", 
            "The image has been cleared. Click 'Save Changes' to apply."
        )

    # ──────────────────────────────────────────
    #  SAVING DATA
    # ──────────────────────────────────────────
    def save_changes(self):
        name = self.name_input.text()
        if name:
            self.db.execute_query("UPDATE products SET name = ?, expiry_date = ? WHERE id = ?",
                                  (name, self.expiry_date.text(), self.prod_id))
            
            # 🟢 IMAGE SAVING LOGIC PARA SA RETAIL EDIT
            if getattr(self, 'selected_image_path', None):
                if self.selected_image_path == "REMOVE":
                    self.db.execute_query("UPDATE products SET image_path = NULL WHERE id = ?", (self.prod_id,))
                else:
                    try:
                        import os, shutil
                        images_dir = PRODUCT_IMAGES_DIR
                        if not os.path.exists(images_dir):
                            os.makedirs(images_dir)
                        
                        _, ext = os.path.splitext(self.selected_image_path)
                        new_filename = f"prod_{self.prod_id}{ext}"
                        final_path = os.path.join(images_dir, new_filename).replace("\\", "/")
                        
                        shutil.copy(self.selected_image_path, final_path)
                        self.db.execute_query("UPDATE products SET image_path = ? WHERE id = ?", (os.path.basename(final_path), self.prod_id))
                    except Exception as e:
                        print("Image save error:", e)

            self.accept()

class ProductSummaryDialog(QDialog):
    """Opened by clicking a row: the product at a glance, with its actions as small
    buttons at the top right (Add stock, Edit / Price, Archive)."""

    def __init__(self, db, prod_id, current_user="", parent=None):
        super().__init__(parent)
        from bakesync.widgets.ui import THEME as T, card as ui_card, icon_label, chip, button as ui_button, svg_icon, InfoIcon
        self.db, self.prod_id, self.current_user = db, prod_id, current_user
        self.changed = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(680)
        p = db.fetch_one("SELECT * FROM products WHERE id = ?", (prod_id,))
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        box = ui_card(16, name="ps")
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
        box.setGraphicsEffect(sh)
        outer.addWidget(box)
        lay = QVBoxLayout(box); lay.setContentsMargins(22, 18, 18, 18); lay.setSpacing(12)
        if not p:
            lay.addWidget(QLabel("This product could not be found."))
            return
        p = dict(p)
        self.is_bread = p["product_type"] == "bread"
        self.name = p["name"]
        today = _date.today().isoformat()
        exp = db.fetch_one("SELECT COALESCE(SUM(quantity_remaining),0) AS q FROM product_batches WHERE product_id = ? "
                           "AND quantity_remaining > 0 AND expiry_date <= ?", (prod_id, today))["q"]
        usable = max(0, (p["stock_qty"] or 0) - (exp or 0))
        sold_today = db.fetch_one("SELECT COALESCE(SUM(quantity),0) FROM sales WHERE product_id = ? AND COALESCE(is_voided,0) = 0 "
                                  "AND date(created_at) = date('now','localtime')", (prod_id,))[0]
        sold_7 = db.fetch_one("SELECT COALESCE(SUM(quantity),0) FROM sales WHERE product_id = ? AND COALESCE(is_voided,0) = 0 "
                              "AND date(created_at) > date('now','localtime','-7 days')", (prod_id,))[0]
        nxt = db.fetch_one("SELECT MIN(expiry_date) FROM product_batches WHERE product_id = ? AND quantity_remaining > 0 "
                           "AND expiry_date > ?", (prod_id, today))[0]

        # header: icon, name, chips | small actions on the right
        head = QHBoxLayout(); head.setSpacing(12)
        head.addWidget(icon_label("bread" if self.is_bread else "bag", T["brown"], 22, bg=T["cream_dark"], box=46, radius=12),
                       alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout(); col.setSpacing(4)
        n = QLabel(self.name); n.setStyleSheet(f"color: {T['text']}; font-size: 18px; font-weight: bold;")
        col.addWidget(n)
        chips = QHBoxLayout(); chips.setSpacing(6)
        chips.addWidget(chip("Bread" if self.is_bread else (p["product_type"] or "Retail").title(), T["brown"], T["cream_dark"]))
        low = 10 if self.is_bread else 5
        st = ("Out of stock", T["red"], T["red_bg"]) if usable <= 0 else (("Low", T["amber"], T["amber_bg"]) if usable < low
                                                                       else ("In stock", T["green"], T["green_bg"]))
        chips.addWidget(chip(*st)); chips.addStretch()
        col.addLayout(chips)
        head.addLayout(col, 1)
        acts = QHBoxLayout(); acts.setSpacing(6)
        for text, icon, kind, slot in (("Add stock", "plus", "primary", self._add_stock),
                                       ("Edit" if not self.is_bread else "Price", "edit" if not self.is_bread else "tag", "secondary", self._edit),
                                       ("Archive", "trash", "danger", self._archive)):
            b = ui_button(text, kind, icon=icon, h=34)
            b.clicked.connect(slot)
            acts.addWidget(b)
        x = QPushButton(); x.setIcon(svg_icon("x", T["mid"], 18)); x.setFixedSize(34, 34); x.setToolTip("Close (Esc)")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setStyleSheet(f"QPushButton {{ border: none; border-radius: 17px; background: transparent; }} QPushButton:hover {{ background: {T['cream_dark']}; }}")
        x.clicked.connect(self.reject)
        acts.addWidget(x)
        head.addLayout(acts)
        lay.addLayout(head)

        # four numbers
        stats = QHBoxLayout(); stats.setSpacing(8)
        last = "—"
        if nxt:
            ld = _date.fromisoformat(nxt[:10]) - _timedelta(days=1)
            last = "Today" if ld <= _date.today() else ("Tomorrow" if ld == _date.today() + _timedelta(days=1) else ld.strftime("%b %d"))
        for label, value, info in (("Ready to sell", f"{usable:g} pcs", "Pieces you can still sell (expired pieces are not counted)."),
                                   ("Sold today", f"{sold_today:g} pcs", "Pieces sold at the POS today."),
                                   ("Sold a day", f"{sold_7 / 7:.1f} pcs", "Average pieces sold per day over the last 7 days."),
                                   ("Sell by", last, "The last day the oldest pieces can be sold.")):
            b = QFrame(); b.setObjectName("sb")
            b.setStyleSheet(f"QFrame#sb {{ background: {T['cream']}; border-radius: 10px; }}")
            bl = QVBoxLayout(b); bl.setContentsMargins(12, 8, 6, 8); bl.setSpacing(0)
            tr = QHBoxLayout(); tl = QLabel(label); tl.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
            tr.addWidget(tl); tr.addStretch(); tr.addWidget(InfoIcon(info, label, size=13))
            v = QLabel(value); v.setStyleSheet(f"color: {T['text']}; font-size: 17px; font-weight: bold;")
            bl.addLayout(tr); bl.addWidget(v)
            stats.addWidget(b)
        lay.addLayout(stats)
        pr = QLabel(f"Puhunan ₱{(p['production_cost'] or 0):,.2f}   ·   Selling price ₱{(p['retail_price'] or 0):,.2f}   ·   "
                    f"Tubo ₱{(p['retail_price'] or 0) - (p['production_cost'] or 0):,.2f} per piece")
        pr.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")
        lay.addWidget(pr)

        # batches
        bt = QLabel("Stock batches (oldest first)"); bt.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: bold;")
        lay.addWidget(bt)
        rows = db.fetch_all("SELECT received_date, quantity_remaining, initial_qty, expiry_date, stocked_by FROM product_batches "
                            "WHERE product_id = ? AND quantity_remaining > 0 ORDER BY expiry_date LIMIT 8", (prod_id,))
        tbl = QTableWidget(len(rows), 4)
        tbl.setHorizontalHeaderLabels(["Added on", "Pieces left", "Sell by", "Added by"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False); tbl.setShowGrid(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setStyleSheet(f"QTableWidget {{ border: 1px solid {T['line']}; border-radius: 8px; font-size: 12px; color: {T['text']}; }}"
                          f"QHeaderView::section {{ background: {T['cream_dark']}; color: {T['brown']}; border: none; padding: 6px; font-weight: bold; }}")
        for i, r in enumerate(rows):
            sell = "—"
            if r["expiry_date"]:
                ld = _date.fromisoformat(r["expiry_date"][:10]) - _timedelta(days=1)
                sell = "Expired" if ld < _date.today() else ("Today" if ld == _date.today() else ld.strftime("%b %d"))
            vals = [str(r["received_date"] or "")[:10] or "—", f"{r['quantity_remaining']:g}", sell, r["stocked_by"] or "—"]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 2 and v in ("Expired", "Today"):
                    it.setForeground(QBrush(QColor(T["red"])))
                tbl.setItem(i, c, it)
        if not rows:
            tbl.setRowCount(1); tbl.setSpan(0, 0, 1, 4)
            it = QTableWidgetItem("No stock right now. Click 'Add stock'."); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setForeground(QBrush(QColor(T["muted"]))); tbl.setItem(0, 0, it)
        tbl.setFixedHeight(min(230, 34 + 30 * max(1, len(rows))))
        lay.addWidget(tbl)

    def showEvent(self, e):
        super().showEvent(e)
        from PyQt6.QtWidgets import QApplication
        g = QApplication.primaryScreen().availableGeometry()
        self.move(g.center().x() - self.width() // 2, g.center().y() - self.height() // 2)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)

    def _done(self):
        self.changed = True
        self.accept()

    def _add_stock(self):
        dlg = (UpdateBreadStockDialog if self.is_bread else UpdateRetailBatchDialog)(self.db, self.prod_id, current_user=self.current_user)
        if dlg.exec():
            self._done()

    def _edit(self):
        if self.is_bread:
            from bakesync.modules.recipe import EditPriceDialog
            if EditPriceDialog(self.db, self.prod_id, current_user=self.current_user, item_type="bread", parent=self).exec():
                self._done()
        elif EditRetailDialog(self.db, self.prod_id).exec():
            self._done()

    def _archive(self):
        from bakesync.widgets.custom_alerts import BakeSyncAlert
        if not BakeSyncAlert.ask_yes_no(self, "Archive this item?",
                                        f"'{self.name}' will be hidden from Inventory and the POS.\n"
                                        "You can bring it back from 'Archived Items'.", yes_text="ARCHIVE", no_text="CANCEL"):
            return
        self.db.execute_query("UPDATE products SET is_archived = 1 WHERE id = ?", (self.prod_id,))
        self.db.execute_query(
            "INSERT INTO inventory_action_log (item_type, item_id, item_name, action, action_by) VALUES (?,?,?,?,?)",
            ("bread" if self.is_bread else "retail", self.prod_id, self.name, "archived", self.current_user))
        self._done()


class _BaseSummaryDialog(_BaseDialog):
    def _build_summary_wrapper(self, min_w, min_h):
        from PyQt6.QtGui import QPainter, QPainterPath, QPen
        from PyQt6.QtCore import QRectF

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(min_w, min_h)
        self.setStyleSheet("QDialog { background-color: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        class RoundedFrame(QFrame):
            def paintEvent(self, event):
                from PyQt6.QtGui import QPainter, QPainterPath, QColor as _QColor
                from PyQt6.QtCore import QRectF
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(QRectF(self.rect()), 7, 7)
                painter.setClipPath(path)
                painter.fillPath(path, _QColor("white"))
                from PyQt6.QtGui import QPen
                painter.setPen(QPen(_QColor("#000000"), 1))
                painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)

        wrapper = RoundedFrame()
        wrapper.setStyleSheet("QFrame { background-color: white; border: none; border-radius: 7px; }")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer.addWidget(wrapper)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(12)
        return layout

    def _tab_icon(self, icon_name):
        # 🟢 TRUE VECTOR SVG CODES PARA SA MGA TABS
        SVGS = {
            "overview.png": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            """,
            "queue.png": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 12 12 17 22 12"></polyline>
                <polyline points="2 17 12 22 22 17"></polyline>
            </svg>
            """,
            "expired.png": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            """,
            "connected.png": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
            """,
            "timeline.png": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            """
        }
        
        # Kukunin yung SVG string base sa lumang "image_name" para di mo na baguhin ang ibang code
        svg_string = SVGS.get(icon_name, SVGS["overview.png"])
        
        # Iko-convert ang SVG code sa totoong Icon gamit ang method na inadd natin kanina
        return self._create_vector_icon(svg_string, "#693903")

    def _std_table(self, columns):
        t = QTableWidget()
        t.setColumnCount(len(columns))
        t.setHorizontalHeaderLabels(columns)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(True)
        t.setFrameShape(QTableWidget.Shape.NoFrame)
        t.setStyleSheet(TABLE_STYLE_SUMMARY)
        return t

    def _color_row(self, item, value_str):
        v = value_str.upper()
        if "EXPIRED" in v or "OUT OF STOCK" in v:
            item.setForeground(QBrush(QColor("#841717"))); item.setBackground(QColor("#FEE2E2"))
        elif "LOW STOCK" in v or "EXPIRES IN" in v or "LOCKED" in v:
            item.setForeground(QBrush(QColor("#704406"))); item.setBackground(QColor("#FEF9C3"))
        elif "GOOD" in v or "FRESH" in v or "ALL STOCK" in v:
            item.setForeground(QBrush(QColor("#065F46"))); item.setBackground(QColor("#D1FAE5"))
        elif "HIGH STOCK" in v:
            item.setForeground(QBrush(QColor("#10602D"))); item.setBackground(QColor("#DCFCE7"))

    def _close_footer(self, layout):
        btn = QPushButton("Close"); btn.clicked.connect(self.close)
        btn.setFixedHeight(36)
        btn.setStyleSheet("QPushButton { background-color: white; color: black; border: 1px solid; font-size: 13px; padding: 4px 24px; } QPushButton:hover { background-color: #E2E8F0; }")
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _tabs_widget(self):
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.tabBar().setExpanding(True)
        tabs.setStyleSheet(TAB_STYLE)
        tabs.setIconSize(QSize(16, 16))
        tabs.setContentsMargins(0, 0, 0, 0)
        return tabs


class BeverageSummaryDialog(_BaseSummaryDialog):
    def __init__(self, db, prod_id):
        super().__init__()
        self.db = db; self.prod_id = prod_id
        self.setWindowTitle("Beverage Comprehensive Intelligence")
        layout = self._build_summary_wrapper(720, 520)
        self._build(layout)

    def _build(self, layout):
        prod = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.prod_id,))
        if not prod: self.reject(); return
        today = QDate.currentDate()
        stock = prod['stock_qty'] if prod['stock_qty'] is not None else 0
        unit  = prod['unit'] if prod['unit'] else "pcs"
        usage = prod['avg_daily_usage'] if prod['avg_daily_usage'] else 0
        try:
            er = self.db.fetch_one(
                "SELECT COALESCE(SUM(quantity_remaining), 0) AS expired_qty FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND expiry_date IS NOT NULL AND expiry_date <= date('now', 'localtime')",
                (self.prod_id,))
            bev_expired_qty = er['expired_qty'] if er else 0
        except Exception:
            bev_expired_qty = 0
        usable_stock = max(0, stock - bev_expired_qty)
        expiry_str = str(prod['expiry_date']) if prod['expiry_date'] else "N/A"
        expiry_date = QDate.fromString(expiry_str, "yyyy-MM-dd")
        is_expired = expiry_date.isValid() and expiry_date <= today
        days_left  = today.daysTo(expiry_date) if expiry_date.isValid() else None
        days_stock = int(usable_stock / usage) if usage > 0 else None
        retail_price    = prod['retail_price'] if prod['retail_price'] else 0.0
        production_cost = prod['production_cost'] if prod['production_cost'] else 0.0
        margin = ((retail_price - production_cost) / retail_price * 100) if retail_price > 0 else 0.0

        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 8)
        
        # 🟢 VECTOR SVG PARA SA RETAIL (SHOPPING BAG)
        RETAIL_SVG = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <path d="M16 10a4 4 0 0 1-8 0"></path>
        </svg>
        """
        title_icon = QLabel()
        title_icon.setPixmap(self._create_vector_icon(RETAIL_SVG, "#693903").pixmap(QSize(22, 22)))
        title_icon.setFixedSize(24, 24)
        tl = QLabel(f"{prod['name']}")
        tl.setStyleSheet("font-size: 20px; font-weight: normal; color: #0F172A;")
        title_row.addWidget(title_icon)
        title_row.addWidget(tl)
        title_row.addStretch()
        sc = "#B91C1C" if usable_stock <= 0 else "#065F46"
        sb = QLabel(f"Usable Stock: {usable_stock:g} {unit}"); sb.setStyleSheet(f"color: {sc}; font-size: 14px;")
        title_row.addWidget(sb)
        if bev_expired_qty > 0:
            eb = QLabel(f"  ⚠ {bev_expired_qty:g} expired")
            eb.setStyleSheet("background-color: #FEE2E2; color: #B91C1C; font-size: 12px; font-weight: bold; padding: 3px 8px; border-radius: 4px;")
            title_row.addWidget(eb)
        cb = _close_btn(); cb.clicked.connect(self.reject); title_row.addWidget(cb)
        layout.addLayout(title_row)

        tabs = self._tabs_widget()

        rows_data = [
            ("Item Name",          prod['name']),
            ("Unit",               unit),
            ("Current Stock",      f"{stock:g} {unit}"),
            ("Usable Stock",       f"{usable_stock:g} {unit}"),
            ("Expired (cannot be sold)", f"{bev_expired_qty:g} {unit}" if bev_expired_qty > 0 else "None"),
            ("Avg Daily Sales",    f"{usage:g} {unit}/day" if usage > 0 else "Not set"),
            ("Days of Stock Left", f"{days_stock} days" if days_stock is not None else "N/A"),
            ("Expiry Date",        expiry_str),
            ("Expiry Status",      "EXPIRED" if is_expired else (f"Expires in {days_left} day(s)" if days_left is not None and days_left <= 7 else "GOOD")),
            ("Retail Price",       f"₱{retail_price:,.2f}" if retail_price else "Not set"),
            ("Production Cost",    f"₱{production_cost:,.2f}" if production_cost else "Not set"),
            ("Profit Margin",      f"{margin:.1f}%" if retail_price > 0 else "N/A"),
        ]
        ov_tab = QWidget(); ov_layout = QVBoxLayout(ov_tab); ov_layout.setContentsMargins(0, 0, 0, 0)
        t = self._std_table(["Field", "Value"])
        t.setRowCount(len(rows_data))
        for r, (field, value) in enumerate(rows_data):
            fi = QTableWidgetItem(field); fi.setTextAlignment(Qt.AlignmentFlag.AlignCenter); fi.setBackground(QColor("#F8FAFC"))
            vi = QTableWidgetItem(str(value)); vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._color_row(vi, str(value))
            t.setItem(r, 0, fi); t.setItem(r, 1, vi); t.setRowHeight(r, 36)
        ov_layout.addWidget(t); 
        tabs.addTab(ov_tab, "  Product Overview")
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("overview.png"))


        # ── Active Batches tab (with Stocked By) ────────────────────
        batch_tab = QWidget(); batch_layout = QVBoxLayout(batch_tab); batch_layout.setContentsMargins(0, 0, 0, 0)
        bt = self._std_table(["Batch Date", "Expiry Date", "Qty Remaining", "Stocked By", "Status"])
        try:
            active_batches = self.db.fetch_all(
                "SELECT received_date, expiry_date, quantity_remaining, stocked_by FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND (expiry_date IS NULL OR expiry_date > date('now', 'localtime')) ORDER BY expiry_date ASC",
                (self.prod_id,))
        except Exception:
            active_batches = []
        bt.setRowCount(len(active_batches) if active_batches else 1)
        if active_batches:
            for r, b in enumerate(active_batches):
                exp = QDate.fromString(str(b['expiry_date']), "yyyy-MM-dd")
                dlb = today.daysTo(exp) if exp.isValid() else None
                status = "USE SOON" if dlb is not None and dlb <= 7 else "FRESH"
                stocked_by_val = b['stocked_by'] if b['stocked_by'] else "—"
                for col, val in enumerate([str(b['received_date'])[:10] if b['received_date'] else "N/A",
                                           str(b['expiry_date']) if b['expiry_date'] else "N/A",
                                           f"{b['quantity_remaining']:g} {unit}", stocked_by_val, status]):
                    cell = QTableWidgetItem(val); cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if status == "USE SOON":
                        cell.setBackground(QColor("#FEF9C3")); cell.setForeground(QBrush(QColor("#704406")))
                    else:
                        cell.setBackground(QColor("#D1FAE5")); cell.setForeground(QBrush(QColor("#065F46")))
                    bt.setItem(r, col, cell); bt.setRowHeight(r, 36)
        else:
            nr = QTableWidgetItem("No active batches"); nr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            nr.setForeground(QBrush(QColor("#94A3B8"))); bt.setItem(0, 0, nr); bt.setSpan(0, 0, 1, 5)
        batch_layout.addWidget(bt)
        tabs.addTab(batch_tab, "  Batches (oldest first)")
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("queue.png"))

        # ── Expired Batches tab ──────────────────────────────────────
        expired_tab = QWidget(); expired_layout = QVBoxLayout(expired_tab); expired_layout.setContentsMargins(0, 0, 0, 0)
        try:
            expired_batches_retail = self.db.fetch_all(
                "SELECT received_date, expiry_date, quantity_remaining, stocked_by FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND expiry_date IS NOT NULL AND expiry_date <= date('now', 'localtime') ORDER BY expiry_date DESC",
                (self.prod_id,))
        except Exception:
            expired_batches_retail = []
        if expired_batches_retail:
            wl = QLabel(f"These batches are expired and cannot be sold. Total locked: {sum(b['quantity_remaining'] for b in expired_batches_retail):g} {unit}")
            wl.setStyleSheet("background-color: #FEE2E2; color: #841717; font-size: 12px; font-weight: bold; padding: 8px 12px; border: 1px solid #F87171; border-radius: 4px;")
            wl.setWordWrap(True); expired_layout.addWidget(wl)
        et = self._std_table(["Batch Date", "Expiry Date", "Qty (Locked)", "Stocked By", "Status"])
        et.setRowCount(len(expired_batches_retail) if expired_batches_retail else 1)
        if expired_batches_retail:
            for r, b in enumerate(expired_batches_retail):
                stocked_by_val = b['stocked_by'] if b['stocked_by'] else "—"
                for col, val in enumerate([str(b['received_date'])[:10] if b['received_date'] else "N/A",
                                           str(b['expiry_date']), f"{b['quantity_remaining']:g} {unit}",
                                           stocked_by_val, "EXPIRED"]):
                    cell = QTableWidgetItem(val); cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    cell.setBackground(QColor("#FFCDD2")); cell.setForeground(QBrush(QColor("#841717")))
                    et.setItem(r, col, cell); et.setRowHeight(r, 36)
        else:
            nr = QTableWidgetItem("No expired batches"); nr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            nr.setForeground(QBrush(QColor("#94A3B8"))); et.setItem(0, 0, nr); et.setSpan(0, 0, 1, 5)
        expired_layout.addWidget(et)
        tabs.addTab(expired_tab, f"  Expired" + (f" ({len(expired_batches_retail)})" if expired_batches_retail else ""))
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("expired.png"))

        layout.addWidget(tabs)
        self._close_footer(layout)


class BreadSummaryDialog(_BaseSummaryDialog):
    def __init__(self, db, prod_id):
        super().__init__()
        self.db = db; self.prod_id = prod_id
        self.setWindowTitle("Bread Comprehensive Intelligence")
        layout = self._build_summary_wrapper(800, 555)
        self._build(layout)

    def _build(self, layout):
        prod = self.db.fetch_one("SELECT * FROM products WHERE id = ?", (self.prod_id,))
        if not prod: self.reject(); return
        today = QDate.currentDate()
        stock = prod['stock_qty'] if prod['stock_qty'] is not None else 0
        unit  = prod['unit'] if prod['unit'] else "pcs"
        try:
            er = self.db.fetch_one(
                "SELECT COALESCE(SUM(quantity_remaining), 0) AS expired_qty FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND expiry_date IS NOT NULL AND expiry_date <= date('now', 'localtime')",
                (self.prod_id,))
            expired_qty = er['expired_qty'] if er else 0
        except Exception:
            expired_qty = 0
        usable_stock = max(0, stock - expired_qty)
        retail_price    = prod['retail_price'] if prod['retail_price'] else 0.0
        production_cost = prod['production_cost'] if prod['production_cost'] else 0.0
        margin = ((retail_price - production_cost) / retail_price * 100) if retail_price > 0 else 0.0

        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 8)
        
        # 🟢 VECTOR SVG PARA SA BREAD (TINAPAY NA MAY USOK)
        BREAD_SVG = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a5 5 0 0 1 5-5h8a5 5 0 0 1 5 5v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6z"></path>
            <line x1="7" y1="7" x2="7" y2="3"></line>
            <line x1="12" y1="7" x2="12" y2="2"></line>
            <line x1="17" y1="7" x2="17" y2="3"></line>
        </svg>
        """
        title_icon = QLabel()
        title_icon.setPixmap(self._create_vector_icon(BREAD_SVG, "#693903").pixmap(QSize(22, 22)))
        title_icon.setFixedSize(24, 24)
        tl = QLabel(f"{prod['name']}"); tl.setStyleSheet("font-size: 20px; font-weight: normal; color: #0F172A;")
        title_row.addWidget(title_icon); title_row.addWidget(tl)
        title_row.addStretch()
        sc = "#B91C1C" if usable_stock <= 0 else "#065F46"
        sb = QLabel(f"Usable Stock: {usable_stock:g} {unit}"); sb.setStyleSheet(f"color: {sc}; font-size: 14px;")
        title_row.addWidget(sb)
        if expired_qty > 0:
            eb = QLabel(f"  ⚠ {expired_qty:g} expired")
            eb.setStyleSheet("background-color: #FEE2E2; color: #B91C1C; font-size: 12px; font-weight: bold; padding: 3px 8px; border-radius: 4px;")
            title_row.addWidget(eb)
        cb = _close_btn(); cb.clicked.connect(self.reject); title_row.addWidget(cb)
        layout.addLayout(title_row)

        tabs = self._tabs_widget()

        expiry_status = ("Out of Stock" if usable_stock <= 0 else
                        f"{expired_qty:g} {unit} in expired batches (locked)" if expired_qty > 0 else
                        "All stock is fresh")
        rows_data = [
            ("Product Name",     prod['name']),
            ("Unit",             unit),
            ("Current Stock",    f"{stock:g} {unit}"),
            ("Usable Stock",     f"{usable_stock:g} {unit}"),
            ("Expired (cannot be sold)", f"{expired_qty:g} {unit}" if expired_qty > 0 else "None"),
            ("Batch Status",     expiry_status),
            ("Shelf Life",       "2 days after baking"),
            ("Retail Price",     f"₱{retail_price:,.2f}" if retail_price else "Not set"),
            ("Production Cost",  f"₱{production_cost:,.2f}" if production_cost else "Not set"),
            ("Profit Margin",    f"{margin:.1f}%" if retail_price > 0 else "N/A"),
        ]
        ov_tab = QWidget(); ov_layout = QVBoxLayout(ov_tab); ov_layout.setContentsMargins(0, 0, 0, 0)
        t = self._std_table(["Field", "Value"])
        t.setRowCount(len(rows_data))
        for r, (field, value) in enumerate(rows_data):
            fi = QTableWidgetItem(field); fi.setTextAlignment(Qt.AlignmentFlag.AlignCenter); fi.setBackground(QColor("#F8FAFC"))
            vi = QTableWidgetItem(str(value)); vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._color_row(vi, str(value))
            t.setItem(r, 0, fi); t.setItem(r, 1, vi); t.setRowHeight(r, 36)
        ov_layout.addWidget(t); 
        tabs.addTab(ov_tab, "  Bread Overview")
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("overview.png"))


        batch_tab = QWidget(); batch_layout = QVBoxLayout(batch_tab); batch_layout.setContentsMargins(0, 0, 0, 0)
        bt = self._std_table(["Batch Date", "Expiry Date", "Qty Remaining", "Stocked By", "Status"])
        try:
            active_batches = self.db.fetch_all(
                "SELECT received_date, expiry_date, quantity_remaining, stocked_by FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND (expiry_date IS NULL OR expiry_date > date('now', 'localtime')) ORDER BY expiry_date ASC",
                (self.prod_id,))
        except Exception:
            active_batches = []
        bt.setRowCount(len(active_batches) if active_batches else 1)
        if active_batches:
            for r, b in enumerate(active_batches):
                exp = QDate.fromString(str(b['expiry_date']), "yyyy-MM-dd")
                dlb = today.daysTo(exp) if exp.isValid() else None
                status = "USE SOON" if dlb is not None and dlb <= 1 else "FRESH"
                stocked_by_val = b['stocked_by'] if b['stocked_by'] else "—"
                for col, val in enumerate([str(b['received_date'])[:10] if b['received_date'] else "N/A",
                                        str(b['expiry_date']) if b['expiry_date'] else "N/A",
                                        f"{b['quantity_remaining']:g} {unit}", stocked_by_val, status]):
                    cell = QTableWidgetItem(val); cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if status == "USE SOON":
                        cell.setBackground(QColor("#FEF9C3")); cell.setForeground(QBrush(QColor("#704406")))
                    else:
                        cell.setBackground(QColor("#D1FAE5")); cell.setForeground(QBrush(QColor("#065F46")))
                    bt.setItem(r, col, cell); bt.setRowHeight(r, 36)
        else:
            nr = QTableWidgetItem("No active batches"); nr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            nr.setForeground(QBrush(QColor("#94A3B8"))); bt.setItem(0, 0, nr); bt.setSpan(0, 0, 1, 5)
        batch_layout.addWidget(bt); tabs.addTab(batch_tab, "  Batches (oldest first)")
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("queue.png"))

        expired_tab = QWidget(); expired_layout = QVBoxLayout(expired_tab); expired_layout.setContentsMargins(0, 0, 0, 0)
        if expired_qty > 0:
            wl = QLabel(f"These batches are expired and cannot be sold. Total locked: {expired_qty:g} {unit}")
            wl.setStyleSheet("background-color: #FEE2E2; color: #841717; font-size: 12px; font-weight: bold; padding: 8px 12px; border: 1px solid #F87171; border-radius: 4px;")
            wl.setWordWrap(True); expired_layout.addWidget(wl)
        et = self._std_table(["Batch Date", "Expiry Date", "Qty (Locked)", "Status"])
        try:
            expired_batches = self.db.fetch_all(
                "SELECT received_date, expiry_date, quantity_remaining FROM product_batches "
                "WHERE product_id = ? AND quantity_remaining > 0 AND expiry_date IS NOT NULL AND expiry_date <= date('now', 'localtime') ORDER BY expiry_date DESC",
                (self.prod_id,))
        except Exception:
            expired_batches = []
        et.setRowCount(len(expired_batches) if expired_batches else 1)
        if expired_batches:
            for r, b in enumerate(expired_batches):
                for col, val in enumerate([str(b['received_date'])[:10] if b['received_date'] else "N/A",
                                           str(b['expiry_date']), f"{b['quantity_remaining']:g} {unit}", "EXPIRED"]):
                    cell = QTableWidgetItem(val); cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    cell.setBackground(QColor("#FFCDD2")); cell.setForeground(QBrush(QColor("#841717")))
                    et.setItem(r, col, cell); et.setRowHeight(r, 36)
        else:
            nr = QTableWidgetItem("No expired batches"); nr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            nr.setForeground(QBrush(QColor("#94A3B8"))); et.setItem(0, 0, nr); et.setSpan(0, 0, 1, 4)
        expired_layout.addWidget(et)
        tabs.addTab(expired_tab, f"  Expired" + (f" ({len(expired_batches)})" if expired_batches else ""))
        tabs.setTabIcon(tabs.count() - 1, self._tab_icon("expired.png"))

        layout.addWidget(tabs)
        self._close_footer(layout)

