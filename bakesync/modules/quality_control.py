from bakesync.paths import IMAGES_DIR
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QComboBox,
                             QRadioButton, QButtonGroup, QSpinBox, QTabWidget, QHeaderView, QLineEdit,
                             QTextEdit, QMessageBox, QFrame, QAbstractSpinBox)
from PyQt6.QtGui import QFont, QColor, QPainter, QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, QTimer, QTime, QByteArray

from bakesync.core.database import DatabaseManager
from bakesync.widgets.ui import (intro_row, title_row as ui_title_row, legend_row, BarChart, InfoIcon,
                               THEME as UI)
from bakesync.core.audit import log_activity
from datetime import datetime

from bakesync.widgets.custom_alerts import BakeSyncAlert


from bakesync.core.leftovers import expire_old_batches
from bakesync.widgets.leftover_dialog import LeftoverDialog
from datetime import date as _date


class QualityControlWidget(QWidget):
    def __init__(self, db: DatabaseManager, current_user: str = ""):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.current_filter = "Today"
        self.current_type_filter = "All Types"
        self.init_ui()

        self.alert_1130_shown = False
        self.alert_1145_shown = False
        self.alert_1155_shown = False
        self.auto_waste_done = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_auto_waste_time)
        self.timer.start(30000)
        QTimer.singleShot(0, self.check_auto_waste_time)

    def _create_vector_icon(self, svg_string, color):
        colored_svg = svg_string.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(colored_svg.encode('utf-8')), "SVG")
        return QIcon(pixmap)

    def init_ui(self):
        self.setStyleSheet("QualityControlWidget { background-color: #F8FAFC; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 20, 40, 20)

        # ==========================================
        # SVG ICONS
        # ==========================================
        EOD_SVG    = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8v13H3V8"></path><polyline points="1 3 23 3 23 8 1 8 1 3"></polyline><line x1="10" y1="12" x2="14" y2="12"></line></svg>'
        HISTORY_SVG= '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
        ANALYTICS_SVG='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
        PLUS_SVG   = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>'
        FORCE_SVG  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'

        # ==========================================
        # FIX 4: IMPROVED TABLE STYLE — bolder font matching Recipe tab
        # ==========================================
        RECIPE_TABLE_STYLE = """
            QTableWidget {
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                background-color: transparent;
                color: #1F2937;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #6B3F27;
                padding: 12px 15px;
                border: none;
                border-bottom: 1px solid #5a3520;
                font-weight: 600;
                font-family: 'Segoe UI';
                color: #FFFFFF;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.3px;
            }
            QTableWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #F3F4F6;
            }
            QTableWidget::item:selected {
                background-color: #F3E8DC;
                color: #1F2937;
            }
            QScrollBar:vertical { background: #F5F2EB; width: 6px; border-radius: 3px; margin: 0; border: none; }
            QScrollBar::handle:vertical { background: #9A7B4F; border-radius: 3px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #3A2318; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """

        # ==========================================
        # TAB WIDGET
        # ==========================================
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
                margin: 0px;
                padding: 0px;
                margin-left: -1px;
                margin-right: -1px;
                margin-bottom: -1px;
            }
            QTabBar::tab {
                background: transparent;
                color: #555555;
                font-size: 13px;
                font-weight: normal;
                padding: 12px 24px 10px 24px;
                border: none;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:selected {
                color: #4E2D1A;
                border-bottom: 3px solid #4E2D1A;
            }
            QTabBar::tab:!selected:hover {
                color: black;
                border-bottom: 3px solid #B09882;
            }
        """)
        self.tabs.setIconSize(QSize(18, 18))

        # ==========================================
        # FIX 3: COMBO STYLE — matching POS dropdown design
        # ==========================================
        import os as _os
        _arrow_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6B3F27" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>'''
        _images_dir = IMAGES_DIR
        if not _os.path.exists(_images_dir):
            _os.makedirs(_images_dir)
        _arrow_path = _os.path.join(_images_dir, "brown_arrow.svg").replace("\\", "/")
        with open(_arrow_path, "w", encoding="utf-8") as _f:
            _f.write(_arrow_svg)

        COMBO_STYLE = f"""
            QComboBox {{
                background: white;
                border: 1.5px solid #6B3F27;
                border-radius: 6px;
                padding: 0px 12px;
                color: #4A2C1C;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:hover {{ border-color: #4A2C1C; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border-left: 1.5px solid #6B3F27;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: url("{_arrow_path}");
                width: 16px;
                height: 16px;
            }}
            QComboBox QAbstractItemView {{
                border: 1.5px solid #6B3F27;
                background-color: white;
                color: #4A2C1C;
                selection-background-color: #F0E6DC;
                selection-color: #4A2C1C;
                font-size: 13px;
            }}
        """

        # ==========================================
        # TAB 1 — EOD CLOSING
        # ==========================================
        self.eod_tab = QWidget()
        eod_layout = QVBoxLayout(self.eod_tab)
        eod_layout.setContentsMargins(20, 20, 20, 20)
        eod_layout.setSpacing(15)

        eod_header = QHBoxLayout()
        BELL_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>'
        eod_notif_widget = QWidget()
        eod_notif_widget.setStyleSheet("background: #693903; border-left: 4px solid #693903; border-radius: 4px;")
        eod_notif_layout = QHBoxLayout(eod_notif_widget)
        eod_notif_layout.setContentsMargins(10, 6, 10, 6)
        eod_notif_layout.setSpacing(8)

        bell_icon_label = QLabel()
        bell_icon_label.setPixmap(self._create_vector_icon(BELL_SVG, "white").pixmap(QSize(16, 16)))
        bell_icon_label.setFixedSize(18, 18)
        bell_icon_label.setStyleSheet("background: transparent; border: none;")

        eod_info = QLabel("After closing: decide what to do with leftover bread")
        eod_info.setStyleSheet("""
            color: white;
            font-size: 12px;
            font-weight: demibold;
            background: transparent;
            border: none;
        """)
        eod_notif_layout.addWidget(bell_icon_label)
        eod_notif_layout.addWidget(eod_info)
        eod_header.addWidget(eod_notif_widget)
        eod_header.addStretch()

        self.today_search = QLineEdit()
        self.today_search.setPlaceholderText("Search product...")
        self.today_search.setFixedSize(190, 36)
        self.today_search.setStyleSheet("QLineEdit { background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; font-size: 13px; color: #0F172A; } QLineEdit:focus { border: 1px solid #693903; }")
        self.today_search.textChanged.connect(self.load_eod_data)
        eod_header.addWidget(self.today_search)

        self.today_cat = QComboBox()
        self.today_cat.addItems(["All Products", "Bread", "Retail"])
        self.today_cat.setFixedSize(140, 36)
        self.today_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.today_cat.setStyleSheet("QComboBox { background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; font-size: 13px; color: #0F172A; } QComboBox:hover { border: 1px solid #693903; } QComboBox QAbstractItemView { background: white; color: #0F172A; selection-background-color: #F3E8DC; selection-color: #693903; }")
        self.today_cat.currentTextChanged.connect(self.load_eod_data)
        eod_header.addWidget(self.today_cat)

        force_waste_btn = QPushButton("  Leftover Bread (End of Day)")
        force_waste_btn.setIcon(self._create_vector_icon(FORCE_SVG, "#FFFFFF"))
        force_waste_btn.setStyleSheet("""
            QPushButton { background-color: #A83535; color: white; border: 1px solid #FECACA;
                          padding: 10px 14px; font-size: 12px; border-radius: 8px; font-weight: demibold; }
            QPushButton:hover { background-color: #5C1D1D; }
        """)
        force_waste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        force_waste_btn.clicked.connect(self.open_leftovers)
        eod_header.addWidget(force_waste_btn)

        from bakesync.widgets.ui import RefreshButton
        self.refresh_btn = RefreshButton(h=36)
        self.refresh_btn.clicked.connect(self.load_eod_data)
        eod_header.addWidget(self.refresh_btn)
        eod_layout.addLayout(eod_header)

        # Buod ng araw: ilan ang na-stock, nabenta, nasayang at natira ngayon
        self.today_summary = QLabel()
        self.today_summary.setWordWrap(True)
        self.today_summary.setStyleSheet(
            "background-color: #FFF7ED; border: 1px solid #FED7AA; border-radius: 8px; "
            "padding: 10px 14px; font-size: 13px; color: #7C2D12;")
        eod_layout.addWidget(self.today_summary)

        tdesc, _ = intro_row("To record waste: type the pieces in 'Qty wasted', then click Record.",
                             "Stocked Today = pieces put out today.  Sold Today = sold at the POS.  Wasted Today = already recorded as waste.  "
                             "Left = still on the shelf.  After closing, click 'Leftover Bread' to decide what happens to what is left.",
                             "Today's table")
        eod_layout.addWidget(tdesc)
        eod_card = QFrame()
        eod_card.setStyleSheet(
            "background-color: white; border: 1px solid #E5E7EB; border-radius: 8px;"
        )
        eod_card_layout = QVBoxLayout(eod_card)
        eod_card_layout.setContentsMargins(0, 0, 0, 0)
        eod_card_layout.setSpacing(0)

        EOD_TABLE_STYLE = """
            QTableWidget {
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                background-color: transparent;
                color: #1F2937;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #693903;
                padding: 12px 15px;
                border: none;
                border-bottom: 1px solid #5a3520;
                font-weight: normal;
                font-family: 'Segoe UI';
                color: #FFFFFF;
                font-size: 12px;
                letter-spacing: 0.3px;
            }
            QTableWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #F3F4F6;
            }
            QTableWidget::item:selected {
                background-color: #F3E8DC;
                color: #1F2937;
            }
            QScrollBar:vertical { background: #F5F2EB; width: 6px; border-radius: 3px; margin: 0; border: none; }
            QScrollBar::handle:vertical { background: #9A7B4F; border-radius: 3px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #3A2318; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """

        self.eod_table = QTableWidget()
        self.eod_table.setColumnCount(7)
        self.eod_table.setHorizontalHeaderLabels(["Product", "Stocked Today", "Sold Today", "Wasted Today", "Left (Unsold)", "Qty wasted", "Action"])
        self.eod_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.eod_table.setStyleSheet(EOD_TABLE_STYLE)
        self.eod_table.verticalHeader().setVisible(False)
        self.eod_table.setShowGrid(False)
        self.eod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.eod_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.eod_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.eod_table.setAlternatingRowColors(False)
        eod_card_layout.addWidget(self.eod_table)
        eod_layout.addWidget(eod_card)

        self.tabs.addTab(self.eod_tab, self._create_vector_icon(EOD_SVG, "#6B3F27"), "  Today")

        # ==========================================
        # TAB 2 — WASTE HISTORY
        # ==========================================
        self.dash_tab = QWidget()
        dash_layout = QVBoxLayout(self.dash_tab)
        dash_layout.setContentsMargins(20, 20, 20, 20)
        dash_layout.setSpacing(15)

        dash_header = QHBoxLayout()
        history_title = QLabel("  Waste Records")
        history_title.setStyleSheet("color: #0F172A; font-size: 15px; font-weight: bold;")
        dash_header.addWidget(history_title)
        dash_header.addStretch()

        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search product...")
        self.history_search.setFixedSize(180, 32)
        self.history_search.setStyleSheet("QLineEdit { background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; font-size: 13px; color: #0F172A; } QLineEdit:focus { border: 1px solid #693903; }")
        self.history_search.textChanged.connect(lambda _t: self.load_loss_data())
        dash_header.addWidget(self.history_search)

        self.history_cat = QComboBox()
        self.history_cat.addItems(["All Products", "Bread", "Retail"])
        self.history_cat.setFixedSize(130, 32)
        self.history_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_cat.setStyleSheet("QComboBox { background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px 10px; font-size: 13px; color: #0F172A; } QComboBox:hover { border: 1px solid #693903; } QComboBox QAbstractItemView { background: white; color: #0F172A; selection-background-color: #F3E8DC; selection-color: #693903; }")
        self.history_cat.currentTextChanged.connect(lambda _t: self.load_loss_data())
        dash_header.addWidget(self.history_cat)

        # FIX 3: Type filter with POS-style dropdown
        import os as _os2
        _arrow_path2 = _os.path.join(_images_dir, "brown_arrow.svg").replace("\\", "/")

        INV_COMBO_STYLE = f"""
            QComboBox {{
                background-color: white;
                border: 1px solid #0F172A;
                padding: 4px 40px 4px 12px;
                font-size: 13px;
                color: #0F172A;
                min-width: 120px;
            }}
            QComboBox:hover {{ border: 1px solid #735F48; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: url("{_arrow_path2}");
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid #948778;
                outline: none;
                padding: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 0px 12px;
                color: #0F172A;
                border: none;
                margin: 0px;
                min-width: 120px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #693903;
                color: white;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #693903;
                color: white;
            }}
        """

        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(["All types", "Not sold", "Kitchen waste", "Expired"])
        self.type_filter_combo.setCurrentText("All types")
        self.type_filter_combo.setFixedHeight(32)
        self.type_filter_combo.setFixedWidth(150)
        self.type_filter_combo.setStyleSheet(INV_COMBO_STYLE)
        self.type_filter_combo.currentTextChanged.connect(self.on_type_filter_changed)
        dash_header.addWidget(self.type_filter_combo)

        self.date_filter_combo = QComboBox()
        self.date_filter_combo.addItems([
            "Today", "Yesterday", "Last 7 Days",
            "This Month", "Last Month", "This Year", "All Time"
        ])
        self.date_filter_combo.setCurrentText("All Time")
        self.date_filter_combo.setFixedHeight(32)
        self.date_filter_combo.setFixedWidth(130)
        self.date_filter_combo.setStyleSheet(INV_COMBO_STYLE)
        self.date_filter_combo.currentTextChanged.connect(self.on_filter_changed)
        dash_header.addWidget(self.date_filter_combo)

        log_btn = QPushButton("  Record Waste")
        log_btn.setIcon(self._create_vector_icon(PLUS_SVG, "#FFFFFF"))
        log_btn.setStyleSheet("""
            QPushButton { background-color: #693903; border: none; color: white; border-radius: 6px;
                          padding: 8px 16px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #452803; }
        """)
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(self.log_waste)
        dash_header.addWidget(log_btn)
        dash_layout.addLayout(dash_header)

        loss_card = QFrame()
        loss_card.setStyleSheet(
            "background-color: white; border: 1px solid #E5E7EB; border-radius: 8px;"
        )
        loss_card_layout = QVBoxLayout(loss_card)
        loss_card_layout.setContentsMargins(0, 0, 0, 0)
        loss_card_layout.setSpacing(0)

        LOSS_TABLE_STYLE = """
            QTableWidget {
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                background-color: transparent;
                color: #1F2937;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #693903;
                padding: 12px 15px;
                border: none;
                border-bottom: 1px solid #5a3520;
                font-weight: normal;
                font-family: 'Segoe UI';
                color: #FFFFFF;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #F3F4F6;
            }
            QTableWidget::item:selected {
                background-color: #F3E8DC;
                color: #1F2937;
            }
            QScrollBar:vertical { background: #F5F2EB; width: 6px; border-radius: 3px; margin: 0; border: none; }
            QScrollBar::handle:vertical { background: #9A7B4F; border-radius: 3px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #3A2318; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """

        self.loss_table = QTableWidget()
        self.loss_table.setColumnCount(6)
        self.loss_table.setHorizontalHeaderLabels(["Date & Time", "Product", "Waste Type", "Qty Wasted", "Spoilage Loss (₱)", "Incident Reason"])
        self.loss_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.loss_table.setStyleSheet(LOSS_TABLE_STYLE)
        self.loss_table.verticalHeader().setVisible(False)
        self.loss_table.setShowGrid(False)
        self.loss_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.loss_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.loss_table.setAlternatingRowColors(False)
        loss_card_layout.addWidget(self.loss_table)
        dash_layout.addWidget(loss_card)

        hdesc, _ = intro_row("Every piece recorded as waste, newest first.",
                             "Use the filters to see one kind of waste (not sold, burnt or damaged, expired) or one product. "
                             "Not sold = left over at the end of the day.  Kitchen waste = burnt, dropped or damaged.  "
                             "Expired = passed its sell-by date.", "Waste History")
        dash_layout.insertWidget(0, hdesc)
        self.tabs.addTab(self.dash_tab, self._create_vector_icon(HISTORY_SVG, "#4E2D1A"), "  Waste History")

        # ==========================================
        # TAB 3 — PERFORMANCE ANALYTICS
        # ==========================================
        self.analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(self.analytics_tab)
        analytics_layout.setContentsMargins(20, 20, 20, 20)
        analytics_layout.setSpacing(20)

        side_by_side = QHBoxLayout()
        side_by_side.setSpacing(20)

        left_col = QVBoxLayout()
        perf_title, ptl = ui_title_row("Most wasted (last 7 days)", icon="trash", size=13,
                                       info="'% wasted' = pieces wasted out of all pieces sold and wasted. "
                                            "Under 5% is good. 5-15%: watch it. Over 15%: bake or order fewer.")
        ptl.addWidget(legend_row([(UI["green"], "Good"), (UI["amber"], "Watch"), (UI["red"], "Bake / order fewer")]))
        left_col.addWidget(perf_title)

        perf_card = QFrame()
        perf_card.setStyleSheet(
            "background-color: white; border: 1px solid #E5E7EB; border-radius: 8px;"
        )
        perf_card_layout = QVBoxLayout(perf_card)
        perf_card_layout.setContentsMargins(0, 0, 0, 0)
        perf_card_layout.setSpacing(0)

        PERF_TABLE_STYLE = """
            QTableWidget {
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                background-color: transparent;
                color: #1F2937;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #693903;
                padding: 12px 15px;
                border: none;
                border-bottom: 1px solid #5a3520;
                font-weight: normal;
                font-family: 'Segoe UI';
                color: #FFFFFF;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 10px 15px;
                border-bottom: 1px solid #F3F4F6;
            }
            QTableWidget::item:selected {
                background-color: #F3E8DC;
                color: #1F2937;
            }
            QScrollBar:vertical { background: #F5F2EB; width: 6px; border-radius: 3px; margin: 0; border: none; }
            QScrollBar::handle:vertical { background: #9A7B4F; border-radius: 3px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #3A2318; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """

        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(4)
        self.performance_table.setHorizontalHeaderLabels(["Product", "Wasted", "% wasted", "Advice"])
        self.performance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.performance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)   # advice never cut off
        self.performance_table.setStyleSheet(PERF_TABLE_STYLE)
        self.performance_table.verticalHeader().setVisible(False)
        self.performance_table.setShowGrid(False)
        self.performance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.performance_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.performance_table.setAlternatingRowColors(False)
        perf_card_layout.addWidget(self.performance_table)
        left_col.addWidget(perf_card)
        side_by_side.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        chart_title, _ = ui_title_row("Pieces wasted per day (last 7 days)", icon="chart", size=13,
                                      info="Each day has up to three bars, one for each reason: orange = not sold, "
                                           "red = burnt or damaged, purple = expired. Taller bars = more pieces wasted. "
                                           "Point at a day to see the exact numbers.")
        right_col.addWidget(chart_title)
        self.waste_note = QLabel(""); self.waste_note.setWordWrap(True)
        self.waste_note.setStyleSheet("color: #64748B; font-size: 12px;")
        right_col.addWidget(self.waste_note)
        chart_box = QFrame(); chart_box.setObjectName("wchart")
        chart_box.setStyleSheet("QFrame#wchart { background: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        cbl = QVBoxLayout(chart_box); cbl.setContentsMargins(10, 10, 10, 6)
        self.waste_chart = BarChart(money=False, y_title="Pieces", empty_text="Nothing wasted in the last 7 days")
        cbl.addWidget(self.waste_chart)
        right_col.addWidget(chart_box, 1)
        self.chart_view = None

        side_by_side.addLayout(right_col, 1)
        analytics_layout.addLayout(side_by_side)

        self.tabs.addTab(self.analytics_tab, self._create_vector_icon(ANALYTICS_SVG, "#4E2D1A"), "  Most Wasted")
        intro, _ = intro_row("Bread and items that could not be sold: record them here so you know what to bake or order less of.",
                             "Today = record waste and decide on leftover bread.  Waste History = everything recorded before.  "
                             "Most Wasted = which products are wasted the most, with simple advice.", "Waste")
        layout.addWidget(intro)
        layout.addWidget(self.tabs)

        self.load_eod_data()
        self.load_loss_data()
        self.tabs.currentChanged.connect(self.on_tab_changed)

    # ==========================================
    # REFRESH BUTTON FEEDBACK
    # ==========================================
    def trigger_refresh_feedback(self):
        self.refresh_btn.click()

    # ==========================================
    # FILTER HANDLERS
    # ==========================================
    def on_filter_changed(self, text):
        self.current_filter = text
        self.load_loss_data()

    def on_type_filter_changed(self, text):
        self.current_type_filter = text
        self.load_loss_data()

    # ==========================================
    # AUTO-WASTE LOGIC
    # ==========================================
    def check_auto_waste_time(self):
        """Once a day (and right after midnight): write off stock whose expiry date has arrived.
        Leftover bread is no longer thrown away automatically; use 'Natirang Tinapay' to decide."""
        today = _date.today().isoformat()
        if getattr(self, "_expired_checked", None) == today:
            return
        self._expired_checked = today
        try:
            if expire_old_batches(self.db, self.current_user or "System"):
                self.load_eod_data(); self.load_loss_data(); self.load_analytics_data()
        except Exception as e:
            print(f"[Waste] expired check error: {e}")

    def open_leftovers(self):
        if LeftoverDialog(self.db, self.current_user, self).exec():
            self.load_eod_data(); self.load_loss_data(); self.load_analytics_data()

    # ==========================================
    # DATA LOADING
    # ==========================================
    def on_tab_changed(self, index):
        if index == 0: self.load_eod_data()
        elif index == 1: self.load_loss_data()
        elif index == 2: self.load_analytics_data()

    def load_eod_data(self, *_):
        """Today tab: stocked / sold / wasted today and what is left unsold, per product."""
        TODAY = "date('now','localtime')"
        cat = self.today_cat.currentText() if hasattr(self, 'today_cat') else "All Products"
        cat_cond = {"Bread": "AND p.product_type = 'bread'",
                    "Retail": "AND COALESCE(p.product_type, '') != 'bread'"}.get(cat, "")
        search = self.today_search.text().strip() if hasattr(self, 'today_search') else ""
        search_cond, params = ("AND p.name LIKE ?", (f"%{search}%",)) if search else ("", ())
        query = f"""
            SELECT p.id AS product_id, p.name, COALESCE(p.stock_qty, 0) AS left_qty, COALESCE(p.production_cost, 0) AS cost,
                   (SELECT COALESCE(SUM(COALESCE(b.initial_qty, b.quantity_remaining)), 0) FROM product_batches b
                     WHERE b.product_id = p.id AND date(b.received_date) = {TODAY}) AS stocked,
                   (SELECT COALESCE(SUM(s.quantity), 0) FROM sales s
                     WHERE s.product_id = p.id AND date(s.created_at) = {TODAY} AND COALESCE(s.is_voided, 0) = 0) AS sold,
                   (SELECT COALESCE(SUM(w.quantity), 0) FROM waste_logs w
                     WHERE w.product_id = p.id AND date(w.created_at) = {TODAY}) AS wasted
            FROM products p
            WHERE p.is_archived = 0 {cat_cond} {search_cond}
            ORDER BY CASE WHEN p.product_type = 'bread' THEN 0 ELSE 1 END, p.name
        """
        try:
            data = self.db.fetch_all(query, params)
        except Exception as e:
            print(f"Error EOD Data: {e}")
            return

        if not search:
            data = [d for d in data if d['left_qty'] > 0 or d['stocked'] or d['sold'] or d['wasted']]
        tot = {"stocked": 0, "sold": 0, "wasted": 0, "left": 0, "loss": 0.0}
        for item in data:
            tot["stocked"] += item['stocked']; tot["sold"] += item['sold']
            tot["wasted"] += item['wasted']; tot["left"] += item['left_qty']
            tot["loss"] += item['wasted'] * item['cost']   # valued at cost, same as the Sales page
        self.today_summary.setText(
            f"<b>Today:</b> {tot['stocked']:g} pcs stocked &nbsp;·&nbsp; {tot['sold']:g} sold &nbsp;·&nbsp; "
            f"<b>{tot['wasted']:g} wasted</b> (₱{tot['loss']:,.2f} at cost) &nbsp;·&nbsp; <b>{tot['left']:g} left unsold</b>")

        TRASH_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>'

        self.eod_table.clearContents()
        self.eod_table.setRowCount(len(data))
        for row, item in enumerate(data):
            left = int(item['left_qty'])
            cells = [item['name'], f"{item['stocked']:g} pcs", f"{item['sold']:g} pcs",
                     f"{item['wasted']:g} pcs", f"{left} pcs"]
            for col, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 3 and item['wasted'] > 0:
                    cell.setForeground(QColor("#B91C1C"))
                self.eod_table.setItem(row, col, cell)

            spin_wrapper = QWidget()
            spin_wrapper.setStyleSheet("background: transparent; border: none;")
            spin_layout = QHBoxLayout(spin_wrapper)
            spin_layout.setContentsMargins(4, 4, 4, 4)
            spin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            leftover_spin = QSpinBox()
            leftover_spin.setRange(0, left)
            leftover_spin.setValue(0)   # type how many were wasted; never pre-filled with everything
            leftover_spin.setEnabled(left > 0)
            leftover_spin.setFixedSize(80, 32)
            leftover_spin.setStyleSheet("""
                QSpinBox { border: 1px solid #CBD5E1; border-radius: 4px;
                           padding: 4px 8px; font-size: 13px; color: #0F172A; background: white;
                           qproperty-alignment: AlignCenter; }
                QSpinBox:disabled { background: #F1F5F9; color: #94A3B8; }
                QSpinBox::up-button { background: transparent; border: none; width: 0px; }
                QSpinBox::down-button { background: transparent; border: none; width: 0px; }
            """)
            spin_layout.addWidget(leftover_spin)
            all_btn = QPushButton("All")
            all_btn.setFixedSize(52, 32)
            all_btn.setEnabled(left > 0)
            all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            all_btn.setToolTip("Fill in everything left")
            all_btn.setStyleSheet("QPushButton { background: #F5ECE5; color: #693903; border: 1px solid #E8D5C4; border-radius: 6px; "
                                  "font-size: 11px; font-weight: bold; } QPushButton:disabled { color: #CBD5E1; background: #F8FAFC; }")
            all_btn.clicked.connect(lambda _, s=leftover_spin, n=left: s.setValue(n))
            spin_layout.addWidget(all_btn)
            self.eod_table.setCellWidget(row, 5, spin_wrapper)

            btn_wrapper = QWidget()
            btn_wrapper.setStyleSheet("background: transparent; border: none;")
            btn_layout = QHBoxLayout(btn_wrapper)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            log_btn = QPushButton("  Record")
            log_btn.setIcon(self._create_vector_icon(TRASH_SVG, "#FFFFFF"))
            log_btn.setFixedSize(90, 32)
            log_btn.setEnabled(left > 0)
            log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            log_btn.setStyleSheet("""
                QPushButton { background-color: #B91C1C; color: #FFFFFF; border: none;
                              border-radius: 6px; font-weight: bold; font-size: 12px; padding: 6px 10px}
                QPushButton:hover { background-color: #991B1B; }
                QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
            """)
            log_btn.clicked.connect(
                lambda ch, r=row, p_id=item['product_id'], p_name=item['name']:
                self.submit_eod_spoilage(r, p_id, p_name)
            )
            btn_layout.addWidget(log_btn)
            self.eod_table.setCellWidget(row, 6, btn_wrapper)
            self.eod_table.setRowHeight(row, 60)

    def submit_eod_spoilage(self, row, prod_id, prod_name):
        spin_box = self.eod_table.cellWidget(row, 5)
        qty = spin_box.layout().itemAt(0).widget().value()

        if qty <= 0:
            BakeSyncAlert.show_warning(self, "Invalid Quantity", "Please enter a quantity greater than 0.")
            return

        choice = self._ask_waste_reason(prod_name, qty)
        is_confirmed = choice is not None
        waste_type, reason = choice if choice else ("", "")

        if is_confirmed:
            with self.db.transaction():
                self.db.execute_query(
                    "INSERT INTO waste_logs (product_id, waste_type, quantity, reason) VALUES (?, ?, ?, ?)",
                    (prod_id, waste_type, qty, reason)
                )
                self.db.execute_query(
                    "UPDATE products SET stock_qty = MAX(0, COALESCE(stock_qty,0) - ?) WHERE id = ?",
                    (qty, prod_id)
                )
                batches = self.db.fetch_all(
                    "SELECT id, quantity_remaining FROM product_batches WHERE product_id = ? AND quantity_remaining > 0 ORDER BY expiry_date ASC",
                    (prod_id,)
                )
                rem = qty
                for b in batches:
                    if rem <= 0: break
                    deduct = min(b['quantity_remaining'], rem)
                    self.db.execute_query(
                        "UPDATE product_batches SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                        (deduct, b['id'])
                    )
                    rem -= deduct

            log_activity(self.db, self.current_user, "waste recorded", "waste", f"{qty} x {prod_name} - {reason}")
            BakeSyncAlert.show_success(
                self,
                title="Recorded",
                message=f"Recorded {qty} pcs of {prod_name} ({reason}) and removed them from stock.",
                details={
                    "Product": prod_name,
                    "Quantity Spoiled": f"{qty} pcs",
                    "Status": "Deducted from inventory"
                }
            )
            self.load_eod_data()
            self.load_loss_data()
            self.load_analytics_data()

    def load_loss_data(self):
        try:
            filter_text = getattr(self, 'current_filter', 'All Time')
            type_text   = getattr(self, 'current_type_filter', 'All Types')

            date_condition = ""
            if filter_text == "Today":
                date_condition = "AND DATE(w.created_at) = DATE('now', 'localtime')"
            elif filter_text == "Yesterday":
                date_condition = "AND DATE(w.created_at) = DATE('now', '-1 day', 'localtime')"
            elif filter_text == "Last 7 Days":
                date_condition = "AND w.created_at >= DATE('now', '-7 days', 'localtime')"
            elif filter_text == "This Month":
                date_condition = "AND strftime('%Y-%m', w.created_at) = strftime('%Y-%m', 'now', 'localtime')"
            elif filter_text == "Last Month":
                date_condition = "AND strftime('%Y-%m', w.created_at) = strftime('%Y-%m', DATE('now', '-1 month', 'localtime'))"
            elif filter_text == "This Year":
                date_condition = "AND strftime('%Y', w.created_at) = strftime('%Y', 'now', 'localtime')"

            type_condition = ""
            if type_text == "Not sold":
                type_condition = "AND w.waste_type = 'Market Spoilage'"
            elif type_text == "Kitchen waste":
                type_condition = "AND w.waste_type = 'Kitchen Waste'"
            elif type_text == "Expired":
                type_condition = "AND w.waste_type IN ('Expired', 'EXPIRED', 'Expired Retail')"

            cat_text = self.history_cat.currentText() if hasattr(self, 'history_cat') else "All Products"
            cat_condition = {"Bread": "AND p.product_type = 'bread'",
                             "Retail": "AND p.id IS NOT NULL AND COALESCE(p.product_type, '') != 'bread'"}.get(cat_text, "")
            search = self.history_search.text().strip() if hasattr(self, 'history_search') else ""
            search_condition, search_params = ("AND COALESCE(p.name, w.reason) LIKE ?", (f"%{search}%",)) if search else ("", ())

            data = self.db.fetch_all(f"""
                SELECT w.created_at,
                       COALESCE(p.name, w.reason) AS name,
                       w.waste_type, w.quantity, w.reason,
                       COALESCE(p.production_cost, 0) AS production_cost
                FROM waste_logs w
                LEFT JOIN products p ON w.product_id = p.id
                WHERE 1=1 {date_condition} {type_condition} {cat_condition} {search_condition}
                ORDER BY w.created_at DESC LIMIT 100
            """, search_params)

            self.loss_table.setRowCount(len(data))
            for row, item in enumerate(data):
                def centered(text):
                    i = QTableWidgetItem(text)
                    i.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    return i

                self.loss_table.setItem(row, 0, centered(str(item['created_at'])[:16]))
                self.loss_table.setItem(row, 1, centered(item['name']))

                w_type = item['waste_type']
                wt_item = QTableWidgetItem(w_type)
                wt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if w_type == "Kitchen Waste":
                    wt_item.setBackground(QColor("#FFCDD2"))
                    wt_item.setForeground(QColor("#B71C1C"))
                elif w_type == "Market Spoilage":
                    wt_item.setBackground(QColor("#FFE0B2"))
                    wt_item.setForeground(QColor("#E65100"))
                elif w_type == "Expired Retail":
                    wt_item.setBackground(QColor("#EDE7F6"))
                    wt_item.setForeground(QColor("#4527A0"))
                elif w_type == "EXPIRED":
                    wt_item.setBackground(QColor("#FCE4EC"))
                    wt_item.setForeground(QColor("#880E4F"))
                self.loss_table.setItem(row, 2, wt_item)

                self.loss_table.setItem(row, 3, centered(f"{item['quantity']} pcs"))

                # ── Spoilage Loss (₱) — cost only, walang tubo ──
                cost = item['production_cost'] or 0
                spoilage_loss = cost * item['quantity']
                loss_item = QTableWidgetItem(f"₱{spoilage_loss:,.2f}" if spoilage_loss > 0 else "—")
                loss_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if spoilage_loss > 0:
                    loss_item.setForeground(QColor("#B91C1C"))
                self.loss_table.setItem(row, 4, loss_item)

                self.loss_table.setItem(row, 5, centered(item['reason'] if item['reason'] else "N/A"))
                self.loss_table.setRowHeight(row, 48)
        except Exception as e:
            print(f"Error loading loss data: {e}")

    def load_analytics_data(self):
        """Last 7 days: what was wasted most, as a share of what was sold + wasted, with plain advice."""
        rows = self.db.fetch_all("""
            SELECT p.name, p.product_type,
                   COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id AND COALESCE(is_voided, 0) = 0
                             AND created_at >= date('now', '-6 days', 'localtime')), 0) AS sold,
                   COALESCE((SELECT SUM(quantity) FROM waste_logs WHERE product_id = p.id
                             AND created_at >= date('now', '-6 days', 'localtime')), 0) AS wasted
            FROM products p WHERE p.is_archived = 0
        """)
        rows = sorted((r for r in rows if r['wasted'] > 0), key=lambda r: -r['wasted'])
        self.performance_table.setRowCount(max(len(rows), 1))
        self.performance_table.clearSpans()
        if not rows:
            self.performance_table.setSpan(0, 0, 1, 4)
            it = QTableWidgetItem("Nothing wasted in the last 7 days. Great job!")
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.performance_table.setItem(0, 0, it)
        for row, r in enumerate(rows):
            rate = r['wasted'] / (r['sold'] + r['wasted']) * 100
            is_bread = (r['product_type'] or 'bread') == 'bread'
            if rate >= 15:
                advice, color = ("Bake fewer" if is_bread else "Order fewer"), "#B91C1C"
            elif rate >= 5:
                advice, color = "Watch", "#92400E"
            else:
                advice, color = "Good", "#065F46"
            for col, text in enumerate((r['name'], f"{r['wasted']:g} pcs", f"{rate:.0f}%", advice)):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 3:
                    it.setForeground(QColor(color))
                    f = it.font(); f.setBold(True); it.setFont(f)
                self.performance_table.setItem(row, col, it)
            self.performance_table.setRowHeight(row, 44)

        from datetime import date as _d, timedelta as _td
        data = {r["d"]: r for r in self.db.fetch_all("""
            SELECT DATE(created_at) AS d,
                SUM(CASE WHEN waste_type = 'Market Spoilage' THEN quantity ELSE 0 END) AS unsold,
                SUM(CASE WHEN waste_type = 'Kitchen Waste' THEN quantity ELSE 0 END) AS kitchen,
                SUM(CASE WHEN waste_type IN ('Expired', 'EXPIRED', 'Expired Retail') THEN quantity ELSE 0 END) AS expired
            FROM waste_logs WHERE created_at >= date('now', '-6 days', 'localtime')
            GROUP BY DATE(created_at)
        """)}
        days = [_d.today() - _td(days=i) for i in range(6, -1, -1)]
        def col(key):
            return [float(data[d.isoformat()][key] or 0) if d.isoformat() in data else 0 for d in days]
        series = [("Not sold", col("unsold"), "#D97706"), ("Burnt / damaged", col("kitchen"), "#B91C1C"),
                  ("Expired", col("expired"), "#7C3AED")]
        self.waste_chart.set_data([("Today" if d == _d.today() else d.strftime("%a %d")) for d in days], series,
                                  full_labels=[d.strftime("%A, %b %d") for d in days])
        totals = [(name, sum(vals)) for name, vals, _ in series]
        total = sum(t for _, t in totals)
        if total:
            top = max(totals, key=lambda x: x[1])
            self.waste_note.setText(f"In 7 days: <b>{total:g} pieces</b> wasted. Most of it: <b>{top[0].lower()}</b> ({top[1]:g} pcs).")
        else:
            self.waste_note.setText("Nothing wasted in the last 7 days. Great job!")

    def log_waste(self):
        dialog = ManualWasteLogDialog(self.db)
        dialog.current_user = self.current_user
        if dialog.exec():
            self.load_eod_data()
            self.load_loss_data()
            self.load_analytics_data()

    def _ask_waste_reason(self, prod_name, qty):
        """Small dialog: why was it wasted? Returns (waste_type, reason) or None if cancelled."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGridLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("Why was it wasted?")
        dlg.setModal(True)
        dlg.setStyleSheet("QDialog { background: white; } QLabel { color: #1F2937; }")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(24, 20, 24, 18); lay.setSpacing(12)
        t = QLabel(f"<b>{qty} pcs of {prod_name}</b><br>Why was it wasted?")
        t.setStyleSheet("font-size: 15px;")
        lay.addWidget(t)
        grid = QGridLayout(); grid.setSpacing(8)
        options = [("Not sold", "Market Spoilage"), ("Burnt", "Kitchen Waste"),
                   ("Dropped / Damaged", "Kitchen Waste"), ("Expired", "Expired")]
        picked = {}
        for i, (label, wtype) in enumerate(options):
            b = QPushButton(label)
            b.setFixedHeight(46)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("QPushButton { background: #F5ECE5; color: #693903; border: 1px solid #E8D5C4; border-radius: 10px; "
                            "font-size: 14px; font-weight: bold; } QPushButton:hover { background: #EBDCCF; }")
            b.clicked.connect(lambda _, l=label, w=wtype: (picked.update(choice=(w, l)), dlg.accept()))
            grid.addWidget(b, i // 2, i % 2)
        lay.addLayout(grid)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(38)
        cancel.setStyleSheet("QPushButton { background: white; color: #64748B; border: 1px solid #E2E8F0; border-radius: 8px; }")
        cancel.clicked.connect(dlg.reject)
        lay.addWidget(cancel)
        dlg.setFixedWidth(400)
        return picked.get("choice") if dlg.exec() else None


# ==========================================
# MANUAL WASTE LOG DIALOG
# ==========================================
class ManualWasteLogDialog(QDialog):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self._drag_pos = None
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QDialog { background-color: transparent; }")
        self.setFixedWidth(520)
        self.init_ui()

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

    def init_ui(self):
        import os as _os
        ARROW_DOWN_PATH = _os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
        ARROW_UP_PATH   = _os.path.join(IMAGES_DIR, "arrowup.png").replace("\\", "/")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)

        from bakesync.modules.inventory import DIALOG_WRAPPER_STYLE, LABEL_STYLE as INV_LABEL_STYLE, _close_btn, _make_spin_container
        from PyQt6.QtGui import QPalette, QColor as _QColor

        wrapper = QFrame()
        wrapper.setStyleSheet(DIALOG_WRAPPER_STYLE)
        pal = wrapper.palette()
        pal.setColor(QPalette.ColorRole.Window,     _QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.WindowText, _QColor("#0F172A"))
        pal.setColor(QPalette.ColorRole.Base,       _QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.Text,       _QColor("#0F172A"))
        wrapper.setPalette(pal)
        wrapper.setAutoFillBackground(True)
        outer_layout.addWidget(wrapper)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(32, 25, 32, 38)
        layout.setSpacing(16)

        # --- TITLE ROW ---
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 15)
        title_lbl = QLabel("Manual Waste Entry")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: normal; color: #0F172A;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        cb = _close_btn(); cb.clicked.connect(self.reject)
        title_row.addWidget(cb)
        layout.addLayout(title_row)

        FIELD_STYLE_COMBO = f"""
            QComboBox {{ border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px;
                         font-size: 13px; color: #0F172A; background-color: white; }}
            QComboBox:focus {{ border: 1px solid #693903; }}
            QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
                                    width: 28px; border: none; }}
            QComboBox::down-arrow {{ image: url("{ARROW_DOWN_PATH}"); width: 12px; height: 12px; }}
            QComboBox QAbstractItemView {{ background-color: white; border: 1px solid #948778;
                                           outline: none; padding: 0px; }}
            QComboBox QAbstractItemView::item {{ padding: 6px 12px; color: #0F172A; border: none; }}
            QComboBox QAbstractItemView::item:hover {{ background-color: #6B3F27; color: white; }}
            QComboBox QAbstractItemView::item:selected {{ background-color: #6B3F27; color: white; }}
        """

        FIELD_STYLE_INPUT = """
            border: 1px solid #D1D5DB; border-radius: 4px; padding: 8px 12px;
            font-size: 13px; color: #0F172A; background-color: white;
        """

        def make_field(label_text, widget):
            col = QVBoxLayout(); col.setSpacing(6)
            lbl = QLabel(label_text); lbl.setStyleSheet(INV_LABEL_STYLE)
            col.addWidget(lbl); col.addWidget(widget)
            return col

        # --- PRODUCT COMBO ---
        self.product_combo = QComboBox()
        self.product_combo.setFixedHeight(38)
        self.product_combo.setStyleSheet(FIELD_STYLE_COMBO)
        products = self.db.fetch_all("SELECT id, name, stock_qty FROM products WHERE is_archived = 0")
        self.product_combo.addItems([f"{p['name']} (Stock: {p['stock_qty'] or 0})" for p in products])
        for i, p in enumerate(products):
            self.product_combo.setItemData(i, p['id'], Qt.ItemDataRole.UserRole)
        layout.addLayout(make_field("Select Product", self.product_combo))

        # --- WASTE TYPE ---
        lbl_type = QLabel("Waste Type"); lbl_type.setStyleSheet(INV_LABEL_STYLE)
        layout.addWidget(lbl_type)

        self.waste_group = QButtonGroup()
        waste_row = QHBoxLayout(); waste_row.setSpacing(10)

        TYPE_DEFS = [
            ("Market Spoilage", 0, "#FFF3E0", "#E65100", "#FFE0B2"),
            ("Kitchen Waste",   1, "#FFF8F8", "#B71C1C", "#FFCDD2"),
            ("Expired Retail",  2, "#F3E8FF", "#4527A0", "#D1C4E9"),
        ]

        for label, bid, bg, fg, border in TYPE_DEFS:
            f = QFrame()
            f.setFixedHeight(46)
            f.setCursor(Qt.CursorShape.PointingHandCursor)
            f.setStyleSheet(f"QFrame {{ border: 1px solid {border}; border-radius: 6px; background: {bg}; }}")
            h = QHBoxLayout(f)
            h.setContentsMargins(10, 0, 10, 0)
            r = QRadioButton(label)
            r.setStyleSheet(f"""
                QRadioButton {{ font-size: 12px; font-weight: bold; color: {fg};
                                border: none; background: transparent; spacing: 8px; }}
                QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 7px;
                                           border: 2px solid {border}; background: white; }}
                QRadioButton::indicator:checked {{ border: 2px solid {fg}; background: {fg}; }}
            """)
            self.waste_group.addButton(r, bid)
            h.addWidget(r)
            waste_row.addWidget(f)
            if bid == 0:
                r.setChecked(True)

        layout.addLayout(waste_row)

        # --- QUANTITY ---
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setFixedHeight(38)
        self.qty_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.qty_spin.setStyleSheet(
            "border: none; padding: 8px 12px; font-size: 13px; color: #0F172A; background: transparent;"
        )
        qty_col = QVBoxLayout(); qty_col.setSpacing(6)
        qty_lbl = QLabel("Quantity to Waste (Will be deducted from Stock)")
        qty_lbl.setStyleSheet(INV_LABEL_STYLE)
        qty_col.addWidget(qty_lbl)
        qty_col.addWidget(_make_spin_container(self.qty_spin, ARROW_DOWN_PATH, ARROW_UP_PATH))
        layout.addLayout(qty_col)

        # --- REASON ---
        self.reason_input = QTextEdit()
        self.reason_input.setFixedHeight(75)
        self.reason_input.setStyleSheet(f"QTextEdit {{ {FIELD_STYLE_INPUT} }}")
        layout.addLayout(make_field("Reason / Remarks", self.reason_input))

        layout.addSpacing(8)

        # --- BUTTONS ROW ---
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(42)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton { background: white; color: #242424; padding: 8px 25px;
                          border: 1px solid #D1D5DB; border-radius: 4px; font-size: 14px; }
            QPushButton:hover { background: #F3F4F6; }
        """)
        cancel_btn.clicked.connect(self.reject)

        submit_btn = QPushButton("Deduct & Log Waste")
        submit_btn.setFixedHeight(42)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton { background-color: #693903; color: white; border: 1px solid #693903;
                          border-radius: 4px; font-size: 14px; font-weight: normal;
                          padding: 8px 30px; }
            QPushButton:hover { background-color: #452803; }
        """)
        submit_btn.clicked.connect(self.submit_waste)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(submit_btn)
        layout.addLayout(btn_row)

    def submit_waste(self):
        prod_id = self.product_combo.currentData(Qt.ItemDataRole.UserRole)
        bid     = self.waste_group.checkedId()
        type_map = {0: "Market Spoilage", 1: "Kitchen Waste", 2: "Expired Retail"}
        w_type  = type_map.get(bid, "Market Spoilage")
        qty     = self.qty_spin.value()
        reason  = self.reason_input.toPlainText().strip()

        self.db.execute_query(
            "INSERT INTO waste_logs (product_id, waste_type, quantity, reason) VALUES (?, ?, ?, ?)",
            (prod_id, w_type, qty, reason)
        )
        self.db.execute_query(
            "UPDATE products SET stock_qty = MAX(0, COALESCE(stock_qty,0) - ?) WHERE id = ?",
            (qty, prod_id)
        )

        batches = self.db.fetch_all(
            "SELECT id, quantity_remaining FROM product_batches WHERE product_id = ? AND quantity_remaining > 0 ORDER BY expiry_date ASC",
            (prod_id,)
        )
        rem = qty
        for b in batches:
            if rem <= 0: break
            deduct = min(b['quantity_remaining'], rem)
            self.db.execute_query(
                "UPDATE product_batches SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                (deduct, b['id'])
            )
            rem -= deduct

        log_activity(self.db, getattr(self, "current_user", "") or "Unknown", "waste recorded", "waste",
                     f"{qty} x {self.product_combo.currentText()} - {w_type}" + (f" ({reason})" if reason else ""))
        self.accept()
        BakeSyncAlert.show_success(
            self.parent(),
            title="Waste Logged",
            message="Waste entry has been successfully logged and deducted from inventory.",
            details={
                "Waste Type": w_type,
                "Quantity": f"{qty} pcs",
                "Status": "Deducted from inventory"
            }
        )
