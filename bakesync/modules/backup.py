import os
import shutil
import sqlite3
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QScrollArea, QFileDialog, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor, QColor

from bakesync.core.audit import log_activity
from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.ui import THEME as T, InfoIcon, icon_label, svg_pixmap, button, card

REQUIRED_TABLES = {"users", "products", "sales"}
AUTO_BACKUPS_TO_KEEP = 14
KIND_WORDS = {"auto": "Automatic (daily)", "manual": "Made by hand", "pre_restore": "Safety copy (before a restore)",
              "usb": "Copy for USB"}


def backup_dir_for(db):
    return os.path.join(os.path.dirname(db.db_path), "backups")


def make_backup(db, tag="manual"):
    """Copies the live database to backups/ and returns the new file path."""
    folder = backup_dir_for(db)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"bakesync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tag}.db")
    db.conn.commit()
    dest = sqlite3.connect(path)
    try:
        db.conn.backup(dest)
    finally:
        dest.close()
    return path


def auto_backup(db):
    """Once a day, on app start: make an "auto" backup and keep only the newest
    AUTO_BACKUPS_TO_KEEP of them. Returns the new path, or None if today's exists."""
    folder = backup_dir_for(db)
    os.makedirs(folder, exist_ok=True)
    autos = sorted(f for f in os.listdir(folder) if f.endswith("_auto.db"))
    if any(f.startswith(f"bakesync_{datetime.now().strftime('%Y%m%d')}_") for f in autos):
        return None
    path = make_backup(db, tag="auto")
    log_activity(db, "System", "backup made", "system", "Automatic daily backup")
    autos.append(os.path.basename(path))
    for old in sorted(autos)[:-AUTO_BACKUPS_TO_KEEP]:
        try:
            os.remove(os.path.join(folder, old))
        except OSError as e:
            print(f"[Backup] could not remove old auto backup {old}: {e}")
    return path


def validate_backup(path):
    """Returns None if `path` is a usable BakeSync database, otherwise an error message."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                return "The file failed SQLite's integrity check (it may be corrupted)."
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        return f"The file is not a valid SQLite database.\n\n{e}"
    missing = REQUIRED_TABLES - tables
    if missing:
        return f"The file is not a BakeSync database (missing tables: {', '.join(sorted(missing))})."
    return None


def _kind(name):
    for tag in ("pre_restore", "auto", "manual", "usb"):
        if name.endswith(f"_{tag}.db"):
            return tag
    return "manual"


def _when(dt):
    today = datetime.now().date()
    day = ("Today" if dt.date() == today else "Yesterday" if dt.date() == today - timedelta(days=1)
           else dt.strftime("%A, %b %d, %Y"))
    return f"{day}  ·  {dt.strftime('%I:%M %p').lstrip('0')}"


def _size(n):
    kb = n / 1024
    return f"{kb / 1024:.1f} MB" if kb >= 1024 else f"{kb:.0f} KB"


class _Tile(QPushButton):
    """Big clickable tile: icon, title, one short line."""

    def __init__(self, icon, title, line, color, bg):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(120)
        self.setStyleSheet(f"QPushButton {{ background: white; border: 1px solid {T['line']}; border-radius: 14px; text-align: left; }}"
                           f"QPushButton:hover {{ border: 2px solid {color}; background: {T['cream']}; }}")
        lay = QVBoxLayout(self); lay.setContentsMargins(18, 16, 18, 14); lay.setSpacing(6)
        ic = icon_label(icon, color, 22, bg=bg, box=44, radius=12)
        t = QLabel(title); t.setStyleSheet(f"color: {T['text']}; font-size: 15px; font-weight: bold; background: transparent;")
        l = QLabel(line); l.setWordWrap(True); l.setStyleSheet(f"color: {T['mid']}; font-size: 12px; background: transparent;")
        for w in (ic, t, l):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            lay.addWidget(w)
        self.sub = l


class BackupRestoreWidget(QWidget):
    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.current_user = current_user or "Unknown"
        self.backup_dir = backup_dir_for(self.db)
        os.makedirs(self.backup_dir, exist_ok=True)
        self.init_ui()
        self.load_backups()

    def showEvent(self, e):
        super().showEvent(e)
        self.load_backups()

    # ── UI ───────────────────────────────────────────────────────────────
    def init_ui(self):
        self.setStyleSheet(f"background-color: {T['cream']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 18, 32, 18)
        layout.setSpacing(14)

        # is my data safe?
        self.status = QFrame(); self.status.setObjectName("status")
        sl = QHBoxLayout(self.status); sl.setContentsMargins(20, 14, 16, 14); sl.setSpacing(16)
        self.status_icon = QLabel(); self.status_icon.setFixedSize(52, 52); self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self.status_icon)
        col = QVBoxLayout(); col.setSpacing(2)
        self.status_title = QLabel(""); self.status_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.status_sub = QLabel(""); self.status_sub.setStyleSheet("font-size: 13px;")
        col.addWidget(self.status_title); col.addWidget(self.status_sub)
        sl.addLayout(col, 1)
        sl.addWidget(InfoIcon(f"A backup is a full copy of all your data (sales, stock, prices, accounts). "
                              f"BakeSync makes one by itself every day and keeps the last {AUTO_BACKUPS_TO_KEEP}. "
                              "Green means your newest backup is from today or yesterday.", "Backups"), alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.status)

        # three big actions
        tiles = QHBoxLayout(); tiles.setSpacing(14)
        self.btn_create = _Tile("database", "Back up now", "Save a fresh copy of all your data on this computer.",
                                T["brown"], T["cream_dark"])
        self.btn_create.clicked.connect(self.create_backup_clicked)
        self.btn_usb = _Tile("drive", "Copy to USB", "Keep a copy outside this computer, in case it breaks.",
                             T["blue"], T["blue_bg"])
        self.btn_usb.clicked.connect(self.copy_to_usb)
        self.btn_restore_file = _Tile("restore", "Restore from USB / file", "Bring back data from a copy you saved before.",
                                      T["amber"], T["amber_bg"])
        self.btn_restore_file.clicked.connect(self.restore_from_file)
        for t in (self.btn_create, self.btn_usb, self.btn_restore_file):
            tiles.addWidget(t)
        layout.addLayout(tiles)

        # the list
        head = QHBoxLayout(); head.setSpacing(6)
        lt = QLabel("Your backups"); lt.setStyleSheet(f"color: {T['text']}; font-size: 15px; font-weight: bold; background: transparent;")
        head.addWidget(lt)
        head.addWidget(InfoIcon("Click 'Restore' on a row to go back to how your data was at that time. "
                                "A safety copy of today's data is saved first, so you can undo it.", "Your backups"))
        self.count_lbl = QLabel(""); self.count_lbl.setStyleSheet(f"color: {T['mid']}; font-size: 12px; background: transparent;")
        head.addWidget(self.count_lbl)
        head.addStretch()
        self.btn_folder = button("Open backup folder", "ghost", icon="folder", h=34)
        self.btn_folder.clicked.connect(lambda: os.startfile(self.backup_dir))
        head.addWidget(self.btn_folder)
        layout.addLayout(head)

        box = card(12, name="list")
        bl = QVBoxLayout(box); bl.setContentsMargins(0, 0, 0, 0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                         f"QScrollBar:vertical {{ width: 8px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 4px; }}")
        holder = QWidget(); holder.setStyleSheet("background: white;")
        self.list_lay = QVBoxLayout(holder); self.list_lay.setContentsMargins(0, 0, 0, 0); self.list_lay.setSpacing(0)
        sc.setWidget(holder)
        bl.addWidget(sc)
        layout.addWidget(box, 1)

    # ── data ─────────────────────────────────────────────────────────────
    def _files(self):
        files = [f for f in os.listdir(self.backup_dir) if f.lower().endswith(".db")]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(self.backup_dir, f)), reverse=True)
        return files

    def load_backups(self):
        files = self._files()
        total = sum(os.path.getsize(os.path.join(self.backup_dir, f)) for f in files)
        self.count_lbl.setText(f"  {len(files)} saved  ·  {_size(total)}" if files else "")

        if files:
            newest = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.backup_dir, files[0])))
            age = datetime.now() - newest
            if age < timedelta(days=1, hours=12):
                kind = (T["green_bg"], "#BFE3CB", T["green"], "check_circle", "Your data is safe", f"Last backup: {_when(newest)}")
            elif age < timedelta(days=4):
                kind = (T["amber_bg"], "#F3D49B", T["amber"], "alert", f"Last backup was {age.days} days ago",
                        "Click 'Back up now' to make a fresh one.")
            else:
                kind = (T["red_bg"], "#F1C2BE", T["red"], "alert", f"No backup for {age.days} days",
                        "Please click 'Back up now'.")
        else:
            kind = (T["red_bg"], "#F1C2BE", T["red"], "alert", "No backup yet", "Click 'Back up now' to save a copy of your data.")
        bg, border, fg, icon, title, sub = kind
        self.status.setStyleSheet(f"QFrame#status {{ background: {bg}; border: 1px solid {border}; border-radius: 14px; }}"
                                  "QLabel { background: transparent; border: none; }")
        self.status_icon.setPixmap(svg_pixmap(icon, "white", 28))
        self.status_icon.setStyleSheet(f"background: {fg}; border-radius: 26px;")
        self.status_title.setText(title); self.status_title.setStyleSheet(f"color: {fg};")
        self.status_sub.setText(sub); self.status_sub.setStyleSheet(f"color: {T['text']}; font-size: 13px;")
        last_usb = self.db.get_setting("backup_usb_last")
        self.btn_usb.sub.setText(f"Last copy: {_when(datetime.fromisoformat(last_usb))}" if last_usb
                                 else "Keep a copy outside this computer, in case it breaks.")

        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if not files:
            e = QLabel("No backups yet."); e.setStyleSheet(f"color: {T['muted']}; font-size: 13px; padding: 24px;")
            self.list_lay.addWidget(e, alignment=Qt.AlignmentFlag.AlignCenter)
        styles = {"auto": ("refresh", T["green"], T["green_bg"]), "manual": ("save", T["brown"], T["cream_dark"]),
                  "pre_restore": ("shield", T["amber"], T["amber_bg"]), "usb": ("drive", T["blue"], T["blue_bg"])}
        for name in files:
            path = os.path.join(self.backup_dir, name)
            dt = datetime.fromtimestamp(os.path.getmtime(path))
            k = _kind(name)
            row = QWidget(); row.setStyleSheet(f"QWidget {{ background: white; }} QWidget#r {{ border-bottom: 1px solid {T['line']}; }}")
            row.setObjectName("r")
            h = QHBoxLayout(row); h.setContentsMargins(14, 8, 14, 8); h.setSpacing(12)
            ic, fg, bg = styles.get(k, styles["manual"])
            h.addWidget(icon_label(ic, fg, 16, bg=bg, box=34, radius=17))
            c = QVBoxLayout(); c.setSpacing(0)
            w = QLabel(_when(dt)); w.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 600;")
            w.setToolTip(name)
            kl = QLabel(f"{KIND_WORDS.get(k, 'Backup')}  ·  {_size(os.path.getsize(path))}")
            kl.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
            c.addWidget(w); c.addWidget(kl)
            h.addLayout(c, 1)
            b = button("Restore", "secondary", icon="restore", h=34)
            b.clicked.connect(lambda _, p=path: self._restore(p))
            h.addWidget(b)
            self.list_lay.addWidget(row)
        self.list_lay.addStretch()

    # ── actions ──────────────────────────────────────────────────────────
    def create_backup(self, tag="manual"):
        return make_backup(self.db, tag)

    def create_backup_clicked(self):
        try:
            path = self.create_backup()
        except (sqlite3.Error, OSError) as e:
            BakeSyncAlert.show_error(self, "Backup Failed", f"Could not make the backup.\n\n{e}")
            return
        log_activity(self.db, self.current_user, "backup made", "system", os.path.basename(path))
        self.load_backups()
        BakeSyncAlert.show_success(self, "Backup Done", "A copy of all your data was saved.")

    def copy_to_usb(self):
        start = self.db.get_setting("backup_usb_folder", "") or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "Choose your USB drive (or another folder)", start)
        if not folder:
            return
        try:
            path = self.create_backup(tag="usb")
            dest = os.path.join(folder, os.path.basename(path))
            shutil.copy2(path, dest)
            os.remove(path)          # the USB copy is the point; don't fill the local folder
        except (sqlite3.Error, OSError) as e:
            BakeSyncAlert.show_error(self, "Could not save the copy",
                                     f"Check that the USB drive is plugged in and not full.\n\n{e}")
            return
        self.db.set_setting("backup_usb_folder", folder)
        self.db.set_setting("backup_usb_last", datetime.now().isoformat(timespec="seconds"))
        log_activity(self.db, self.current_user, "backup copied", "system", f"Copy saved to {folder}")
        self.load_backups()
        BakeSyncAlert.show_success(self, "Copy Saved",
                                   f"A copy of all your data was saved to:\n{folder}\n\nKeep the USB drive somewhere safe.")

    def restore_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a BakeSync backup",
                                              self.db.get_setting("backup_usb_folder", "") or self.backup_dir,
                                              "BakeSync backup (*.db *.sqlite);;All Files (*)")
        if path:
            self._restore(path)

    def _restore(self, path):
        error = validate_backup(path)
        if error:
            BakeSyncAlert.show_error(self, "Not a Backup", error)
            return
        when = _when(datetime.fromtimestamp(os.path.getmtime(path)))
        if not BakeSyncAlert.ask_yes_no(
            self, "Go back to this backup?",
            f"All data will go back to how it was on:\n{when}\n\n"
            "Anything recorded after that (sales, stock, prices) will be replaced.\n"
            "A safety copy of today's data is saved first, so you can undo this.\n\n"
            "BakeSync will close after restoring.",
            yes_text="RESTORE", no_text="CANCEL"
        ):
            return
        try:
            safety = self.create_backup(tag="pre_restore")
            src = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            try:
                src.backup(self.db.conn)
            finally:
                src.close()
        except (sqlite3.Error, OSError) as e:
            BakeSyncAlert.show_error(self, "Restore Failed",
                                     "The restore did not finish. If any data looks wrong, restore the newest "
                                     f"'Safety copy' from the list.\n\n{e}")
            return
        log_activity(self.db, self.current_user, "data restored", "system",
                     f"Went back to the backup from {when} ({os.path.basename(path)}); safety copy: {os.path.basename(safety)}")
        BakeSyncAlert.show_success(
            self, "Restore Complete",
            f"Your data is back to how it was on {when}.\n"
            "A safety copy of the data before the restore was also saved.\n\n"
            "BakeSync will now close. Please open it again.")
        # Every open screen still holds the old data, so a restart is required
        QApplication.quit()
