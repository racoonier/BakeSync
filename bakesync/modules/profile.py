"""My Profile: a full page for the signed-in person (opened from the avatar or the
sidebar user card). Cover banner, initials avatar, About, today's numbers,
recent activity, Edit profile and Change password."""
from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QLineEdit,
                             QGridLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient

from bakesync.core.audit import log_activity
from bakesync.widgets.ui import THEME as T, svg_pixmap, icon_label, initials, card, button, title_row
from bakesync.widgets.custom_alerts import BakeSyncAlert

AREA_ICON = {"signin": "login", "account": "user", "sale": "cart", "void": "ban", "stock": "box",
             "waste": "trash", "price": "tag", "money": "wallet", "system": "settings"}


def _nice(ts):
    try:
        d = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return str(ts)[:16] if ts else "—"
    day = ("Today" if d.date() == date.today() else "Yesterday" if d.date() == date.today() - timedelta(days=1)
           else d.strftime("%b %d, %Y"))
    return f"{day}, {d.strftime('%I:%M %p').lstrip('0')}"


class _Cover(QFrame):
    """Warm caramel-to-chocolate banner with a faint pattern of bread icons."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(118)
        self._bread = svg_pixmap("bread", "#FFFFFF", 26, 1.6)
        self._wheat = svg_pixmap("sun", "#FFFFFF", 22, 1.6)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor("#C98A4B")); g.setColorAt(0.55, QColor("#8A5230")); g.setColorAt(1, QColor("#4A2B1A"))
        p.setBrush(g); p.setPen(Qt.PenStyle.NoPen)
        r = QRectF(self.rect())
        p.drawRoundedRect(r, 16, 16)
        p.drawRect(QRectF(0, 20, r.width(), r.height() - 20))   # square bottom corners
        p.setOpacity(0.10)
        for row, y in enumerate(range(14, self.height(), 46)):
            for i, x in enumerate(range(-20 + (row % 2) * 40, self.width(), 80)):
                p.drawPixmap(x, y, self._bread if (i + row) % 2 == 0 else self._wheat)
        p.end()


class EditProfileDialog(QDialog):
    def __init__(self, db, username, parent=None):
        super().__init__(parent)
        self.db, self.username = db, username
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True); self.setFixedWidth(440)
        u = db.fetch_one("SELECT full_name, email, phone FROM users WHERE username = ?", (username,))
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        c = card(16, name="dlg")
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(30); sh.setYOffset(4); sh.setColor(QColor(0, 0, 0, 70))
        c.setGraphicsEffect(sh)
        outer.addWidget(c)
        lay = QVBoxLayout(c); lay.setContentsMargins(26, 22, 26, 22); lay.setSpacing(8)
        t, _ = title_row("Edit my profile", icon="edit", size=15, color=T["brown_dark"])
        lay.addWidget(t)
        self.inputs = {}
        for key, label, icon, placeholder in (("full_name", "Full name", "user", "e.g. Juan Dela Cruz"),
                                              ("email", "Email", "mail", "e.g. juan@email.com"),
                                              ("phone", "Phone", "phone", "e.g. 0917 123 4567")):
            l = QLabel(label); l.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 600;")
            lay.addWidget(l)
            wrap = QFrame(); wrap.setObjectName("in")
            wrap.setStyleSheet("QFrame#in { background: white; border: 1px solid #D6CCC2; border-radius: 9px; }")
            h = QHBoxLayout(wrap); h.setContentsMargins(12, 0, 12, 0); h.setSpacing(8)
            h.addWidget(icon_label(icon, T["muted"], 16))
            e = QLineEdit(str(u[key] or "") if u else ""); e.setPlaceholderText(placeholder); e.setFixedHeight(40)
            e.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 14px; color: {T['text']}; }}")
            h.addWidget(e)
            lay.addWidget(wrap)
            self.inputs[key] = e
        self.err = QLabel(""); self.err.setStyleSheet(f"color: {T['red']}; font-size: 12px;"); self.err.hide()
        lay.addWidget(self.err)
        btns = QHBoxLayout(); btns.setSpacing(10)
        cancel = button("Cancel", "secondary", h=44); cancel.clicked.connect(self.reject)
        save = button("Save", "primary", icon="check", h=44); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save, 2)
        lay.addSpacing(6); lay.addLayout(btns)

    def _save(self):
        v = {k: e.text().strip() for k, e in self.inputs.items()}
        if not v["full_name"]:
            self.err.setText("Please type your full name."); self.err.show(); return
        if v["email"] and ("@" not in v["email"] or "." not in v["email"].split("@")[-1]):
            self.err.setText("That email does not look right."); self.err.show(); return
        if v["phone"] and sum(ch.isdigit() for ch in v["phone"]) < 7:
            self.err.setText("That phone number looks too short."); self.err.show(); return
        self.db.execute_query("UPDATE users SET full_name = ?, email = ?, phone = ? WHERE username = ?",
                              (v["full_name"], v["email"], v["phone"], self.username))
        log_activity(self.db, self.username, "profile edited", "account", "Updated own name / email / phone")
        self.accept()


class ProfileWidget(QWidget):
    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.username = current_user
        self.setStyleSheet(f"background: {T['cream']};")
        self._build()

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place_avatar()

    def _place_avatar(self):
        if hasattr(self, "avatar"):
            self.avatar.move(36, self.cover.height() - 50)
            self.avatar.raise_()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(28, 18, 28, 18); root.setSpacing(14)

        # header card: cover, avatar, name, buttons
        self.head = card(16, name="head")
        hl = QVBoxLayout(self.head); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(0)
        self.cover = _Cover(); hl.addWidget(self.cover)
        info = QHBoxLayout(); info.setContentsMargins(160, 10, 24, 14); info.setSpacing(10)
        col = QVBoxLayout(); col.setSpacing(2)
        self.name_lbl = QLabel(); self.name_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {T['text']};")
        self.sub_lbl = QLabel(); self.sub_lbl.setStyleSheet(f"color: {T['mid']}; font-size: 13px;")
        col.addWidget(self.name_lbl); col.addWidget(self.sub_lbl)
        info.addLayout(col); info.addStretch()
        self.btn_edit = button("Edit profile", "primary", icon="edit", h=40)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_pw = button("Change password", "secondary", icon="key", h=40)
        self.btn_pw.clicked.connect(self._change_password)
        info.addWidget(self.btn_edit, alignment=Qt.AlignmentFlag.AlignTop)
        info.addWidget(self.btn_pw, alignment=Qt.AlignmentFlag.AlignTop)
        hl.addLayout(info)
        self.avatar = QLabel(self.head)
        self.avatar.setFixedSize(100, 100)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        self.avatar.setStyleSheet(f"background: {T['brown']}; color: {T['cream']}; border: 5px solid white; border-radius: 50px;")
        root.addWidget(self.head)

        row = QHBoxLayout(); row.setSpacing(16)
        # About
        about = card(14, name="about")
        al = QVBoxLayout(about); al.setContentsMargins(22, 16, 22, 16); al.setSpacing(8)
        t, _ = title_row("About", info="Your account details. Click 'Edit profile' to change your name, email or phone.", size=14)
        al.addWidget(t)
        self.about_rows = {}
        for key, icon, label in (("full_name", "user", "Full name"), ("username", "login", "Username"),
                                 ("role", "award", "Role"), ("email", "mail", "Email"), ("phone", "phone", "Phone"),
                                 ("joined", "calendar", "Joined"), ("last", "clock", "Last sign-in")):
            r = QHBoxLayout(); r.setSpacing(12)
            r.addWidget(icon_label(icon, T["brown"], 16, bg=T["cream_dark"], box=32, radius=8))
            c = QVBoxLayout(); c.setSpacing(0)
            k = QLabel(label); k.setStyleSheet(f"color: {T['muted']}; font-size: 11px;")
            v = QLabel("—"); v.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: 600;")
            c.addWidget(k); c.addWidget(v)
            r.addLayout(c); r.addStretch()
            al.addLayout(r)
            self.about_rows[key] = v
        al.addStretch()
        row.addWidget(about, 2)

        right = QVBoxLayout(); right.setSpacing(16)
        today = card(14, name="today")
        tl = QVBoxLayout(today); tl.setContentsMargins(22, 16, 22, 16); tl.setSpacing(10)
        t, _ = title_row("My day", info="What you did today in BakeSync. Sales and customers count only the sales you made at the POS.", size=14)
        tl.addWidget(t)
        grid = QHBoxLayout(); grid.setSpacing(12)
        self.stats = {}
        for key, icon, label, color, bg in (("sales", "wallet", "My sales today", T["green"], T["green_bg"]),
                                            ("customers", "users", "Customers served", T["blue"], T["blue_bg"]),
                                            ("voids", "ban", "Voids today", T["red"], T["red_bg"]),
                                            ("signins", "login", "Sign-ins this month", T["brown"], T["cream_dark"])):
            box = QFrame(); box.setObjectName("st")
            box.setStyleSheet(f"QFrame#st {{ background: {T['cream']}; border-radius: 12px; }}")
            b = QVBoxLayout(box); b.setContentsMargins(14, 10, 14, 10); b.setSpacing(4)
            b.addWidget(icon_label(icon, color, 18, bg=bg, box=34, radius=17))
            v = QLabel("0"); v.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)); v.setStyleSheet(f"color: {T['text']};")
            l = QLabel(label); l.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
            b.addWidget(v); b.addWidget(l)
            grid.addWidget(box)
            self.stats[key] = v
        tl.addLayout(grid)
        right.addWidget(today)

        act = card(14, name="act")
        acl = QVBoxLayout(act); acl.setContentsMargins(22, 18, 22, 18); acl.setSpacing(10)
        t, _ = title_row("My recent activity", info="The last things you did. The full list is in Settings > Audit Log.", size=14)
        acl.addWidget(t)
        from PyQt6.QtWidgets import QScrollArea
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 6px; background: transparent; }"
                         f"QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 3px; }}")
        holder = QWidget(); holder.setStyleSheet("background: transparent;")
        self.act_list = QVBoxLayout(holder); self.act_list.setContentsMargins(0, 0, 6, 0); self.act_list.setSpacing(6)
        self.act_list.addStretch()
        sc.setWidget(holder)
        acl.addWidget(sc, 1)
        right.addWidget(act, 1)
        row.addLayout(right, 3)
        root.addLayout(row, 1)

    def refresh(self):
        if self.db.is_closed():
            return
        u = self.db.fetch_one("SELECT full_name, username, role, email, phone, created_at FROM users WHERE username = ?",
                              (self.username,))
        if not u:
            return
        name = (u["full_name"] or "").strip() or u["username"]
        self.avatar.setText(initials(name))
        self.name_lbl.setText(name)
        joined = ""
        try:
            joined = datetime.strptime(str(u["created_at"])[:10], "%Y-%m-%d").strftime("%B %Y")
        except ValueError:
            pass
        self.sub_lbl.setText(f"@{u['username']}   ·   {u['role']}" + (f"   ·   Member since {joined}" if joined else ""))
        last = self.db.fetch_one("SELECT created_at FROM activity_log WHERE username = ? AND action = 'signed in' "
                                 "ORDER BY id DESC LIMIT 1 OFFSET 1", (self.username,))
        vals = {"full_name": name, "username": u["username"], "role": u["role"],
                "email": u["email"] or "Not added yet", "phone": u["phone"] or "Not added yet",
                "joined": _nice(u["created_at"]).split(",")[0] if u["created_at"] else "—",
                "last": _nice(last["created_at"]) if last else "This is your first time"}
        for k, v in vals.items():
            self.about_rows[k].setText(v)
            self.about_rows[k].setStyleSheet(f"color: {T['muted'] if v == 'Not added yet' else T['text']}; font-size: 13px; font-weight: 600;")

        s = self.db.fetch_one("SELECT COALESCE(SUM(amount),0) AS t, COUNT(DISTINCT created_at) AS c FROM sales "
                              "WHERE cashier = ? AND COALESCE(is_voided,0) = 0 AND date(created_at) = date('now','localtime')",
                              (self.username,))
        v = self.db.fetch_one("SELECT COUNT(*) FROM void_logs WHERE voided_by = ? AND date(created_at) = date('now','localtime')",
                              (self.username,))[0]
        si = self.db.fetch_one("SELECT COUNT(*) FROM activity_log WHERE username = ? AND action = 'signed in' "
                               "AND strftime('%Y-%m', created_at) = strftime('%Y-%m','now','localtime')", (self.username,))[0]
        self.stats["sales"].setText(f"₱{s['t']:,.2f}")
        self.stats["customers"].setText(f"{s['c']:,}")
        self.stats["voids"].setText(str(v))
        self.stats["signins"].setText(str(si))

        while self.act_list.count() > 1:          # keep the stretch at the end
            it = self.act_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                while it.layout().count():
                    w = it.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()
        rows = self.db.fetch_all("SELECT created_at, action, area, details FROM activity_log WHERE username = ? "
                                 "ORDER BY id DESC LIMIT 15", (self.username,))
        if not rows:
            l = QLabel("Nothing yet."); l.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
            self.act_list.insertWidget(0, l)
        for i, r in enumerate(rows):
            w = QWidget(); w.setFixedHeight(42); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(12)
            h.addWidget(icon_label(AREA_ICON.get(r["area"], "activity"), T["brown"], 15, bg=T["cream_dark"], box=30, radius=15))
            c = QVBoxLayout(); c.setSpacing(0)
            det = r["details"] or ""
            det = det if len(det) <= 70 else det[:67] + "..."
            a = QLabel(r["action"].capitalize() + (f"  —  {det}" if det else ""))
            a.setToolTip(r["details"] or "")
            a.setStyleSheet(f"color: {T['text']}; font-size: 13px;")
            tm = QLabel(_nice(r["created_at"])); tm.setStyleSheet(f"color: {T['muted']}; font-size: 11px;")
            c.addWidget(a); c.addWidget(tm)
            h.addLayout(c, 1)
            self.act_list.insertWidget(i, w)
        self._place_avatar()

    def _edit(self):
        if EditProfileDialog(self.db, self.username, self).exec():
            self.refresh()
            win = self.window()
            if hasattr(win, "refresh_identity"):
                win.refresh_identity()
            BakeSyncAlert.show_success(self, "Saved", "Your profile was updated.")

    def _change_password(self):
        from bakesync.auth.change_password_dialog import ChangePasswordDialog
        user = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (self.username,))
        if user and ChangePasswordDialog(self.db, user, self, forced=False).exec():
            BakeSyncAlert.show_success(self, "Password Changed", "Your new password is saved. Use it the next time you sign in.")
            self.refresh()
