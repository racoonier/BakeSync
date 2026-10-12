from bakesync.paths import CACHE_DIR, IMAGES_DIR
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QApplication, QFrame)
from bakesync.widgets.custom_dialog import show_info, show_warning, show_error, ForgotPasswordDialog
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray, QSize, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from bakesync.core.database import DatabaseManager

from PyQt6.QtWidgets import QDialog, QScrollArea

from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.auth.signup_window import SignUpWindow
from bakesync.auth.forgot_password_window import ForgotPasswordWindow

from bakesync.core.auth_utils import hash_password, verify_password, is_hashed
from bakesync.core.audit import log_activity
from bakesync.auth.change_password_dialog import ChangePasswordDialog
import os
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix



class TermsAndConditionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terms and Conditions")
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("QDialog { background-color: white; border: 2px solid #5C2D0E; border-radius: 12px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Terms & Conditions")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scrollable Text Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #D9CFC7; border-radius: 6px; background-color: #F9FAFB; }")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        
        tc_text = """<b>Welcome to Popeye's Bakery Management System!</b><br><br>
        By accessing and using this system, you agree to comply with the following terms:<br><br>
        <b>1. Data Privacy and Security:</b> All data, recipes, inventory counts, and financial records are strictly confidential. Sharing of this information outside the bakery is strictly prohibited.<br><br>
        <b>2. Account Responsibility:</b> You are fully responsible for all actions made under your account. Never share your Mastery Key or Password with anyone.<br><br>
        <b>3. Accurate Logging:</b> As an employee, you are expected to accurately log sales, voids, and waste. Falsifying system data may lead to disciplinary action.<br><br>
        <b>4. System Usage:</b> This system is strictly for business operations only.<br><br>
        <i>By clicking 'I Agree', you acknowledge that you have read and understood your responsibilities as an authorized user of Popeye's Bakery.</i>
        """
        
        lbl_text = QLabel(tc_text)
        lbl_text.setFont(QFont("Segoe UI", 11))
        lbl_text.setStyleSheet("color: #444; border: none;")
        lbl_text.setWordWrap(True)
        content_layout.addWidget(lbl_text)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_decline = QPushButton("I Decline")
        btn_decline.setMinimumHeight(40)
        btn_decline.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_decline.setStyleSheet("QPushButton { background: transparent; color: #C0392B; border: 1.5px solid #C0392B; border-radius: 6px; font-weight: bold; font-size: 13px;} QPushButton:hover { background: #FEF2F2; }")
        btn_decline.clicked.connect(self.reject)
        
        btn_agree = QPushButton("I Agree")
        btn_agree.setMinimumHeight(40)
        btn_agree.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agree.setStyleSheet("QPushButton { background-color: #5C2D0E; color: white; border-radius: 6px; font-weight: bold; font-size: 13px; border: none;} QPushButton:hover { background-color: #4A2208; }")
        btn_agree.clicked.connect(self.accept)

        btn_layout.addWidget(btn_decline)
        btn_layout.addWidget(btn_agree)
        layout.addLayout(btn_layout)

