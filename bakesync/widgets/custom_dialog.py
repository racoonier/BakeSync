from bakesync.paths import IMAGES_DIR
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QWidget, QApplication)
from PyQt6.QtCore import Qt
from bakesync.widgets.ui import svg_pixmap as _ui_pix
from PyQt6.QtGui import QFont, QPixmap


class CustomDialog(QDialog):
    ICONS = {
        "info":    ("ℹ", "#4A90D9", "#EAF3FB"),
        "warning": ("⚠", "#E0A020", "#FDF6E3"),
        "error":   ("✕", "#D94A4A", "#FBE9E9"),
        "success": ("✓", "#4AAD72", "#E9F7EF"),
    }

    def __init__(self, parent=None, title="", message="", dialog_type="info", ok_text="OK", cancel_text=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(380)

        # Dark overlay
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.45);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._init_ui(title, message, dialog_type, ok_text, cancel_text)
        self.adjustSize()
        self._center()

    def _center(self):
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2,
                      (screen.height() - self.height()) // 2)
            
    def closeEvent(self, event):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().closeEvent(event)

    def accept(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().accept()

    def reject(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().reject()

    def _init_ui(self, title, message, dialog_type, ok_text, cancel_text):
        icon_char, accent_color, badge_bg = self.ICONS.get(dialog_type, self.ICONS["info"])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet(f"""
                            QWidget#card {{
                                background-color: #FFFFFF;
                                border-radius: 12px;
                                border: 1px solid #E0E0E0;
                            }}
                            QWidget#card QLabel {{
                                background-color: transparent;
                                color: #1a1a1a;
                            }}
                            QWidget#card QWidget {{
                                background-color: #FFFFFF;
                            }}
                        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(12)

        # ✅ ADD THIS after card = QWidget()
        from PyQt6.QtGui import QPalette, QColor
        palette = card.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#1a1a1a"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#1a1a1a"))
        card.setPalette(palette)
        card.setAutoFillBackground(True)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        badge = QLabel(); badge.setPixmap(_ui_pix({"✓": "check_circle", "✕": "x_circle", "ℹ": "info", "⚠": "alert", "🔑": "key"}.get(icon_char, 'info'), accent_color, 20))
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_bg};
                color: {accent_color};
                border-radius: 18px;
                font-size: 15px;
                font-weight: bold;
            }}
        """)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1a1a1a;")

        top_row.addWidget(badge)
        top_row.addWidget(title_label)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #EEEEEE;")
        card_layout.addWidget(divider)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Arial", 11))
        msg_label.setStyleSheet("color: #444444; line-height: 1.5;")
        card_layout.addWidget(msg_label)

        card_layout.addSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        if cancel_text:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setFixedHeight(36)
            cancel_btn.setMinimumWidth(90)
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F5F5F5;
                    color: #555555;
                    border: 1px solid #DDDDDD;
                    border-radius: 8px;
                    font-size: 13px;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #EBEBEB;
                    border: 1px solid #CCCCCC;
                }
                QPushButton:pressed {
                    background-color: #DCDCDC;
                }
            """)
            cancel_btn.clicked.connect(self.reject)
            btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton(ok_text)
        ok_btn.setFixedHeight(36)
        ok_btn.setMinimumWidth(90)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {self._darken(accent_color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken(accent_color, factor=0.75)};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        card_layout.addLayout(btn_row)
        outer.addWidget(card)

    @staticmethod
    def _darken(hex_color: str, factor: float = 0.85) -> str:
        """Darken a hex color by a given factor."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02X}{g:02X}{b:02X}"

class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(420)

        # ── Overlay ────────────────────────────────────────────
        self._overlay = None
        if parent:
            self._overlay = QWidget(parent)
            self._overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.45);")
            self._overlay.setGeometry(parent.rect())
            self._overlay.show()
            self._overlay.raise_()

        self._init_ui()
        self.adjustSize()
        self._center()

    def _center(self):
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2,
                      (screen.height() - self.height()) // 2)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(15)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        badge = QLabel(); badge.setPixmap(_ui_pix('key', '#4A90D9', 18))
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background-color: #EAF3FB;
                border-radius: 18px;
                font-size: 15px;
            }
        """)

        title_label = QLabel("Password Reset")
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1a1a1a;")

        top_row.addWidget(badge)
        top_row.addWidget(title_label)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #EEEEEE;")
        card_layout.addWidget(divider)

        subtitle = QLabel("Contact your System Admin to reset your credentials.\nClick any row to copy the details.")
        subtitle.setWordWrap(True)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #2B2B2B;")
        card_layout.addWidget(subtitle)

        contacts = [
            ("phone.png",     "Phone",     "+63 912 345 6789"),
            ("mail.png",      "Email",     "admin@bakesync.com"),
            ("facebook.png",  "Facebook",  "facebook.com/BakeSync"),
            ("instagram.png", "Instagram", "@bakesync.official"),
        ]

        for icon, label, value in contacts:
            card_layout.addWidget(self._make_contact_row(icon, label, value))

        card_layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("Got it")
        ok_btn.setFixedHeight(36)
        ok_btn.setMinimumWidth(90)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #3A7BC8; }
            QPushButton:pressed { background-color: #2F6BAD; }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        card_layout.addLayout(btn_row)

        outer.addWidget(card)

    def _make_contact_row(self, icon, label, value):
        row = QWidget()
        row.setObjectName("contactRow")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet("""
            QWidget#contactRow {
                background-color: #F7F7F7;
                border-radius: 8px;
                border: 1px solid #EEEEEE;
            }
            QWidget#contactRow:hover {
                background-color: #EEF4FB;
                border: 1px solid #C5D9F0;
            }
        """)
        row.setFixedHeight(55)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pix = QPixmap(os.path.join(IMAGES_DIR, icon))
        if not pix.isNull():
            icon_label.setPixmap(pix.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setText("•")  

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 9))
        label_widget.setStyleSheet("color: #616161; background: transparent; border: none;")

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Arial", 11, QFont.Weight.Medium))
        value_widget.setStyleSheet("color: #222222; background: transparent; border: none;")

        text_col.addWidget(label_widget)
        text_col.setSpacing(4)
        text_col.addWidget(value_widget)

        copy_hint = QLabel("Copy")
        copy_hint.setFont(QFont("Arial", 9))
        copy_hint.setStyleSheet("color: #4A90D9; background: transparent; border: none;")
        copy_hint.setObjectName("copyHint")

        layout.addWidget(icon_label)
        layout.addLayout(text_col)
        layout.addStretch()
        layout.addWidget(copy_hint)

        def on_click(event, v=value, hint=copy_hint):
            QApplication.clipboard().setText(v)
            hint.setText("Copied ✓")
            hint.setStyleSheet("color: #4AAD72; background: transparent; border: none;")

        row.mousePressEvent = on_click

        return row

    def accept(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().accept()

    def reject(self):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().reject()

    def closeEvent(self, event):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        super().closeEvent(event)


def show_info(parent, title, message):
    dlg = CustomDialog(parent, title, message, dialog_type="info")
    dlg.exec()

def show_warning(parent, title, message):
    dlg = CustomDialog(parent, title, message, dialog_type="warning")
    dlg.exec()

def show_error(parent, title, message):
    dlg = CustomDialog(parent, title, message, dialog_type="error")
    dlg.exec()

def show_success(parent, title, message):
    dlg = CustomDialog(parent, title, message, dialog_type="success")
    dlg.exec()

def show_confirm(parent, title, message, ok_text="Confirm", cancel_text="Cancel") -> bool:
    dlg = CustomDialog(parent, title, message, dialog_type="warning",
                       ok_text=ok_text, cancel_text=cancel_text)
    return dlg.exec() == QDialog.DialogCode.Accepted
