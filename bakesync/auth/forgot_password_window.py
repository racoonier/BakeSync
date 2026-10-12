from bakesync.paths import CACHE_DIR, IMAGES_DIR
import os
import json
import random
import time 
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QApplication, 
                             QFrame, QStackedWidget, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer

# Idagdag sa pinakataas
import smtplib
from bakesync.core.app_config import get_setting
from bakesync.core.auth_utils import hash_password, verify_password
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from bakesync.core.database import DatabaseManager
from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix



# ── DITO MAGSISIMULA ANG CLASS MO ──
class ForgotPasswordWindow(QMainWindow):
    return_to_login = pyqtSignal()
    
    # ---> DITO DAPAT NAKAPWESTO ANG METHOD_LOCKOUTS <---
    METHOD_LOCKOUTS = {
        "gmail": 0.0,
        "masterkey": 0.0,
        "security": 0.0
    }
    
    # ── Vector SVGs ────────────────────────────────────────────────────────
    EYE_OPEN_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>"""
    EYE_OFF_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#888888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>"""
    CHECK_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>"""
    LOCK_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#5C2D0E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>"""
    MAIL_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>"""
    KEY_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg>"""
    SHIELD_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>"""
    SPINNER_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#5C2D0E" stroke-width="2.5" stroke-linecap="round"><path d="M12 2a10 10 0 0 1 10 10" opacity="1"/><path d="M12 2a10 10 0 0 0-10 10" opacity="0.3"/><path d="M22 12a10 10 0 0 1-10 10" opacity="0.6"/><path d="M2 12a10 10 0 0 0 10 10" opacity="0.15"/></svg>"""


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forgot Password - POPEYE'S Bakery")
        self.setMinimumSize(900, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 900) // 2, (screen.height() - 600) // 2)
        
        self.setStyleSheet("QMainWindow { background-color: #FFFFFF; }")
        self.db = DatabaseManager()
        self.user_data = {} # Dito isi-save yung record ng user pag nahanap sa DB
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── LEFT SIDE (Wizard) ──
        left_widget = QWidget()
        left_widget.setObjectName("leftWidget")
        left_widget.setStyleSheet("QWidget#leftWidget { background-color: #FFFFFF; }")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(60, 40, 60, 30)

        self.title_label = QLabel("Password Recovery")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #1A1A1A;")
        left_layout.addWidget(self.title_label)

        self.step_label = QLabel("Step 1 of 4")
        self.step_label.setStyleSheet("color: #888; font-size: 13px; font-family: 'Segoe UI';")
        left_layout.addWidget(self.step_label)
        left_layout.addSpacing(20)

        self.stack = QStackedWidget()
        left_layout.addWidget(self.stack)

        self.setup_step_1_username()
        self.setup_step_2_method()
        self.setup_step_3a_gmail()
        self.setup_step_3b_masterkey()
        self.setup_step_3c_security()
        self.setup_step_4_new_password()
        self.setup_step_5_success()

        # ── RIGHT SIDE (Background Image & Logo) ──
        self.right_widget = QWidget()
        self.right_widget.setObjectName("rightWidget")
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        script_dir = os.path.dirname(__file__)
        bg_pixmap = QPixmap(os.path.join(IMAGES_DIR, "popbg.png"))
        
        if not bg_pixmap.isNull():
            bg_pixmap = bg_pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            temp_bg_path = os.path.join(CACHE_DIR, "popbg_resized.png").replace("\\", "/")
            bg_pixmap.save(temp_bg_path)
            self.right_widget.setStyleSheet(f"QWidget#rightWidget {{ background-image: url({temp_bg_path}); background-position: center; background-repeat: no-repeat; background-color: #E8E0D8; }}")
        else:
            self.right_widget.setStyleSheet("QWidget#rightWidget { background-color: #E8E0D8; }")
            
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(IMAGES_DIR, "poplogo.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        right_layout.addWidget(logo_label)

        self.close_btn = QPushButton("", central_widget); self.close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("QPushButton { color: white; background: transparent; border: none; font-size: 20px; font-weight: bold;} QPushButton:hover { background-color: rgba(0, 0, 0, 40); border-radius: 6px; }")
        self.close_btn.clicked.connect(self.cancel_recovery)
        self.close_btn.move(850, 10)

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(self.right_widget, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 46, 10)

    # ── SETUP STEPS ────────────────────────────────────────────────────────

    def setup_step_1_username(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        info = QLabel("Enter your username to begin the recovery process.")
        info.setStyleSheet("color: #555; font-size: 13px; font-family: 'Segoe UI'; margin-bottom: 10px;")
        layout.addWidget(info)

        self.s1_user, self.s1_user_err = self._create_input("Username", layout, " ")
        
        # ---> I-connect natin sa bagong real-time method <---
        self.s1_user.textChanged.connect(self._rt_check_username)
        
        layout.addSpacing(15)
        
        # ---> Gawing instance variable ang button para ma-disable natin <---
        self.btn_verify_username = self._create_btn("Verify Username")
        self.btn_verify_username.clicked.connect(self.validate_username)
        
        # Naka-disable at gray ang button by default
        self.btn_verify_username.setEnabled(False)
        self.btn_verify_username.setStyleSheet("QPushButton { background-color: #A0A0A0; color: white; border-radius: 4px; font-size: 14px; font-weight: bold;}")
        
        layout.addWidget(self.btn_verify_username)

        layout.addSpacing(15)
        login_link = QPushButton("Remember your password? Login.")
        login_link.setCursor(Qt.CursorShape.PointingHandCursor)
        login_link.setStyleSheet("QPushButton { background: transparent; color: #5C2D0E; border: none; font-size: 13px; font-family: 'Segoe UI'; font-weight: bold;} QPushButton:hover { text-decoration: underline; color: #7A3D15; }")
        login_link.clicked.connect(self.cancel_recovery)
        layout.addWidget(login_link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        self.stack.addWidget(page)
    
    def _rt_check_username(self):
        username = self.s1_user.text().strip()
        
        # Helper function para i-disable ang button at kulayan ng gray
        def disable_btn():
            self.btn_verify_username.setEnabled(False)
            self.btn_verify_username.setStyleSheet("QPushButton { background-color: #A0A0A0; color: white; border-radius: 4px; font-size: 14px; font-weight: bold;}")

        # Kapag binura at walang laman
        if not username:
            self._clear_err(self.s1_user, self.s1_user_err, " ")
            disable_btn()
            return

        # Hanapin agad sa database
        user_db = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        
        # Kapag wala sa database
        if not user_db:
            self._set_err(self.s1_user, self.s1_user_err, "Username not found.", shake=False)
            disable_btn()
            return
            
        status = user_db['status']
        is_archived = user_db['is_archived']

        # Kapag naka-archive o inactive
        if is_archived == 1 or status.lower() == 'inactive':
            self._set_err(self.s1_user, self.s1_user_err, "Account is inactive or archived.", shake=False)
            disable_btn()
            return
            
        # Kapag pending pa rin
        if status.lower() == 'pending':
            self._set_err(self.s1_user, self.s1_user_err, "Account is still pending approval.", shake=False)
            disable_btn()
            return

        # KAPAG PASADO NA LAHAT (Green state)
        self._set_success(self.s1_user, self.s1_user_err)
        self.s1_user_err.setText("Username found") # In-overwrite natin yung default na "Looks good!"
        
        # Buhayin ang button at ibalik sa kulay brown
        self.btn_verify_username.setEnabled(True)
        self.btn_verify_username.setStyleSheet("QPushButton { background-color: #5C2D0E; color: white; border-radius: 4px; font-size: 14px; font-weight: bold;} QPushButton:hover { background-color: #4A2208; }")

    def setup_step_2_method(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        info = QLabel("How would you like to verify your identity?")
        info.setStyleSheet("color: #555; font-size: 14px; font-family: 'Segoe UI'; margin-bottom: 15px; font-weight: bold;")
        layout.addWidget(info)

        # ── GAGAWA TAYO NG CLICKABLE CARDS ──
        self._create_method_card("Send OTP via Gmail", "Receive a 6-digit code on your registered email.", self.MAIL_SVG, "gmail", layout)
        self._create_method_card("Enter Mastery Key", "Use the recovery key provided during registration.", self.KEY_SVG, "masterkey", layout)
        self._create_method_card("Answer Security Question", "Verify your identity using your secret answers.", self.SHIELD_SVG, "security", layout)

        layout.addSpacing(15) 
        
        # ── INAYOS NA BACK BUTTON (Full Width) ──
        back_btn = self._create_btn("Back to Username", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(0))
        layout.addWidget(back_btn)
        
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_3a_gmail(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        self.gmail_desc = QLabel("An OTP has been sent to your registered email.\n(Hint: For this demo, enter 123456)")
        self.gmail_desc.setStyleSheet("color: #555; font-size: 13px; font-family: 'Segoe UI'; margin-bottom: 10px;")
        layout.addWidget(self.gmail_desc)

        lbl = QLabel("Enter 6-Digit OTP")
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        # ── 6 OTP BOXES SETUP ──
        otp_layout = QHBoxLayout()
        otp_layout.setSpacing(10)
        self.otp_boxes = []

        # Style para sa bawat maliit na box
        box_style = """
            QLineEdit {
                border: 1.5px solid #D9CFC7;
                border-radius: 8px;
                font-size: 24px;
                font-weight: bold;
                color: #5C2D0E;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #8B6347;
                background-color: #FCF9F6;
            }
        """

        for i in range(6):
            box = QLineEdit()
            box.setMaxLength(1) # Isang number lang pwede
            box.setFixedSize(50, 60) # Malaki para kitang-kita
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setStyleSheet(box_style)
            
            # Connect text change for auto-focus next
            box.textEdited.connect(lambda text, idx=i: self._on_otp_edited(text, idx))
            
            otp_layout.addWidget(box)
            self.otp_boxes.append(box)

        otp_layout.addStretch() # Push everything to the left
        layout.addLayout(otp_layout)

        # Error label underneath
        self.s3a_otp_err = QLabel(" ")
        self.s3a_otp_err.setStyleSheet("color: #C0392B; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.s3a_otp_err)

        layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(1))
        next_btn = self._create_btn("Verify OTP")
        next_btn.clicked.connect(self.validate_gmail)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def _on_otp_edited(self, text, index):
        """Auto-focus next box kapag may nag-type, auto-focus prev box kapag nag-delete."""
        # Kung nag-type ng number
        if text.isdigit():
            # Ilipat sa next box kung hindi pa huli
            if index < 5:
                self.otp_boxes[index + 1].setFocus()
        # Kung binura
        elif text == "":
            # Ilipat sa prev box kung hindi pa nasa una
            if index > 0:
                self.otp_boxes[index - 1].setFocus()
        else:
            # Kung hindi number ang tinype, burahin
            self.otp_boxes[index].clear()

    def setup_step_3b_masterkey(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        info = QLabel("Please enter the Mastery Key provided during registration.")
        info.setStyleSheet("color: #555; font-size: 13px; font-family: 'Segoe UI'; margin-bottom: 10px;")
        layout.addWidget(info)

        self.s3b_key, self.s3b_key_err = self._create_input("Mastery Key (e.g. PY-12345)", layout, " ")

        layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(1))
        next_btn = self._create_btn("Verify Key")
        next_btn.clicked.connect(self.validate_masterkey)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_3c_security(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        
        info = QLabel("Answer the security questions below to verify your identity.")
        info.setStyleSheet("color: #555; font-size: 13px; font-family: 'Segoe UI'; margin-bottom: 10px;")
        layout.addWidget(info)

        # ── ISANG DISPLAY LABEL LANG ──
        self.s3c_question_lbl = QLabel("Loading question...")
        self.s3c_question_lbl.setStyleSheet("color: #333; font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; margin-bottom: 10px;")
        self.s3c_question_lbl.setWordWrap(True)
        layout.addWidget(self.s3c_question_lbl)

        self.s3c_ans, self.s3c_ans_err = self._create_input("Your Answer", layout, " ")

        layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(1))
        
        next_btn = self._create_btn("Verify Answer")
        next_btn.clicked.connect(self.validate_security)
        
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_4_new_password(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)

        self.s4_pass, self.s4_pass_err, _ = self._create_password_input("New Password", layout, " ")
        self.s4_pass.textChanged.connect(self._rt_check_pass)
        
        req_layout = QVBoxLayout()
        req_layout.setSpacing(2)
        req_layout.setContentsMargins(5, 0, 0, 10)
        self.req_len = QLabel("• At least 8 characters")
        self.req_case = QLabel("• At least 1 Uppercase & 1 Lowercase")
        self.req_num = QLabel("• At least 1 Number (0-9)")
        self.req_spec = QLabel("• At least 1 Special Character (!, @, #, etc.)")
        
        for req in [self.req_len, self.req_case, self.req_num, self.req_spec]:
            req.setStyleSheet("color: #888; font-size: 11px; font-family: 'Segoe UI';")
            req_layout.addWidget(req)
        layout.addLayout(req_layout)
        
        self.s4_conf, self.s4_conf_err, _ = self._create_password_input("Confirm New Password", layout, " ")
        self.s4_conf.textChanged.connect(self._rt_check_conf)

        layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Cancel", secondary=True)
        back_btn.clicked.connect(self.cancel_recovery)
        next_btn = self._create_btn("Reset Password")
        next_btn.clicked.connect(self.validate_new_password)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_5_success(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel()
        icon.setPixmap(self._svg_to_pixmap(self.CHECK_SVG, 80, 80))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Password Reset Successful!")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a1a1a;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("You can now log in using your new password.")
        desc.setFont(QFont("Segoe UI", 13))
        desc.setStyleSheet("color: #555;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(30)
        btn = self._create_btn("Return to Login")
        btn.clicked.connect(self.cancel_recovery)
        layout.addWidget(btn)
        self.stack.addWidget(page)



    # ── BAGONG METHOD CARDS & LOGIC ────────────────────────────────────────

    def _create_method_card(self, title, subtitle, svg_icon, method_id, layout):
        frame = QFrame()
        frame.setObjectName("methodCard")
        
        # Check kung naka-lock pa ang method na 'to
        is_locked = time.time() < ForgotPasswordWindow.METHOD_LOCKOUTS.get(method_id, 0.0)
        
        if is_locked:
            # ── LOCKED STATE STYLING ──
            frame.setStyleSheet("""
                QFrame#methodCard { 
                    background-color: #F5F5F5; 
                    border: 1.5px solid #E0E0E0; 
                    border-radius: 10px; 
                }
            """)
            frame.setCursor(Qt.CursorShape.ForbiddenCursor)
            icon_color = "#AAAAAA"
            title_color = "#999999"
            sub_color = "#C0392B" # Red text para sa warning
            subtitle = "Temporarily locked due to multiple failed attempts."
        else:
            # ── NORMAL STATE STYLING ──
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            frame.setStyleSheet("""
                QFrame#methodCard { 
                    background-color: #FFFFFF; 
                    border: 1.5px solid #D9CFC7; 
                    border-radius: 10px; 
                }
                QFrame#methodCard:hover { 
                    border: 1.5px solid #8B6347; 
                    background-color: #FCF9F6; 
                }
            """)
            icon_color = "#5C2D0E"
            title_color = "#333333"
            sub_color = "#888888"

        frame.setFixedHeight(75)
        
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(20, 10, 20, 10)
        hl.setSpacing(15)
        
        icon = QLabel()
        icon.setPixmap(self._svg_to_pixmap(svg_icon, 28, 28, icon_color))
        icon.setStyleSheet("border: none; background: transparent;") 
        hl.addWidget(icon)
        
        vl = QVBoxLayout()
        vl.setSpacing(2)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {title_color}; border: none; background: transparent; font-family: 'Segoe UI';")
        
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {sub_color}; border: none; background: transparent; font-family: 'Segoe UI';")
        
        vl.addWidget(lbl_title)
        vl.addWidget(lbl_sub)
        vl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        hl.addLayout(vl)
        hl.addStretch()
        
        if not is_locked:
            chevron = QLabel("›")
            chevron.setStyleSheet("font-size: 26px; color: #D9CFC7; border: none; background: transparent; padding-bottom: 4px; font-weight: bold;")
            hl.addWidget(chevron)
        else:
            # Maglalagay tayo ng red lock icon kung naka-lock
            lock_icon = QLabel()
            lock_icon.setPixmap(self._svg_to_pixmap(self.LOCK_SVG, 20, 20, "#C0392B"))
            lock_icon.setStyleSheet("border: none; background: transparent;")
            hl.addWidget(lock_icon)
        
        layout.addWidget(frame)
        layout.addSpacing(10)
        
        if is_locked:
            frame.mousePressEvent = lambda e: self._show_lock_alert(method_id)
        else:
            frame.mousePressEvent = lambda e: self.confirm_method(method_id, title)

    def _show_lock_alert(self, method_id):
        lock_expires = ForgotPasswordWindow.METHOD_LOCKOUTS.get(method_id, 0.0)
        rem_seconds = int(lock_expires - time.time())
        rem_minutes = rem_seconds // 60
        rem_seconds = rem_seconds % 60
        
        BakeSyncAlert.show_warning(
            self, 
            "Method Locked", 
            f"This recovery method is temporarily locked.\nPlease try again in {rem_minutes}m {rem_seconds}s or choose another method."
        )

    def confirm_method(self, method_id, title):
        confirm = BakeSyncAlert.ask_yes_no(
            self,
            "Select Recovery Method",
            f"Are you sure you want to reset your password using:\n\n{title}?",
            yes_text="YES, PROCEED",
            no_text="CANCEL"
        )
        if confirm:
            self.show_loading_and_proceed(method_id)

    def show_loading_and_proceed(self, method_id):
        from PyQt6.QtWidgets import QDialog
        self.loading_dlg = QDialog(self)
        self.loading_dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.loading_dlg.setFixedSize(220, 130)
        self.loading_dlg.setModal(True)
        self.loading_dlg.setStyleSheet("QDialog { background-color: white; border: 2px solid #5C2D0E; border-radius: 12px; }")
        
        l_layout = QVBoxLayout(self.loading_dlg)
        l_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_layout.setSpacing(15)
        
        self.spinner_lbl = QLabel()
        self.spinner_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_layout.addWidget(self.spinner_lbl)
        
        # Baguhin natin ang text kung Gmail ang pinili
        msg = "Sending OTP...\nPlease wait." if method_id == "gmail" else "Redirecting...\nPlease wait."
        text_lbl = QLabel(msg)
        text_lbl.setStyleSheet("color: #5C2D0E; font-weight: bold; font-family: 'Segoe UI'; font-size: 13px;")
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_layout.addWidget(text_lbl)
        
        self.spinner_angle = 0
        self.spinner_timer = QTimer(self.loading_dlg)
        self.spinner_timer.timeout.connect(self._animate_spinner)
        self.spinner_timer.start(50)
        
        self.loading_dlg.show()
        
        # Piliting i-update ang UI para mag-drawing ang loading box bago tayo mag-freeze sa pag-send ng email
        QApplication.processEvents()
        
        # I-execute ang action pagkatapos ng maliit na delay para sure na lumabas ang box
        QTimer.singleShot(100, lambda: self.execute_method(method_id))

    def _animate_spinner(self):
        self.spinner_angle = (self.spinner_angle + 30) % 360
        renderer = QSvgRenderer(QByteArray(self.SPINNER_SVG))
        pixmap = QPixmap(34, 34)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.translate(17, 17)
        painter.rotate(self.spinner_angle)
        painter.translate(-17, -17)
        renderer.render(painter)
        painter.end()
        self.spinner_lbl.setPixmap(pixmap)

    def _close_loading(self):
        # Isasara lang natin ang timer at popup kapag TAPOS NA ang trabaho sa likod
        if hasattr(self, 'spinner_timer'):
            self.spinner_timer.stop()
        if hasattr(self, 'loading_dlg'):
            self.loading_dlg.close()

    def execute_method(self, method_id):
        # Tinanggal na natin dito yung .close() sa unahan!
        
        if method_id == "gmail":
            email = self.user_data.get('email', '')
            if not email:
                self._close_loading() # Isara kung nagka-error
                BakeSyncAlert.show_error(self, "No Email Found", "Your account doesn't have a registered email address. Please use another recovery method.")
                return

            if not hasattr(self, 'generated_otp'):
                self.generated_otp = str(random.randint(100000, 999999))
                
                # Para masigurong umiikot muna saglit bago mag-freeze para sa email sending
                QApplication.processEvents() 
                
                # --- MATAGAL NA PART --- (Naka-display ang loading habang nangyayari to)
                success = self.send_otp_email(email, self.generated_otp)
            else:
                success = True 
            
            # --- PAGKATAPOS MAG-SEND, SAKA NATIN ISASARA ANG LOADING ---
            self._close_loading()
            
            if success:
                masked_email = f"{email[:2]}***@gmail.com" if '@' in email else email
                self.gmail_desc.setText(f"An OTP has been sent to {masked_email}.\nPlease check your inbox/spam folder.")
                self.go_to_step(2) 
            else:
                BakeSyncAlert.show_error(self, "Email Failed", "Failed to send OTP. Please check your internet connection or contact Admin.")

        elif method_id == "masterkey":
            self._close_loading()
            self.go_to_step(3) 
            
        elif method_id == "security":
            self._close_loading()
            self.prepare_security_question()
            self.go_to_step(4)
    # ── VALIDATIONS & LOGIC ────────────────────────────────────────────────

    def validate_username(self):
        username = self.s1_user.text().strip()
        if not username:
            self._set_err(self.s1_user, self.s1_user_err, "Please enter a username.", shake=True)
            return

        user_db = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        
        if not user_db:
            self._set_err(self.s1_user, self.s1_user_err, "Username not found in the database.", shake=True)
            return

        status = user_db['status']
        is_archived = user_db['is_archived']

        if is_archived == 1 or status.lower() == 'inactive':
            self._set_err(self.s1_user, self.s1_user_err, "This account is inactive or archived. Please contact Admin.", shake=True)
            return
            
        if status.lower() == 'pending':
            self._set_err(self.s1_user, self.s1_user_err, "Account is still pending approval. Cannot reset password.", shake=True)
            return

        # Passed! Save user data
        self._set_success(self.s1_user, self.s1_user_err)
        self.user_data = dict(user_db) # convert row to dict
        self.go_to_step(1)

    def validate_method(self):
        if self.rb_gmail.isChecked():
            email = self.user_data.get('email', '')
            if not email:
                BakeSyncAlert.show_error(self, "No Email Found", "Your account doesn't have a registered email address. Please use another recovery method.")
                return

            # FIX: I-check muna kung nakapag-generate na tayo ng OTP para hindi paiba-iba
            if not hasattr(self, 'generated_otp'):
                self.generated_otp = str(random.randint(100000, 999999))
                # I-send ang email kapag bagong generate lang
                success = self.send_otp_email(email, self.generated_otp)
            else:
                # Kung nakapag-send na dati, wag na mag-send ulit ng email. Proceed na agad.
                success = True 
            
            if success:
                masked_email = f"{email[:2]}***@gmail.com" if '@' in email else email
                self.gmail_desc.setText(f"An OTP has been sent to {masked_email}.\nPlease check your inbox/spam folder.")
                self.go_to_step(2) 
            else:
                BakeSyncAlert.show_error(self, "Email Failed", "Failed to send OTP. Please check your internet connection or contact Admin.")

        elif self.rb_masterkey.isChecked():
            self.go_to_step(3) 
            
        elif self.rb_security.isChecked():
            self.prepare_security_question()
            self.go_to_step(4) 

    def validate_gmail(self):
        # I-initialize ang attempt counter kung wala pa
        if not hasattr(self, 'gmail_attempts'):
            self.gmail_attempts = 0
            
        entered_otp = "".join([box.text().strip() for box in self.otp_boxes])
        correct_otp = getattr(self, 'generated_otp', '123456').strip()
        
        if len(entered_otp) < 6:
            self.s3a_otp_err.setText("Please enter the complete 6-digit OTP.")
            self.shake_widget(self.otp_boxes[0].parent()) 
            return

        if entered_otp == correct_otp: 
            self.gmail_attempts = 0 # Reset
            self.s3a_otp_err.setText("Code verified")
            self.s3a_otp_err.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 5px;")
            for box in self.otp_boxes:
                box.setStyleSheet("QLineEdit { border: 1.5px solid #4CAF50; border-radius: 8px; font-size: 24px; font-weight: bold; background-color: #F8FFF8; color: #5C2D0E; }")
            self.go_to_step(5) 
        else:
            self.gmail_attempts += 1
            attempts_left = 3 - self.gmail_attempts
            
            if attempts_left > 0:
                self.s3a_otp_err.setText(f"Invalid OTP. ({attempts_left} attempts left)")
                self.shake_widget(self.otp_boxes[0].parent())
                for box in self.otp_boxes:
                    box.setStyleSheet("QLineEdit { border: 1.5px solid #C0392B; border-radius: 8px; font-size: 24px; font-weight: bold; background-color: #fff5f5; color: #5C2D0E; }")
            else:
                # ── TRIGGER 30 MINUTE LOCK ──
                ForgotPasswordWindow.METHOD_LOCKOUTS["gmail"] = time.time() + (30 * 60)
                BakeSyncAlert.show_warning(self, "Method Locked", "You have exceeded the maximum attempts. This method is disabled for 30 minutes.")
                self.cancel_recovery()


    def validate_masterkey(self):
        if not hasattr(self, 'masterkey_attempts'):
            self.masterkey_attempts = 0
            
        key = self.s3b_key.text().strip()
        correct_key = self.user_data.get('mastery_key', '')
        
        if not correct_key:
            BakeSyncAlert.show_error(self, "No Key Found", "Your account doesn't have a Mastery Key set up.")
            return

        if verify_password(correct_key, key):
            self.masterkey_attempts = 0 # Reset
            self._set_success(self.s3b_key, self.s3b_key_err)
            self.go_to_step(5)
        else:
            self.masterkey_attempts += 1
            attempts_left = 3 - self.masterkey_attempts
            
            if attempts_left > 0:
                self._set_err(self.s3b_key, self.s3b_key_err, f"Incorrect Mastery Key. ({attempts_left} attempts left)", shake=True)
            else:
                # ── TRIGGER 30 MINUTE LOCK ──
                ForgotPasswordWindow.METHOD_LOCKOUTS["masterkey"] = time.time() + (30 * 60)
                BakeSyncAlert.show_warning(self, "Method Locked", "You have exceeded the maximum attempts. This method is disabled for 30 minutes.")
                self.cancel_recovery()


    def prepare_security_question(self):
        sec_data_str = self.user_data.get('security_data', '[]')
        try:
            questions = json.loads(sec_data_str) if sec_data_str else []
        except:
            questions = []

        if len(questions) < 2:
            self.s3c_question_lbl.setText("Security Error: Not enough security questions found.")
            self.s3c_ans.setEnabled(False)
            self.expected_answer = None
        else:
            # Pipili ng dalawang distinct questions
            self.selected_sqs = random.sample(questions, 2)
            self.current_sq_index = 0 # 0 para sa unang tanong
            self.security_attempts = 0 # Counter para sa 3 max attempts
            self.s3c_ans.setEnabled(True)
            self._display_current_sq()

    def _display_current_sq(self):
        # I-load yung tanong base sa current index (0 or 1)
        q_obj = self.selected_sqs[self.current_sq_index]
        self.s3c_question_lbl.setText(f"Question {self.current_sq_index + 1} of 2:\n{q_obj['q']}")
        self.expected_answer = q_obj['a'].strip().lower()
        
        # Linisin yung textbox pagka-lipat
        self.s3c_ans.clear()
        self._clear_err(self.s3c_ans, self.s3c_ans_err, " ")
        self.s3c_ans.setFocus()

    def validate_security(self):
        if not hasattr(self, 'expected_answer') or not self.expected_answer:
            return
            
        ans = self.s3c_ans.text().strip().lower()
        
        if ans == self.expected_answer:
            self._set_success(self.s3c_ans, self.s3c_ans_err)
            
            if self.current_sq_index == 0:
                QTimer.singleShot(400, self._move_to_q2)
            else:
                self.security_attempts = 0 # Reset
                QTimer.singleShot(400, lambda: self.go_to_step(5))
        else:
            self.security_attempts += 1
            attempts_left = 3 - self.security_attempts
            
            if attempts_left > 0:
                self._set_err(self.s3c_ans, self.s3c_ans_err, f"Incorrect answer. ({attempts_left} attempts left)", shake=True)
            else:
                # ── TRIGGER 30 MINUTE LOCK ──
                ForgotPasswordWindow.METHOD_LOCKOUTS["security"] = time.time() + (30 * 60)
                self._set_err(self.s3c_ans, self.s3c_ans_err, "Maximum attempts reached.", shake=True)
                BakeSyncAlert.show_warning(
                    self,
                    "Security Verification Failed",
                    "You have exceeded the maximum attempts. This method is disabled for 30 minutes."
                )
                self.cancel_recovery()

    def _move_to_q2(self):
        self.current_sq_index = 1
        self._display_current_sq()

    # ── REAL TIME PASSWORD CHECKS ──
    def _is_strong_password(self, pwd):
        if len(pwd) < 8: return False
        if not any(c.isupper() for c in pwd): return False
        if not any(c.islower() for c in pwd): return False
        if not any(c.isdigit() for c in pwd): return False
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pwd): return False
        return True

    def _update_req_label(self, lbl, condition):
        original_text = lbl.text().replace("✓ ", "").replace("• ", "")
        if condition:
            lbl.setStyleSheet("color: #4CAF50; font-size: 11px; font-family: 'Segoe UI'; font-weight: bold;")
            lbl.setText(f"• {original_text}")
        else:
            lbl.setStyleSheet("color: #888; font-size: 11px; font-family: 'Segoe UI';")
            lbl.setText(f"• {original_text}")
        return condition

    def _rt_check_pass(self):
        text = self.s4_pass.text()
        len_ok = self._update_req_label(self.req_len, len(text) >= 8)
        case_ok = self._update_req_label(self.req_case, any(c.isupper() for c in text) and any(c.islower() for c in text))
        num_ok = self._update_req_label(self.req_num, any(c.isdigit() for c in text))
        spec_ok = self._update_req_label(self.req_spec, any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in text))
        
        all_ok = len_ok and case_ok and num_ok and spec_ok
        if all_ok: self._set_pwd_success(self.s4_pass, self.s4_pass_err)
        elif text: self._set_pwd_err(self.s4_pass, self.s4_pass_err, "Please meet all the requirements below.", shake=False)
        else: self._clear_pwd_err(self.s4_pass, self.s4_pass_err, " ")
        self._rt_check_conf()

    def _rt_check_conf(self):
        pwd = self.s4_pass.text()
        conf = self.s4_conf.text()
        if conf == "": self._clear_pwd_err(self.s4_conf, self.s4_conf_err, " ")
        elif pwd == conf: self._set_pwd_success(self.s4_conf, self.s4_conf_err)
        else: self._set_pwd_err(self.s4_conf, self.s4_conf_err, "Passwords do not match.", shake=False)

    def validate_new_password(self):
        pwd = self.s4_pass.text()
        conf = self.s4_conf.text()

        if not self._is_strong_password(pwd):
            self._set_pwd_err(self.s4_pass, self.s4_pass_err, "Please meet all the requirements below.", shake=True)
            return
        if pwd != conf:
            self._set_pwd_err(self.s4_conf, self.s4_conf_err, "Passwords do not match.", shake=True)
            return

        # Update Database
        try:
            self.db.execute_query("UPDATE users SET password = ? WHERE id = ?", (hash_password(pwd), self.user_data['id']))
            log_activity(self.db, self.user_data['username'], "password reset", "account",
                         "Reset own password with 'Forgot password'")
            self.go_to_step(6) # Success Page
        except Exception as e:
            BakeSyncAlert.show_error(self, "Database Error", f"Failed to reset password: {e}")

    # ── NAVIGATION & HELPERS ────────────────────────────────────────────────

    def cancel_recovery(self):
        self.return_to_login.emit()
        self.close()

    def go_to_step(self, index):
        self.stack.setCurrentIndex(index)
        titles = ["Verify Username", "Recovery Method", "Email Verification", "Mastery Key", "Security Question", "New Password", ""]
        steps = ["Step 1 of 4", "Step 2 of 4", "Step 3 of 4", "Step 3 of 4", "Step 3 of 4", "Step 4 of 4", ""]
        
        self.title_label.setText(titles[index])
        self.step_label.setText(steps[index])
        if index == 6:
            self.title_label.hide(); self.step_label.hide()
        else:
            self.title_label.show(); self.step_label.show()

    def _create_radio_method(self, title, svg_icon, layout):
        frame = QFrame()
        frame.setObjectName("methodFrame")
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Ang buong frame ang nagla-light brown kapag na-hover
        frame.setStyleSheet("""
            QFrame#methodFrame { 
                background-color: #FFFFFF; 
                border: 1.5px solid #D9CFC7; 
                border-radius: 8px; 
            }
            QFrame#methodFrame:hover { 
                border: 1.5px solid #8B6347; 
                background-color: #FCF9F6; 
            }
        """)
        frame.setFixedHeight(65)
        
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(20, 0, 20, 0)
        hl.setSpacing(15)
        
        icon = QLabel()
        icon.setPixmap(self._svg_to_pixmap(svg_icon, 24, 24, "#5C2D0E"))
        icon.setStyleSheet("border: none; background: transparent;") 
        hl.addWidget(icon)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #333; border: none; background: transparent; font-family: 'Segoe UI';")
        hl.addWidget(lbl)
        
        hl.addStretch()
        
        rb = QRadioButton()
        rb.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Inalis ko yung spacing/background properties na posibleng nag-iinterfere
        rb.setStyleSheet("""
            QRadioButton {
                background: transparent;
                border: none;
            }
            QRadioButton::indicator { 
                width: 16px; 
                height: 16px; 
                border-radius: 10px; /* Exact calculation para maging bilog */
                border: 2px solid #D9CFC7; 
                background: white;
            }
            QRadioButton::indicator:checked { 
                border: 5px solid #5C2D0E; 
                background: white;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #8B6347;
            }
        """)
        hl.addWidget(rb)
        
        layout.addWidget(frame)
        layout.addSpacing(8)
        
        frame.mousePressEvent = lambda e: rb.setChecked(True)
        return rb

    def _create_input(self, label_text, layout, default_info_text):
        lbl = QLabel(label_text); lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)
        inp = QLineEdit(); inp.setMinimumHeight(45); inp.setStyleSheet(self._input_style_normal())
        layout.addWidget(inp)
        err = QLabel(default_info_text); err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(err)
        return inp, err

    def _create_password_input(self, label_text, layout, default_info_text):
        lbl = QLabel(label_text); lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)
        frame = QFrame(); frame.setFixedHeight(45); frame.setStyleSheet("QFrame { background-color: white; border: 1.5px solid #D9CFC7; border-radius: 4px; }")
        fl = QHBoxLayout(frame); fl.setContentsMargins(14, 0, 10, 0)
        inp = QLineEdit(); inp.setEchoMode(QLineEdit.EchoMode.Password); inp.setStyleSheet("QLineEdit { border: none; background: transparent; font-size: 14px; }")
        btn = QPushButton(); btn.setFixedSize(30, 30); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OFF_SVG, 20, 20)))
        btn.clicked.connect(lambda: self._toggle_pwd(inp, btn))
        fl.addWidget(inp); fl.addWidget(btn)
        err = QLabel(default_info_text); err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(frame); layout.addWidget(err)
        return inp, err, btn

    def _toggle_pwd(self, inp, btn):
        if inp.echoMode() == QLineEdit.EchoMode.Password:
            inp.setEchoMode(QLineEdit.EchoMode.Normal); btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OPEN_SVG, 20, 20)))
        else:
            inp.setEchoMode(QLineEdit.EchoMode.Password); btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OFF_SVG, 20, 20)))

    def _create_btn(self, text, secondary=False):
        btn = QPushButton(text); btn.setMinimumHeight(45); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if secondary: btn.setStyleSheet("QPushButton { background-color: #8B6347; color: white; border-radius: 4px; font-weight: bold; font-size: 14px;} QPushButton:hover { background-color: #7A4F2E; }")
        else: btn.setStyleSheet("QPushButton { background-color: #5C2D0E; color: white; border-radius: 4px; font-size: 14px; font-weight: bold;} QPushButton:hover { background-color: #4A2208; }")
        return btn

    def _input_style_normal(self): return "QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #D9CFC7; border-radius: 4px; font-size: 14px; background-color: white;} QLineEdit:focus, QComboBox:focus { border: 1.5px solid #8B6347; }"
    def _input_style_success(self): return "QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #4CAF50; border-radius: 4px; font-size: 14px; background-color: #F8FFF8;} QLineEdit:focus, QComboBox:focus { border: 1.5px solid #4CAF50; }"
    def _input_style_error(self): return "QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #C0392B; border-radius: 4px; font-size: 14px; background-color: #fff5f5; }"
    
    def _set_success(self, inp, err_lbl): 
        inp.setStyleSheet(self._input_style_success()); 
        err_lbl.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 2px;"); 
        err_lbl.setText("Looks good!") 

    def _set_err(self, inp, err_lbl, msg, shake=True): 
        inp.setStyleSheet(self._input_style_error()); 
        err_lbl.setStyleSheet("color: #C0392B; font-size: 11px; margin-top: 2px;"); 
        err_lbl.setText(msg); 
        if shake: 
            self.shake_widget(inp)

    def _clear_err(self, inp, err_lbl, default_msg): 
        inp.setStyleSheet(self._input_style_normal()); 
        err_lbl.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;"); 
        err_lbl.setText(default_msg)
    
    def _set_pwd_success(self, inp, err_lbl): 
        inp.parent().setStyleSheet("QFrame { background-color: #F8FFF8; border: 1.5px solid #4CAF50; border-radius: 4px; }"); 
        err_lbl.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 2px;"); 
        err_lbl.setText("Looks good!")

    def _set_pwd_err(self, inp, err_lbl, msg, shake=True): 
        inp.parent().setStyleSheet("QFrame { background-color: #fff5f5; border: 1.5px solid #C0392B; border-radius: 4px; }"); 
        err_lbl.setStyleSheet("color: #C0392B; font-size: 11px; margin-top: 2px;"); 
        err_lbl.setText(msg); 
        if shake: 
            self.shake_widget(inp.parent())

    def _clear_pwd_err(self, inp, err_lbl, default_msg): inp.parent().setStyleSheet("QFrame { background-color: white; border: 1.5px solid #D9CFC7; border-radius: 4px; }"); err_lbl.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;"); err_lbl.setText(default_msg)

    def _svg_to_pixmap(self, svg_bytes, w, h, color=None):
        if color: svg_bytes = svg_bytes.decode('utf-8').replace('currentColor', color).encode('utf-8')
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(w, h); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); renderer.render(painter); painter.end()
        return pixmap

    def shake_widget(self, widget):
        offsets = [6, -6, 5, -5, 4, -4, 2, -2, 0]; pos = widget.pos()
        def move(i=0):
            if i < len(offsets): widget.move(pos.x() + offsets[i], pos.y()); QTimer.singleShot(30, lambda: move(i + 1))
            else: widget.move(pos)
        move()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'): self.move(event.globalPosition().toPoint() - self._drag_pos)


