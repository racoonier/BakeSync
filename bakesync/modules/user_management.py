from bakesync.paths import IMAGES_DIR
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QTabWidget, QLineEdit, 
                             QComboBox, QDialog, QMessageBox, QMenu, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QCursor, QBrush, QIcon, QPixmap
from PyQt6.QtCore import QByteArray
from datetime import datetime
from bakesync.auth.admin_register import AdminRegisterDialog
from bakesync.core.auth_utils import hash_password
from bakesync.core.audit import log_activity
from bakesync.widgets.ui import (THEME as UI, card as ui_card, icon_label as ui_icon_label, svg_icon as ui_svg_icon,
                               initials as ui_initials, button as ui_button, title_row as title_row_ui, PasswordFields)
from PyQt6.QtWidgets import QGridLayout
import traceback

class SVGIcons:
    """Minimalist Vector Icons"""

    @staticmethod
    def clock(color="#F59E0B"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'''
   
    @staticmethod
    def get_icon(svg_string, size=20):
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(svg_string.encode('utf-8')), "SVG")
        return QIcon(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    @staticmethod
    def users(color="#64748B"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'''

    @staticmethod
    def user_plus(color="#FFFFFF"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>'''

    @staticmethod
    def archive(color="#EF4444"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>'''
    
    @staticmethod
    def check(color="#10B981"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'''

    @staticmethod
    def search(color="#94A3B8"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'''

    @staticmethod
    def eye(color="#3B82F6"): 
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>'''

    @staticmethod
    def more_vertical(color="#64748B"): 
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>'''

class UserManagementWidget(QWidget):
    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.current_user = current_user or "Administrator"
        self._ensure_user_tables()
        self.init_ui()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(30000)

    def _ensure_user_tables(self):
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS system_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, role_name TEXT UNIQUE,
                    description TEXT, access_level TEXT, permissions TEXT
                )
            """)
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN full_name TEXT")
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'Active'")
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN is_archived INTEGER DEFAULT 0")
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN email TEXT") 
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN phone TEXT") 
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT CURRENT_DATE") 
            except: pass
            try: self.db.execute_query("ALTER TABLE users ADD COLUMN admin_pin TEXT")
            except: pass
        except Exception as e:
            pass

    def init_ui(self):
        self.colors = {
            "bg": "#FFFFFF",           
            "text_dark": "#0F172A",    
            "text_mid": "#64748B",     
            "border": "#E2E8F0",       
            "primary": "#6B3F27",      
            "row_alt": "#F8FAFC",      
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "info": "#3B82F6"
        }

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(self.colors["bg"]))
        self.setPalette(palette)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 20)
        main_layout.setSpacing(15)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        kpi_brown = "#5C2D0E" 
        self.kpi_total = self.create_mini_kpi(SVGIcons.users("#FFFFFF"), "Total", "0", "#FFFFFF", kpi_brown)
        self.kpi_active = self.create_mini_kpi(SVGIcons.check("#FFFFFF"), "Active", "0", "#FFFFFF", kpi_brown)
        self.kpi_archived = self.create_mini_kpi(SVGIcons.archive("#FFFFFF"), "Archived", "0", "#FFFFFF", kpi_brown)
        self.kpi_pending = self.create_mini_kpi(SVGIcons.clock("#FFFFFF"), "Pending", "0", "#FFFFFF", kpi_brown)

        toolbar_layout.addWidget(self.kpi_total)
        toolbar_layout.addWidget(self.kpi_active)
        toolbar_layout.addWidget(self.kpi_archived)
        toolbar_layout.addWidget(self.kpi_pending)
        toolbar_layout.addStretch()

        self.role_filter = QComboBox()
        self.role_filter.setFixedWidth(160)
        self.role_filter.setFixedHeight(38)
        import os
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _arrow_path = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")

        self.role_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: {self.colors['row_alt']};
                color: {self.colors['text_dark']};
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: url("{_arrow_path}");
                width: 14px;
                height: 14px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid {self.colors['border']};
                border-radius: 6px;
                padding: 4px;
                selection-background-color: {self.colors['row_alt']};
                selection-color: {self.colors['primary']};
                font-size: 13px;
                color: {self.colors['text_dark']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {self.colors['row_alt']};
                color: {self.colors['primary']};
            }}
        """)
        self.role_filter.addItem("All Roles")
        self.populate_role_filter()
        self.role_filter.currentTextChanged.connect(self.load_directory)
        toolbar_layout.addWidget(self.role_filter)

        search_container = QFrame()
        search_container.setStyleSheet(f"background-color: {self.colors['row_alt']}; border: 1px solid {self.colors['border']}; border-radius: 6px;")
        search_container.setFixedWidth(240)
        search_container.setFixedHeight(38)
        sl = QHBoxLayout(search_container)
        sl.setContentsMargins(10, 0, 10, 0)
        
        s_icon = QLabel()
        s_icon.setPixmap(SVGIcons.get_icon(SVGIcons.search(), 16).pixmap(16, 16))
        s_icon.setStyleSheet("border: none; background: transparent;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name or user...")
        self.search_input.setStyleSheet("border: none; background: transparent; font-size: 13px;")
        self.search_input.textChanged.connect(self.load_directory)
        sl.addWidget(s_icon)
        sl.addWidget(self.search_input)
        toolbar_layout.addWidget(search_container)

        btn_add = QPushButton(" Add Admin")
        btn_add.setIcon(SVGIcons.get_icon(SVGIcons.user_plus()))
        btn_add.setFixedHeight(38)
        btn_add.setStyleSheet(f"QPushButton {{ background-color: {self.colors['primary']}; color: white; border: none; border-radius: 6px; font-weight: bold; padding: 0 20px; font-size: 13px; }} QPushButton:hover {{ background-color: #5a3420; }}")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.open_add_admin)
        toolbar_layout.addWidget(btn_add)

        main_layout.addLayout(toolbar_layout)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; border-top: 1px solid {self.colors['border']}; background: white; }}
            QTabBar::tab {{ background: transparent; color: {self.colors['text_mid']}; font-size: 13px; padding: 10px 16px; margin-right: 15px; border: none; border-bottom: 2px solid transparent; }}
            QTabBar::tab:selected {{ color: {self.colors['primary']}; border-bottom: 2px solid {self.colors['primary']}; font-weight: bold; }}
            QTabBar::tab:hover:!selected {{ color: {self.colors['text_dark']}; }}
        """)

        self.tab_directory = QWidget(); self.setup_directory_tab()

        # ---> BAGONG DAGDAG: Pending Tab <---
        self.tab_pending = QWidget(); self.setup_pending_tab()

        self.tab_roles = QWidget(); self.setup_roles_tab()
        self.tab_archived = QWidget(); self.setup_archived_tab()

        self.tabs.addTab(self.tab_directory, "Directory")
        self.tabs.addTab(self.tab_pending, "Pending Approvals")
        self.tabs.addTab(self.tab_roles, "Roles && Permissions")
        self.tabs.addTab(self.tab_archived, "Archived")

        self.tabs.currentChanged.connect(self.refresh_all_data)
        main_layout.addWidget(self.tabs)
        self.refresh_all_data()

    def create_mini_kpi(self, icon_svg, label, value, val_color, bg_color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border-radius: 8px; }}")
        card.setFixedHeight(38)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(SVGIcons.get_icon(icon_svg, 16).pixmap(16, 16))
        icon_lbl.setStyleSheet("border: none;")
        lbl_text = QLabel(label)
        lbl_text.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
        val_lbl = QLabel(value)
        val_lbl.setObjectName("val")
        val_lbl.setStyleSheet(f"color: {val_color}; font-weight: bold; font-size: 16px;")
        
        lay.addWidget(icon_lbl)
        lay.addWidget(lbl_text)
        lay.addWidget(val_lbl)
        return card

    def populate_role_filter(self):
        try:
            roles = self.db.fetch_all("SELECT role_name FROM system_roles")
            for r in roles: self.role_filter.addItem(r['role_name'])
        except: pass

    def update_kpi(self):
        try:
            total = self.db.fetch_one("SELECT COUNT(*) as c FROM users WHERE is_archived = 0")['c']
            active = self.db.fetch_one("SELECT COUNT(*) as c FROM users WHERE is_archived = 0 AND status = 'Active'")['c']
            archived = self.db.fetch_one("SELECT COUNT(*) as c FROM users WHERE is_archived = 1")['c']
            pending = self.db.fetch_one("SELECT COUNT(*) as c FROM users WHERE status = 'Pending'")['c']
            self.kpi_total.findChild(QLabel, "val").setText(str(total))
            self.kpi_active.findChild(QLabel, "val").setText(str(active))
            self.kpi_archived.findChild(QLabel, "val").setText(str(archived))
            self.kpi_pending.findChild(QLabel, "val").setText(str(pending))
        except: pass

    def refresh_all_data(self):
        self.update_kpi()
        self.load_directory()
        self.load_pending()
        self.load_roles()
        self.load_archived()

    def setup_directory_tab(self):
        layout = QVBoxLayout(self.tab_directory)
        layout.setContentsMargins(0, 15, 0, 0) 
        self.dir_table = self.create_styled_table(["Account ID", "Username", "Full Name", "Role", "Status", "Actions"])
        self.dir_table.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dir_table.setMouseTracking(True)
        self.dir_table.cellClicked.connect(self._open_row_summary)
        hint = QLabel("Click any row to see the account summary.")
        hint.setStyleSheet(f"color: {self.colors['text_mid']}; font-size: 12px; padding: 0 0 6px 2px;")
        layout.addWidget(hint)
        layout.addWidget(self.dir_table)

    def load_directory(self):
        try:
            query = "SELECT id, username, full_name, role, status, email, phone, created_at FROM users WHERE is_archived = 0 AND status != 'Pending'"
            params = []
            s = self.search_input.text().strip()
            role_f = self.role_filter.currentText()

            if s:
                query += " AND (username LIKE ? OR full_name LIKE ?)"
                params += [f"%{s}%", f"%{s}%"]
            if role_f != "All Roles":
                query += " AND role = ?"
                params.append(role_f)

            users = self.db.fetch_all(query + " ORDER BY username", params)
            self.dir_table.setRowCount(len(users) if users else 0)
            if not users: return
            
            for row, u in enumerate(users):
                acc_item = QTableWidgetItem(f"ACC-{u['id']:03d}")
                acc_item.setData(Qt.ItemDataRole.UserRole, u['id'])
                self.dir_table.setItem(row, 0, acc_item)
                self.dir_table.setItem(row, 1, QTableWidgetItem(u['username']))
                self.dir_table.setItem(row, 2, QTableWidgetItem(u['full_name'] or "---"))
                self.dir_table.setItem(row, 3, QTableWidgetItem(u['role']))
                
                status_item = QTableWidgetItem(u['status'] + ("  (you)" if u['username'] == self.current_user else ""))
                color = self.colors['success'] if u['status'] == 'Active' else self.colors['warning']
                status_item.setForeground(QBrush(QColor(color)))
                self.dir_table.setItem(row, 4, status_item)
                
                action_w = QWidget()
                action_w.setStyleSheet("background: transparent;")
                hl = QHBoxLayout(action_w)
                hl.setContentsMargins(8, 0, 0, 0)
                hl.setSpacing(5)
                hl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                def create_action_btn(icon_svg, tooltip):
                    btn = QPushButton()
                    btn.setIcon(SVGIcons.get_icon(icon_svg, 18))
                    btn.setToolTip(tooltip)
                    btn.setFixedSize(30, 30)
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: transparent;
                            border: 1px solid {self.colors['border']};
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {self.colors['row_alt']};
                            border-color: {self.colors['text_mid']};
                        }}
                    """)
                    return btn

                btn_view = create_action_btn(SVGIcons.eye(self.colors['info']), "View Summary")
                btn_view.clicked.connect(lambda ch, uid=u['id']: self.open_view_summary(uid))
                
                btn_more = create_action_btn(SVGIcons.more_vertical(self.colors['text_dark']), "Options")
                btn_more.clicked.connect(lambda ch, btn=btn_more, uid=u['id'], un=u['username']: self.show_action_menu(btn, uid, un))

                hl.addWidget(btn_view)
                hl.addWidget(btn_more)
                self.dir_table.setCellWidget(row, 5, action_w)
        except Exception as e: print(f"Load Error: {e}")

    # ── PENDING APPROVALS TAB ──────────────────────────────────────────────

    def setup_pending_tab(self):
        layout = QVBoxLayout(self.tab_pending)
        layout.setContentsMargins(0, 15, 0, 0)
        self.pending_table = self.create_styled_table(["Date Requested", "Username", "Email", "Phone", "Actions"])
        layout.addWidget(self.pending_table)

    def load_pending(self):
        try:
            # Kunin lang ang mga 'Pending' at hindi naka-archive
            users = self.db.fetch_all("SELECT id, username, email, phone, created_at FROM users WHERE status = 'Pending' AND is_archived = 0")
            self.pending_table.setRowCount(len(users) if users else 0)
            
            if not users: return
            
            for row, u in enumerate(users):
                self.pending_table.setItem(row, 0, QTableWidgetItem(str(u['created_at'])[:10]))
                self.pending_table.setItem(row, 1, QTableWidgetItem(u['username']))
                self.pending_table.setItem(row, 2, QTableWidgetItem(u['email'] or "---"))
                self.pending_table.setItem(row, 3, QTableWidgetItem(u['phone'] or "---"))
                
                # Approve & Reject Buttons
                action_w = QWidget()
                action_w.setStyleSheet("background: transparent;")
                hl = QHBoxLayout(action_w)
                hl.setContentsMargins(8, 0, 0, 0)
                hl.setSpacing(8)
                hl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                btn_approve = QPushButton(" Approve")
                btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_approve.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors['success']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 5px 10px;
                        font-weight: bold;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{ background-color: #059669; }}
                """)
                btn_approve.clicked.connect(lambda ch, uid=u['id'], un=u['username']: self.approve_account(uid, un))
                
                btn_reject = QPushButton(" Reject")
                btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_reject.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {self.colors['danger']};
                        border: 1px solid {self.colors['danger']};
                        border-radius: 8px;
                        padding: 5px 10px;
                        font-weight: bold;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{ background-color: #FEF2F2; }}
                """)
                btn_reject.clicked.connect(lambda ch, uid=u['id']: self.reject_account(uid))

                hl.addWidget(btn_approve)
                hl.addWidget(btn_reject)
                self.pending_table.setCellWidget(row, 4, action_w)
        except Exception as e: 
            print(f"Load Pending Error: {e}")

    def approve_account(self, uid, username):
        roles = []
        try:
            role_db = self.db.fetch_all("SELECT role_name FROM system_roles")
            roles = [r['role_name'] for r in role_db]
        except:
            roles = ["Cashier", "Baker", "Manager"]

        dlg = ApproveAccountDialog(username, roles, self)
        result = self._show_with_overlay(dlg)
        if result and dlg.selected_role:
            self.db.execute_query("UPDATE users SET status = 'Active', role = ? WHERE id = ?", (dlg.selected_role, uid))
            log_activity(self.db, self.current_user, "account approved", "account",
                         f"{username} approved as {dlg.selected_role}")
            self.refresh_all_data()

    def reject_account(self, uid):
        dlg = RejectConfirmDialog(self)
        if self._show_with_overlay(dlg):
            row = self.db.fetch_one("SELECT username FROM users WHERE id = ?", (uid,))
            self.db.execute_query("DELETE FROM users WHERE id = ?", (uid,))
            log_activity(self.db, self.current_user, "account rejected", "account",
                         f"Sign-up request from {row['username'] if row else uid} was rejected")
            self.refresh_all_data()

    def show_action_menu(self, btn_widget, uid, username):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: white; border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 5px; }}
            QMenu::item {{ padding: 8px 20px; border-radius: 4px; color: {self.colors['text_dark']}; }}
            QMenu::item:selected {{ background-color: {self.colors['row_alt']}; color: {self.colors['primary']}; }}
        """)
        edit_action = menu.addAction("Edit Details")
        reset_action = menu.addAction("Reset Password")
        menu.addSeparator()
        archive_action = menu.addAction("Archive Account")

        pos = btn_widget.mapToGlobal(btn_widget.rect().bottomLeft())
        selected = menu.exec(pos)

        if selected == edit_action: self.open_edit(uid)
        elif selected == reset_action: self.open_reset(uid, username)
        elif selected == archive_action: self.archive_account(uid)

    def _open_row_summary(self, row, col):
        item = self.dir_table.item(row, 0)
        if item and item.data(Qt.ItemDataRole.UserRole) is not None:
            self.open_view_summary(item.data(Qt.ItemDataRole.UserRole))

    def _username(self, uid):
        r = self.db.fetch_one("SELECT username FROM users WHERE id = ?", (uid,))
        return r["username"] if r else f"#{uid}"

    def setup_roles_tab(self):
        main_roles_layout = QHBoxLayout(self.tab_roles)
        
        # Left Side: Table
        self.roles_table = self.create_styled_table(["Role Name", "Access Level", "Permissions", "Description"])
        main_roles_layout.addWidget(self.roles_table, 2)
        
        # Right Side: SVG Vector Panel
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PyQt6.QtSvgWidgets import QSvgWidget
        roles_svg_data = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 280">
        <rect x="80" y="10" width="140" height="50" rx="8" fill="#5C2D0E" opacity="0.9"/>
        <text x="150" y="40" text-anchor="middle" fill="white" font-size="13" font-weight="bold" font-family="Segoe UI">Administrator</text>
        <line x1="150" y1="60" x2="150" y2="95" stroke="#888" stroke-width="1.5"/>
        <rect x="80" y="95" width="140" height="50" rx="8" fill="#8B6347" opacity="0.85"/>
        <text x="150" y="125" text-anchor="middle" fill="white" font-size="13" font-weight="bold" font-family="Segoe UI">Manager</text>
        <line x1="110" y1="145" x2="60" y2="180" stroke="#888" stroke-width="1.5"/>
        <line x1="190" y1="145" x2="240" y2="180" stroke="#888" stroke-width="1.5"/>
        <rect x="10" y="180" width="120" height="50" rx="8" fill="#6B3F27" opacity="0.75"/>
        <text x="70" y="210" text-anchor="middle" fill="white" font-size="12" font-family="Segoe UI">Cashier</text>
        <rect x="170" y="180" width="120" height="50" rx="8" fill="#6B3F27" opacity="0.75"/>
        <text x="230" y="210" text-anchor="middle" fill="white" font-size="12" font-family="Segoe UI">Baker</text>
        </svg>'''
        svg_icon = QSvgWidget()
        svg_icon.load(QByteArray(roles_svg_data))
        svg_icon.setFixedSize(260, 240)
        right_panel.addWidget(svg_icon)
        
        # Role Legend labels base sa image
        right_panel.addWidget(QLabel("● Admin (Full access)"))
        right_panel.addWidget(QLabel("● Manager (High access)"))
        right_panel.addWidget(QLabel("● Cashier"))
        
        main_roles_layout.addLayout(right_panel, 1)

    def load_roles(self):
        try:
            roles = self.db.fetch_all("SELECT * FROM system_roles")
            self.roles_table.setRowCount(len(roles) if roles else 0)
            if not roles: return
            for row, r in enumerate(roles):
                r_dict = dict(r) if hasattr(r, 'keys') else { 'role_name': r[1], 'description': r[2], 'access_level': r[3], 'permissions': r[4] }
                self.roles_table.setItem(row, 0, QTableWidgetItem(r_dict.get('role_name', '')))
                self.roles_table.setItem(row, 1, QTableWidgetItem(r_dict.get('access_level', '')))
                self.roles_table.setItem(row, 2, QTableWidgetItem(r_dict.get('permissions', '---')))
                self.roles_table.setItem(row, 3, QTableWidgetItem(r_dict.get('description', '')))
        except: pass

    def setup_archived_tab(self):
        layout = QVBoxLayout(self.tab_archived); layout.setContentsMargins(0, 15, 0, 0)
        self.archived_table = self.create_styled_table(["Account ID", "Username", "Role", "Actions"])
        layout.addWidget(self.archived_table)

    def load_archived(self):
        try:
            users = self.db.fetch_all("SELECT id, username, role FROM users WHERE is_archived = 1")
            self.archived_table.setRowCount(len(users) if users else 0)
            if not users: return
            for row, u in enumerate(users):
                self.archived_table.setItem(row, 0, QTableWidgetItem(f"ACC-{u['id']:03d}"))
                self.archived_table.setItem(row, 1, QTableWidgetItem(u['username']))
                self.archived_table.setItem(row, 2, QTableWidgetItem(u['role']))
                
                aw = QWidget()
                aw.setStyleSheet("background: transparent;")
                hl = QHBoxLayout(aw)
                hl.setContentsMargins(8, 0, 0, 0)
                hl.setSpacing(0)

                btn_rest = QPushButton("Restore")
                btn_rest.setFixedHeight(30)
                btn_rest.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_rest.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {self.colors['success']};
                        border: 1px solid {self.colors['success']};
                        border-radius: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 0 12px;
                    }}
                    QPushButton:hover {{
                        background-color: #F0FDF4;
                    }}
                """)
                btn_rest.clicked.connect(lambda ch, uid=u['id']: self.restore(uid))
                hl.addWidget(btn_rest)
                hl.addStretch()
                self.archived_table.setCellWidget(row, 3, aw)
        except: pass

    def archive_account(self, uid):
        name = self._username(uid)
        if name == self.current_user:
            from bakesync.widgets.custom_alerts import BakeSyncAlert
            BakeSyncAlert.show_warning(self, "Not Allowed", "You cannot archive your own account while you are signed in.")
            return
        dlg = ArchiveConfirmDialog(self)
        if self._show_with_overlay(dlg):
            self.db.execute_query("UPDATE users SET is_archived = 1, status = 'Archived' WHERE id = ?", (uid,))
            log_activity(self.db, self.current_user, "account archived", "account", f"{name} can no longer sign in")
            self.refresh_all_data()

    def restore(self, uid):
        dlg = RestoreConfirmDialog(self)
        if self._show_with_overlay(dlg):
            self.db.execute_query("UPDATE users SET is_archived = 0, status = 'Active' WHERE id = ?", (uid,))
            log_activity(self.db, self.current_user, "account restored", "account", f"{self._username(uid)} can sign in again")
            self.refresh_all_data()

    def create_styled_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if headers[-1] == "Actions":
            table.horizontalHeader().setSectionResizeMode(len(headers)-1, QHeaderView.ResizeMode.Fixed)
            col_width = 180 if len(headers) == 5 else 100
            table.setColumnWidth(len(headers)-1, col_width)
            
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True) 
        table.verticalHeader().setDefaultSectionSize(50) 
             
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: white; alternate-background-color: {self.colors['row_alt']}; border: none; font-size: 13px; color: {self.colors['text_dark']}; }}
            QHeaderView::section {{ background-color: white; color: {self.colors['text_mid']}; font-weight: bold; font-size: 12px; text-transform: uppercase; padding: 15px 10px; border: none; border-bottom: 2px solid {self.colors['border']}; }}
            QTableWidget::item {{ padding: 0px 10px; border: none; border-bottom: 1px solid {self.colors['row_alt']}; }}
            QTableWidget::item:selected {{ background-color: transparent; }}
            QScrollBar:vertical {{ background: {self.colors['row_alt']}; width: 6px; border-radius: 3px; margin: 0; border: none; }}
            QScrollBar::handle:vertical {{ background: #9A7B4F; border-radius: 3px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: #3A2318; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)
        return table
    
    def _show_with_overlay(self, dialog):
        overlay = QWidget(self.window())
        overlay.setStyleSheet("background: rgba(0, 0, 0, 0.45);")
        overlay.setGeometry(self.window().rect())
        overlay.show()
        overlay.raise_()
        result = dialog.exec()
        overlay.deleteLater()
        return result

    def open_view_summary(self, uid):
        dlg = ViewUserDialog(self.db, uid, self, current_user=self.current_user)
        self._show_with_overlay(dlg)
        if dlg.choice == "edit":
            self.open_edit(uid)
        elif dlg.choice == "reset":
            self.open_reset(uid, self._username(uid))
        elif dlg.choice == "archive":
            self.archive_account(uid)
    def open_add_admin(self):
        dlg = AdminRegisterDialog(db=self.db, parent=self)
        dlg.account_created.connect(lambda _: self.refresh_all_data())
        self._show_with_overlay(dlg)
    def open_edit(self, uid):
        before = self.db.fetch_one("SELECT full_name, email, phone, role FROM users WHERE id = ?", (uid,))
        if self._show_with_overlay(EditUserDialog(self.db, uid, self)):
            after = self.db.fetch_one("SELECT full_name, email, phone, role FROM users WHERE id = ?", (uid,))
            changes = [f"{k.replace('_', ' ')}: {before[k] or '-'} -> {after[k] or '-'}"
                       for k in ("full_name", "email", "phone", "role") if before and after and before[k] != after[k]]
            log_activity(self.db, self.current_user, "account edited", "account",
                         f"{self._username(uid)}: " + ("; ".join(changes) if changes else "no changes"))
            self.refresh_all_data()
    def open_reset(self, uid, username):
        if self._show_with_overlay(ResetPasswordDialog(self.db, uid, username, self)):
            log_activity(self.db, self.current_user, "password reset", "account",
                         f"Gave {username} a temporary password (must change at next sign-in)")


# ==========================================
# DIALOGS (Modals)
# ==========================================
class BaseDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._container = QFrame(self)
        self._container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 14px;
                border: none;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self._container.setGraphicsEffect(shadow)
        outer.addWidget(self._container)

        # All subclass widgets go into this layout
        self.layout = QVBoxLayout(self._container)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #0F172A; background: transparent; border: none;")
        self.layout.addWidget(lbl)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()

    def create_field(self, label_text, is_password=False):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("background: transparent; border: none; color: #0F172A;")
        self.layout.addWidget(lbl)
        inp = QLineEdit()
        if is_password: inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setStyleSheet("padding: 10px; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 13px; color: #0F172A; background: white;")
        self.layout.addWidget(inp)
        return inp


from PyQt6.QtWidgets import QGridLayout, QMessageBox
import re
from datetime import datetime

    
class EditUserDialog(BaseDialog):
    def __init__(self, db, uid, parent=None):
        super().__init__("Edit User Details", parent)
        self.db, self.uid = db, uid
        
        try:
            user_row = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (uid,))
            user = {}
            if user_row:
                try:
                    user = dict(user_row)
                except Exception:
                    cols = ['id', 'username', 'password', 'role', 'full_name', 'email', 'phone', 'status', 'is_archived', 'failed_attempts', 'created_at']
                    for i, val in enumerate(user_row):
                        if i < len(cols): user[cols[i]] = val
                    
            self.setFixedWidth(400)
            self.fn_input = self.create_field("Full Name:")
            self.fn_input.setText(user.get('full_name', ''))
            
            self.email_input = self.create_field("Email Address:")
            self.email_input.setText(user.get('email', ''))

            self.phone_input = self.create_field("Phone Number:")
            self.phone_input.setText(user.get('phone', ''))

            self.layout.addWidget(QLabel("System Role:"))
            self.role_combo = QComboBox()
            import os
            _script_dir = os.path.dirname(os.path.abspath(__file__))
            _arrow_path = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")
            self.role_combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 10px;
                    background-color: white;
                    color: #0F172A;
                    font-size: 13px;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 30px;
                }}
                QComboBox::down-arrow {{
                    image: url("{_arrow_path}");
                    width: 14px;
                    height: 14px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: white;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 4px;
                    selection-background-color: #F8FAFC;
                    selection-color: #6B3F27;
                    font-size: 13px;
                    color: #0F172A;
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 6px 12px;
                    border-radius: 4px;
                }}
                QComboBox QAbstractItemView::item:hover {{
                    background-color: #F8FAFC;
                    color: #6B3F27;
                }}
            """)
            try:
                for r in self.db.fetch_all("SELECT role_name FROM system_roles"): self.role_combo.addItem(r['role_name'])
                self.role_combo.setCurrentText(user.get('role', ''))
            except: pass
            self.layout.addWidget(self.role_combo)
            
        except Exception as e:
            err = QLabel(f"Error fetching data:\n{str(e)}")
            err.setStyleSheet("color: red;")
            self.layout.addWidget(err)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Update Info")
        btn_save.setFixedHeight(44)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #6B3F27;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a321f; }
        """)
        btn_save.clicked.connect(self.save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        self.layout.addLayout(btn_row)

    def save(self):
        try:
            fn = self.fn_input.text().strip()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()
            role = self.role_combo.currentText().strip()

            if not fn:
                self._show_error("Full name cannot be empty.")
                return
            if email and "@" not in email:
                self._show_error("Please enter a valid email address.")
                return

            self.db.execute_query(
                "UPDATE users SET full_name = ?, email = ?, phone = ?, role = ? WHERE id = ?",
                (fn, email, phone, role, self.uid)
            )
            self.accept()
        except Exception as e:
            self._show_error(f"Failed to update user:\n{str(e)}")

    def _show_error(self, msg):
        if not hasattr(self, '_err_lbl'):
            self._err_lbl = QLabel()
            self._err_lbl.setWordWrap(True)
            self._err_lbl.setStyleSheet("""
                QLabel {
                    color: #EF4444;
                    background: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
            """)
            self.layout.insertWidget(self.layout.count() - 1, self._err_lbl)
        self._err_lbl.setText(msg)
        self._err_lbl.show()

def _ui_dialog_shell(dlg, width):
    """Frameless white card with shadow; returns the card's layout."""
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
    dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dlg.setModal(True)
    dlg.setFixedWidth(width)
    outer = QVBoxLayout(dlg); outer.setContentsMargins(0, 0, 0, 0)
    c = ui_card(16, name="shell")
    sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
    c.setGraphicsEffect(sh)
    outer.addWidget(c)
    lay = QVBoxLayout(c); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
    return lay


def _ui_header(dlg, lay, title, icon):
    bar = QWidget(); bar.setStyleSheet("background: transparent;")
    h = QHBoxLayout(bar); h.setContentsMargins(24, 18, 16, 12); h.setSpacing(10)
    h.addWidget(ui_icon_label(icon, UI["brown"], 18, bg=UI["cream_dark"], box=34, radius=10))
    t = QLabel(title); t.setStyleSheet(f"color: {UI['text']}; font-size: 16px; font-weight: bold;")
    h.addWidget(t); h.addStretch()
    x = QPushButton(); x.setIcon(ui_svg_icon("x", UI["mid"], 18)); x.setFixedSize(34, 34)
    x.setCursor(Qt.CursorShape.PointingHandCursor); x.setToolTip("Close (Esc)")
    x.setStyleSheet(f"QPushButton {{ border: none; border-radius: 17px; background: transparent; }} QPushButton:hover {{ background: {UI['cream_dark']}; }}")
    x.clicked.connect(dlg.reject)
    h.addWidget(x)
    lay.addWidget(bar)
    line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background: {UI['line']};")
    lay.addWidget(line)


def _nice_ts(ts):
    try:
        d = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return str(ts)[:10] if ts else "—"
    day = "Today" if d.date() == datetime.now().date() else d.strftime("%b %d, %Y")
    return f"{day}, {d.strftime('%I:%M %p').lstrip('0')}"


class ViewUserDialog(QDialog):
    """Account details, opened by clicking a row. Footer buttons set self.choice
    to "edit", "reset" or "archive" so the page can open that next."""

    def __init__(self, db, uid, parent=None, current_user=""):
        super().__init__(parent)
        self.db, self.uid, self.choice = db, uid, None
        lay = _ui_dialog_shell(self, 580)
        _ui_header(self, lay, "Account details", "user")
        u = db.fetch_one("SELECT username, full_name, role, status, email, phone, created_at, locked_until, is_archived "
                         "FROM users WHERE id = ?", (uid,))
        body = QVBoxLayout(); body.setContentsMargins(24, 16, 24, 8); body.setSpacing(14)
        lay.addLayout(body)
        if not u:
            body.addWidget(QLabel("This account could not be found."))
            return
        u = dict(u)
        name = (u["full_name"] or "").strip() or u["username"]
        locked = False
        if u["locked_until"]:
            r = db.fetch_one("SELECT julianday(?) > julianday('now','localtime') AS l", (u["locked_until"],))
            locked = bool(r and r["l"])
        status = "Locked" if locked else (u["status"] or "Active")

        # who
        top = QHBoxLayout(); top.setSpacing(14)
        av = QLabel(ui_initials(name)); av.setFixedSize(56, 56); av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"background: {UI['brown']}; color: {UI['cream']}; border-radius: 28px; font-size: 19px; font-weight: bold;")
        top.addWidget(av)
        col = QVBoxLayout(); col.setSpacing(2)
        n = QLabel(name); n.setStyleSheet(f"color: {UI['text']}; font-size: 17px; font-weight: bold;")
        un = QLabel(f"@{u['username']}"); un.setStyleSheet(f"color: {UI['mid']}; font-size: 12px;")
        col.addWidget(n); col.addWidget(un)
        top.addLayout(col, 1)
        for text, fg, bg in ((u["role"] or "No role", UI["brown"], UI["cream_dark"]),
                             (status, UI["green"] if status == "Active" else UI["red"] if status in ("Locked", "Archived") else UI["amber"],
                              UI["green_bg"] if status == "Active" else UI["red_bg"] if status in ("Locked", "Archived") else UI["amber_bg"])):
            b = QLabel(text); b.setStyleSheet(f"color: {fg}; background: {bg}; border-radius: 11px; padding: 3px 12px; font-size: 12px; font-weight: 600;")
            top.addWidget(b, alignment=Qt.AlignmentFlag.AlignVCenter)
        body.addLayout(top)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; border-top: 1px solid {UI['line']}; }}
            QTabBar::tab {{ background: transparent; color: {UI['mid']}; padding: 8px 16px; font-size: 13px; border: none;
                            border-bottom: 2px solid transparent; }}
            QTabBar::tab:selected {{ color: {UI['brown_dark']}; border-bottom: 2px solid {UI['brown']}; font-weight: bold; }}""")

        # Details tab: label / value list
        det = QWidget(); dl = QVBoxLayout(det); dl.setContentsMargins(0, 10, 0, 0); dl.setSpacing(0)

        def one(sql, params=()):
            try:
                r = db.fetch_one(sql, params)
                return r[0] if r and r[0] is not None else 0
            except Exception:
                return 0
        last_in = one("SELECT MAX(created_at) FROM activity_log WHERE username = ? AND action = 'signed in'", (u["username"],))
        rows = [("Full name", name), ("Username", u["username"]), ("Role", u["role"] or "—"),
                ("Email", u["email"] or "Not added"), ("Phone", u["phone"] or "Not added"),
                ("Joined", _nice_ts(u["created_at"]).split(",")[0] if u["created_at"] else "—"),
                ("Last sign-in", _nice_ts(last_in) if last_in else "Never")]
        if locked:
            rows.append(("Locked until", _nice_ts(u["locked_until"])))
        for i, (k, v) in enumerate(rows):
            r = QWidget(); r.setStyleSheet(f"background: {'#FFFFFF' if i % 2 else UI['cream']}; border-radius: 6px;")
            h = QHBoxLayout(r); h.setContentsMargins(12, 7, 12, 7)
            kl = QLabel(k); kl.setFixedWidth(130); kl.setStyleSheet(f"color: {UI['mid']}; font-size: 13px;")
            vl = QLabel(str(v)); vl.setStyleSheet(f"color: {UI['muted'] if v in ('Not added', 'Never') else UI['text']}; font-size: 13px; font-weight: 600;")
            h.addWidget(kl); h.addWidget(vl, 1)
            dl.addWidget(r)
        dl.addSpacing(12)
        m, mi = title_row_ui("This month", info="Sales and voids made with this account at the POS this month. "
                                                "Wrong passwords are counted for the last 7 days.", size=12)
        dl.addWidget(m)
        stats = QHBoxLayout(); stats.setSpacing(8)
        for label, value, warn in (
                ("Sales", "₱{:,.0f}".format(one("SELECT COALESCE(SUM(amount),0) FROM sales WHERE cashier = ? AND COALESCE(is_voided,0) = 0 "
                                                "AND strftime('%Y-%m', created_at) = strftime('%Y-%m','now','localtime')", (u["username"],))), False),
                ("Voids", str(one("SELECT COUNT(*) FROM void_logs WHERE voided_by = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m','now','localtime')", (u["username"],))), None),
                ("Sign-ins", str(one("SELECT COUNT(*) FROM activity_log WHERE username = ? AND action = 'signed in' AND strftime('%Y-%m', created_at) = strftime('%Y-%m','now','localtime')", (u["username"],))), False),
                ("Wrong passwords", str(one("SELECT COUNT(*) FROM activity_log WHERE username = ? AND action IN ('sign-in failed','account locked') AND created_at >= datetime('now','localtime','-7 days')", (u["username"],))), None)):
            warn = warn if warn is not None else value != "0"
            box = QFrame(); box.setObjectName("sb")
            box.setStyleSheet(f"QFrame#sb {{ background: {UI['red_bg'] if warn else UI['cream']}; border-radius: 10px; }}")
            bl = QVBoxLayout(box); bl.setContentsMargins(12, 8, 12, 8); bl.setSpacing(0)
            v = QLabel(value); v.setStyleSheet(f"color: {UI['red'] if warn else UI['text']}; font-size: 17px; font-weight: bold;")
            t = QLabel(label); t.setStyleSheet(f"color: {UI['mid']}; font-size: 11px;")
            bl.addWidget(v); bl.addWidget(t)
            stats.addWidget(box)
        dl.addLayout(stats)
        dl.addStretch()
        tabs.addTab(det, "Details")

        # Activity tab
        act = QWidget(); al = QVBoxLayout(act); al.setContentsMargins(0, 10, 0, 0); al.setSpacing(6)
        recent = db.fetch_all("SELECT created_at, action, area, details FROM activity_log WHERE username = ? ORDER BY id DESC LIMIT 9",
                              (u["username"],))
        icons = {"signin": "login", "account": "user", "sale": "cart", "void": "ban", "stock": "box",
                 "waste": "trash", "price": "tag", "money": "wallet", "system": "settings"}
        if not recent:
            e = QLabel("Nothing recorded yet."); e.setStyleSheet(f"color: {UI['muted']}; font-size: 13px; padding: 8px;")
            al.addWidget(e)
        for r in recent:
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(4, 2, 4, 2); h.setSpacing(10)
            h.addWidget(ui_icon_label(icons.get(r["area"], "activity"), UI["brown"], 14, bg=UI["cream_dark"], box=28, radius=14))
            d = r["details"] or ""
            d = d if len(d) <= 60 else d[:57] + "..."
            t = QLabel(f"<b>{r['action'].capitalize()}</b>" + (f"  <span style='color:{UI['mid']}'>{d}</span>" if d else ""))
            t.setStyleSheet(f"color: {UI['text']}; font-size: 12px;")
            tm = QLabel(_nice_ts(r["created_at"])); tm.setStyleSheet(f"color: {UI['muted']}; font-size: 11px;")
            h.addWidget(t, 1); h.addWidget(tm)
            al.addWidget(w)
        al.addStretch()
        tabs.addTab(act, "Recent activity")
        tabs.setFixedHeight(420)
        body.addWidget(tabs)

        # footer
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background: {UI['line']};")
        lay.addWidget(line)
        foot = QHBoxLayout(); foot.setContentsMargins(24, 12, 24, 16); foot.setSpacing(8)
        if not u["is_archived"]:
            if u["username"] != current_user:
                b = ui_button("Archive", "danger", icon="trash", h=40); b.clicked.connect(lambda: self._pick("archive"))
                foot.addWidget(b)
            foot.addStretch()
            b = ui_button("Reset password", "secondary", icon="key", h=40); b.clicked.connect(lambda: self._pick("reset"))
            foot.addWidget(b)
            b = ui_button("Edit details", "primary", icon="edit", h=40); b.clicked.connect(lambda: self._pick("edit"))
            foot.addWidget(b)
        else:
            foot.addStretch()
            b = ui_button("Close", "primary", h=40); b.clicked.connect(self.reject)
            foot.addWidget(b)
        lay.addLayout(foot)

    def _pick(self, choice):
        self.choice = choice
        self.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)


class ResetPasswordDialog(QDialog):
    """Give someone a temporary password. A reminder comes first; the password is typed
    twice and must pass every rule before Reset is enabled."""

    def __init__(self, db, uid, username, parent=None):
        super().__init__(parent)
        self.db, self.uid, self.username = db, uid, username
        lay = _ui_dialog_shell(self, 470)
        _ui_header(self, lay, "Reset password", "key")
        body = QVBoxLayout(); body.setContentsMargins(24, 16, 24, 8); body.setSpacing(10)
        lay.addLayout(body)

        note = QFrame(); note.setObjectName("note")
        note.setStyleSheet(f"QFrame#note {{ background: {UI['amber_bg']}; border: 1px solid #F3D49B; border-radius: 10px; }}"
                           "QLabel { background: transparent; border: none; }")
        nl = QHBoxLayout(note); nl.setContentsMargins(12, 10, 12, 10); nl.setSpacing(10)
        nl.addWidget(ui_icon_label("alert", UI["amber"], 20), alignment=Qt.AlignmentFlag.AlignTop)
        nt = QLabel(f"<b>Before you continue</b><br>You are giving <b>{username}</b> a temporary password. "
                    "Tell it to them in person, not by chat. They will be asked to choose their own password "
                    "the next time they sign in.")
        nt.setWordWrap(True); nt.setStyleSheet(f"color: {UI['text']}; font-size: 12px;")
        nl.addWidget(nt, 1)
        body.addWidget(note)

        self.fields = PasswordFields(self, "Temporary password", "Type it again")
        self.pw_input = self.fields.new
        body.addWidget(self.fields)
        self.err = QLabel(""); self.err.setStyleSheet(f"color: {UI['red']}; font-size: 12px;"); self.err.hide()
        body.addWidget(self.err)

        foot = QHBoxLayout(); foot.setContentsMargins(24, 8, 24, 18); foot.setSpacing(10)
        cancel = ui_button("Cancel", "secondary", h=44); cancel.clicked.connect(self.reject)
        self.btn_save = ui_button("Reset password", "primary", icon="key", h=44)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save)
        self.fields.changed.connect(self.btn_save.setEnabled)
        self.fields.confirm.returnPressed.connect(self.save)
        foot.addWidget(cancel); foot.addWidget(self.btn_save, 2)
        lay.addLayout(foot)

    def save(self):
        if not self.fields.is_valid():
            self.err.setText("Please follow every rule above and type the same password twice.")
            self.err.show()
            return
        try:
            self.db.execute_query(
                "UPDATE users SET password = ?, failed_attempts = 0, locked_until = NULL, must_change_password = 1 WHERE id = ?",
                (hash_password(self.fields.password()), self.uid))
            self.accept()
        except Exception as e:
            self.err.setText(f"Could not reset the password: {e}")
            self.err.show()

class ArchiveConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(380, 240)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 14px;
                border: none;
            }
        """)
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        # Archive SVG icon — same vector as the archive button
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        archive_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6B3F27" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>'''
        icon_lbl.setPixmap(SVGIcons.get_icon(archive_svg, 40).pixmap(40, 40))
        layout.addWidget(icon_lbl)

        title = QLabel("Archive Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; background: transparent; border: none;")
        layout.addWidget(title)

        msg = QLabel("This account will be moved to the Archive.\nYou can restore it anytime.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(msg)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Yes, Archive")
        btn_confirm.setFixedHeight(40)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #6B3F27;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a321f; }
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)

