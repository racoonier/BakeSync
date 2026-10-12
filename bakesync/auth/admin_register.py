import os
from bakesync.core.auth_utils import hash_password
import re
import json
import random
import string

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QStackedWidget, QComboBox,
    QApplication, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QByteArray, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QLinearGradient
)
from PyQt6.QtSvg import QSvgRenderer
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix


# ── SVG helpers ────────────────────────────────────────────────────────────────

EYE_OPEN = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
  <circle cx="12" cy="12" r="3"/>
</svg>"""

EYE_OFF = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#888" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
  <line x1="1" y1="1" x2="23" y2="23"/>
</svg>"""

CHECK_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#4CAF50" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
  <polyline points="22 4 12 14.01 9 11.01"/>
</svg>"""

COPY_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#5C2D0E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
</svg>"""

LOCK_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#5C2D0E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
</svg>"""

KEY_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
    stroke="#4CAF50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
</svg>"""


def svg_pixmap(svg_bytes, w, h, color=None):
    if color:
        s = svg_bytes.decode('utf-8').replace('currentColor', color)
        svg_bytes = s.encode('utf-8')
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pix = QPixmap(w, h)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return pix


# ── Styles ─────────────────────────────────────────────────────────────────────

PRIMARY   = "#5C2D0E"
PRIMARY_H = "#7A3D15"
MID       = "#8B6347"
BORDER    = "#D9CFC7"
BG        = "#FFFFFF"
LIGHT_BG  = "#F8F5F2"
TEXT      = "#1A1A1A"
MUTED     = "#888888"
SUCCESS   = "#4CAF50"
DANGER    = "#C0392B"
PANEL_BG  = "#F0EAE3"

def field_style(state="normal"):
    base = "padding: 10px 14px; border-radius: 6px; font-size: 13px; font-family: 'Segoe UI';"
    if state == "normal":
        return f"QLineEdit {{ {base} border: 1.5px solid {BORDER}; background: white; color: {TEXT}; }} QLineEdit:focus {{ border: 1.5px solid {MID}; }}"
    elif state == "success":
        return f"QLineEdit {{ {base} border: 1.5px solid {SUCCESS}; background: #F8FFF8; color: {TEXT}; }}"
    elif state == "error":
        return f"QLineEdit {{ {base} border: 1.5px solid {DANGER}; background: #fff5f5; color: {TEXT}; }}"

def combo_style():
    return f"""
        QComboBox {{ padding: 10px 14px; border: 1.5px solid {BORDER}; border-radius: 6px;
                    font-size: 13px; color: {TEXT}; background: white; font-family: 'Segoe UI'; }}
        QComboBox:focus {{ border: 1.5px solid {MID}; }}
        QComboBox::drop-down {{ border: none; width: 30px; }}
        QComboBox QAbstractItemView {{ background: white; border: 1px solid {BORDER}; selection-background-color: {LIGHT_BG}; }}
    """

def label_style(bold=True, size=12, color=TEXT):
    w = "bold" if bold else "normal"
    return f"color: {color}; font-size: {size}px; font-weight: {w}; font-family: 'Segoe UI';"

def err_label_style(color=DANGER):
    return f"color: {color}; font-size: 11px; font-family: 'Segoe UI';"

def primary_btn_style():
    return f"""
        QPushButton {{ background: {PRIMARY}; color: white; border: none; border-radius: 6px;
                       font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; padding: 12px; }}
        QPushButton:hover {{ background: {PRIMARY_H}; }}
        QPushButton:disabled {{ background: #ccc; color: #888; }}
    """

def secondary_btn_style():
    return f"""
        QPushButton {{ background: {MID}; color: white; border: none; border-radius: 6px;
                       font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; padding: 12px; }}
        QPushButton:hover {{ background: #7A5534; }}
    """


# ── Helper: password field with eye toggle ─────────────────────────────────────

