# custom_alerts.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtSvgWidgets import QSvgWidget

class BakeSyncAlert(QDialog):
    """
    BakeSync Alert System with Drop Shadow, Bold Information, and Custom Buttons.
    """
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    QUESTION = "question"

    def __init__(self, parent=None, alert_type=INFO, title="", message="", details=None, yes_text="CONFIRM", no_text="CANCEL"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(440) 
        
        self.alert_type = alert_type
        self.title_text = title
        self.msg_text = message
        self.details = details or {}
        
        self.yes_text = yes_text
        self.no_text = no_text
        
        self._init_ui()
        self.adjustSize()

    def _init_ui(self):
        theme = {
            self.SUCCESS:  {"icon_color": "#157A3C", "header_bg": "#5C3A21", "btn_hover": "#4A2E1A", "svg": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>"""},
            self.ERROR:    {"icon_color": "#B91C1C", "header_bg": "#841717", "btn_hover": "#6B1111", "svg": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>"""},
            self.WARNING:  {"icon_color": "#D97706", "header_bg": "#9A3412", "btn_hover": "#7C2D12", "svg": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""},
            self.INFO:     {"icon_color": "#5C3A21", "header_bg": "#5C3A21", "btn_hover": "#4A2E1A", "svg": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>"""},
            self.QUESTION: {"icon_color": "#5C3A21", "header_bg": "#5C3A21", "btn_hover": "#4A2E1A", "svg": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""}
        }
        cfg = theme.get(self.alert_type, theme[self.INFO])

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 25) 

        card = QWidget()
        card.setObjectName("MainCard")
        card.setStyleSheet("""
            QWidget#MainCard {
                background-color: #F7F7F4;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['header_bg']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 0, 25, 0)

        title_lbl = QLabel(self.title_text)
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        card_layout.addWidget(header)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(35, 30, 35, 25)
        content_layout.setSpacing(25)

        msg_row = QHBoxLayout()
        msg_row.setSpacing(20)
        msg_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        svg_str = cfg['svg'].replace('stroke="currentColor"', f'stroke="{cfg["icon_color"]}"')
        icon_svg = QSvgWidget()
        icon_svg.load(QByteArray(svg_str.encode('utf-8')))
        icon_svg.setFixedSize(45, 45) 
        msg_row.addWidget(icon_svg, alignment=Qt.AlignmentFlag.AlignTop)

        msg_lbl = QLabel(self.msg_text)
        msg_lbl.setFont(QFont("Segoe UI", 13))
        msg_lbl.setStyleSheet("color: #737373;")
        msg_lbl.setWordWrap(True)
        msg_row.addWidget(msg_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        content_layout.addLayout(msg_row)

        if self.details:
            details_layout = QVBoxLayout()
            details_layout.setSpacing(12)
            details_layout.setContentsMargins(30, 15, 30, 15)

            for key, val in self.details.items():
                row = QHBoxLayout()
                lbl_k = QLabel(str(key))
                lbl_k.setStyleSheet("color: #9CA3AF; font-size: 13px;")
                
                lbl_v = QLabel(str(val))
                lbl_v.setStyleSheet("color: #1F2937; font-size: 14px; font-weight: 900;") 
                lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                row.addWidget(lbl_k)
                row.addWidget(lbl_v)
                details_layout.addLayout(row)
            
            content_layout.addLayout(details_layout)

        # 🟢 FIX: Ginawang `self.btn_layout` para laging mahanap at ma-edit ng system!
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style_solid = f"""
            QPushButton {{ 
                background: {cfg['header_bg']}; 
                color: white; 
                border: none; 
                border-radius: 4px;
                font-weight: bold; 
                font-size: 14px; 
                padding: 10px 40px;
            }}
            QPushButton:hover {{ background: {cfg['btn_hover']}; }}
        """

        if self.alert_type == self.QUESTION:
            btn_no = QPushButton(self.no_text.upper())
            btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_no.setStyleSheet("""
                QPushButton { background: transparent; color: #949494; font-size: 14px; font-weight: bold; border: none; padding: 10px 20px; }
                QPushButton:hover { color: #5C3A21; }
            """)
            btn_no.clicked.connect(self.reject)
            
            btn_yes = QPushButton(self.yes_text.upper())
            btn_yes.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_yes.setStyleSheet(btn_style_solid)
            btn_yes.clicked.connect(self.accept)
            
            self.btn_layout.addWidget(btn_no)
            self.btn_layout.addSpacing(10)
            self.btn_layout.addWidget(btn_yes)
        else:
            btn_ok = QPushButton("OKAY")
            btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_ok.setStyleSheet(btn_style_solid)
            btn_ok.clicked.connect(self.accept)
            self.btn_layout.addWidget(btn_ok)

        content_layout.addLayout(self.btn_layout)
        card_layout.addWidget(content_widget)

        main_layout.addWidget(card)

    @staticmethod
    def show_success(parent, title, message, details=None):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.SUCCESS, title, message, details)
        dialog.exec()

    @staticmethod
    def show_error(parent, title, message, details=None):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.ERROR, title, message, details)
        dialog.exec()

    @staticmethod
    def show_warning(parent, title, message, details=None):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.WARNING, title, message, details)
        dialog.exec()

    @staticmethod
    def show_info(parent, title, message, details=None):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.INFO, title, message, details)
        dialog.exec()

    @staticmethod
    def ask_yes_no(parent, title, message, details=None, yes_text="CONFIRM", no_text="CANCEL"):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.QUESTION, title, message, details, yes_text, no_text)
        return dialog.exec() == QDialog.DialogCode.Accepted

    @staticmethod
    def ask_three_options(parent, title, message, details=None, btn1_text="Restore Old", btn2_text="Save as New", cancel_text="Cancel"):
        dialog = BakeSyncAlert(parent, BakeSyncAlert.WARNING, title, message, details)
        
        # 🟢 FIX: Ngayong alam na natin ang self.btn_layout, buburahin natin yung lumang "OKAY" button
        while dialog.btn_layout.count():
            item = dialog.btn_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 🟢 At ipapalit natin yung magandang tatlong options
        btn_cancel = QPushButton(cancel_text.upper())
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #949494; font-size: 13px; font-weight: bold; border: none; padding: 10px 15px; }
            QPushButton:hover { color: #5C3A21; }
        """)
        btn_cancel.clicked.connect(lambda: dialog.done(0))

        btn_2 = QPushButton(btn2_text.upper())
        btn_2.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_2.setStyleSheet("""
            QPushButton { background: transparent; color: #D97706; border: 1px solid #D97706; border-radius: 4px; font-size: 13px; font-weight: bold; padding: 10px 15px; }
            QPushButton:hover { background: #FEF3C7; }
        """)
        btn_2.clicked.connect(lambda: dialog.done(2))

        btn_1 = QPushButton(btn1_text.upper())
        btn_1.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_1.setStyleSheet("""
            QPushButton { background: #D97706; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 13px; padding: 10px 20px; }
            QPushButton:hover { background: #B45309; }
        """)
        btn_1.clicked.connect(lambda: dialog.done(1))
        
        # Ilalagay natin isa-isa sa layout
        dialog.btn_layout.addWidget(btn_cancel)
        dialog.btn_layout.addSpacing(5)
        dialog.btn_layout.addWidget(btn_2)
        dialog.btn_layout.addSpacing(5)
        dialog.btn_layout.addWidget(btn_1)
        
        return dialog.exec()