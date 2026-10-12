from bakesync.paths import CACHE_DIR, IMAGES_DIR
import os
from bakesync.core.auth_utils import hash_password
import re
import random
import string
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QApplication, 
                             QFrame, QStackedWidget, QComboBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QByteArray, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer

import json
from bakesync.core.database import DatabaseManager
from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix

class SignUpWindow(QMainWindow):
    # Signals
    return_to_login = pyqtSignal()
    
    # ── Vector SVGs ────────────────────────────────────────────────────────
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
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
    """
    CHECK_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="#4CAF50" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
    """
    LOCK_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="#5C2D0E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    """
    COPY_SVG = b"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Up - POPEYE'S Bakery")
        self.setMinimumSize(900, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Center Window
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 900) // 2, (screen.height() - 600) // 2)
        
        self.setStyleSheet("QMainWindow { background-color: #FFFFFF; }")
        self.collected_data = {}
        
        self.all_questions = [
            "What is your mother's maiden name?",
            "What was the name of your first pet?",
            "In what city were you born?",
            "What is your favorite food?",
            "What high school did you attend?"
        ]
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── LEFT SIDE (Form Wizard) ───────────────────────────────────────
        left_widget = QWidget()
        left_widget.setObjectName("leftWidget")
        left_widget.setStyleSheet("QWidget#leftWidget { background-color: #FFFFFF; }")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(60, 40, 60, 30)

        self.title_label = QLabel("Account Information")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #1A1A1A;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(self.title_label)

        self.step_label = QLabel("Step 1 of 4")
        self.step_label.setStyleSheet("color: #888; font-size: 13px; font-family: 'Segoe UI';")
        left_layout.addWidget(self.step_label)
        left_layout.addSpacing(20)

        self.stack = QStackedWidget()
        left_layout.addWidget(self.stack)

        self.setup_step_1()
        self.setup_step_2()
        self.setup_step_3_1()
        self.setup_step_3_2()
        self.setup_step_3_3()

        # ── RIGHT SIDE (Background Image & Logo) ──────────────────────────
        self.right_widget = QWidget()
        self.right_widget.setObjectName("rightWidget")
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        script_dir = os.path.dirname(__file__)
        original_bg_path = os.path.join(IMAGES_DIR, "popbg.png")
        bg_pixmap = QPixmap(original_bg_path)
        
        if not bg_pixmap.isNull():
            bg_pixmap = bg_pixmap.scaled(
                600, 600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            temp_bg_path = os.path.join(CACHE_DIR, "popbg_resized.png")
            bg_pixmap.save(temp_bg_path)
            final_bg_path = temp_bg_path.replace("\\", "/")

            self.right_widget.setStyleSheet(f"""
                QWidget#rightWidget {{
                    background-image: url({final_bg_path});
                    background-position: center;
                    background-repeat: no-repeat;
                    background-color: #E8E0D8;
                }}
            """)
        else:
            self.right_widget.setStyleSheet("QWidget#rightWidget { background-color: #E8E0D8; }")
            
        logo_label = QLabel()
        logo_path = os.path.join(IMAGES_DIR, "poplogo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setPixmap(_ui_pix("bread", "#6B3F27", 64))
            logo_label.setStyleSheet("font-size: 80px; background: transparent;")
            
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        right_layout.addWidget(logo_label)

        # Close Button sa taas (White)
        self.close_btn = QPushButton("", central_widget); self.close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { color: white; background: transparent; border: none; font-size: 20px; font-weight: bold;} 
            QPushButton:hover { background-color: rgba(0, 0, 0, 40); border-radius: 6px; }
        """)
        self.close_btn.clicked.connect(self.cancel_sign_up)
        self.close_btn.move(850, 10)

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(self.right_widget, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 46, 10)
            self.close_btn.raise_()

    # ── SETUP STEPS ────────────────────────────────────────────────────────

    def setup_step_1(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.s1_user, self.s1_user_err = self._create_input("Username", layout, " ")
        self.s1_user.textChanged.connect(self._rt_check_user)
        
        self.s1_email, self.s1_email_err = self._create_input("Email Address", layout, " ")
        self.s1_email.textChanged.connect(self._rt_check_email)
        
        self.s1_phone, self.s1_phone_err = self._create_input("Phone Number", layout, " ")
        self.s1_phone.setMaxLength(11)
        self.s1_phone.textChanged.connect(self._rt_check_phone)
        
        layout.addSpacing(15)
        
        next_btn = self._create_btn("Next")
        next_btn.clicked.connect(self.validate_step_1)
        layout.addWidget(next_btn)

        layout.addSpacing(15)

        login_link = QPushButton("Already have an account? Login.")
        login_link.setCursor(Qt.CursorShape.PointingHandCursor)
        login_link.setStyleSheet("""
            QPushButton { background: transparent; color: #5C2D0E; border: none; font-size: 13px; font-family: 'Segoe UI'; font-weight: bold;}
            QPushButton:hover { text-decoration: underline; color: #7A3D15; }
        """)
        login_link.clicked.connect(self.cancel_sign_up)
        layout.addWidget(login_link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_2(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.s2_pass, self.s2_pass_err, self.s2_t1 = self._create_password_input("Password", layout, " ")
        self.s2_pass.textChanged.connect(self._rt_check_pass)
        
        # Real-time Checklist for Password Requirements
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
        
        self.s2_conf, self.s2_conf_err, self.s2_t2 = self._create_password_input("Confirm Password", layout, " ")
        self.s2_conf.textChanged.connect(self._rt_check_conf)

        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(0))
        next_btn = self._create_btn("Next")
        next_btn.clicked.connect(self.validate_step_2)
        
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_3_1(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)

        lbl = QLabel("Security Question 1")
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        self.q1_combo = QComboBox()
        self.q1_combo.addItems(self.all_questions)
        self.q1_combo.setStyleSheet(self._input_style_normal() + "QComboBox { height: 42px; }")
        layout.addWidget(self.q1_combo)

        self.q1_ans = QLineEdit()
        self.q1_ans.setStyleSheet(self._input_style_normal())
        self.q1_ans.setMinimumHeight(42)
        self.q1_ans.textChanged.connect(lambda text: self._rt_check_ans(text, self.q1_ans, self.q1_err, " "))
        layout.addWidget(self.q1_ans)

        self.q1_err = QLabel(" ")
        self.q1_err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(self.q1_err)

        layout.addSpacing(15)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(1))
        next_btn = self._create_btn("Next")
        next_btn.clicked.connect(self.validate_step_3_1)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_3_2(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)

        lbl = QLabel("Security Question 2")
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        self.q2_combo = QComboBox()
        self.q2_combo.setStyleSheet(self._input_style_normal() + "QComboBox { height: 42px; }")
        layout.addWidget(self.q2_combo)

        self.q2_ans = QLineEdit()
        self.q2_ans.setStyleSheet(self._input_style_normal())
        self.q2_ans.setMinimumHeight(42)
        self.q2_ans.textChanged.connect(lambda text: self._rt_check_ans(text, self.q2_ans, self.q2_err, " "))
        layout.addWidget(self.q2_ans)

        self.q2_err = QLabel(" ")
        self.q2_err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(self.q2_err)

        layout.addSpacing(15)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(2))
        next_btn = self._create_btn("Next")
        next_btn.clicked.connect(self.validate_step_3_2)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_step_3_3(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)

        lbl = QLabel("Security Question 3")
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        self.q3_combo = QComboBox()
        self.q3_combo.setStyleSheet(self._input_style_normal() + "QComboBox { height: 42px; }")
        layout.addWidget(self.q3_combo)

        self.q3_ans = QLineEdit()
        self.q3_ans.setStyleSheet(self._input_style_normal())
        self.q3_ans.setMinimumHeight(42)
        self.q3_ans.textChanged.connect(lambda text: self._rt_check_ans(text, self.q3_ans, self.q3_err, " "))
        layout.addWidget(self.q3_ans)

        self.q3_err = QLabel(" ")
        self.q3_err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(self.q3_err)

        layout.addSpacing(15)
        btn_layout = QHBoxLayout()
        back_btn = self._create_btn("Back", secondary=True)
        back_btn.clicked.connect(lambda: self.go_to_step(3))
        # Changed text to "Create Account"
        next_btn = self._create_btn("Create Account")
        next_btn.clicked.connect(self.validate_step_3_3)
        btn_layout.addWidget(back_btn, 1)
        btn_layout.addWidget(next_btn, 2)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)


    # ── REAL-TIME VALIDATIONS ──────────────────────────────────────────────

    def _rt_check_user(self):
        text = self.s1_user.text().strip()
        if len(text) >= 3:
            self._set_success(self.s1_user, self.s1_user_err)
        elif text:
            self._set_err(self.s1_user, self.s1_user_err, "Username must be at least 3 characters.", shake=False)
        else:
            self._clear_err(self.s1_user, self.s1_user_err, " ")

    def _rt_check_email(self):
        text = self.s1_email.text().strip()
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.match(email_regex, text):
            self._set_success(self.s1_email, self.s1_email_err)
        elif text:
            self._set_err(self.s1_email, self.s1_email_err, "Requires a valid email format (e.g. name@domain.com)", shake=False)
        else:
            self._clear_err(self.s1_email, self.s1_email_err, " ")

    def _rt_check_phone(self):
        text = self.s1_phone.text().strip()
        if not text:
            self._clear_err(self.s1_phone, self.s1_phone_err, " ")
            return
            
        if not text.isdigit():
            self._set_err(self.s1_phone, self.s1_phone_err, "Phone must contain numbers only.", shake=False)
            return

        if len(text) == 11:
            if text.startswith("09"):
                self._set_success(self.s1_phone, self.s1_phone_err)
            else:
                self._set_err(self.s1_phone, self.s1_phone_err, "Phone must start with 09.", shake=False)
        else:
            self._set_err(self.s1_phone, self.s1_phone_err, "Must be 11 digits starting with 09.", shake=False)

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
        text = self.s2_pass.text()
        
        # Individual rules checking
        len_ok = self._update_req_label(self.req_len, len(text) >= 8)
        case_ok = self._update_req_label(self.req_case, any(c.isupper() for c in text) and any(c.islower() for c in text))
        num_ok = self._update_req_label(self.req_num, any(c.isdigit() for c in text))
        spec_ok = self._update_req_label(self.req_spec, any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in text))
        
        all_ok = len_ok and case_ok and num_ok and spec_ok

        if all_ok:
            self._set_pwd_success(self.s2_pass, self.s2_pass_err)
        elif text:
            self._set_pwd_err(self.s2_pass, self.s2_pass_err, "Please meet all the requirements below.", shake=False)
        else:
            self._clear_pwd_err(self.s2_pass, self.s2_pass_err, " ")
        self._rt_check_conf()

    def _rt_check_conf(self):
        pwd = self.s2_pass.text()
        conf = self.s2_conf.text()
        if conf == "":
            self._clear_pwd_err(self.s2_conf, self.s2_conf_err, " ")
        elif pwd == conf:
            self._set_pwd_success(self.s2_conf, self.s2_conf_err)
        else:
            self._set_pwd_err(self.s2_conf, self.s2_conf_err, "Passwords do not match.", shake=False)

    def _rt_check_ans(self, text, inp, err, default_msg=" "):
        if text.strip():
            self._set_success(inp, err)
        else:
            self._clear_err(inp, err, default_msg)

    # ── BUTTON VALIDATIONS (With Shake) ────────────────────────────────────

    def validate_step_1(self):
        has_err = False
        user = self.s1_user.text().strip()
        email = self.s1_email.text().strip()
        phone = self.s1_phone.text().strip()

        if len(user) < 3:
            self._set_err(self.s1_user, self.s1_user_err, "Username must be at least 3 characters.", shake=True)
            has_err = True
        
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            self._set_err(self.s1_email, self.s1_email_err, "Requires a valid email format (e.g. name@domain.com)", shake=True)
            has_err = True

        if phone:
            if not phone.isdigit() or len(phone) != 11 or not phone.startswith("09"):
                self._set_err(self.s1_phone, self.s1_phone_err, "Must be 11 digits starting with 09.", shake=True)
                has_err = True

        if not has_err:
            self.collected_data['username'] = user
            self.collected_data['email'] = email
            self.collected_data['phone'] = phone
            self.go_to_step(1)

    def validate_step_2(self):
        has_err = False
        pwd = self.s2_pass.text()
        conf = self.s2_conf.text()

        len_ok = len(pwd) >= 8
        case_ok = any(c.isupper() for c in pwd) and any(c.islower() for c in pwd)
        num_ok = any(c.isdigit() for c in pwd)
        spec_ok = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pwd)

        if not (len_ok and case_ok and num_ok and spec_ok):
            self._set_pwd_err(self.s2_pass, self.s2_pass_err, "Please meet all the requirements below.", shake=True)
            has_err = True
        elif pwd != conf:
            self._set_pwd_err(self.s2_conf, self.s2_conf_err, "Passwords do not match.", shake=True)
            has_err = True

        if not has_err:
            self.collected_data['password'] = pwd
            self.go_to_step(2)

    def validate_step_3_1(self):
        ans = self.q1_ans.text().strip()
        if not ans:
            self._set_err(self.q1_ans, self.q1_err, "Answer is required.", shake=True)
            return
            
        self.collected_data['q1'] = self.q1_combo.currentText()
        self.collected_data['a1'] = ans
        
        self.q2_combo.clear()
        available_q2 = [q for q in self.all_questions if q != self.collected_data['q1']]
        self.q2_combo.addItems(available_q2)
        
        self.go_to_step(3)

    def validate_step_3_2(self):
        ans = self.q2_ans.text().strip()
        if not ans:
            self._set_err(self.q2_ans, self.q2_err, "Answer is required.", shake=True)
            return
            
        self.collected_data['q2'] = self.q2_combo.currentText()
        self.collected_data['a2'] = ans
        
        self.q3_combo.clear()
        available_q3 = [q for q in self.all_questions if q not in (self.collected_data['q1'], self.collected_data['q2'])]
        self.q3_combo.addItems(available_q3)
        
        self.go_to_step(4)

    def validate_step_3_3(self):
        ans = self.q3_ans.text().strip()
        if not ans:
            self._set_err(self.q3_ans, self.q3_err, "Answer is required.", shake=True)
            return
            
        self.collected_data['q3'] = self.q3_combo.currentText()
        self.collected_data['a3'] = ans
        
        self.collected_data['security'] = [
            {"q": self.collected_data['q1'], "a": self.collected_data['a1']},
            {"q": self.collected_data['q2'], "a": self.collected_data['a2']},
            {"q": self.collected_data['q3'], "a": self.collected_data['a3']}
        ]

        # Trigger Dialog instead of moving to another setup step
        self.generate_and_show_master_key()

    def generate_and_show_master_key(self):
        random_chars = ''.join(random.choices(string.digits, k=5))
        key = f"PY-{random_chars}"
        self.collected_data['mastery_key'] = key
        
        # --- DATABASE SAVING LOGIC ---
        db = DatabaseManager()
        
        username = self.collected_data.get('username')
        password = self.collected_data.get('password')
        email = self.collected_data.get('email')
        phone = self.collected_data.get('phone')
        mastery_key = self.collected_data.get('mastery_key')
        security_data = json.dumps(self.collected_data.get('security', []))
        
        role = 'Unassigned'
        status = 'Pending'

        try:
            db.execute_query(
                """
                INSERT INTO users (username, password, email, phone, role, status, mastery_key, security_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, hash_password(password), email, phone, role, status, hash_password(mastery_key) if mastery_key else None, security_data)
            )
            log_activity(db, username, "account requested", "account",
                         "Signed up - waiting for Administrator approval")
        except Exception as e:
            if "UNIQUE constraint failed: users.username" in str(e):
                BakeSyncAlert.show_error(
                    self, 
                    "Username Taken", 
                    "Sorry, that username is already taken. Please choose another one."
                )
                self.go_to_step(0) 
                return
            else:
                BakeSyncAlert.show_error(self, "Database Error", f"An error occurred: {str(e)}")
                return
        # -----------------------------

        # Show Custom Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Account Created")
        dlg.setModal(True)
        dlg.setFixedSize(450, 440) # Tumaas ng onti para mas makahinga
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Mas malambot na border color
        dlg.setStyleSheet("""
            QDialog { background-color: white; border: 2px solid #8B6347; border-radius: 12px; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(self._svg_to_pixmap(self.CHECK_SVG, 60, 60))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Title
        title = QLabel("Account Created!")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instruction - Binago sa dark gray imbes na red para di masakit sa mata
        inst = QLabel("Your account is pending Admin approval.\nBelow is your Mastery Key. It is required for password resets. Please save it securely.")
        inst.setFont(QFont("Segoe UI", 11))
        inst.setStyleSheet("color: #555555; border: none;")
        inst.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inst.setWordWrap(True)
        layout.addWidget(inst)

        layout.addSpacing(15)

        # Key Box & Copy Button
        key_layout = QHBoxLayout()
        key_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_layout.setSpacing(10) # Nagdagdag ng onting space between key and button
        
        key_display = QLabel(key)
        key_display.setFont(QFont("Courier New", 20, QFont.Weight.Bold))
        # Mas subtle na background color
        key_display.setStyleSheet("color: #4CAF50; background: #F8FFF8; padding: 10px 20px; border-radius: 6px; border: 1px solid #C8E6C9;")
        key_layout.addWidget(key_display)

        copy_btn = QPushButton()
        copy_btn.setIcon(QIcon(self._svg_to_pixmap(self.COPY_SVG, 20, 20, "#5C2D0E"))) # Dark brown icon
        copy_btn.setFixedSize(44, 44)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Better visual feedback styling
        copy_btn.setStyleSheet("""
            QPushButton { 
                background-color: #FFFFFF; 
                border: 1px solid #D9CFC7; 
                border-radius: 6px; 
            }
            QPushButton:hover { 
                background-color: #F9FAFB; 
                border: 1px solid #8B6347;
            }
        """)
        
        def copy_key():
            QApplication.clipboard().setText(key)
            # Mas malinis na "copied" state (light green outline, not solid block)
            copy_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #F8FFF8; 
                    border: 1.5px solid #4CAF50; 
                    border-radius: 6px; 
                }
            """)
            copy_btn.setIcon(QIcon(self._svg_to_pixmap(self.CHECK_SVG, 20, 20)))

        copy_btn.clicked.connect(copy_key)
        key_layout.addWidget(copy_btn)
        
        layout.addLayout(key_layout)
        layout.addSpacing(25)

        # Okay Button
        ok_btn = QPushButton("Done, Take me to Login")
        ok_btn.setMinimumHeight(45)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton { 
                background-color: #5C2D0E; 
                color: white; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #7A3D15; 
            }
        """)
        
        def close_all():
            # Ipakita muna ang confirmation (using BakeSyncAlert) bago mag-close
            confirm = BakeSyncAlert.ask_yes_no(
                self,
                "Ready to Login?",
                "Are you sure you have saved your Mastery Key? You won't be able to see it again.",
                yes_text="YES, I SAVED IT",
                no_text="NO, GO BACK"
            )
            
            if confirm:
                dlg.accept()
                self.cancel_sign_up() 

        ok_btn.clicked.connect(close_all)
        layout.addWidget(ok_btn)

        dlg.exec()

    def cancel_sign_up(self):
        self.return_to_login.emit()
        self.close()

    def go_to_step(self, index):
        self.stack.setCurrentIndex(index)
        titles = [
            "Account Information", 
            "Security Setup", 
            "Recovery Setup", 
            "Recovery Setup", 
            "Recovery Setup"
        ]
        steps = [
            "Step 1 of 3", 
            "Step 2 of 3", 
            "Step 3 of 3 (1/3)", 
            "Step 3 of 3 (2/3)", 
            "Step 3 of 3 (3/3)"
        ]
        
        self.title_label.setText(titles[index])
        self.step_label.setText(steps[index])

    # ── UI HELPERS (Styles & Animations) ───────────────────────────────────

    def _create_input(self, label_text, layout, default_info_text):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        inp = QLineEdit()
        inp.setMinimumHeight(45)
        inp.setStyleSheet(self._input_style_normal())
        layout.addWidget(inp)

        err = QLabel(default_info_text)
        err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        layout.addWidget(err)
        return inp, err

    def _create_password_input(self, label_text, layout, default_info_text):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #333; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        layout.addWidget(lbl)

        frame = QFrame()
        frame.setFixedHeight(45)
        frame.setStyleSheet("QFrame { background-color: white; border: 1.5px solid #D9CFC7; border-radius: 4px; }")
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(14, 0, 10, 0)
        
        inp = QLineEdit()
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setStyleSheet("QLineEdit { border: none; background: transparent; font-size: 14px; }")
        
        btn = QPushButton()
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OFF_SVG, 20, 20)))
        btn.clicked.connect(lambda: self._toggle_pwd(inp, btn))
        
        fl.addWidget(inp)
        fl.addWidget(btn)
        
        err = QLabel(default_info_text)
        err.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        
        layout.addWidget(frame)
        layout.addWidget(err)
        return inp, err, btn

    def _toggle_pwd(self, inp, btn):
        if inp.echoMode() == QLineEdit.EchoMode.Password:
            inp.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OPEN_SVG, 20, 20)))
        else:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            btn.setIcon(QIcon(self._svg_to_pixmap(self.EYE_OFF_SVG, 20, 20)))

    def _create_btn(self, text, secondary=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if secondary:
            btn.setStyleSheet("""
                QPushButton { background-color: #8B6347; color: white; border-radius: 4px; font-weight: bold; font-size: 14px;}
                QPushButton:hover { background-color: #7A4F2E; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton { background-color: #5C2D0E; color: white; border-radius: 4px; font-size: 14px; font-weight: bold;}
                QPushButton:hover { background-color: #4A2208; }
            """)
        return btn

    def _input_style_normal(self):
        return """
            QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #D9CFC7; border-radius: 4px; font-size: 14px; background-color: white;}
            QLineEdit:focus, QComboBox:focus { border: 1.5px solid #8B6347; }
        """

    def _input_style_success(self):
        return """
            QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #4CAF50; border-radius: 4px; font-size: 14px; background-color: #F8FFF8;}
            QLineEdit:focus, QComboBox:focus { border: 1.5px solid #4CAF50; }
        """

    def _input_style_error(self):
        return "QLineEdit, QComboBox { padding: 10px 14px; border: 1.5px solid #C0392B; border-radius: 4px; font-size: 14px; background-color: #fff5f5; }"

    def _set_success(self, inp, err_lbl):
        inp.setStyleSheet(self._input_style_success())
        err_lbl.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 2px;")
        err_lbl.setText("Looks good!") 

    def _set_err(self, inp, err_lbl, msg, shake=True):
        inp.setStyleSheet(self._input_style_error())
        err_lbl.setStyleSheet("color: #C0392B; font-size: 11px; margin-top: 2px;")
        err_lbl.setText(msg)
        if shake: self.shake_widget(inp)

    def _clear_err(self, inp, err_lbl, default_msg):
        inp.setStyleSheet(self._input_style_normal())
        err_lbl.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        err_lbl.setText(default_msg)

    def _set_pwd_success(self, inp, err_lbl):
        inp.parent().setStyleSheet("QFrame { background-color: #F8FFF8; border: 1.5px solid #4CAF50; border-radius: 4px; }")
        err_lbl.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 2px;")
        err_lbl.setText("Looks good!")

    def _set_pwd_err(self, inp, err_lbl, msg, shake=True):
        inp.parent().setStyleSheet("QFrame { background-color: #fff5f5; border: 1.5px solid #C0392B; border-radius: 4px; }")
        err_lbl.setStyleSheet("color: #C0392B; font-size: 11px; margin-top: 2px;")
        err_lbl.setText(msg)
        if shake: self.shake_widget(inp.parent())

    def _clear_pwd_err(self, inp, err_lbl, default_msg):
        inp.parent().setStyleSheet("QFrame { background-color: white; border: 1.5px solid #D9CFC7; border-radius: 4px; }")
        err_lbl.setStyleSheet("color: #888; font-size: 11px; margin-top: 2px;")
        err_lbl.setText(default_msg)

    def _svg_to_pixmap(self, svg_bytes, w, h, color=None):
        if color:
            svg_str = svg_bytes.decode('utf-8').replace('currentColor', color)
            svg_bytes = svg_str.encode('utf-8')
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    def shake_widget(self, widget):
        offsets = [6, -6, 5, -5, 4, -4, 2, -2, 0]
        pos = widget.pos()
        def move(i=0):
            if i < len(offsets):
                widget.move(pos.x() + offsets[i], pos.y())
                QTimer.singleShot(30, lambda: move(i + 1))
            else:
                widget.move(pos)
        move()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SignUpWindow()
    window.show()
    sys.exit(app.exec())