def make_password_row(placeholder=""):
    frame = QFrame()
    frame.setFixedHeight(44)
    frame.setStyleSheet(f"QFrame {{ border: 1.5px solid {BORDER}; border-radius: 6px; background: white; }}")
    fl = QHBoxLayout(frame)
    fl.setContentsMargins(14, 0, 10, 0)
    fl.setSpacing(0)
    inp = QLineEdit()
    inp.setEchoMode(QLineEdit.EchoMode.Password)
    inp.setPlaceholderText(placeholder)
    inp.setStyleSheet("QLineEdit { border: none; background: transparent; font-size: 13px; color: #1A1A1A; font-family: 'Segoe UI'; }")
    eye = QPushButton()
    eye.setFixedSize(28, 28)
    eye.setCursor(Qt.CursorShape.PointingHandCursor)
    eye.setStyleSheet("QPushButton { border: none; background: transparent; }")
    eye.setIcon(QIcon(svg_pixmap(EYE_OFF, 20, 20)))
    eye._visible = False

    def toggle():
        eye._visible = not eye._visible
        inp.setEchoMode(QLineEdit.EchoMode.Normal if eye._visible else QLineEdit.EchoMode.Password)
        eye.setIcon(QIcon(svg_pixmap(EYE_OPEN if eye._visible else EYE_OFF, 20, 20)))

    eye.clicked.connect(toggle)
    fl.addWidget(inp)
    fl.addWidget(eye)
    return frame, inp, eye


def set_frame_state(frame, state="normal"):
    colors = {"normal": BORDER, "success": SUCCESS, "error": DANGER}
    c = colors.get(state, BORDER)
    bg = {"normal": "white", "success": "#F8FFF8", "error": "#fff5f5"}.get(state, "white")
    frame.setStyleSheet(f"QFrame {{ border: 1.5px solid {c}; border-radius: 6px; background: {bg}; }}")

# ── Mastery Key popup ──────────────────────────────────────────────────────────

class MasteryKeyDialog(QDialog):
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.key = key
        self.setWindowTitle("Your Mastery Key")
        self.setFixedSize(420, 360)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(f"QDialog {{ background: transparent; }}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel()
        icon.setPixmap(svg_pixmap(KEY_SVG, 52, 52))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("border: none; background: transparent;")
        lay.addWidget(icon)

        title = QLabel("Save Your Mastery Key!")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        desc = QLabel("This key is required for password resets.\nYou will NOT be able to see this again.")
        desc.setStyleSheet(f"color: {MUTED}; font-size: 12px; border: none; font-family: 'Segoe UI';")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        lay.addWidget(desc)

        lay.addSpacing(6)

        key_row = QHBoxLayout()
        key_row.setSpacing(10)
        key_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        key_lbl = QLabel(key)
        key_lbl.setFont(QFont("Courier New", 22, QFont.Weight.Bold))
        key_lbl.setStyleSheet("color: #4CAF50; background: #F8FFF8; padding: 10px 18px; border-radius: 8px; border: 1.5px solid #C8E6C9;")
        key_row.addWidget(key_lbl)

        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon(svg_pixmap(COPY_SVG, 18, 18)))
        self.copy_btn.setFixedSize(42, 42)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet(f"QPushButton {{ background: white; border: 1.5px solid {BORDER}; border-radius: 6px; }} QPushButton:hover {{ background: {LIGHT_BG}; border: 1.5px solid {MID}; }}")
        self.copy_btn.clicked.connect(self._copy)
        key_row.addWidget(self.copy_btn)
        lay.addLayout(key_row)

        lay.addSpacing(10)

        ok_btn = QPushButton("I've saved it — Continue")
        ok_btn.setMinimumHeight(44)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(primary_btn_style())
        ok_btn.clicked.connect(self.accept)
        lay.addWidget(ok_btn)

    def _copy(self):
        QApplication.clipboard().setText(self.key)
        self.copy_btn.setIcon(QIcon(svg_pixmap(CHECK_SVG, 18, 18)))
        self.copy_btn.setStyleSheet(f"QPushButton {{ background: #F8FFF8; border: 1.5px solid {SUCCESS}; border-radius: 6px; }}")


# ── Main Register Window ───────────────────────────────────────────────────────