class WelcomeGreetingDialog(QDialog):
    def __init__(self, username, role, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome!")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("QDialog { background-color: white; border: 2px solid #4CAF50; border-radius: 12px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Welcome Aboard!")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(f"Hello <b>{username}</b>!<br><br>Your account has been fully activated.<br>You are logged in as a <b>{role}</b>.")
        desc.setFont(QFont("Segoe UI", 12))
        desc.setStyleSheet("color: #555; border: none;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        btn_start = QPushButton("Let's Get Started!")
        btn_start.setMinimumHeight(45)
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; border: none;} QPushButton:hover { background-color: #388E3C; }")
        btn_start.clicked.connect(self.accept)
        layout.addWidget(btn_start)


class LoginWindow(QMainWindow):
    login_success = pyqtSignal(str, str)  # username, role

    EYE_OPEN_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="#888888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
    """

    EYE_OFF_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="#888888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8
               a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8
               a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
    """

    SPINNER_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="white" stroke-width="2.5" stroke-linecap="round">
    <path d="M12 2a10 10 0 0 1 10 10" opacity="1"/>
    <path d="M12 2a10 10 0 0 0-10 10" opacity="0.3"/>
    <path d="M22 12a10 10 0 0 1-10 10" opacity="0.6"/>
    <path d="M2 12a10 10 0 0 0 10 10" opacity="0.15"/>
    </svg>
    """

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()

        self.failed_attempts = 0
        self.is_locked = False
        self.lock_timer_count = 0

        self.setWindowTitle("POPEYE'S Bakery")
        self.setMinimumSize(900, 550)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 900) // 2
        y = (screen.height() - 600) // 2
        self.move(x, y)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
        """)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── LEFT SIDE (Login Form) ──────────────────────────────────────────────
        left_widget = QWidget()
        left_widget.setObjectName("leftWidget")
        left_widget.setStyleSheet("QWidget#leftWidget { background-color: #FFFFFF; }")

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(55, 10, 55, 10)
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Logo Setup
        logo_label = QLabel()

        # Kunin ang path gamit ang relative directory
        script_dir = os.path.dirname(__file__)
        image_path = os.path.join(IMAGES_DIR, "poplogo.png")

        # I-load ang image sa variable na 'logo_pixmap'
        logo_pixmap = QPixmap(image_path)

        # Check kung successful ang pag-load
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            # Fallback kapag hindi nahanap ang image
            logo_label.setPixmap(_ui_pix("bread", "#6B3F27", 64))
            logo_label.setStyleSheet("font-size: 50px;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedSize(120, 120)

        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(0, 0, 0, 0)
        logo_row.addStretch()
        logo_row.addWidget(logo_label)
        logo_row.addStretch()
        left_layout.addLayout(logo_row)
        left_layout.addSpacing(0)

        # Title
        title = QLabel("Login")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #5C2D0E; letter-spacing: 0px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        left_layout.addSpacing(10)

        tagline = QLabel("Welcome back to <i>Popeye's Bakery</i>")
        tagline.setTextFormat(Qt.TextFormat.RichText)
        tagline.setStyleSheet("color: #9E8472; font-size: 13px; font-family: Arial;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(tagline)
        left_layout.addSpacing(30)

        # Username Field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(48)
        self.username_input.setStyleSheet(self._input_style_normal())
        left_layout.addWidget(self.username_input)

        self.username_error = QLabel("")
        self.username_error.setStyleSheet("color: #C0392B; font-size: 11px; padding-left: 4px; margin-top: 2px;")
        self.username_error.setVisible(False)
        left_layout.addWidget(self.username_error)
        left_layout.addSpacing(12)

        # Password Field
        password_frame = QFrame()
        password_frame.setObjectName("passwordFrame")
        password_frame.setFixedHeight(48)
        password_frame.setStyleSheet(self._password_frame_style_normal())

        password_frame_layout = QHBoxLayout(password_frame)
        password_frame_layout.setContentsMargins(14, 0, 10, 0)
        password_frame_layout.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #333;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; padding: 4px; }
            QPushButton:hover { background-color: rgba(0,0,0,0.05); border-radius: 4px; }
        """)
        self.toggle_btn.setIcon(self._make_svg_icon(visible=False))
        self.toggle_btn.setIconSize(QSize(20, 20))
        self.toggle_btn.clicked.connect(self.toggle_password)

        self.password_input.focusInEvent = self.focusInEvent_password
        self.password_input.focusOutEvent = self.focusOutEvent_password

        password_frame_layout.addWidget(self.password_input)
        password_frame_layout.addWidget(self.toggle_btn)

        left_layout.addWidget(password_frame)

        self.password_error = QLabel("")
        self.password_error.setStyleSheet("color: #C0392B; font-size: 11px; padding-left: 4px; margin-top: 2px;")
        self.password_error.setVisible(False)
        left_layout.addWidget(self.password_error)
        left_layout.addSpacing(8)

        # Forgot Password
        forgot_layout = QHBoxLayout()
        forgot_layout.setContentsMargins(0, 0, 0, 0)
        forgot_link = QPushButton("Forgot Password?")
        forgot_link.setStyleSheet("""
            QPushButton {
                color: #7A4F2E;
                background: none;
                border: none;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
                text-align: right;
                padding: 0;
            }
            QPushButton:hover { color: #4a2e14; text-decoration: underline; }
        """)
        forgot_link.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_link.clicked.connect(self.show_forgot_password)
        forgot_layout.addStretch()
        forgot_layout.addWidget(forgot_link)
        left_layout.addLayout(forgot_layout)
        left_layout.addSpacing(20)

        # Sign In Button
        self.sign_in_btn = QPushButton("Sign In")
        self.sign_in_btn.setObjectName("signInBtn")
        self.sign_in_btn.setMinimumHeight(50)
        self.sign_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sign_in_btn.setStyleSheet("""
            QPushButton#signInBtn {
                background-color: #5C2D0E;
                color: white;
                border-radius: 8px;
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
                padding: 12px;
                border: none;
                letter-spacing: 0.3px;
            }
            QPushButton#signInBtn:hover { background-color: #7A3D15; }
            QPushButton#signInBtn:pressed { background-color: #4A2208; }
        """)
        self.sign_in_btn.clicked.connect(self.handle_login)
        left_layout.addWidget(self.sign_in_btn)
        left_layout.addSpacing(22)

        # Don't have an account
        signup_layout = QHBoxLayout()
        signup_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_account_label = QLabel("Don't have an account?")
        no_account_label.setStyleSheet("color: #888; font-size: 13px; font-family: 'Segoe UI', sans-serif;")
        signup_btn = QPushButton("Sign up")
        signup_btn.setStyleSheet("""
            QPushButton {
                color: #7A4F2E;
                background: none;
                border: none;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                padding: 0 0 0 4px;
            }
            QPushButton:hover { text-decoration: underline; color: #4a2e14; }
        """)
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # ---> IDAGDAG ITO PARA MA-CLICK ANG BUTTON <---
        signup_btn.clicked.connect(self.open_signup_window) 

        signup_layout.addWidget(no_account_label)
        signup_layout.addWidget(signup_btn)
        left_layout.addLayout(signup_layout)

        left_layout.addStretch()

        # ── RIGHT SIDE (Background Image) ──────────────────────────────────────
        self.right_widget = QWidget()
        self.right_widget.setObjectName("rightWidget")
        right_widget = self.right_widget

       # 1. Kunin ang base directory ng script mo
        script_dir = os.path.dirname(__file__)

        # 2. Ituro ang path papunta sa original image
        original_bg_path = os.path.join(IMAGES_DIR, "popbg.png")

        # 3. I-load at i-resize
        bg_pixmap = QPixmap(original_bg_path)

        if not bg_pixmap.isNull():
            bg_pixmap = bg_pixmap.scaled(
                600, 600,   # <-- adjust these to resize
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 4. I-save ang temp copy sa loob din ng script directory
            temp_bg_path = os.path.join(CACHE_DIR, "popbg_resized.png")
            bg_pixmap.save(temp_bg_path)
            
            # 5. I-format ang path para sa QSS (StyleSheet)
            # Kailangan ng forward slashes (/) sa CSS url kahit sa Windows
            final_bg_path = temp_bg_path.replace("\\", "/")

            right_widget.setStyleSheet(f"""
                QWidget#rightWidget {{
                    background-image: url({final_bg_path});
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            print("Error: Background image not found at", original_bg_path)

        # ── Floating cards overlay (absolute positioning) ──────────────────────
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        def make_shadow(radius=20, offset_x=0, offset_y=4, opacity=80):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(radius)
            shadow.setOffset(offset_x, offset_y)
            shadow.setColor(QColor(0, 0, 0, opacity))
            return shadow

        card_style = """
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
        """

        # ── Card 1: Daily Sales ────────────────────────────────────────────────
        sales_card = QWidget(right_widget)
        sales_card.setStyleSheet(card_style)
        sales_card.setGraphicsEffect(make_shadow(radius=25, offset_y=6, opacity=100))

        sales_layout = QVBoxLayout(sales_card)
        sales_layout.setContentsMargins(20, 16, 20, 10)
        sales_layout.setSpacing(8)

        sales_header = QHBoxLayout()
        sales_title = QLabel("Daily  Sales")
        sales_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        sales_title.setStyleSheet("color: #1a1a1a; background: transparent;")

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        for label, active in [("Weekly", True), ("Monthly", False), ("Yearly", False)]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#7A3D15' if active else '#E8E0D8'};
                    color: {'white' if active else '#888'};
                    border-radius: 12px;
                    font-size: 10px;
                    padding: 0 10px;
                    border: none;
                }}
            """)
            filter_row.addWidget(btn)

        sales_header.addWidget(sales_title)
        sales_header.addStretch()
        sales_header.addLayout(filter_row)
        sales_layout.addLayout(sales_header)

        chart_widget = QWidget()
        chart_widget.setMinimumHeight(90)
        chart_widget.setStyleSheet("background: transparent;")

        def paint_chart(widget, event):
            from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath
            from PyQt6.QtCore import QPointF
            p = QPainter(widget)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            w, h = widget.width(), widget.height()
            points = [0.2, 0.55, 0.45, 0.6, 0.5, 0.7, 0.65, 0.8, 0.75, 0.9]
            coords = [QPointF(i * w / (len(points)-1), h - p_val * h * 0.85 - h * 0.05)
                    for i, p_val in enumerate(points)]
            pen = QPen(QColor("#F0EDE8"))
            pen.setWidth(1)
            p.setPen(pen)
            for i in range(5):
                y = int(h * 0.05 + i * h * 0.85 / 4)
                p.drawLine(0, y, w, y)
            path = QPainterPath()
            path.moveTo(coords[0])
            for c in coords[1:]:
                path.lineTo(c)
            pen = QPen(QColor("#6B3F27"))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawPath(path)
            p.setBrush(QColor("#6B3F27"))
            p.setPen(QPen(QColor("white"), 2))
            p.drawEllipse(coords[-1], 5, 5)
            p.end()

        chart_widget.paintEvent = lambda event: paint_chart(chart_widget, event)
        sales_layout.addWidget(chart_widget)

        axis_row = QHBoxLayout()
        for year in ["2021", "2022", "2023", "2024"]:
            lbl = QLabel(year)
            lbl.setStyleSheet("color: #AAA; font-size: 10px; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            axis_row.addWidget(lbl)
        sales_layout.addLayout(axis_row)

        # ── Card 2: Bake Target donut ──────────────────────────────────────────
        donut_card = QWidget(right_widget)
        donut_card.setStyleSheet(card_style)
        donut_card.setGraphicsEffect(make_shadow(radius=20, offset_y=5, opacity=100))

        donut_layout = QVBoxLayout(donut_card)
        donut_layout.setContentsMargins(10, 14, 10, 14)
        donut_layout.setSpacing(6)
        donut_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        donut_widget = QWidget()
        donut_widget.setFixedSize(80, 80)
        donut_widget.setStyleSheet("background: transparent;")

        def paint_donut(widget, event):
            from PyQt6.QtGui import QPainter, QPen, QColor, QFont as QF
            from PyQt6.QtCore import QRectF
            p = QPainter(widget)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(8, 8, 64, 64)
            pen = QPen(QColor("#E8E0D8"))
            pen.setWidth(10)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(rect, 0, 360 * 16)
            pen = QPen(QColor("#6B3F27"))
            pen.setWidth(10)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(rect, 90 * 16, -int(0.42 * 360 * 16))
            p.setPen(QPen(QColor("#1a1a1a")))
            f = QF("Arial", 11, QF.Weight.Bold)
            p.setFont(f)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "42%")
            p.end()

        donut_widget.paintEvent = lambda event: paint_donut(donut_widget, event)

        total_label = QLabel("Total")
        total_label.setStyleSheet("color: #AAA; font-size: 10px; background: transparent;")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bake_label = QLabel("Bake target")
        bake_label.setStyleSheet("color: #555; font-size: 10px; background: transparent;")
        bake_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        donut_layout.addWidget(donut_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        donut_layout.addWidget(total_label)
        donut_layout.addWidget(bake_label)

        # ── Card 3: Name card ──────────────────────────────────────────────────
        name_card = QWidget(right_widget)
        name_card.setStyleSheet("QWidget { background-color: white; border-radius: 5px; }")
        name_card.setGraphicsEffect(make_shadow(radius=20, offset_y=5, opacity=80))

        name_layout = QVBoxLayout(name_card)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel("<i>Popeye's Bakery</i>")
        name_label.setTextFormat(Qt.TextFormat.RichText)
        name_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #1a1a1a; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_layout.addWidget(name_label)

        # ── Card 4: Description ────────────────────────────────────────────────
        desc_card = QWidget(right_widget)
        desc_card.setStyleSheet("QWidget { background-color: white; border-radius: 10px; }")
        desc_card.setGraphicsEffect(make_shadow(radius=20, offset_y=5, opacity=100))

        desc_layout = QVBoxLayout(desc_card)
        desc_layout.setContentsMargins(20, 16, 20, 16)

        desc_label = QLabel("At Popeye's Bakery, every loaf, pastry, and roll is crafted from the finest ingredients — baked fresh daily to bring warmth and flavor to your table.")
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet("color: #555; background: transparent;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_layout.addWidget(desc_label)

        # ── Position cards absolutely using resizeEvent ────────────────────────
        self.sales_card = sales_card
        self.donut_card = donut_card
        self.name_card = name_card
        self.desc_card = desc_card

        def position_cards():
            rw = right_widget.width()
            rh = right_widget.height()
            pad = 30

            # Sales card: top, slightly right of center
            sw, sh = int(rw * 0.72), 185
            sales_card.setGeometry(int(rw * 0.08), int(rh * 0.12), sw, sh)

            # Donut card: middle right, overlapping sales card bottom
            dw, dh = 140, 160
            donut_card.setGeometry(rw - dw - pad, int(rh * 0.30), dw, dh)

            # Name card: lower left
            nw, nh = int(rw * 0.42), 40
            name_card.setGeometry(50, int(rh * 0.60), nw, nh)

            # Description card: lower right, overlapping name card
            ew, eh = int(rw * 0.62), 110
            desc_card.setGeometry(int(rw * 0.27), int(rh * 0.65), ew, eh)

        self._position_cards = position_cards

        # Raise all cards above background
        for c in [sales_card, donut_card, name_card, desc_card]:
            c.raise_()
        name_card.raise_()

        # Connect signals
        self.username_input.textChanged.connect(lambda: (
            self.clear_input_error("username"),
            self.username_error.setVisible(False)
        ))
        self.password_input.textChanged.connect(lambda: (
            self.clear_input_error("password"),
            self.password_error.setVisible(False)
        ))
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

        # ── Close button ───────────────────────────────────────────────────────
        self.close_btn = QPushButton("", central_widget); self.close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
                border-radius: 6px;
            }
        """)
        self.close_btn.clicked.connect(self.confirm_exit)
        self.close_btn.raise_()

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)

    # ── Helper styles ──────────────────────────────────────────────────────────

    def _input_style_normal(self):
        return """
            QLineEdit {
                padding: 10px 14px;
                border: 1.5px solid #D9CFC7;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #8B6347;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #AAAAAA;
            }
        """

    def _input_style_error(self):
        return """
            QLineEdit {
                padding: 10px 14px;
                border: 1.5px solid #C0392B;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
                background-color: #fff5f5;
                color: #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #C0392B;
                background-color: #fff5f5;
            }
        """

    def _password_frame_style_normal(self):
        return """
            QFrame#passwordFrame {
                background-color: white;
                border: 1.5px solid #D9CFC7;
                border-radius: 8px;
            }
        """

    def _password_frame_style_focus(self):
        return """
            QFrame#passwordFrame {
                background-color: white;
                border: 1.5px solid #8B6347;
                border-radius: 8px;
            }
        """

    def _password_frame_style_error(self):
        return """
            QFrame#passwordFrame {
                background-color: #fff5f5;
                border: 1.5px solid #C0392B;
                border-radius: 8px;
            }
        """

    def _password_frame_style_success(self):
        return """
            QFrame#passwordFrame {
                background-color: white;
                border: 1.5px solid #4CAF50;
                border-radius: 8px;
            }
        """

    # ── SVG Icon helpers ───────────────────────────────────────────────────────

    def _make_svg_icon(self, visible: bool) -> QIcon:
        svg_data = self.EYE_OPEN_SVG if visible else self.EYE_OFF_SVG
        renderer = QSvgRenderer(QByteArray(svg_data))
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setIcon(self._make_svg_icon(visible=True))
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setIcon(self._make_svg_icon(visible=False))

    # ── Error / shake helpers ──────────────────────────────────────────────────

    def shake_label(self, label):
        from PyQt6.QtCore import QTimer
        offsets = [6, -6, 5, -5, 4, -4, 2, -2, 0]
        original_pos = label.pos()

        def move_step(i=0):
            if i < len(offsets):
                label.move(original_pos.x() + offsets[i], original_pos.y())
                QTimer.singleShot(30, lambda: move_step(i + 1))
            else:
                label.move(original_pos)

        move_step()

    def set_input_error(self, field: str):
        if field == "username":
            self.username_input.setStyleSheet(self._input_style_error())
        elif field == "password":
            self.password_input.parent().setStyleSheet(self._password_frame_style_error())

    def clear_input_error(self, field: str):
        if field == "username":
            self.username_input.setStyleSheet(self._input_style_normal())
        elif field == "password":
            self.password_input.parent().setStyleSheet(self._password_frame_style_normal())

    # ── Spinner ────────────────────────────────────────────────────────────────

    def start_spinner(self):
        from PyQt6.QtCore import QTimer
        self._spinner_angle = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._rotate_spinner)
        self._spinner_timer.start(60)

    def _rotate_spinner(self):
        self._spinner_angle = (self._spinner_angle + 30) % 360
        renderer = QSvgRenderer(QByteArray(self.SPINNER_SVG))
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.translate(10, 10)
        painter.rotate(self._spinner_angle)
        painter.translate(-10, -10)
        renderer.render(painter)
        painter.end()
        self.sign_in_btn.setIcon(QIcon(pixmap))
        self.sign_in_btn.setIconSize(QSize(18, 18))

    def stop_spinner(self):
        if hasattr(self, '_spinner_timer'):
            self._spinner_timer.stop()
            self._spinner_timer.deleteLater()
        self.sign_in_btn.setIcon(QIcon())
        self.sign_in_btn.setText("Sign In")
        self.sign_in_btn.setEnabled(True)

    # ── Login logic ────────────────────────────────────────────────────────────

    def handle_login(self):
        from PyQt6.QtCore import QTimer

        if self.is_locked:
            BakeSyncAlert.show_warning(
                self, 
                "Account Locked", 
                f"Please wait {self.lock_timer_count} seconds before trying again."
            )
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.username_error.setVisible(False)
        self.password_error.setVisible(False)
        self.clear_input_error("username")
        self.clear_input_error("password")

        has_error = False

        if not username:
            self.username_error.setText("Username is required.")
            self.username_error.setVisible(True)
            self.set_input_error("username")
            self.shake_label(self.username_error)
            has_error = True

        if not password:
            self.password_error.setText("Password is required.")
            self.password_error.setVisible(True)
            self.set_input_error("password")
            self.shake_label(self.password_error)
            has_error = True

        if has_error:
            return

        self.sign_in_btn.setText("  Signing in...")
        self.sign_in_btn.setEnabled(False)
        self.start_spinner()

        QTimer.singleShot(2000, lambda: self._verify_credentials(username, password))

    def _verify_credentials(self, username, password):
        self.stop_spinner()
        self._login_success = False

        account = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

        # ── PERSISTENT ACCOUNT LOCK (naka-save sa DB, hindi nare-reset ng pag-restart) ──
        if account and account['locked_until']:
            remaining = self.db.fetch_one(
                "SELECT CAST((julianday(?) - julianday('now','localtime')) * 86400 AS INTEGER) AS secs",
                (account['locked_until'],))['secs']
            if remaining > 0:
                log_activity(self.db, username, "sign-in blocked", "signin",
                             "Tried to sign in while the account is locked")
                self.start_lockout(remaining)
                return

        user = account if account and verify_password(account['password'], password) else None
        if user:
            updates = "failed_attempts = 0, locked_until = NULL"
            params = [user['id']]
            if not is_hashed(user['password']):
                # Upgrade a legacy plaintext row on first successful login
                updates += ", password = ?"
                params.insert(0, hash_password(password))
            self.db.execute_query(f"UPDATE users SET {updates} WHERE id = ?", tuple(params))

        if user:
            # ── PENDING STATUS CHECK ──
            if user['status'] == 'Archived' or ('is_archived' in user.keys() and user['is_archived']):
                log_activity(self.db, username, "sign-in blocked", "signin", "Account is archived")
                BakeSyncAlert.show_warning(
                    self, "Account Not Active",
                    "This account has been turned off by the Administrator.\n\nPlease ask your manager.")
                self.password_input.clear()
                return

            if user['status'] == 'Pending':
                BakeSyncAlert.show_info(
                    self,
                    "Account Pending Approval",
                    f"Hi {username}, your account has been created but is still waiting for Administrator approval.\n\nPlease contact your manager or wait until your access is granted before trying to log in."
                )
                self.password_input.clear()
                return

            # ── FIRST TIME LOGIN (TERMS & CONDITIONS) CHECK ──
            # I-check kung may 'terms_accepted' na column at kung 0 pa siya
            terms_accepted = user['terms_accepted'] if 'terms_accepted' in user.keys() else 1 
            
            if terms_accepted == 0:
                # Ipakita ang T&C
                tc_dialog = TermsAndConditionsDialog(self)
                if tc_dialog.exec():
                    # Kung nag-agree, i-update ang database para hindi na lumabas ulit
                    self.db.execute_query("UPDATE users SET terms_accepted = 1 WHERE id = ?", (user['id'],))
                    
                    # Ipakita ang Welcome Greeting
                    welcome = WelcomeGreetingDialog(username, user['role'], self)
                    welcome.exec()
                else:
                    # Kung nag-decline, i-cancel ang pag-login
                    BakeSyncAlert.show_warning(self, "Login Cancelled", "You must agree to the Terms and Conditions to access the system.")
                    self.password_input.clear()
                    return

            # ── DEFAULT / TEMPORARY PASSWORD CHECK ──
            # Kailangang magpalit ng password bago makapasok (default accounts, o ni-reset ng Admin)
            if 'must_change_password' in user.keys() and user['must_change_password']:
                if not ChangePasswordDialog(self.db, user, self).exec():
                    BakeSyncAlert.show_warning(self, "Login Cancelled", "You need to set a new password before you can use BakeSync.")
                    self.password_input.clear()
                    return

            # ── PROCEED TO LOGIN ──
            self.failed_attempts = 0
            log_activity(self.db, username, "signed in", "signin", f"Role: {user['role']}")
            self.show_success_popup(username, user['role'])
        else:
            # Dagdagan ang failed attempts. Kilalang account: naka-save sa DB (5-minute lock);
            # hindi kilalang username: sa memory lang (30-second cooldown)
            if account:
                self.failed_attempts = (account['failed_attempts'] or 0) + 1
                if self.failed_attempts >= 3:
                    self.db.execute_query(
                        "UPDATE users SET failed_attempts = 0, locked_until = datetime('now','localtime','+5 minutes') WHERE id = ?",
                        (account['id'],))
                    log_activity(self.db, username, "account locked", "signin",
                                 "3 wrong passwords in a row - locked for 5 minutes")
                else:
                    self.db.execute_query("UPDATE users SET failed_attempts = ? WHERE id = ?",
                                          (self.failed_attempts, account['id']))
                    log_activity(self.db, username, "sign-in failed", "signin",
                                 f"Wrong password (try {self.failed_attempts} of 3)")
            else:
                self.failed_attempts += 1
                log_activity(self.db, username, "sign-in failed", "signin", "Unknown username")

            if self.failed_attempts >= 3:
                self.start_lockout(300 if account else 30)
            else:
                attempts_left = 3 - self.failed_attempts
                self.password_error.setText(f"Invalid username or password. ({attempts_left} attempts left)")
                self.password_input.clear()
                self.password_error.setVisible(True)
                self.set_input_error("username")
                self.set_input_error("password")
                self.shake_label(self.password_error)

    # ── Bagong Lockout System ──────────────────────────────────────────────────
    def start_lockout(self, seconds=30):
        self.is_locked = True
        self.lock_timer_count = seconds
        
        # I-disable ang mga input at button
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.sign_in_btn.setEnabled(False)
        self.sign_in_btn.setText(f"Locked ({self.lock_timer_count}s)")
        self.sign_in_btn.setStyleSheet("background-color: #A0A0A0; color: white; border-radius: 8px; font-size: 15px; padding: 12px; border: none;")

        # Ipakita yung magandang BakeSyncAlert warning mo
        BakeSyncAlert.show_warning(
            self, 
            "Too Many Failed Attempts", 
            "For security reasons, your login capability has been temporarily disabled.", 
            {"Status": "Locked",
             "Timeout": f"{seconds // 60} minute(s) {seconds % 60} second(s)" if seconds >= 60 else f"{seconds} seconds"}
        )
        
        # Simulan ang countdown
        self.lockout_timer = QTimer(self)
        self.lockout_timer.timeout.connect(self.update_lockout)
        self.lockout_timer.start(1000) # Tumitibok every 1000ms (1 second)

    def update_lockout(self):
        self.lock_timer_count -= 1
        
        if self.lock_timer_count > 0:
            # Update yung text ng button para makita nila ang countdown
            self.sign_in_btn.setText(f"Locked ({self.lock_timer_count}s)")
        else:
            # Tapos na ang 30 seconds
            self.lockout_timer.stop()
            self.is_locked = False
            self.failed_attempts = 0
            
            # I-enable ulit ang form
            self.username_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.password_input.clear()
            self.sign_in_btn.setEnabled(True)
            self.sign_in_btn.setText("Sign In")
            
            # I-balik sa original styling ang button
            self.sign_in_btn.setStyleSheet("""
                QPushButton#signInBtn {
                    background-color: #5C2D0E;
                    color: white;
                    border-radius: 8px;
                    font-size: 15px;
                    font-family: 'Segoe UI', sans-serif;
                    font-weight: 500;
                    padding: 12px;
                    border: none;
                    letter-spacing: 0.3px;
                }
                QPushButton#signInBtn:hover { background-color: #7A3D15; }
                QPushButton#signInBtn:pressed { background-color: #4A2208; }
            """)
            
            # Optional: Ipaalam sa kanila na pwede na ulit
            BakeSyncAlert.show_info(self, "Account Unlocked", "You can now try logging in again.")

    def show_success_popup(self, username, role):
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout
        from PyQt6.QtSvg import QSvgRenderer

        self._login_success = True
        self.username_input.clearFocus()
        self.password_input.clearFocus()

        # ── Disable dragging ───────────────────────────────────────────────────
        self._drag_disabled = True

        # ── Overlay dim screen ─────────────────────────────────────────────────
        self._overlay = QWidget(self.centralWidget())
        self._overlay.setStyleSheet("background-color: rgba(0, 0, 0, 140);")
        self._overlay.setGeometry(self.centralWidget().rect())
        self._overlay.raise_()
        self._overlay.show()

        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 1.5px solid #4CAF50;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #333;
            }
        """)
        self.password_input.parent().setStyleSheet(self._password_frame_style_success())

        self.sign_in_btn.setText("Redirecting...")
        self.sign_in_btn.setStyleSheet("""
            QPushButton#signInBtn {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-size: 15px;
                padding: 12px;
                border: none;
            }
        """)

        from PyQt6.QtWidgets import QWidget as _QWidget
        self._redirect_progress = _QWidget(self.sign_in_btn)
        self._redirect_progress.setStyleSheet("background-color: rgba(21,110,10,0.6); border-radius: 2px;")
        self._redirect_progress.show()
        self._redirect_progress.raise_()
        self._progress_value = 0

        def update_progress():
            self._progress_value += 1
            btn_w = self.sign_in_btn.width()
            btn_h = self.sign_in_btn.height() or self.sign_in_btn.minimumHeight()
            progress_width = int((self._progress_value / 100) * btn_w)
            self._redirect_progress.setGeometry(0, btn_h - 6, progress_width, 6)
            self._redirect_progress.raise_()
            if self._progress_value >= 100:
                self._progress_timer.stop()

        QTimer.singleShot(50, update_progress)
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(update_progress)
        self._progress_timer.start(20)

        popup = QDialog(self)
        popup.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        popup.setFixedSize(300, 72)
        popup.setStyleSheet("""
            QDialog {
                background-color: #4CAF50;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border: 1px solid #e0e0e0;
                border-left: 5px solid #4CAF50;
            }
        """)

        geo = self.geometry()
        popup.move(geo.x() + geo.width() - popup.width(), geo.y())

        outer_layout = QHBoxLayout(popup)
        outer_layout.setContentsMargins(7, 0, 0, 0)
        outer_layout.setSpacing(0)

        inner = QWidget()
        inner.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border: none;
            }
        """)
        outer_layout.addWidget(inner)

        main_layout = QHBoxLayout(inner)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(12)

        CHECK_SVG = b"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
            stroke="#4CAF50" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
        </svg>
        """
        renderer = QSvgRenderer(QByteArray(CHECK_SVG))
        pixmap = QPixmap(28, 28)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        title_label = QLabel("Successfully Logged In")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1a1a1a;")

        sub_label = QLabel(f"Welcome Back! <b>{username}</b>.")
        sub_label.setTextFormat(Qt.TextFormat.RichText)
        sub_label.setStyleSheet("color: #888; font-size: 11px;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(sub_label)

        main_layout.addWidget(icon_label)
        main_layout.addLayout(text_layout)

        popup.show()
        popup.raise_()
        QTimer.singleShot(2500, lambda: (popup.close(), self.login_success.emit(username, role), self.close()))

    def show_forgot_password(self):
        dlg = ForgotPasswordDialog(self)
        dlg.exec()

    def focusInEvent_password(self, event):
        self.password_input.parent().setStyleSheet(self._password_frame_style_focus())
        QLineEdit.focusInEvent(self.password_input, event)

    def focusOutEvent_password(self, event):
        if not getattr(self, '_login_success', False):
            self.password_input.parent().setStyleSheet(self._password_frame_style_normal())
        QLineEdit.focusOutEvent(self.password_input, event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 46, 10)
            self.close_btn.raise_()
        if hasattr(self, '_position_cards'):
            self._position_cards()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 46, 10)
            self.close_btn.raise_()
        if hasattr(self, '_position_cards'):
            self._position_cards()
        if hasattr(self, '_overlay') and self._overlay.isVisible():
            self._overlay.setGeometry(self.centralWidget().rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not getattr(self, '_drag_disabled', False):
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos') and not getattr(self, '_drag_disabled', False):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()




# ── Sign Up Navigation ─────────────────────────────────────────────────────
    
    def open_signup_window(self):
        # Gumawa ng instance ng SignUpWindow
        self.signup_window = SignUpWindow()
        
        # Kapag nag-trigger ang return_to_login (pagka-cancel or success), ibabalik ang login screen
        self.signup_window.return_to_login.connect(self.show)
        
        # Ipakita ang Sign Up, itago ang Login
        self.signup_window.show()
        self.hide()
    
    def show_forgot_password(self):
        # Gumawa ng instance ng ForgotPasswordWindow
        self.forgot_window = ForgotPasswordWindow()
        
        # Kapag natapos o kinancel, ibabalik ang Login screen
        self.forgot_window.return_to_login.connect(self.show)
        
        # Ipakita ang Forgot Password, itago ang Login
        self.forgot_window.show()
        self.hide()


# ── EXIT CONFIRMATION ──────────────────────────────────────────────────────
    def confirm_exit(self):
        # Tatawagin natin yung BakeSyncAlert para maganda at uniform ang pop-up
        response = BakeSyncAlert.ask_yes_no(
            self, 
            "Exit Application", 
            "Are you sure you want to exit Popeye's Bakery?", 
            yes_text="YES", 
            no_text="NO"
        )
        
        # Kung True ang response (pinindot ang YES), isasara na ang window
        if response:
            QApplication.quit() # Para siguradong patay ang buong program

# --- ITO YUNG PINAKA-DULO NG FILE MO ---
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())