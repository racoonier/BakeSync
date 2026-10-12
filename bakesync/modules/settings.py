from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QCursor, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QSvgWidget
import io

# I-import ang mga modules na ililipat natin dito
from bakesync.modules.financial import FinancialWidget
from bakesync.modules.reports import ReportsWidget
from bakesync.modules.user_management import UserManagementWidget
from bakesync.modules.audit_logs import SystemAuditLogsWidget
from bakesync.modules.backup import BackupRestoreWidget
from bakesync.widgets.store_hours import StoreHoursWidget, store_status, closing_time_today, fmt as fmt_time
import os
from datetime import date, datetime, timedelta
from bakesync.widgets.ui import svg_icon as _ui_icon, svg_pixmap as _ui_pix

class SVGIcons:
    """Collection of vector SVG icons for the Settings module"""
    
    @staticmethod
    def get_user_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-fill {{ fill: {color}; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-fill {{ fill: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <circle cx="32" cy="20" r="10" class="icon-fill"/>
            <path d="M 10 55 Q 10 40 32 40 Q 54 40 54 55" class="icon-fill"/>
        </svg>'''
        return svg
    
    @staticmethod
    def get_finance_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-chart {{ stroke: {color}; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
                    .icon-dot {{ fill: {color}; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-chart {{ stroke: #E8D5C4; }}
                        .icon-dot {{ fill: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <path d="M 12 48 L 20 32 L 28 38 L 36 20 L 44 40 L 52 28 L 58 44" class="icon-chart" stroke-width="2.5"/>
            <circle cx="20" cy="32" r="2.5" class="icon-dot"/>
            <circle cx="28" cy="38" r="2.5" class="icon-dot"/>
            <circle cx="36" cy="20" r="2.5" class="icon-dot"/>
            <circle cx="44" cy="40" r="2.5" class="icon-dot"/>
            <circle cx="52" cy="28" r="2.5" class="icon-dot"/>
            <line x1="10" y1="52" x2="54" y2="52" class="icon-chart" stroke-width="2"/>
        </svg>'''
        return svg
    
    @staticmethod
    def get_analytics_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-bar {{ fill: {color}; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-bar {{ fill: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <rect x="12" y="32" width="10" height="18" rx="2" class="icon-bar"/>
            <rect x="28" y="20" width="10" height="30" rx="2" class="icon-bar"/>
            <rect x="44" y="26" width="10" height="24" rx="2" class="icon-bar"/>
            <line x1="10" y1="52" x2="56" y2="52" stroke="{color}" stroke-width="2"/>
        </svg>'''
        return svg
    
    @staticmethod
    def get_audit_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-audit-stroke {{ stroke: {color}; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-audit-stroke {{ stroke: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <rect x="12" y="10" width="40" height="44" rx="3" class="icon-audit-stroke" stroke-width="2"/>
            <line x1="20" y1="22" x2="44" y2="22" class="icon-audit-stroke" stroke-width="2"/>
            <line x1="20" y1="32" x2="44" y2="32" class="icon-audit-stroke" stroke-width="1.5"/>
            <line x1="20" y1="40" x2="44" y2="40" class="icon-audit-stroke" stroke-width="1.5"/>
            <line x1="20" y1="48" x2="44" y2="48" class="icon-audit-stroke" stroke-width="1.5"/>
            <path d="M 16 16 L 14 18 L 18 22" class="icon-audit-stroke" stroke-width="1.5"/>
        </svg>'''
        return svg
    
    # Idagdag ito bago matapos ang SVGIcons class
    @staticmethod
    def get_audit_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-fill {{ fill: {color}; }}
                    .icon-stroke {{ stroke: {color}; stroke-width: 4; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-fill {{ fill: #E8D5C4; }}
                        .icon-stroke {{ stroke: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <path d="M42 10H22c-2.2 0-4 1.8-4 4v36c0 2.2 1.8 4 4 4h20c2.2 0 4-1.8 4-4V14c0-2.2-1.8-4-4-4z" class="icon-stroke"/>
            <line x1="24" y1="22" x2="40" y2="22" class="icon-stroke"/>
            <line x1="24" y1="32" x2="40" y2="32" class="icon-stroke"/>
            <line x1="24" y1="42" x2="32" y2="42" class="icon-stroke"/>
        </svg>'''
        return svg
    
    @staticmethod
    def get_clock_icon(color="#6B3F27"):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="22" stroke="{color}" stroke-width="4" fill="none"/>
            <path d="M32 18v15l10 6" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''

    @staticmethod
    def get_backup_icon(color="#6B3F27"):
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <defs>
                <style>
                    .icon-stroke {{ stroke: {color}; stroke-width: 4; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
                    @media (prefers-color-scheme: dark) {{
                        .icon-stroke {{ stroke: #E8D5C4; }}
                    }}
                </style>
            </defs>
            <ellipse cx="32" cy="14" rx="18" ry="6" class="icon-stroke"/>
            <path d="M14 14v12c0 3.3 8 6 18 6s18-2.7 18-6V14" class="icon-stroke"/>
            <path d="M14 26v12c0 3.3 8 6 18 6" class="icon-stroke"/>
            <path d="M44 40v14M37 47l7 7 7-7" class="icon-stroke"/>
        </svg>'''
        return svg

    @staticmethod
    def create_svg_widget(svg_string, size=40):
        """Create a QLabel with SVG Pixmap (Consistent with other modules)"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray, Qt
        
        pixmap = QPixmap()
        # I-load ang SVG string as QByteArray
        pixmap.loadFromData(QByteArray(svg_string.encode('utf-8')), "SVG")
        
        # I-scale sa tamang size para malinaw (Anti-aliased)
        scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        label = QLabel()
        label.setPixmap(scaled_pixmap)
        label.setFixedSize(size, size)
        label.setStyleSheet("background: transparent; border: none;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return label

class SettingsWidget(QWidget):
    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db

        self.current_user = current_user

        self.colors = {
            "bg_main": "#FAF9F7",
            "card_bg": "#FFFFFF",
            "text_dark": "#3E3E3E",
            "text_mid": "#7F8C8D",
            "brown_dark": "#6B3F27",
            "brown_light": "#A0563D",
            "border": "#E0E0E0",
            "hover_bg": "#F5ECE5",
            "border_hover": "#D4A574",
            "shadow_light": "#0000000A",
            "accent": "#8B5A3C"
        }
        self.init_ui()

    def init_ui(self):
        # Ang main layout ng Settings ay gagamit din ng Stacked Widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # ==========================================
        # INDEX 0: Ang Settings Dashboard (Menu Grid)
        # ==========================================
        self.dashboard_view = QWidget()
        self.setup_dashboard_view()
        self.stacked_widget.addWidget(self.dashboard_view)

        # ==========================================
        # SAFE LOADER (Pumipigil sa pag-crash ng buong Settings)
        # ==========================================
        def safe_load(module_name, widget_class):
            try:
                # Every page gets the signed-in user, so its actions are logged under the right name
                return widget_class(self.db, self.current_user)
            except Exception as e:
                # Kung may error, gagawa ng error page imbes na i-crash ang buong app
                print(f"Crash isolated in {module_name}: {e}")
                err_widget = QWidget()
                lay = QVBoxLayout(err_widget)
                err_lbl = QLabel(f"⚠️ FAILED TO LOAD: {module_name}\n\nExact Error: {str(e)}")
                err_lbl.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")
                err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.addWidget(err_lbl)
                return err_widget

        # ==========================================
        # INDEXES 1+: Ang mga Sub-Modules
        # ==========================================
        self.finance_view = self.create_sub_module_wrapper("Finance", safe_load("Finance", FinancialWidget))
        self.stacked_widget.addWidget(self.finance_view) # Index 1

        self.analytics_view = self.create_sub_module_wrapper("Reports", safe_load("Reports", ReportsWidget))
        self.stacked_widget.addWidget(self.analytics_view) # Index 2

        self.user_mgmt_view = self.create_sub_module_wrapper("User Management", safe_load("User Management", UserManagementWidget))
        self.stacked_widget.addWidget(self.user_mgmt_view) # Index 3

        self.audit_log_view = self.create_sub_module_wrapper(
            "Audit Log",
            safe_load("Audit Log", SystemAuditLogsWidget)
        )
        self.stacked_widget.addWidget(self.audit_log_view) # Index 4

        self.backup_view = self.create_sub_module_wrapper(
            "Backup & Restore",
            safe_load("Backup & Restore", BackupRestoreWidget)
        )
        self.stacked_widget.addWidget(self.backup_view) # Index 5

        self.hours_view = self.create_sub_module_wrapper("Store Hours", safe_load("Store Hours", StoreHoursWidget))
        self.stacked_widget.addWidget(self.hours_view) # Index 6

        # Set default view
        self.stacked_widget.setCurrentIndex(0)

    def setup_dashboard_view(self):
        """Ito ang magsisilbing menu ng Settings na mukhang Dashboard"""
        layout = QVBoxLayout(self.dashboard_view)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(24)

        # The page name is already in the top bar; one short line is enough here
        desc = QLabel("Choose what you want to manage.")
        desc.setFont(QFont("Segoe UI", 13))
        desc.setStyleSheet(f"color: {self.colors['text_mid']};")
        layout.addWidget(desc)

        # Grid Layout para sa mga Cards with improved spacing
        grid = QGridLayout()
        grid.setSpacing(24)
        grid.setContentsMargins(0, 0, 0, 0)

        # Define the cards: (Icon, Title, Description, Stack_Index_Target)
        cards = [
            (SVGIcons.get_user_icon(), "Users", "Add or approve staff, and reset passwords.", 3),
            (SVGIcons.get_finance_icon(), "Finance", "Count the cash and record expenses.", 1),
            (SVGIcons.get_analytics_icon(), "Reports", "Sales, profit, best sellers and busy hours.", 2),
            (SVGIcons.get_audit_icon(), "Audit Log", "Every sign-in and action, kept safe.", 4),
            (SVGIcons.get_backup_icon(), "Backup & Restore", "A copy of all your data, so nothing is lost.", 5),
            (SVGIcons.get_clock_icon(), "Store Hours", "Open and close times, closed days.", 6),
        ]

        # Administrator lang ang may access sa User Management, Audit Log at Backup;
        # ang Manager ay Finance at Reports lang
        ADMIN_ONLY = {3, 4, 5}
        role_row = self.db.fetch_one("SELECT role FROM users WHERE username = ?", (self.current_user,))
        is_admin = bool(role_row) and (role_row['role'] or "").lower() in ("administrator", "admin")
        if not is_admin:
            cards = [c for c in cards if c[3] not in ADMIN_ONLY]

        self._card_status = {}
        row, col = 0, 0
        for svg_icon, title_str, desc_str, index_target in cards:
            card = self.create_menu_card(svg_icon, title_str, desc_str, index_target)
            self._card_status[index_target] = card._status
            grid.addWidget(card, row, col)
            col += 1
            if col > 2: # 3 cards per row
                col = 0
                row += 1

        layout.addLayout(grid)
        layout.addStretch()

    def create_menu_card(self, svg_string, title, description, target_index):
        """Gagawa ng clickable card button with SVG icon"""
        card_btn = QPushButton()
        card_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        card_btn.setFixedSize(320, 160)
        card_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Enhanced stylesheet for Card with shadow effect
        card_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 14px;
                text-align: left;
                padding: 0px;
                transition: all 200ms ease;
                box-shadow: 0 2px 8px {self.colors['shadow_light']};
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover_bg']};
                border: 1.5px solid {self.colors['brown_dark']};
                box-shadow: 0 8px 16px {self.colors['shadow_light']};
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                box-shadow: 0 4px 12px {self.colors['shadow_light']};
            }}
        """)

        # Custom Layout sa loob ng button
        card_layout = QVBoxLayout(card_btn)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(8)

        # Icon area at Title sa isang horizontal row
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)
        
        # SVG Icon container
        icon_container = QFrame()
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['hover_bg']};
                border-radius: 10px;
                border: none;
            }}
        """)
        icon_container.setFixedSize(48, 48)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        
        try:
            icon_widget = SVGIcons.create_svg_widget(svg_string, 32)
            icon_layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        except:
            # Fallback if SVG rendering fails
            icon_label = QLabel(); icon_label.setPixmap(_ui_pix("file", "#6B3F27", 24))
            icon_label.setFont(QFont("Segoe UI", 20))
            icon_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        top_row.addWidget(icon_container)
        
        # Title with better typography
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"""
            color: {self.colors['text_dark']};
            background: transparent;
            border: none;
        """)
        
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        card_layout.addLayout(top_row)

        # Description with improved styling
        desc_lbl = QLabel(description)
        desc_lbl.setFont(QFont("Segoe UI", 11))
        desc_lbl.setStyleSheet(f"""
            color: {self.colors['text_mid']};
            background: transparent;
            border: none;
            line-height: 1.4;
        """)
        desc_lbl.setWordWrap(True)
        card_layout.addWidget(desc_lbl)
        card_layout.addStretch()

        # Live status (e.g. "4 active · 1 naghihintay"), filled in by refresh_statuses()
        card_btn._status = QLabel("")
        card_btn._status.setWordWrap(True)
        card_btn._status.setStyleSheet(f"color: {self.colors['brown_dark']}; font-size: 12px; font-weight: 600; "
                                       "background: transparent; border: none;")
        card_layout.addWidget(card_btn._status)

        # Event: Kapag kinlik ang card, pupunta sa specific na sub-module index
        card_btn.clicked.connect(lambda: self.switch_view(target_index))

        return card_btn

    def create_sub_module_wrapper(self, module_name, widget_instance):
        """Babalutin nito ang sub-module mo para magkaroon ng 'Back' button sa taas"""
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Enhanced Header Bar with improved styling
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['card_bg']};
                border-bottom: 1px solid {self.colors['border']};
                box-shadow: 0 2px 4px {self.colors['shadow_light']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(0)

        # Back button with improved styling
        back_btn = QPushButton("  Back to Settings")
        back_btn.setIcon(_ui_icon("chevron_left", "#6B3F27", 16))
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setFixedHeight(40)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.colors['brown_dark']};
                border: none;
                font-weight: 600;
                font-size: 13px;
                padding: 0px 12px;
                border-radius: 6px;
                transition: all 150ms ease;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover_bg']};
                color: {self.colors['brown_light']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['border']};
            }}
        """)
        back_btn.clicked.connect(lambda: self.switch_view(0)) # Bumalik sa Index 0 (Dashboard)
        
        # Module title with improved styling
        module_title = QLabel(module_name)
        module_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        module_title.setStyleSheet(f"""
            color: {self.colors['text_dark']};
            border: none;
            font-weight: 600;
        """)

        back_btn.setStyleSheet(back_btn.styleSheet().replace("font-size: 13px;", "font-size: 14px;")
                               .replace("background-color: transparent;", f"background-color: {self.colors['hover_bg']};", 1))
        header_layout.addWidget(back_btn)
        header_layout.addSpacing(16)
        header_layout.addWidget(module_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()

        layout.addWidget(header)
        layout.addWidget(widget_instance, stretch=1) # Ilagay ang mismong module (e.g. FinancialWidget) sa ilalim
        
        return wrapper

    def switch_view(self, index):
        """Pinapalitan ang view ng StackedWidget"""
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:
            self.refresh_statuses()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_statuses()

    def hideEvent(self, event):
        # Leaving Settings for another page closes the open sub-page (Store Hours, Finance, ...),
        # so coming back always shows the Settings menu. Minimizing the window does not count.
        super().hideEvent(event)
        if not event.spontaneous():
            self.stacked_widget.setCurrentIndex(0)

    def stop_timers(self):
        for i in range(self.stacked_widget.count()):
            for w in self.stacked_widget.widget(i).findChildren(QWidget):
                if hasattr(w, "stop_timers") and w is not self:
                    try:
                        w.stop_timers()
                    except Exception:
                        pass

    def refresh_statuses(self):
        """Short, live status line on each card so you know if anything needs doing."""
        st = getattr(self, "_card_status", {})
        warn, ok = "#B45309", self.colors['brown_dark']

        def put(key, text, color=ok):
            if key in st:
                st[key].setText(text)
                st[key].setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        try:
            u = self.db.fetch_one("SELECT SUM(status = 'Active' AND COALESCE(is_archived, 0) = 0) AS active, "
                                  "SUM(status = 'Pending') AS pending FROM users")
            pending = u["pending"] or 0
            put(3, f"{u['active'] or 0} active  ·  {pending} waiting for approval", warn if pending else ok)

            counted = self.db.fetch_one("SELECT COUNT(*) AS n FROM reconciliation WHERE date(created_at) = date('now', 'localtime')")["n"]
            put(1, "Cash counted today" if counted else "Cash not counted yet today", ok if counted else warn)

            sales = self.db.fetch_one("SELECT COALESCE(SUM(amount), 0) AS s FROM sales WHERE COALESCE(is_voided, 0) = 0 "
                                      "AND date(created_at) = date('now', 'localtime')")["s"]
            put(2, f"Sales today: ₱{sales:,.2f}")

            failed = self.db.fetch_one("SELECT COUNT(*) AS n FROM activity_log WHERE action IN ('sign-in failed','account locked') "
                                       "AND date(created_at) = date('now','localtime')")["n"]
            last = self.db.fetch_one("SELECT action, username, created_at FROM activity_log "
                                     "WHERE action NOT IN ('sale completed') ORDER BY id DESC LIMIT 1")
            if failed:
                put(4, f"{failed} wrong password{'s' if failed != 1 else ''} today — check who", warn)
            elif last:
                when = datetime.strptime(last["created_at"][:16], "%Y-%m-%d %H:%M").strftime("%I:%M %p").lstrip("0")
                put(4, f"Last: {last['action']} — {last['username'] or '?'}, {when}")
            else:
                put(4, "Nothing recorded yet")

            folder = os.path.join(os.path.dirname(self.db.db_path), "backups")
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".db")] if os.path.isdir(folder) else []
            if files:
                newest = datetime.fromtimestamp(max(os.path.getmtime(f) for f in files))
                day = "today" if newest.date() == date.today() else ("yesterday" if newest.date() == date.today() - timedelta(days=1)
                                                                   else newest.strftime("%b %d"))
                old = datetime.now() - newest > timedelta(days=2)
                put(5, f"Last backup: {day}, {newest.strftime('%I:%M %p').lstrip('0')}", "#B91C1C" if old else ok)
            else:
                put(5, "No backup yet", "#B91C1C")

            is_open, title, _ = store_status(self.db)
            if title in ("Open now", "Not open yet"):
                title += f" · closes {fmt_time(closing_time_today(self.db))}"
            put(6, title)
        except Exception as e:
            print(f"[Settings] status error: {e}")