# ── EMAIL SENDER FUNCTION ─────────────────────────────────────────────
    def send_otp_email(self, receiver_email, otp):
        sender_email = get_setting("BAKESYNC_SMTP_EMAIL")
        sender_password = get_setting("BAKESYNC_SMTP_PASSWORD")
        if not sender_email or not sender_password:
            print("Email Error: BAKESYNC_SMTP_EMAIL / BAKESYNC_SMTP_PASSWORD are not set (see config.example.json).")
            return False

        # Binago natin from "alternative" to "related" para maka-embed ng image
        message = MIMEMultipart("related")
        message["Subject"] = "Popeye's Bakery - Your Password Reset Code"
        message["From"] = f"Popeye's Bakery <{sender_email}>"
        message["To"] = receiver_email

        # ── PROFESSIONAL HTML EMAIL TEMPLATE (With Logo) ──
        html = f"""\
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
        </head>
        <body style="margin: 0; padding: 0; background-color: #F5F1ED; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #F5F1ED; padding: 40px 20px;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" style="background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E5DCD3; overflow: hidden; width: 100%; max-width: 500px;">
                  
                  <!-- HEADER WITH LOGO -->
                  <tr>
                    <td align="center" style="background-color: #E8E0D8; padding: 25px 0;">
                      <!-- Gagamitin natin ang cid (Content-ID) para i-display ang in-attach na image -->
                      <img src="cid:bakery_logo" alt="Popeye's Bakery" style="display: block; max-width: 140px; height: auto;">
                    </td>
                  </tr>
                  
                  <!-- BODY CONTENT -->
                  <tr>
                    <td style="padding: 35px 40px;">
                      <h2 style="margin-top: 0; color: #5C2D0E; font-size: 20px;">Password Reset Request</h2>
                      <p style="font-size: 15px; line-height: 1.6; color: #555555; margin-bottom: 25px;">
                        Hello,<br><br>
                        We received a request to reset the password for your Popeye's Bakery account. Please enter the following 6-digit One-Time Password (OTP) to verify your identity:
                      </p>
                      
                      <!-- OTP BOX -->
                      <div style="text-align: center; margin: 35px 0;">
                        <div style="background-color: #FCF9F6; border: 2px dashed #8B6347; border-radius: 8px; display: inline-block; padding: 15px 35px;">
                          <h1 style="color: #5C2D0E; font-size: 40px; letter-spacing: 8px; margin: 0; font-family: 'Courier New', Courier, monospace;">{otp}</h1>
                        </div>
                      </div>
                      
                      <p style="font-size: 15px; line-height: 1.6; color: #555555;">
                        <b>Do not share this code with anyone.</b> No one from Popeye's Bakery will ever ask for this code.
                      </p>
                      
                      <hr style="border: none; border-top: 1px solid #E5DCD3; margin: 30px 0;">
                      
                      <!-- FOOTER -->
                      <p style="font-size: 12px; line-height: 1.5; color: #888888; margin: 0; text-align: center;">
                        If you did not request a password reset, you can safely ignore this email. Your account remains secure.
                        <br><br>
                        <i>This is an automated message. Please do not reply.</i>
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """
        message.attach(MIMEText(html, "html"))

        # ── ATTACH LOCAL LOGO AS INLINE IMAGE ──
        script_dir = os.path.dirname(__file__)
        logo_path = os.path.join(IMAGES_DIR, "poplogo.png")
        
        try:
            with open(logo_path, "rb") as img_file:
                logo_img = MIMEImage(img_file.read())
                # Ito yung CID na tinatawag natin sa <img src="cid:bakery_logo"> sa itaas
                logo_img.add_header('Content-ID', '<bakery_logo>')
                logo_img.add_header('Content-Disposition', 'inline', filename="poplogo.png")
                message.attach(logo_img)
        except Exception as e:
            # Kung hindi mahanap yung image, ipi-print niya lang pero mag-sesend pa rin yung email (walang logo)
            print(f"Warning: Logo not attached to email: {e}")

        # ── SENDING ──
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            return True
        except Exception as e:
            print("Email Error:", e)
            return False


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = ForgotPasswordWindow()
    window.show()
    sys.exit(app.exec())