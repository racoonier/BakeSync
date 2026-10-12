import sqlite3
import os
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from bakesync.core.auth_utils import hash_password, is_hashed, verify_password
from bakesync.core.app_config import get_setting
from bakesync.core import audit
from bakesync.paths import DATA_DIR

class DatabaseManager:
    def __init__(self, db_name=None):
        # BAKESYNC_DB (env var or config.local.json) picks the database, e.g. bakesync_demo.db
        db_name = db_name or get_setting("BAKESYNC_DB", "bakesync.db")
        # data/ folder (katabi ng BakeSync.exe kapag packaged app)
        self.db_path = os.path.join(DATA_DIR, db_name)
        
        self.conn = None
        self._in_transaction = False
        self.init_database()

    def init_database(self):
        """Initialize database and create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # --- 1. BAGONG DAGDAG: System Roles Table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE,
                description TEXT,
                access_level TEXT,
                permissions TEXT
            )
        """)

        # --- 2. IN-UPDATE: Users Table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                status TEXT DEFAULT 'Active',
                is_archived INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                admin_pin TEXT,              -- NEW: Para sa 6-digit PIN
                mastery_key TEXT,            -- NEW: Para sa auto-generated key
                security_data TEXT,          -- NEW: Para sa security questions
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)


        # Products/Breads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                retail_price REAL NOT NULL,
                production_cost REAL NOT NULL,
                stock_qty REAL DEFAULT 0,
                unit TEXT DEFAULT 'Pieces',
                avg_daily_usage REAL DEFAULT 0,
                baking_time INTEGER DEFAULT 30,
                baking_temp TEXT DEFAULT '180',
                estimated_yield INTEGER DEFAULT 50,
                expiry_date DATE,
                is_archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity_remaining REAL,
                expiry_date DATE,
                received_date TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        
        
        # Ingredients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                bulk_qty REAL NOT NULL,
                unit TEXT DEFAULT 'Grams',
                avg_daily_usage REAL NOT NULL,
                expiry_date DATE,           
                is_archived INTEGER DEFAULT 0, 
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        # Recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
            )
        """)

       # Production Schedule
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS production_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                forecast_qty INTEGER NOT NULL,
                special_order_qty INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Queued',
                scheduled_date DATE DEFAULT (date('now','localtime')),
                customer_name TEXT,
                pickup_time TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        # Inventory movements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredient_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER,
                quantity_remaining REAL,
                expiry_date DATE,
                batch_cost REAL DEFAULT 0.0, 
                cost_per_unit REAL DEFAULT 0.0,
                received_date TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
            )
        """)

        # Waste logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waste_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                waste_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        # Sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        # Financial reconciliation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT (date('now','localtime')),
                system_sales REAL NOT NULL,
                actual_cash REAL,
                variance REAL,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_at    TIMESTAMP DEFAULT (datetime('now','localtime')),
                closed_at    TIMESTAMP,
                total_sales  REAL DEFAULT 0.0,
                total_txns   INTEGER DEFAULT 0,
                closed_by    TEXT,
                status       TEXT DEFAULT 'Open'
            )
        """)

        


        try: cursor.execute("ALTER TABLE sales ADD COLUMN discount REAL DEFAULT 0.0")
        except: pass
        try: cursor.execute("ALTER TABLE sales ADD COLUMN session_id INTEGER")
        except: pass
        try: cursor.execute("ALTER TABLE sales ADD COLUMN tendered REAL DEFAULT 0.0")
        except: pass
        try: cursor.execute("ALTER TABLE sales ADD COLUMN change_given REAL DEFAULT 0.0")
        except: pass
        try: cursor.execute("ALTER TABLE sales ADD COLUMN cashier TEXT")
        except: pass

        try: cursor.execute("ALTER TABLE sales ADD COLUMN is_voided INTEGER DEFAULT 0")
        except: pass

        # ---> IDAGDAG ITO PARA SA BAGONG SIGNUP DATA <---
        try: cursor.execute("ALTER TABLE users ADD COLUMN admin_pin TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN mastery_key TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN security_data TEXT")
        except: pass


        # FOR FINANCIALS & AUDIT UPDATE
        try: cursor.execute("ALTER TABLE ingredients ADD COLUMN cost_per_unit REAL DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE reconciliation ADD COLUMN denominations TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE reconciliation ADD COLUMN verified_by TEXT")
        except: pass

        # OpEx (Operating Expenses) Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operating_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_name TEXT NOT NULL,
                amount REAL NOT NULL,
                expense_date DATE DEFAULT (date('now','localtime')),
                logged_by TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        # Void & Refund Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS void_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                amount REAL NOT NULL,
                reason TEXT NOT NULL,
                voided_by TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        # FOR INGREDIENTS UPDATE
        try: cursor.execute("ALTER TABLE ingredients ADD COLUMN expiry_date DATE")
        except: pass
        try: cursor.execute("ALTER TABLE ingredients ADD COLUMN is_archived INTEGER DEFAULT 0")
        except: pass


        # ---> BAGONG DAGDAG PARA SA TERMS AND CONDITIONS <---
        try: cursor.execute("ALTER TABLE users ADD COLUMN terms_accepted INTEGER DEFAULT 0")
        except: pass

        # Pilitin magpalit ng password ang mga account na naka-default/temporary password pa
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
            for row in cursor.execute("SELECT id, password FROM users").fetchall():
                if verify_password(row["password"], "password123"):
                    cursor.execute("UPDATE users SET must_change_password = 1 WHERE id = ?", (row["id"],))
        except sqlite3.OperationalError:
            pass  # column already exists

        # Account lockout na hindi nare-reset ng pag-restart ng app
        try: cursor.execute("ALTER TABLE users ADD COLUMN locked_until TEXT")
        except sqlite3.OperationalError: pass

        # Orihinal na dami ng bawat batch (para sa "Stocked Today" sa Waste page)
        try:
            cursor.execute("ALTER TABLE product_batches ADD COLUMN initial_qty REAL")
            cursor.execute("UPDATE product_batches SET initial_qty = quantity_remaining WHERE initial_qty IS NULL")
        except sqlite3.OperationalError:
            pass  # column already exists

        # FOR RETAIL/PRODUCTS UPDATE
        try: cursor.execute("ALTER TABLE products ADD COLUMN stock_qty REAL DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE products ADD COLUMN expiry_date DATE")
        except: pass
        try: cursor.execute("ALTER TABLE products ADD COLUMN is_archived INTEGER DEFAULT 0")
        except: pass

        # 🟢 IDAGDAG ANG LINYANG ITO PARA SA PRODUCT TYPE:
        try: cursor.execute("ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'bread'")
        except: pass

        # FOR QUALITY CONTROL UPDATE
        try: cursor.execute("ALTER TABLE waste_logs ADD COLUMN reason TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE waste_logs ADD COLUMN ingredients_lost TEXT")
        except: pass

        # Inventory Action Log — tracks who added/archived/restored items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT,
                action TEXT NOT NULL,
                action_by TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)


        # 🟢 BAGONG DAGDAG: Para sa Finance Recent Activity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT,
                description TEXT NOT NULL,
                action_by TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        # Simple key/value settings (e.g. store closing time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # action_by column on inventory_movements for ingredient restock tracking
        try: cursor.execute("ALTER TABLE inventory_movements ADD COLUMN action_by TEXT")
        except: pass

        # Expense category (Rent, Electricity, ...) for the Finance filters
        try: cursor.execute("ALTER TABLE operating_expenses ADD COLUMN category TEXT")
        except sqlite3.OperationalError: pass

        self.conn.commit()
        audit.ensure_table(self.conn)
        self._migrate_local_time_defaults()
        self._migrate_plaintext_passwords()
        self._insert_demo_data()

    def _migrate_local_time_defaults(self):
        """Older databases used CURRENT_TIMESTAMP / CURRENT_DATE defaults, which are UTC
        (8 hours behind PH time). Rebuild those tables so new rows get local time like
        the rest of the app. SQLite cannot change a column default in place."""
        cursor = self.conn.cursor()
        tables = cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' "
            "AND (sql LIKE '%CURRENT_TIMESTAMP%' OR sql LIKE '%CURRENT_DATE%')"
        ).fetchall()
        if not tables:
            return
        cursor.execute("BEGIN")
        try:
            for name, sql in tables:
                tmp = f"{name}__migrating"
                new_sql = re.sub(r"DEFAULT\s+CURRENT_TIMESTAMP", "DEFAULT (datetime('now','localtime'))", sql, flags=re.I)
                new_sql = re.sub(r"DEFAULT\s+CURRENT_DATE", "DEFAULT (date('now','localtime'))", new_sql, flags=re.I)
                new_sql = re.sub(r'^CREATE TABLE\s+["`]?' + re.escape(name) + r'["`]?', f'CREATE TABLE "{tmp}"',
                                 new_sql, count=1, flags=re.I)
                cols = ", ".join(f'"{r[1]}"' for r in cursor.execute(f'PRAGMA table_info("{name}")'))
                cursor.execute(new_sql)
                cursor.execute(f'INSERT INTO "{tmp}" ({cols}) SELECT {cols} FROM "{name}"')
                cursor.execute(f'DROP TABLE "{name}"')
                cursor.execute(f'ALTER TABLE "{tmp}" RENAME TO "{name}"')
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"[Migration] local-time defaults skipped: {e}")

    def _migrate_plaintext_passwords(self):
        """One-time upgrade: hash any password, Admin PIN or mastery key still stored as plaintext."""
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT id, password, admin_pin, mastery_key FROM users").fetchall()
        for row in rows:
            for col in ("password", "admin_pin", "mastery_key"):
                if row[col] and not is_hashed(row[col]):
                    cursor.execute(f"UPDATE users SET {col} = ? WHERE id = ?",
                                   (hash_password(row[col]), row["id"]))
        self.conn.commit()

    def _insert_demo_data(self):
        """Insert default users only. No products or ingredients injected for a clean slate."""
        cursor = self.conn.cursor()
        
        # --- Default Data Insertions ---
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                
                # I-insert ang Default Roles
                cursor.execute("INSERT INTO system_roles (role_name, description, access_level, permissions) VALUES ('Administrator', 'Full system access', 'High', 'all')")
                cursor.execute("INSERT INTO system_roles (role_name, description, access_level, permissions) VALUES ('Manager', 'Can manage inventory', 'Medium', 'read,write')")
                cursor.execute("INSERT INTO system_roles (role_name, description, access_level, permissions) VALUES ('Cashier', 'POS access only', 'Low', 'read,transact')")
                cursor.execute("INSERT INTO system_roles (role_name, description, access_level, permissions) VALUES ('Baker', 'Production access only', 'Low', 'read')")

                # I-insert ang Default Users (Updated para tugma sa bagong columns)
                cursor.execute("""
                    INSERT INTO users (username, password, role, full_name, status, must_change_password)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, ('admin', hash_password('password123'), 'Administrator', 'Admin User', 'Active'))
                
                cursor.execute("""
                    INSERT INTO users (username, password, role, full_name, status, must_change_password)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, ('baker', hash_password('password123'), 'Baker', 'John Baker', 'Active'))
                
                cursor.execute("""
                    INSERT INTO users (username, password, role, full_name, status, must_change_password)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, ('cashier', hash_password('password123'), 'Cashier', 'Jane Cashier', 'Active'))

                self.conn.commit()
        except sqlite3.IntegrityError:
            pass


    def is_closed(self):
        """Check if database is closed to prevent timer errors after logout"""
        try:
            self.conn.cursor()
            return False
        except (sqlite3.ProgrammingError, AttributeError):
            return True

    def execute_query(self, query, params=()):
        """Execute a query with parameters"""
        if self.is_closed(): return None
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        if not self._in_transaction:
            self.conn.commit()
        return cursor

    @contextmanager
    def transaction(self):
        """Group several writes so they are saved all together or not at all:
            with db.transaction():
                db.execute_query(...)
                db.execute_query(...)
        If anything inside raises, every write in the block is rolled back."""
        if self._in_transaction:          # nested: the outer block decides
            yield
            return
        self._in_transaction = True
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self._in_transaction = False

    def fetch_all(self, query, params=()):
        """Fetch all results"""
        if self.is_closed(): return []
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_setting(self, key, default=None):
        row = self.fetch_one("SELECT value FROM app_settings WHERE key = ?", (key,))
        return row["value"] if row and row["value"] is not None else default

    def set_setting(self, key, value):
        self.execute_query(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))

    def fetch_one(self, query, params=()):
        """Fetch single result"""
        if self.is_closed(): return None
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def close(self):
        """Close database connection"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass