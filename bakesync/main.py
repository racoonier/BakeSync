from bakesync.paths import IMAGES_DIR
import sys

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QFrame, QDialog)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QByteArray, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon, QPixmap, QPainter
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer


from bakesync.core.database import DatabaseManager
from bakesync.auth.login_window import LoginWindow
from bakesync.modules.dashboard import DashboardWidget
from bakesync.modules.inventory import InventoryWidget
from bakesync.modules.recipe import RecipeWidget
from bakesync.modules.quality_control import QualityControlWidget
from bakesync.modules.settings import SettingsWidget
from bakesync.modules.backup import auto_backup
from bakesync.widgets.theme import install_combo_theme
from bakesync.core.alerts import collect_alerts
from bakesync.modules.profile import ProfileWidget
from bakesync.widgets.ui import THEME, svg_icon, svg_pixmap, initials
from bakesync.widgets.store_hours import store_status, closing_time_today, fmt as fmt_time
import os

# Which pages each role may open (roles not listed see everything) and where they start
ROLE_PAGES = {"cashier": ["POS", "Sales"], "baker": ["Inventory", "Waste Control"]}
ROLE_HOME = {"cashier": "POS", "baker": "Inventory"}
BELL_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6B3F27" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>"""

from bakesync.modules.pos import POSWidget
from bakesync.modules.sales import SalesWidget
from bakesync.core.audit import log_activity


class ExitConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ang nag-iisang linya na magtatanggal ng default title bar at 'X' sa taas!
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(400, 200)
        
        # BakeSync Theme Colors
        theme_bg = "#FAF9F7"
        theme_brown = "#6B3F27"
        theme_brown_light = "#7A4A2E"
        theme_text_dark = "#3E3E3E"
        theme_text_sec = "#7F8C8D"
        theme_border = "#E0E0E0"

        # Nagdagdag tayo ng border para ma-highlight yung panel kahit walang title bar
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme_bg};
                border: 2px solid {theme_border};
                border-radius: 10px;
            }}
            QLabel {{
                color: {theme_text_dark};
                border: none; /* Para hindi madamay ang labels sa border ng QDialog */
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 20) # In-adjust ng kaunti yung top margin
        layout.setSpacing(15)

        # --- Top Section (Icon + Text) ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # Vector SVG Icon (Logout / Exit Door)
        exit_svg_data = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{theme_brown}">
            <path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/>
        </svg>
        """
        svg_bytes = QByteArray(exit_svg_data.encode('utf-8'))
        icon_widget = QSvgWidget()
        icon_widget.load(svg_bytes)
        icon_widget.setFixedSize(45, 45)
        top_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # Text Section
        text_layout = QVBoxLayout()
        title_lbl = QLabel("Exit System?")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        msg_lbl = QLabel("Do you want to exit the system\nand return to the login page?")
        msg_lbl.setFont(QFont("Segoe UI", 11))
        msg_lbl.setStyleSheet(f"color: {theme_text_sec};")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(msg_lbl)
        top_layout.addLayout(text_layout)
        
        layout.addLayout(top_layout)
        layout.addStretch()

        # --- Buttons Section ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Cancel Button (Outline Style)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 38)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme_text_sec};
                border: 1px solid #D5D5D5;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #EAEAEA;
                color: {theme_text_dark};
            }}
        """)
        cancel_btn.clicked.connect(self.reject) # Magre-return ng 0 (Rejected)

        # Yes, Exit Button (Solid Brown Style)
        exit_btn = QPushButton("Yes, Exit")
        exit_btn.setFixedSize(110, 38)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme_brown};
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme_brown_light};
            }}
            QPushButton:pressed {{
                background-color: #55321F;
            }}
        """)
        exit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)

    def keyPressEvent(self, event):    
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    SIDEBAR_W = 264
    # ── VECTOR SVGS ──
    BURGER_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6B3F27" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
    """

    BAKERY_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 5c-4 0-8 2-8 6v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7c0-4-4-6-8-6z"/>
        <path d="M8 5v-1a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1"/>
    </svg>
    """

    # ── SIDEBAR ICONS (VECTOR SVGS) ──
    ICON_DASHBOARD = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>"""
    ICON_POS = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16.01" y1="10" y2="10"/><line x1="16" x2="16.01" y1="14" y2="14"/><line x1="16" x2="16.01" y1="18" y2="18"/><line x1="8" x2="8.01" y1="10" y2="10"/><line x1="8" x2="8.01" y1="14" y2="14"/><line x1="8" x2="8.01" y1="18" y2="18"/><line x1="12" x2="12.01" y1="10" y2="10"/><line x1="12" x2="12.01" y1="14" y2="14"/><line x1="12" x2="12.01" y1="18" y2="18"/></svg>"""
    ICON_INVENTORY = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>"""
    ICON_RECIPE = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>"""
    ICON_QC = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>"""
    ICON_SALES = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>"""
    ICON_SETTINGS = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>"""
    ICON_LOGOUT = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>"""

    def __init__(self, username: str, role: str, db: DatabaseManager):
        super().__init__()
        self.username = username
        self.role = role
        self.db = db
        self.display_name = self._display_name()

        # Awtomatikong backup isang beses kada araw (huling 14 lang ang itinatabi)
        try:
            auto_backup(self.db)
        except Exception as e:
            print(f"[MainWindow] auto backup failed: {e}")

        self.setWindowTitle(f"BakeSync - {role}")
        self.showMaximized()
        
        # --- Color Palette ---
        self.colors = {
            "sidebar_bg": "#6B3F27",
            "sidebar_active": "#7A4A2E",
            "content_bg": "#FAF9F7",
            "text_white": "#FFFFFF",
            "text_dark": "#3E3E3E",
            "text_secondary": "#7F8C8D", 
            "status_green": "#66BB6A",
            "border_color": "#E0E0E0"
        }

        self.init_ui()

    def init_ui(self):
        # Main Window Styling
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {self.colors['content_bg']}; }}
            QWidget {{ font-family: 'Segoe UI', 'Helvetica', sans-serif; color: {self.colors['text_dark']}; }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------------------------------------------------
        # 1. Left Sidebar (With Animation Support)
        # ---------------------------------------------------------
        T = THEME
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(self.SIDEBAR_W)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A2B1A, stop:1 #2B190F); border: none; }}
            QLabel {{ color: {T['cream']}; background: transparent; }}
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 0, 12, 14)
        sidebar_layout.setSpacing(0)

        # -- Brand: logo, store name and a live "Open now" chip --
        brand = QWidget(); brand.setFixedHeight(104)
        bl = QHBoxLayout(brand); bl.setContentsMargins(6, 0, 0, 0); bl.setSpacing(10)
        logo_icon = QLabel()
        logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "app_icon.png"))
        if logo_pixmap.isNull():
            logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "poplogo.png"))
        if not logo_pixmap.isNull():
            logo_icon.setPixmap(logo_pixmap.scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))
        else:
            logo_icon.setPixmap(svg_pixmap("bread", T["caramel"], 40))
        logo_icon.setFixedSize(58, 58)
        bl.addWidget(logo_icon)
        name_col = QVBoxLayout(); name_col.setSpacing(4)
        brand_text = QLabel("Popeye's Bakery")
        brand_text.setFont(QFont("Georgia", 14, QFont.Weight.Bold))
        brand_text.setStyleSheet(f"color: {T['cream']}; font-style: italic;")
        name_col.addStretch()
        name_col.addWidget(brand_text)
        self.store_chip = QLabel("")
        self.store_chip.setStyleSheet(f"color: {T['caramel_light']}; font-size: 11px;")
        name_col.addWidget(self.store_chip)
        name_col.addStretch()
        bl.addLayout(name_col)
        bl.addStretch()
        sidebar_layout.addWidget(brand)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background: rgba(255,255,255,0.08);")
        sidebar_layout.addWidget(line)

        # -- Navigation, grouped by how often it is used; each role only sees its own pages --
        self.nav_buttons = {}
        menu_groups = [
            ("DAILY", [("POS", "POS", "cart"), ("Inventory", "Inventory", "box"), ("Waste", "Waste Control", "trash")]),
            ("REPORTS & PRICES", [("Dashboard", "Dashboard", "chart"), ("Sales", "Sales", "trend_up"),
                                  ("Pricing", "Recipe and Pricing", "tag")]),
        ]
        for group_title, items in menu_groups:
            items = [it for it in items if self._allowed(it[1])]
            if not items:
                continue
            section = QLabel(group_title)
            section.setStyleSheet(f"color: rgba(243, 217, 184, 0.55); font-size: 10px; font-weight: bold; "
                                  "letter-spacing: 1.5px; padding: 18px 0 8px 14px;")
            sidebar_layout.addWidget(section)
            for label, page_id, icon_name in items:
                btn = self.create_nav_button(label, page_id, icon_name)
                sidebar_layout.addWidget(btn)
                sidebar_layout.addSpacing(4)
                self.nav_buttons[page_id] = btn
        sidebar_layout.addStretch()

        # -- Bottom: who is signed in (opens the profile), Settings, Logout --
        self.settings_btn = self.create_nav_button("Settings", "Settings", "settings")
        self.nav_buttons["Settings"] = self.settings_btn
        self.settings_btn.setVisible(self._allowed("Settings"))
        sidebar_layout.addWidget(self.settings_btn)
        sidebar_layout.addSpacing(4)
        logout_btn = self.create_nav_button("Logout", "Logout", "logout")
        logout_btn.clicked.disconnect()
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)
        sidebar_layout.addSpacing(10)

        me = QPushButton(); me.setFixedHeight(58); me.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        me.setToolTip("Open my profile")
        me.setStyleSheet("QPushButton { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; }"
                         "QPushButton:hover { background: rgba(255,255,255,0.12); }")
        ml = QHBoxLayout(me); ml.setContentsMargins(10, 0, 10, 0); ml.setSpacing(10)
        av = self._me_av = QLabel(initials(self.display_name)); av.setFixedSize(36, 36); av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"background: {T['caramel']}; color: {T['choc']}; border-radius: 18px; font-weight: bold; font-size: 13px;")
        av.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ml.addWidget(av)
        mt = QVBoxLayout(); mt.setSpacing(0)
        n = self._me_name = QLabel(self.display_name); n.setStyleSheet(f"color: {T['cream']}; font-size: 13px; font-weight: bold;")
        r = QLabel(self.role); r.setStyleSheet(f"color: {T['caramel_light']}; font-size: 11px;")
        for w in (n, r):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            mt.addWidget(w)
        ml.addLayout(mt); ml.addStretch()
        chev = QLabel(); chev.setPixmap(svg_pixmap("chevron_right", T["caramel_light"], 16))
        chev.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ml.addWidget(chev)
        me.clicked.connect(lambda: self.change_page("Profile"))
        sidebar_layout.addWidget(me)

        version_label = QLabel("BakeSync v1.0")
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.35); font-size: 10px; padding: 8px 0 0 6px;")
        sidebar_layout.addWidget(version_label)
        main_layout.addWidget(self.sidebar)

        # ---------------------------------------------------------
        # 2. Main Content Area (Right Panel)
        # ---------------------------------------------------------
        content_container = QWidget()
        content_container.setStyleSheet(f"background-color: {self.colors['content_bg']};")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # -- Top bar: menu, page title + date, greeting, alerts, account --
        header_frame = QFrame(); header_frame.setObjectName("topbar")
        header_frame.setFixedHeight(74)
        header_frame.setStyleSheet(f"QFrame#topbar {{ background: #FFFFFF; border: none; border-bottom: 1px solid {T['line']}; }}"
                                   "QLabel { background: transparent; }")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(10)

        def icon_btn(name, tip, size=22, hover=T["cream_dark"]):
            b = QPushButton(); b.setFixedSize(42, 42); b.setToolTip(tip)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setIcon(svg_icon(name, T["brown"], size)); b.setIconSize(QSize(size, size))
            b.setStyleSheet(f"QPushButton {{ border: none; background: transparent; border-radius: 21px; }}"
                            f"QPushButton:hover {{ background: {hover}; }}")
            return b

        self.burger_btn = icon_btn("menu", "Show / hide the menu")
        self.burger_btn.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.burger_btn)
        self.header_logo = QLabel()
        _lp = QPixmap(os.path.join(IMAGES_DIR, "app_icon.png"))
        if not _lp.isNull():
            self.header_logo.setPixmap(_lp.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.header_logo.setToolTip("Popeye's Bakery")
        self.header_logo.hide()                       # shown only while the sidebar (which has the logo) is hidden
        header_layout.addWidget(self.header_logo)

        title_col = QVBoxLayout(); title_col.setSpacing(0)
        self.header_title = QLabel("Dashboard")
        self.header_title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        self.header_title.setStyleSheet(f"color: {T['text']};")
        self.header_date = QLabel(header_frame)      # centered in the bar (placed in eventFilter)
        self.header_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_date.setStyleSheet(f"color: {T['text']}; background: {T['cream']}; border: 1px solid {T['line']}; "
                                       "border-radius: 17px; padding: 6px 18px; font-size: 15px; font-weight: 600;")
        self._header_frame = header_frame
        header_frame.installEventFilter(self)
        title_col.addStretch()
        title_col.addWidget(self.header_title)
        title_col.addStretch()
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        greet_col = QVBoxLayout(); greet_col.setSpacing(0)
        self.greet_lbl = QLabel("")
        self.greet_lbl.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: bold;")
        self.greet_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        role_lbl = QLabel(self.role); role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        role_lbl.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
        greet_col.addStretch(); greet_col.addWidget(self.greet_lbl); greet_col.addWidget(role_lbl); greet_col.addStretch()

        self.bell_btn = icon_btn("bell", "Alerts")
        self.bell_btn.clicked.connect(self._show_alerts_menu)
        self.bell_count = QLabel(self.bell_btn)
        self.bell_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bell_count.setGeometry(22, 2, 20, 18)
        self.bell_count.setStyleSheet(f"background: {T['red']}; color: white; border-radius: 9px; font-size: 10px; font-weight: bold;")
        self.bell_count.hide()

        self.avatar_btn = QPushButton(initials(self.display_name))
        self.avatar_btn.setFixedSize(42, 42)
        self.avatar_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.avatar_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.avatar_btn.setToolTip("My account")
        self.avatar_btn.setStyleSheet(f"QPushButton {{ background: {T['brown']}; color: {T['cream']}; border-radius: 21px; border: 2px solid {T['caramel_light']}; }}"
                                      f"QPushButton:hover {{ background: {T['brown_hover']}; }}")
        self.avatar_btn.clicked.connect(self._show_account_menu)

        sep = QFrame(); sep.setFixedSize(1, 30); sep.setStyleSheet(f"background: {T['line']};")
        min_btn = icon_btn("minus", "Minimize", size=18)
        min_btn.clicked.connect(self.showMinimized)
        close_btn = icon_btn("x", "Close BakeSync", size=18, hover="#FBE3E1")
        close_btn.clicked.connect(self.logout)

        header_layout.addWidget(self.bell_btn)
        header_layout.addSpacing(6)
        header_layout.addLayout(greet_col)
        header_layout.addWidget(self.avatar_btn)
        header_layout.addSpacing(4)
        header_layout.addWidget(sep)
        header_layout.addWidget(min_btn)
        header_layout.addWidget(close_btn)
        content_layout.addWidget(header_frame)

        # -- Content Body (Stacked Widget) --
        self.content_area = QStackedWidget()
        self.pages = {}
        
        self.widgets_map = {
            "Profile":            ProfileWidget,
            "Dashboard":          DashboardWidget,
            "POS":                POSWidget,           
            "Inventory":          InventoryWidget,
            "Recipe and Pricing": RecipeWidget,
            "Waste Control":    QualityControlWidget,
            "Sales":              SalesWidget, 
            "Settings":           SettingsWidget, 
        }

        USER_AWARE_WIDGETS = (InventoryWidget, SettingsWidget, RecipeWidget, POSWidget, QualityControlWidget, ProfileWidget)

        for name, widget_class in self.widgets_map.items():
            try:
                if widget_class in USER_AWARE_WIDGETS:
                    widget = widget_class(self.db, current_user=self.username)
                else:
                    widget = widget_class(self.db)
                self.content_area.addWidget(widget)
                self.pages[name] = widget
            except Exception as e:
                print(f"Error loading {name}: {e}")
                lbl = QLabel(f"Error loading {name}")
                self.content_area.addWidget(lbl)
                self.pages[name] = lbl

        # ── Connect POS sale_completed → Dashboard refresh ──
        pos_widget = self.pages.get("POS")
        dash_widget = self.pages.get("Dashboard")
        if (isinstance(pos_widget, POSWidget) and
                isinstance(dash_widget, DashboardWidget)):
            pos_widget.sale_completed.connect(dash_widget.refresh_dashboard)

        content_layout.addWidget(self.content_area)
        main_layout.addWidget(content_container)

        self.change_page(ROLE_HOME.get((self.role or "").lower(), "Dashboard"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()

        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.refresh_alerts)
        self.alert_timer.start(60_000)
        self.refresh_alerts()
        if isinstance(pos_widget, POSWidget):
            pos_widget.sale_completed.connect(self.refresh_alerts)

    # ── METHOD PARA MAG-TOGGLE NG SIDEBAR ──
    def toggle_sidebar(self):
        # Kukunin ang current width ng sidebar
        width = self.sidebar.width()
        
        # Palitan ang 260 ng 280 dito:
        new_width = 0 if width >= self.SIDEBAR_W else self.SIDEBAR_W
        self.header_logo.setVisible(new_width == 0)

        # Animation para sa Minimum Width
        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim_min.setDuration(300) # Speed ng animation in milliseconds
        self.anim_min.setStartValue(width)
        self.anim_min.setEndValue(new_width)
        self.anim_min.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # Animation para sa Maximum Width
        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_max.setDuration(300)
        self.anim_max.setStartValue(width)
        self.anim_max.setEndValue(new_width)
        self.anim_max.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # I-play ang animation!
        self.anim_min.start()
        self.anim_max.start()

        # Trigger POS grid recalculation during animation
        def _refresh_pos_grid():
            pos = self.pages.get("POS")
            if pos and hasattr(pos, '_apply_filters'):
                pos._apply_filters()

        self._sidebar_refresh_timer = QTimer(self)
        self._sidebar_refresh_timer.setInterval(16)
        self._sidebar_refresh_timer.timeout.connect(_refresh_pos_grid)
        self._sidebar_refresh_timer.start()
        self.anim_max.finished.connect(self._sidebar_refresh_timer.stop)
        self.anim_max.finished.connect(_refresh_pos_grid)
        self.anim_max.finished.connect(
            lambda: QTimer.singleShot(50, _refresh_pos_grid))
        self.anim_max.finished.connect(
            lambda: QTimer.singleShot(150, _refresh_pos_grid))

    def create_nav_button(self, text, page_id, icon_name=None):
        T = THEME
        btn = QPushButton(f"  {text}")
        btn.setFont(QFont("Segoe UI", 11))
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setCheckable(True)
        btn.setFixedHeight(44)
        if icon_name:
            btn.icon_white = svg_icon(icon_name, "#E9C9A0", 20)     # normal: soft caramel
            btn.icon_yellow = svg_icon(icon_name, T["brown"], 20)   # open page: brown on cream
            btn.icon_hover = svg_icon(icon_name, "#FFFFFF", 20)
            btn.setIcon(btn.icon_white)
            btn.setIconSize(QSize(20, 20))

            def enterEvent(event, b=btn):
                if not b.isChecked():
                    b.setIcon(b.icon_hover)
                QPushButton.enterEvent(b, event)

            def leaveEvent(event, b=btn):
                b.setIcon(b.icon_yellow if b.isChecked() else b.icon_white)
                QPushButton.leaveEvent(b, event)
            btn.enterEvent = enterEvent
            btn.leaveEvent = leaveEvent

        btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: rgba(251, 246, 240, 0.85); text-align: left;
                           padding-left: 14px; border: none; border-radius: 10px; }}
            QPushButton:hover {{ background: rgba(255, 255, 255, 0.08); color: #FFFFFF; }}
            QPushButton:checked {{ background: {T['cream']}; color: {T['choc']}; font-weight: bold;
                                   border-left: 4px solid {T['gold']}; padding-left: 10px; }}
        """)

        # count bubble (e.g. low-stock items) on the right of the button
        btn._badge = QLabel(btn)
        btn._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn._badge.setStyleSheet(f"background: {T['red']}; color: white; border-radius: 10px; font-size: 11px; "
                                 "font-weight: bold; padding: 0 6px;")
        btn._badge.setGeometry(self.SIDEBAR_W - 24 - 50, 12, 36, 20)
        btn._badge.hide()

        btn.clicked.connect(lambda: self.change_page(page_id))
        return btn

    def _display_name(self):
        row = self.db.fetch_one("SELECT full_name FROM users WHERE username = ?", (self.username,))
        return (row["full_name"] if row and row["full_name"] else self.username) or "User"

    def refresh_identity(self):
        """After the profile is edited: new name / initials everywhere."""
        self.display_name = self._display_name()
        self.avatar_btn.setText(initials(self.display_name))
        self._me_av.setText(initials(self.display_name))
        self._me_name.setText(self.display_name)
        self.update_datetime()

    def _allowed(self, page_name):
        if page_name in ("Profile", "Logout"):
            return True
        role = (self.role or "").lower()
        if page_name == "Settings":
            return role not in ("cashier", "baker")
        return page_name in ROLE_PAGES[role] if role in ROLE_PAGES else True

    def _set_badge(self, page_id, count):
        btn = self.nav_buttons.get(page_id)
        if btn is None or not hasattr(btn, "_badge"):
            return
        btn._badge.setText(str(count) if count < 100 else "99+")
        btn._badge.setVisible(count > 0)

    # ── Alerts bell ─────────────────────────────────────────
    def refresh_alerts(self):
        try:
            self._alerts = collect_alerts(self.db)
        except Exception as e:
            print(f"[MainWindow] alerts error: {e}")
            return
        total = sum(len(v) for v in self._alerts.values())
        self.bell_count.setText(str(total) if total < 100 else "99+")
        self.bell_count.setVisible(total > 0)
        self.bell_btn.setToolTip(f"{total} alert{'s' if total != 1 else ''}" if total else "No alerts")
        self._set_badge("Inventory", len(self._alerts["low"]) + len(self._alerts["expiring"]))
        self._set_badge("Waste Control", len(self._alerts["expired"]))

    def _menu_style(self):
        return f"""
            QMenu {{ background: #FFFFFF; border: 1px solid #D6CCC2; border-radius: 10px; padding: 6px; }}
            QMenu::item {{ padding: 8px 22px 8px 14px; border-radius: 6px; color: #1F2937; font-size: 13px; }}
            QMenu::item:selected {{ background: #F5ECE5; color: #693903; }}
            QMenu::item:disabled {{ color: #693903; font-weight: bold; font-size: 12px; background: transparent; }}
            QMenu::separator {{ height: 1px; background: #EEE7E0; margin: 6px 8px; }}
        """

    def _show_alerts_menu(self):
        from bakesync.widgets.alerts_popup import AlertsPopup
        self.refresh_alerts()
        alerts = getattr(self, "_alerts", {"low": [], "expiring": [], "expired": []})
        AlertsPopup(alerts, self.change_page, self._allowed, self).show_under(self.bell_btn)

    # ── Account menu (avatar) ───────────────────────────────
    def _show_account_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        menu.addAction(f"{self.display_name}  ·  {self.role}").setEnabled(False)
        menu.addSeparator()
        menu.addAction(svg_icon("user", THEME["brown"], 16), "My Profile").triggered.connect(lambda: self.change_page("Profile"))
        menu.addSeparator()
        menu.addAction(svg_icon("logout", THEME["red"], 16), "Logout").triggered.connect(self.logout)
        menu.exec(self.avatar_btn.mapToGlobal(self.avatar_btn.rect().bottomLeft()))

    def change_page(self, page_name):
        # Role-based access guard (the button is hidden too, this blocks every other route)
        if not self._allowed(page_name):
            return
        
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.setChecked(True)
                # Siguraduhing magiging yellow ang icon ng piniling page
                if hasattr(btn, 'icon_yellow'):
                    btn.setIcon(btn.icon_yellow)
            else:
                btn.setChecked(False)
                # I-reset sa puti yung ibang pages, maliban na lang kung nandun yung mouse mo
                if hasattr(btn, 'icon_white'):
                    if not btn.underMouse():
                        btn.setIcon(btn.icon_white)

        if page_name in self.pages:
            widget = self.pages[page_name]
            self.content_area.setCurrentWidget(widget)
            
        if hasattr(self, 'header_title'):
            display_title = {"Waste Control": "Waste", "Recipe and Pricing": "Pricing",
                             "Profile": "My Profile"}.get(page_name, page_name)
            self.header_title.setText(display_title)
    
    def eventFilter(self, obj, event):
        if obj is getattr(self, "_header_frame", None) and event.type() in (event.Type.Resize, event.Type.Show):
            self._place_date()
        return super().eventFilter(obj, event)

    def _place_date(self):
        d = self.header_date
        d.adjustSize()
        f = self._header_frame
        d.move((f.width() - d.width()) // 2, (f.height() - d.height()) // 2)
        d.raise_()

    def update_datetime(self):
        now = QDateTime.currentDateTime()
        txt = now.toString("dddd, MMMM d, yyyy   ·   h:mm AP")
        if self.header_date.text() != txt:
            self.header_date.setText(txt)
            self._place_date()
        h = now.time().hour()
        part = "morning" if h < 12 else ("afternoon" if h < 18 else "evening")
        self.greet_lbl.setText(f"Good {part}, {self.display_name.split()[0]}")
        if now.time().second() % 30 == 0 or not self.store_chip.text():
            self._update_store_chip()

    def _update_store_chip(self):
        try:
            is_open, title, _ = store_status(self.db)
        except Exception:
            return
        color = "#7BD88F" if is_open else "#D9C2A8"
        text = f"Open now  ·  closes {fmt_time(closing_time_today(self.db))}" if is_open else title
        self.store_chip.setText(f"<span style='color:{color}; font-size:14px;'>&#9679;</span>&nbsp; {text}")

    def show_profile_popup(self):
        self.change_page("Profile")

    def logout(self):
        dialog = ExitConfirmDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._is_logging_out = True  # 🟢 DAGDAG ITO: Set flag para malaman ng closeEvent na nag-logout na
            log_activity(self.db, self.username, "signed out", "signin")
            self.login_window = LoginWindow()
            self.login_window.login_success.connect(self.on_login_success)
            self.login_window.show()
            self.close()
            self.db.close()

    def on_login_success(self, username, role):
        db = DatabaseManager()
        self.new_window = MainWindow(username, role, db)
        self.new_window.showMaximized()
        self.login_window.close()

    def closeEvent(self, event):
        # 🟢 DAGDAG ITO: I-bypass ang dialog kung galing sa logout() button
        if getattr(self, '_is_logging_out', False):
            event.accept()
            return
            
        dialog = ExitConfirmDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            log_activity(self.db, self.username, "closed BakeSync", "signin")
            self.db.close()
            event.accept()
        else:
            event.ignore()

    def _stop_all_timers(self):
        try:
            if hasattr(self, 'timer'):
                self.timer.stop()
            for name, widget in self.pages.items():
                if hasattr(widget, 'stop_timers'):
                    widget.stop_timers()
                # Stop any QTimer children directly
                for child in widget.findChildren(QTimer):
                    child.stop()
        except Exception as e:
            print(f"[MainWindow] stop_timers error: {e}")

# cmment muna para di na need mag login


def _app_icon():
    """The bakery logo, used for every window (taskbar, Alt+Tab, Task Manager)."""
    path = os.path.join(IMAGES_DIR, "app_icon.png")
    return QIcon(path) if os.path.exists(path) else QIcon(os.path.join(IMAGES_DIR, "poplogo.png"))


def main():
    if sys.platform == "win32":
        # Own taskbar entry, so Windows shows the BakeSync logo instead of the Python icon
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PopeyesBakery.BakeSync")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName("BakeSync")
    app.setWindowIcon(_app_icon())
    install_combo_theme(app)   # iisang itsura para sa lahat ng dropdown
    
    login_window = LoginWindow()

    def start_main(username, role):
        db = DatabaseManager()
        global main_window 
        main_window = MainWindow(username, role, db)
        main_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        main_window.setWindowIcon(_app_icon())
        main_window.showMaximized()
        
    # Ito ang sumasalo sa signal kapag tama ang credentials sa login window
    login_window.login_success.connect(start_main)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


#sonic gumawa neto