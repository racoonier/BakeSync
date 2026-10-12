from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from bakesync.core.auth_utils import hash_password, verify_password, password_strength_error
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import PasswordFields, svg_pixmap, THEME


class ChangePasswordDialog(QDialog):
    """Shown after login when users.must_change_password = 1 (default accounts and
    passwords reset by an Administrator), or from the avatar menu (forced=False),
    where the current password is asked first."""

    def __init__(self, db, user_row, parent=None, forced=True):
        super().__init__(parent)
        self.forced = forced
        self.db = db
        self.user_id = user_row['id']
        self.username = user_row['username'] if 'username' in user_row.keys() else str(self.user_id)
        self.current_hash = user_row['password']

        self.setWindowTitle("Change Password")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(440)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        container = QFrame(self)
        container.setStyleSheet("QFrame { background-color: white; border-radius: 14px; border: none; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)
        outer.addWidget(container)

        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(12)

        title = QLabel("Set Your Own Password" if forced else "Change Password")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #6B3F27; background: transparent;")
        self.layout.addWidget(title)

        info = QLabel(
            f"Hi {user_row['username']}, you're using a default or temporary password. "
            "Please choose a new one before continuing." if forced else
            "Enter your current password, then choose a new one."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")
        self.layout.addWidget(info)

        # Reminder before changing anything
        note = QFrame()
        note.setStyleSheet(f"QFrame {{ background: {THEME['amber_bg']}; border: 1px solid #F3D49B; border-radius: 9px; }}"
                           "QLabel { background: transparent; border: none; }")
        nl = QHBoxLayout(note); nl.setContentsMargins(12, 9, 12, 9); nl.setSpacing(10)
        ic = QLabel(); ic.setPixmap(svg_pixmap("alert", THEME["amber"], 18)); ic.setFixedSize(18, 18)
        nl.addWidget(ic, alignment=Qt.AlignmentFlag.AlignTop)
        nt = QLabel("Remember your new password. Do not share it with anyone. "
                    "You will use it the next time you sign in.")
        nt.setWordWrap(True); nt.setStyleSheet(f"color: {THEME['text']}; font-size: 12px;")
        nl.addWidget(nt, 1)
        self.layout.addWidget(note)

        self.current_input = None if forced else self._field("Current password")
        self.fields = PasswordFields(self)
        self.new_input, self.confirm_input = self.fields.new, self.fields.confirm
        self.confirm_input.returnPressed.connect(self.save)
        self.layout.addWidget(self.fields)

        self.err_lbl = QLabel()
        self.err_lbl.setWordWrap(True)
        self.err_lbl.setStyleSheet(
            "QLabel { color: #EF4444; background: #FEF2F2; border: 1px solid #FECACA;"
            " border-radius: 6px; padding: 8px 12px; font-size: 12px; }")
        self.err_lbl.hide()
        self.layout.addWidget(self.err_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_cancel = QPushButton("Cancel Login" if forced else "Cancel")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B; border: 1px solid #E2E8F0;
                          border-radius: 8px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Password")
        btn_save.setFixedHeight(44)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #5C2D0E; color: white; border: none;
                          border-radius: 8px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #7A3D15; }
        """)
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet(btn_save.styleSheet() + " QPushButton:disabled { background: #E7E1DB; color: #B0A69D; }")
        btn_save.setEnabled(False)
        self.btn_save = btn_save
        self.fields.changed.connect(lambda ok: btn_save.setEnabled(ok))
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        self.layout.addLayout(btn_row)

    def _field(self, label_text):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #0F172A; font-size: 13px; background: transparent;")
        self.layout.addWidget(lbl)
        inp = QLineEdit()
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setStyleSheet("padding: 10px; border: 1px solid #E2E8F0; border-radius: 6px;"
                          " font-size: 13px; color: #0F172A; background: white;")
        self.layout.addWidget(inp)
        return inp

    def validate(self, new_pw, confirm_pw, current_pw=None):
        """Returns an error message, or None if the new password can be saved."""
        if not self.forced and not verify_password(self.current_hash, current_pw or ""):
            return "Your current password is not correct."
        problem = password_strength_error(new_pw)
        if problem:
            return problem
        if new_pw != confirm_pw:
            return "Passwords do not match."
        if verify_password(self.current_hash, new_pw):
            return "Your new password must be different from the current one."
        return None

    def save(self):
        new_pw, confirm_pw = self.new_input.text(), self.confirm_input.text()
        current_pw = self.current_input.text() if self.current_input else None
        error = self.validate(new_pw, confirm_pw, current_pw)
        if error:
            self.err_lbl.setText(error)
            self.err_lbl.show()
            self.adjustSize()
            return
        try:
            self.db.execute_query(
                "UPDATE users SET password = ?, must_change_password = 0, failed_attempts = 0 WHERE id = ?",
                (hash_password(new_pw), self.user_id))
            log_activity(self.db, self.username, "password changed", "account",
                         "Set a new password at first sign-in" if self.forced else "Changed own password")
        except Exception as e:
            self.err_lbl.setText(f"Could not save the password: {e}")
            self.err_lbl.show()
            return
        self.accept()