class ApproveAccountDialog(QDialog):
    def __init__(self, username, roles, parent=None):
        super().__init__(parent)
        self.selected_role = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedWidth(400)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setStyleSheet("QFrame { background-color: white; border-radius: 14px; border: none; }")
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        check_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'''
        icon_lbl.setPixmap(SVGIcons.get_icon(check_svg, 40).pixmap(40, 40))
        layout.addWidget(icon_lbl)

        title = QLabel("Approve Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; background: transparent; border: none;")
        layout.addWidget(title)

        msg = QLabel(f"Assign a role for <b>{username}</b> to complete approval.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(msg)

        # Role ComboBox
        import os
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _arrow_path = os.path.join(IMAGES_DIR, "arrowdown.png").replace("\\", "/")

        self.role_combo = QComboBox()
        for r in roles:
            self.role_combo.addItem(r)
        self.role_combo.setFixedHeight(42)
        self.role_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 12px;
                background-color: #F8FAFC;
                color: #0F172A;
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{ image: url("{_arrow_path}"); width: 14px; height: 14px; }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #F8FAFC;
                selection-color: #6B3F27;
                font-size: 13px;
                color: #0F172A;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{ padding: 6px 12px; border-radius: 4px; }}
            QComboBox QAbstractItemView::item:hover {{ background-color: #F8FAFC; color: #6B3F27; }}
        """)
        layout.addWidget(self.role_combo)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Approve")
        btn_confirm.setFixedHeight(42)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_confirm.clicked.connect(self._confirm)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)

    def _confirm(self):
        self.selected_role = self.role_combo.currentText()
        self.accept()


class RejectConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedWidth(380)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setStyleSheet("QFrame { background-color: white; border-radius: 14px; border: none; }")
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        reject_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'''
        icon_lbl.setPixmap(SVGIcons.get_icon(reject_svg, 40).pixmap(40, 40))
        layout.addWidget(icon_lbl)

        title = QLabel("Reject Sign-up Request")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; background: transparent; border: none;")
        layout.addWidget(title)

        msg = QLabel("This request will be permanently deleted.\nThis action cannot be undone.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Yes, Reject")
        btn_confirm.setFixedHeight(42)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)

class RestoreConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedWidth(380)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setStyleSheet("QFrame { background-color: white; border-radius: 14px; border: none; }")
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        restore_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 .49-4.95"></path></svg>'''
        icon_lbl.setPixmap(SVGIcons.get_icon(restore_svg, 40).pixmap(40, 40))
        layout.addWidget(icon_lbl)

        title = QLabel("Restore Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; background: transparent; border: none;")
        layout.addWidget(title)

        msg = QLabel("This account will be restored and set back to Active.\nThe user will be able to log in again.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: #64748B; background: transparent; border: none;")
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; color: #64748B;
                border: 1px solid #E2E8F0; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Yes, Restore")
        btn_confirm.setFixedHeight(42)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)