class AdminRegisterDialog(QDialog):
    """
    Multi-step admin account registration dialog.
    Steps:
      0 — Basic info (name, username, email, phone, password, confirm password)
      1 — Security questions (3 questions, cascading unlock)
    Between steps 0→1 an AdminPINDialog pops up.
    After step 1 a MasteryKeyDialog pops up, then the dialog accepts.
    """

    account_created = pyqtSignal(dict)   # emits the full account dict on success

    ALL_QUESTIONS = [
        "What is your mother's maiden name?",
        "What was the name of your first pet?",
        "In what city were you born?",
        "What is your favorite food?",
        "What high school did you attend?",
    ]

    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self._collected = {}
        self._admin_pin = ""
        self._pin_shown = False

        self.setWindowTitle("Register Admin Account")
        self.setFixedSize(900, 580)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 900) // 2,
            (screen.height() - 580) // 2
        )
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(f"""
            QDialog {{
                background: white;
                border: 2px solid {MID};
                border-radius: 10px;
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT PANEL ──────────────────────────────────────────────────
        self._left = QStackedWidget()
        self._left.setFixedWidth(460)

        # Left page 0 — form
        self._form_page = self._build_form_page()
        self._left.addWidget(self._form_page)

        # Left page 1 — decorative panel shown during security questions
        self._deco_page = self._build_deco_page()
        self._left.addWidget(self._deco_page)

        root.addWidget(self._left)

        # ── RIGHT PANEL ─────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background: {PANEL_BG};")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self._right_stack = QStackedWidget()

        # Right page 0 — empty / decorative during step 0
        right_blank = self._build_right_blank()
        self._right_stack.addWidget(right_blank)

        # Right page 1 — security questions
        self._sq_page = self._build_sq_page()
        self._right_stack.addWidget(self._sq_page)

        right_lay.addWidget(self._right_stack)
        root.addWidget(right)

        # Close button
        self._close_btn = QPushButton("", self); self._close_btn.setIcon(_ui_icon("x", "#7A6A5E", 16))
        self._close_btn.setFixedSize(34, 34)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet("QPushButton { color: #5C2D0E; background: transparent; border: none; font-size: 18px; font-weight: bold; } QPushButton:hover { background: rgba(0,0,0,40); border-radius: 6px; }")
        self._close_btn.move(self.width() - 44, 10)
        self._close_btn.clicked.connect(self.reject)
        self._close_btn.raise_()

    # ── Page builders ──────────────────────────────────────────────────────────

    def _build_form_page(self):
        page = QWidget()
        page.setStyleSheet("background: white;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(48, 40, 48, 30)
        lay.setSpacing(0)

        # Header
        title = QLabel("Register Admin Account")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; font-family: 'Segoe UI';")
        lay.addWidget(title)

        step = QLabel("Step 1 of 2 — Account Details")
        step.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-family: 'Segoe UI'; margin-bottom: 18px;")
        lay.addWidget(step)
        lay.addSpacing(16)

        def field_block(label_text):
            vb = QVBoxLayout()
            vb.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style(bold=True, size=12))
            vb.addWidget(lbl)
            return vb

        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        # Full Name
        fn_vb = field_block("Full Name *")
        self._fn = QLineEdit(); self._fn.setMinimumHeight(42); self._fn.setStyleSheet(field_style())
        self._fn_err = QLabel(""); self._fn_err.setStyleSheet(err_label_style()); self._fn_err.hide()
        fn_vb.addWidget(self._fn); fn_vb.addWidget(self._fn_err)
        grid.addLayout(fn_vb, 0, 0)

        # Username
        un_vb = field_block("Username *")
        self._un = QLineEdit(); self._un.setMinimumHeight(42); self._un.setStyleSheet(field_style())
        self._un_err = QLabel(""); self._un_err.setStyleSheet(err_label_style()); self._un_err.hide()
        un_vb.addWidget(self._un); un_vb.addWidget(self._un_err)
        grid.addLayout(un_vb, 0, 1)

        # Email
        em_vb = field_block("Email Address (Optional)")
        self._em = QLineEdit(); self._em.setMinimumHeight(42); self._em.setStyleSheet(field_style())
        self._em_err = QLabel(""); self._em_err.setStyleSheet(err_label_style()); self._em_err.hide()
        em_vb.addWidget(self._em); em_vb.addWidget(self._em_err)
        grid.addLayout(em_vb, 1, 0)

        # Phone
        ph_vb = field_block("Phone Number (Optional)")
        self._ph = QLineEdit(); self._ph.setMinimumHeight(42); self._ph.setStyleSheet(field_style())
        self._ph_err = QLabel(""); self._ph_err.setStyleSheet(err_label_style()); self._ph_err.hide()
        ph_vb.addWidget(self._ph); ph_vb.addWidget(self._ph_err)
        grid.addLayout(ph_vb, 1, 1)

        # Password
        pw_vb = field_block("Temporary Password *")
        self._pw_frame, self._pw, _ = make_password_row("At least 6 characters")
        self._pw_err = QLabel(""); self._pw_err.setStyleSheet(err_label_style()); self._pw_err.hide()
        pw_vb.addWidget(self._pw_frame); pw_vb.addWidget(self._pw_err)
        grid.addLayout(pw_vb, 2, 0)

        # Confirm Password
        cp_vb = field_block("Confirm Password *")
        self._cp_frame, self._cp, _ = make_password_row("Repeat password")
        self._cp_err = QLabel(""); self._cp_err.setStyleSheet(err_label_style()); self._cp_err.hide()
        cp_vb.addWidget(self._cp_frame); cp_vb.addWidget(self._cp_err)
        grid.addLayout(cp_vb, 2, 1)

        lay.addLayout(grid)
        lay.addSpacing(12)

        # ── Admin PIN (below password fields) ──
        pin_outer = QVBoxLayout()
        pin_outer.setSpacing(4)

        pin_lbl = QLabel("Admin PIN * (6 digits)")
        pin_lbl.setStyleSheet(label_style(bold=True, size=12))
        pin_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_outer.addWidget(pin_lbl)

        pin_field_row = QHBoxLayout()
        pin_field_row.setSpacing(6)
        pin_field_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pin_boxes = []
        for i in range(6):
            box = QLineEdit()
            box.setFixedSize(46, 46)
            box.setMaxLength(1)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setEchoMode(QLineEdit.EchoMode.Password)
            box.setStyleSheet(f"""
                QLineEdit {{
                    border: 1.5px solid {BORDER}; border-radius: 8px;
                    font-size: 18px; font-weight: bold; color: {PRIMARY};
                    background: {LIGHT_BG};
                }}
                QLineEdit:focus {{ border: 1.5px solid {MID}; background: white; }}
            """)
            box.textChanged.connect(lambda txt, idx=i: self._on_pin_changed(txt, idx))
            pin_field_row.addWidget(box)
            self._pin_boxes.append(box)

        pin_outer.addLayout(pin_field_row)

        self._pin_err = QLabel("")
        self._pin_err.setStyleSheet(err_label_style())
        self._pin_err.hide()
        pin_outer.addWidget(self._pin_err)

        self._pin_widget = QWidget()
        self._pin_widget.setLayout(pin_outer)
        self._pin_widget.hide()
        lay.addWidget(self._pin_widget)
        lay.addSpacing(16)

        self._next_btn = QPushButton("Next: Step 2")
        self._next_btn.setMinimumHeight(46)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setStyleSheet(primary_btn_style())
        self._next_btn.clicked.connect(self._validate_step1)
        lay.addWidget(self._next_btn)
        lay.addStretch()

        return page

    def _build_deco_page(self):
        """Left panel shown during step 2 — brown card with bakery branding."""
        page = QWidget()
        page.setStyleSheet(f"background: {PRIMARY};")
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(40, 160, 40, 40)
        lay.setSpacing(20)

        # Logo / icon area
        icon_lbl = QLabel()
        icon_lbl.setPixmap(svg_pixmap(KEY_SVG, 72, 72, "#FFFFFF"))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(icon_lbl)

        title = QLabel("Almost there!")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Answer your security questions to\ncomplete the admin registration.")
        sub.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 13px; font-family: 'Segoe UI'; background: transparent; border: none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # Progress dots
        dots_row = QHBoxLayout()
        dots_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dots_row.setSpacing(8)
        self._dots = []
        for i in range(3):
            d = QLabel()
            d.setFixedSize(10, 10)
            self._dots.append(d)
            dots_row.addWidget(d)
        self._update_dots(0)
        lay.addLayout(dots_row)

        lay.addStretch()

        return page

    def _build_right_blank(self):
        """Right panel during step 1 — decorative."""
        page = QWidget()
        page.setStyleSheet(f"background: {PANEL_BG};")
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(48, 178, 48, 48)
        lay.setSpacing(16)

        icon = QLabel()
        icon.setPixmap(svg_pixmap(LOCK_SVG, 80, 80, PRIMARY))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(icon)

        h = QLabel("Admin Registration")
        h.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        h.setStyleSheet(f"color: {PRIMARY}; background: transparent; border: none;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(h)

        s = QLabel("Fill in the details on the left to\ncreate a new administrator account.")
        s.setStyleSheet(f"color: {MUTED}; font-size: 13px; font-family: 'Segoe UI'; background: transparent; border: none;")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setWordWrap(True)
        lay.addWidget(s)

        lay.addStretch()
        return page

    def _build_sq_page(self):
        """Right panel — security questions step."""
        page = QWidget()
        page.setStyleSheet(f"background: {PANEL_BG};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 30)
        lay.setSpacing(0)

        title = QLabel("Security Questions")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        lay.addWidget(title)

        step_lbl = QLabel("Step 2 of 2 — Recovery Setup")
        step_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px; font-family: 'Segoe UI'; background: transparent; border: none; margin-bottom: 16px;")
        lay.addWidget(step_lbl)
        lay.addSpacing(14)

        self._sq_combos = []
        self._sq_answers = []
        self._sq_errs = []
        self._sq_blocks = []

        for i in range(3):
            block = QWidget()
            block.setStyleSheet("background: transparent;")
            blay = QVBoxLayout(block)
            blay.setContentsMargins(0, 0, 0, 0)
            blay.setSpacing(5)

            lbl = QLabel(f"Security Question {i+1} {'*' if i < 3 else ''}")
            lbl.setStyleSheet(label_style(bold=True, size=12))
            blay.addWidget(lbl)

            combo = QComboBox()
            combo.setStyleSheet(combo_style())
            combo.setMinimumHeight(42)
            combo.setEnabled(i == 0)
            blay.addWidget(combo)

            ans = QLineEdit()
            ans.setPlaceholderText("Your answer")
            ans.setStyleSheet(field_style("normal" if i == 0 else "normal"))
            ans.setMinimumHeight(40)
            ans.setEnabled(i == 0)
            blay.addWidget(ans)

            err = QLabel("")
            err.setStyleSheet(err_label_style())
            err.hide()
            blay.addWidget(err)

            self._sq_combos.append(combo)
            self._sq_answers.append(ans)
            self._sq_errs.append(err)
            self._sq_blocks.append(block)

            lay.addWidget(block)
            if i < 2:
                lay.addSpacing(8)

        # Populate q1 immediately; q2/q3 get populated when previous answer is filled
        self._sq_combos[0].addItems(self.ALL_QUESTIONS)
        self._sq_answers[0].textChanged.connect(lambda t: self._on_ans_changed(0, t))
        self._sq_answers[1].textChanged.connect(lambda t: self._on_ans_changed(1, t))
        self._sq_combos[0].currentIndexChanged.connect(lambda: self._refresh_q_options())
        self._sq_combos[1].currentIndexChanged.connect(lambda: self._refresh_q_options())

        lay.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        back_btn = QPushButton("Go Back")
        back_btn.setMinimumHeight(46)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(secondary_btn_style())
        back_btn.clicked.connect(self._go_back_to_step1)
        btn_row.addWidget(back_btn, 1)

        self._finish_btn = QPushButton("Complete Registration")
        self._finish_btn.setMinimumHeight(46)
        self._finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._finish_btn.setStyleSheet(primary_btn_style())
        self._finish_btn.clicked.connect(self._validate_step2)
        btn_row.addWidget(self._finish_btn, 2)

        lay.addLayout(btn_row)
        lay.addStretch()

        return page
    
    def _on_pin_changed(self, txt, idx):
        if txt and idx < 5:
            self._pin_boxes[idx + 1].setFocus()
        for box in self._pin_boxes:
            box.setStyleSheet(f"""
                QLineEdit {{
                    border: 1.5px solid {"#4CAF50" if box.text() else BORDER};
                    border-radius: 8px; font-size: 18px; font-weight: bold;
                    color: {PRIMARY}; background: {"#F8FFF8" if box.text() else LIGHT_BG};
                }}
                QLineEdit:focus {{ border: 1.5px solid {MID}; background: white; }}
            """)

    # ── Logic ──────────────────────────────────────────────────────────────────

    def _update_dots(self, active_idx):
        for i, d in enumerate(self._dots):
            if i == active_idx:
                d.setStyleSheet("background: white; border-radius: 5px;")
            elif i < active_idx:
                d.setStyleSheet(f"background: rgba(255,255,255,0.5); border-radius: 5px;")
            else:
                d.setStyleSheet("background: rgba(255,255,255,0.25); border-radius: 5px;")

    def _on_ans_changed(self, idx, text):
        if idx == 0 and text.strip():
            # unlock q2
            self._sq_combos[1].setEnabled(True)
            self._sq_answers[1].setEnabled(True)
            self._refresh_q_options()
        elif idx == 1 and text.strip():
            # unlock q3
            self._sq_combos[2].setEnabled(True)
            self._sq_answers[2].setEnabled(True)
            self._refresh_q_options()

        # visual feedback
        inp = self._sq_answers[idx]
        if text.strip():
            inp.setStyleSheet(field_style("success"))
        else:
            inp.setStyleSheet(field_style("normal"))

        # update dot
        filled = sum(1 for a in self._sq_answers if a.text().strip())
        self._update_dots(min(filled, 2))

    def _refresh_q_options(self):
        chosen = []
        for i, combo in enumerate(self._sq_combos):
            if combo.isEnabled():
                chosen.append(combo.currentText())
            else:
                chosen.append(None)

        for i, combo in enumerate(self._sq_combos):
            if not combo.isEnabled():
                continue
            current = combo.currentText()
            blocked = [c for j, c in enumerate(chosen) if j != i and c is not None]
            combo.blockSignals(True)
            combo.clear()
            available = [q for q in self.ALL_QUESTIONS if q not in blocked]
            combo.addItems(available)
            if current in available:
                combo.setCurrentText(current)
            combo.blockSignals(False)

    def _validate_step1(self):
        has_err = False

        def show(inp, err, msg):
            nonlocal has_err
            has_err = True
            err.setText(msg); err.show()
            inp.setStyleSheet(field_style("error"))

        def clear(inp, err):
            err.hide()
            inp.setStyleSheet(field_style("normal"))

        for inp, err in [(self._fn, self._fn_err),(self._un, self._un_err),
                         (self._em, self._em_err),(self._ph, self._ph_err)]:
            clear(inp, err)
        for frame, err in [(self._pw_frame, self._pw_err),(self._cp_frame, self._cp_err)]:
            err.hide()
            set_frame_state(frame, "normal")

        fn = self._fn.text().strip()
        un = self._un.text().strip()
        em = self._em.text().strip()
        ph = self._ph.text().strip()
        pw = self._pw.text()
        cp = self._cp.text()

        if not fn:
            show(self._fn, self._fn_err, "Full name is required.")
        if not un:
            show(self._un, self._un_err, "Username is required.")
        elif len(un) < 4:
            show(self._un, self._un_err, "Username must be at least 4 characters.")
        elif self.db:
            try:
                if self.db.fetch_one("SELECT id FROM users WHERE username = ?", (un,)):
                    show(self._un, self._un_err, "Username already exists.")
            except: pass
        if em and not re.match(r"[^@]+@[^@]+\.[^@]+", em):
            show(self._em, self._em_err, "Invalid email format.")
        if ph and (not ph.isdigit() or len(ph) < 10):
            show(self._ph, self._ph_err, "Must be at least 10 digits.")
        if not pw:
            self._pw_err.setText("Password is required."); self._pw_err.show()
            set_frame_state(self._pw_frame, "error"); has_err = True
        elif len(pw) < 6:
            self._pw_err.setText("At least 6 characters."); self._pw_err.show()
            set_frame_state(self._pw_frame, "error"); has_err = True
        if not cp:
            self._cp_err.setText("Please confirm your password."); self._cp_err.show()
            set_frame_state(self._cp_frame, "error"); has_err = True
        elif pw and cp != pw:
            self._cp_err.setText("Passwords do not match."); self._cp_err.show()
            set_frame_state(self._cp_frame, "error"); has_err = True
        else:
            set_frame_state(self._cp_frame, "success")

        if has_err:
            return

        if not self._pin_shown:
            self._pin_shown = True
            self._pin_widget.show()
            self._pin_boxes[0].setFocus()
            return

        # Validate PIN
        pin = "".join(b.text() for b in self._pin_boxes)
        if not pin:
            self._pin_err.setText("Admin PIN is required.")
            self._pin_err.show()
            for box in self._pin_boxes:
                box.setStyleSheet(f"""
                    QLineEdit {{
                        border: 1.5px solid {DANGER}; border-radius: 8px;
                        font-size: 18px; font-weight: bold; color: {PRIMARY};
                        background: #fff5f5;
                    }}
                """)
            return
        elif len(pin) != 6 or not pin.isdigit():
            self._pin_err.setText("PIN must be exactly 6 digits.")
            self._pin_err.show()
            for box in self._pin_boxes:
                box.setStyleSheet(f"""
                    QLineEdit {{
                        border: 1.5px solid {DANGER}; border-radius: 8px;
                        font-size: 18px; font-weight: bold; color: {PRIMARY};
                        background: #fff5f5;
                    }}
                """)
            return

        self._pin_err.hide()
        self._admin_pin = pin
        self._collected.update({"full_name": fn, "username": un, "email": em, "phone": ph, "password": pw})
        self._go_to_sq()

    def _go_to_sq(self):
        self._left.setCurrentIndex(1)
        self._right_stack.setCurrentIndex(1)

    def _go_back_to_step1(self):
        self._left.setCurrentIndex(0)
        self._right_stack.setCurrentIndex(0)
        self._pin_shown = False
        self._pin_widget.hide()
        self._next_btn.setText("Next: Step 2")
        for box in self._pin_boxes:
            box.clear()
        self._pin_err.hide()

    def _validate_step2(self):
        has_err = False
        answers = []
        for i, (combo, ans, err) in enumerate(zip(self._sq_combos, self._sq_answers, self._sq_errs)):
            err.hide()
            val = ans.text().strip()
            if not val:
                err.setText("Answer is required."); err.show()
                ans.setStyleSheet(field_style("error")); has_err = True
            else:
                ans.setStyleSheet(field_style("success"))
                answers.append({"q": combo.currentText(), "a": val})

        if has_err:
            return

        # Generate mastery key
        mk = f"PY-{''.join(random.choices(string.digits, k=5))}"
        self._collected["security"] = answers
        self._collected["mastery_key"] = mk
        self._collected["admin_pin"] = self._admin_pin

        # Show mastery key dialog
        mk_dlg = MasteryKeyDialog(mk, self)
        mk_dlg.exec()

        # Save to DB if provided
        if self.db:
            try:
                from datetime import datetime
                d = self._collected
                self.db.execute_query(
                    """INSERT INTO users (username, password, role, full_name, email, phone,
                       status, is_archived, created_at, admin_pin, mastery_key, security_data)
                       VALUES (?, ?, 'Administrator', ?, ?, ?, 'Active', 0, ?, ?, ?, ?)""",
                    (d["username"], hash_password(d["password"]), d["full_name"], d["email"], d["phone"],
                     datetime.now().strftime("%Y-%m-%d"), hash_password(d["admin_pin"]) if d["admin_pin"] else None, hash_password(d["mastery_key"]) if d["mastery_key"] else None,
                     json.dumps(d["security"]))
                )
                log_activity(self.db, getattr(self.parent(), "current_user", "") or "Administrator", "account added", "account",
                             f"New Administrator account: {d['username']}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "DB Error", str(e))
                return

        self.account_created.emit(self._collected)
        self.accept()

# ── Standalone test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dlg = AdminRegisterDialog(db=None)
    dlg.account_created.connect(lambda d: print("Created:", d))
    dlg.show()
    sys.exit(app.exec())
