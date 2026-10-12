"""Audit Log page: who did what, and when, as an easy-to-read timeline.

Rows come from the secure activity log (sign-ins, accounts, sales, voids, prices,
money, system) plus the older stock log. "Check the records" re-computes the hash
chain to prove nothing was changed or deleted outside BakeSync."""
import csv
import os
from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QComboBox, QLineEdit, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QCursor

from bakesync.core.audit import AREAS, WARNING_ACTIONS, verify_log, log_activity
from bakesync.widgets.custom_alerts import BakeSyncAlert
from bakesync.widgets.ui import (THEME as T, InfoIcon, svg_icon, icon_label, button, card, ToggleSwitch)

TYPE_FILTERS = [("All", None, "list"), ("Sign-ins", "signin", "login"), ("Accounts", "account", "user"),
                ("Sales", "sale", "cart"), ("Voids", "void", "ban"), ("Stock & Waste", "stock", "box"),
                ("Prices", "price", "tag"), ("Money", "money", "wallet"), ("System", "system", "settings")]
AREA_STYLE = {"signin": ("login", "#2457A6", "#E8EFFA"), "account": ("user", "#6D28D9", "#EFE9FB"),
              "sale": ("cart", "#2F7D4F", "#E8F4EC"), "void": ("ban", "#B3261E", "#FCEBEA"),
              "stock": ("box", "#92400E", "#FDF1DE"), "waste": ("trash", "#92400E", "#FDF1DE"),
              "price": ("tag", "#0E7490", "#E2F5F8"), "money": ("wallet", "#166534", "#E3F4E8"),
              "system": ("settings", "#4B5563", "#EEF0F2")}
OLD_ACTIONS = {"added": "product added", "restocked": "stock added", "archived": "product archived",
               "restored": "product restored", "price_set": "price changed", "recipe_set": "price changed",
               "voided": "sale voided", "voided_sale": "sale voided", "leftovers decided": "leftovers decided",
               "backup created": "backup made", "database restored": "data restored"}
# action -> what the person did, as part of a sentence
SENTENCE = {
    "signed in": "signed in", "signed out": "signed out", "closed BakeSync": "closed BakeSync",
    "sign-in failed": "typed a wrong password", "account locked": "was locked out after 3 wrong passwords",
    "sign-in blocked": "tried to sign in but was blocked", "password changed": "changed their password",
    "password reset": "reset a password", "account requested": "asked for a new account",
    "account approved": "approved an account", "account rejected": "rejected an account request",
    "account archived": "turned off an account", "account restored": "turned an account back on",
    "account edited": "edited an account", "account added": "added an account", "profile edited": "edited their profile",
    "sale completed": "made a sale", "sale voided": "voided a sale", "POS day closed": "closed the POS for the day",
    "price changed": "changed a price", "product archived": "hid a product", "product restored": "brought back a product",
    "product added": "added a new product", "stock added": "added stock", "waste recorded": "recorded waste",
    "expired stock removed": "removed expired stock", "leftovers decided": "decided on leftover bread",
    "expense added": "added an expense", "cash counted": "counted the cash", "cash short": "counted the cash and it was SHORT",
    "cash count checked": "checked a cash count", "cash count done": "finished a cash count",
    "cash count archived": "archived a cash count", "backup made": "made a backup", "backup copied": "copied a backup to USB",
    "data restored": "restored a backup", "store hours changed": "changed the store hours",
    "records checked": "checked the records", "audit log saved": "saved the audit log",
}


def _time(ts):
    try:
        return datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return str(ts)[11:16]


def _day_title(ts):
    try:
        d = datetime.strptime(str(ts)[:10], "%Y-%m-%d").date()
    except ValueError:
        return "Earlier"
    if d == date.today():
        return "Today"
    if d == date.today() - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%A, %B %d, %Y")


class _Row(QPushButton):
    """One line of the timeline; click to see everything about it."""

    def __init__(self, r, on_click):
        super().__init__()
        warn = r["action"] in WARNING_ACTIONS
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(52)
        self.setStyleSheet(f"QPushButton {{ background: {'#FFF8F7' if warn else 'white'}; border: none; "
                           f"border-bottom: 1px solid {T['line']}; text-align: left; }}"
                           f"QPushButton:hover {{ background: {T['cream']}; }}")
        h = QHBoxLayout(self); h.setContentsMargins(14, 6, 14, 6); h.setSpacing(12)
        icon, fg, bg = AREA_STYLE.get(r["area"], AREA_STYLE["system"])
        if warn:
            icon, fg, bg = "alert", T["red"], T["red_bg"]
        ic = icon_label(icon, fg, 16, bg=bg, box=34, radius=17)
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        h.addWidget(ic)
        who = r["username"] or "System"
        what = SENTENCE.get(r["action"], r["action"])
        det = r["details"] or ""
        det = det if len(det) <= 95 else det[:92] + "..."
        txt = QLabel(f"<b>{who}</b> <span style='color:{T['red'] if warn else T['text']}'>{what}</span>"
                     + (f"<br><span style='color:{T['mid']}; font-size:11px'>{det}</span>" if det else ""))
        txt.setStyleSheet(f"color: {T['text']}; font-size: 13px; background: transparent;")
        txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        h.addWidget(txt, 1)
        tm = QLabel(_time(r["created_at"])); tm.setStyleSheet(f"color: {T['muted']}; font-size: 12px; background: transparent;")
        tm.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        h.addWidget(tm)
        self.clicked.connect(lambda: on_click(r))


class SystemAuditLogsWidget(QWidget):
    PAGE = 200

    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.current_user = current_user
        self.rows = []
        self._type = None
        self._shown = self.PAGE
        self.setStyleSheet(f"background: {T['cream']};")
        self._build()
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.isVisible() and self.load_logs())
        self.timer.start(30000)

    def stop_timers(self):
        self.timer.stop()

    def showEvent(self, e):
        super().showEvent(e)
        self._load_people()
        self.load_logs()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(28, 14, 28, 14); root.setSpacing(10)

        # banner: anything to check today?
        self.banner = QFrame(); self.banner.setObjectName("banner")
        bl = QHBoxLayout(self.banner); bl.setContentsMargins(14, 10, 14, 10); bl.setSpacing(10)
        self.banner_icon = QLabel(); self.banner_icon.setFixedSize(22, 22)
        self.banner_text = QLabel(""); self.banner_text.setStyleSheet("font-size: 13px; background: transparent;")
        self.banner_btn = button("Show them", "danger", icon="filter", h=32)
        self.banner_btn.clicked.connect(lambda: (self.only_warn.setChecked(True), self.when.setCurrentText("Today"), self.load_logs()))
        bl.addWidget(self.banner_icon); bl.addWidget(self.banner_text, 1); bl.addWidget(self.banner_btn)
        root.addWidget(self.banner)

        # today at a glance + tools
        top = QHBoxLayout(); top.setSpacing(8)
        self.glance = {}
        for key, label, icon, color in (("signins", "Sign-ins", "login", T["blue"]), ("failed", "Wrong passwords", "key", T["red"]),
                                        ("sales", "Sales", "cart", T["green"]), ("voids", "Voids", "ban", T["red"]),
                                        ("changes", "Price & account changes", "edit", T["brown"])):
            f = card(12, name="g")
            l = QHBoxLayout(f); l.setContentsMargins(10, 8, 14, 8); l.setSpacing(8)
            l.addWidget(icon_label(icon, color, 16, bg=T["cream_dark"], box=32, radius=16))
            c = QVBoxLayout(); c.setSpacing(0)
            v = QLabel("0"); v.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
            t = QLabel(label + " today"); t.setStyleSheet(f"color: {T['mid']}; font-size: 11px;")
            c.addWidget(v); c.addWidget(t)
            l.addLayout(c)
            self.glance[key] = v
            top.addWidget(f)
        top.addStretch()
        self.check_btn = button("Check the records", "secondary", icon="shield", h=40)
        self.check_btn.clicked.connect(self._check)
        top.addWidget(self.check_btn)
        top.addWidget(InfoIcon("Every record is locked when it is saved. This button makes sure none of them were "
                               "changed or deleted outside BakeSync.", "Check the records"))
        exp = button("Save for Excel", "secondary", icon="download", h=40)
        exp.clicked.connect(self._export)
        top.addWidget(exp)
        root.addLayout(top)

        # filters
        pills = QHBoxLayout(); pills.setSpacing(6)
        self._pills = {}
        for label, area, icon in TYPE_FILTERS:
            b = QPushButton(" " + label.replace("&", "&&")); b.setCheckable(True); b.setFixedHeight(32)
            b.setIcon(svg_icon(icon, T["mid"], 14)); b.setIconSize(QSize(14, 14))
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet(f"QPushButton {{ background: white; color: {T['mid']}; border: 1px solid {T['line']}; border-radius: 16px; "
                            f"padding: 0 12px; font-size: 12px; font-weight: 600; }}"
                            f"QPushButton:checked {{ background: {T['brown']}; color: white; border-color: {T['brown']}; }}")
            b.clicked.connect(lambda _, a=area: self._set_type(a))
            pills.addWidget(b)
            self._pills[area] = (b, icon)
        pills.addStretch()
        root.addLayout(pills)

        f = QHBoxLayout(); f.setSpacing(8)
        self.when = QComboBox(); self.when.addItems(["Today", "Yesterday", "Last 7 days", "Last 30 days", "All time"])
        self.when.setCurrentText("Last 7 days")
        self.person = QComboBox(); self.person.addItem("Everyone")
        for cb, w in ((self.when, 140), (self.person, 160)):
            cb.setFixedHeight(36); cb.setMinimumWidth(w); cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            cb.currentTextChanged.connect(self.load_logs)
        sw = QFrame(); sw.setObjectName("sw")
        sw.setStyleSheet(f"QFrame#sw {{ background: white; border: 1px solid {T['line']}; border-radius: 9px; }}")
        sl = QHBoxLayout(sw); sl.setContentsMargins(10, 0, 6, 0); sl.setSpacing(6)
        sl.addWidget(icon_label("search", T["muted"], 15))
        self.search = QLineEdit(); self.search.setPlaceholderText("Search a name, product or amount")
        self.search.setFixedHeight(34); self.search.setMinimumWidth(230); self.search.setClearButtonEnabled(True)
        self.search.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; font-size: 13px; color: {T['text']}; }}")
        self.search.textChanged.connect(self.load_logs)
        sl.addWidget(self.search)
        warn_box = QHBoxLayout(); warn_box.setSpacing(6)
        self.only_warn = ToggleSwitch(on_color=T["red"])
        self.only_warn.toggled.connect(self.load_logs)
        wl = QLabel("Only things to check"); wl.setStyleSheet(f"color: {T['text']}; font-size: 12px; background: transparent;")
        warn_box.addWidget(self.only_warn); warn_box.addWidget(wl)
        warn_box.addWidget(InfoIcon("Shows only wrong passwords, lockouts, voids, short cash, turned-off accounts, "
                                    "password resets and restores.", "Things to check"))
        f.addWidget(self.when); f.addWidget(self.person); f.addWidget(sw); f.addSpacing(6); f.addLayout(warn_box)
        f.addStretch()
        self.count_lbl = QLabel(""); self.count_lbl.setStyleSheet(f"color: {T['mid']}; font-size: 12px; background: transparent;")
        f.addWidget(self.count_lbl)
        root.addLayout(f)

        # timeline
        box = card(12, name="tl")
        bl2 = QVBoxLayout(box); bl2.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                                  f"QScrollBar:vertical {{ width: 8px; background: transparent; }} QScrollBar::handle:vertical {{ background: {T['line']}; border-radius: 4px; }}")
        self.list_holder = QWidget(); self.list_holder.setStyleSheet("background: white;")
        self.list_lay = QVBoxLayout(self.list_holder); self.list_lay.setContentsMargins(0, 0, 0, 0); self.list_lay.setSpacing(0)
        self.scroll.setWidget(self.list_holder)
        bl2.addWidget(self.scroll)
        root.addWidget(box, 1)
        self._set_type(None, reload=False)

    # ── data ──────────────────────────────────────────────────────────────
    def _load_people(self):
        names = sorted({r[0] for r in self.db.fetch_all(
            "SELECT username FROM activity_log WHERE username IS NOT NULL UNION "
            "SELECT action_by FROM inventory_action_log WHERE action_by IS NOT NULL") if r[0]})
        cur = self.person.currentText()
        self.person.blockSignals(True)
        self.person.clear(); self.person.addItem("Everyone"); self.person.addItems(names)
        self.person.setCurrentText(cur if cur in names else "Everyone")
        self.person.blockSignals(False)

    def _set_type(self, area, reload=True):
        self._type = area
        for a, (b, icon) in self._pills.items():
            b.setChecked(a == area)
            b.setIcon(svg_icon(icon, "white" if a == area else T["mid"], 14))
        if reload:
            self.load_logs()

    def _since(self):
        t = date.today()
        return {"Today": t, "Yesterday": t - timedelta(days=1), "Last 7 days": t - timedelta(days=6),
                "Last 30 days": t - timedelta(days=29)}.get(self.when.currentText(), date(2000, 1, 1)).isoformat()

    def _fetch(self):
        since = self._since()
        until = (date.today() - timedelta(days=1)).isoformat() if self.when.currentText() == "Yesterday" else date.today().isoformat()
        rows = [dict(r, source="log") for r in self.db.fetch_all(
            "SELECT id, created_at, username, action, area, details FROM activity_log "
            "WHERE date(created_at) BETWEEN ? AND ?", (since, until))]
        # older stock log (Inventory, Waste, End of Day) - skip actions the new log already records
        for r in self.db.fetch_all(
                "SELECT id, created_at, action_by, action, item_type, item_name FROM inventory_action_log "
                "WHERE date(created_at) BETWEEN ? AND ?", (since, until)):
            action = OLD_ACTIONS.get(r["action"], r["action"].replace("_", " "))
            if action in ("sale voided", "price changed") and r["created_at"] >= self._log_start():
                continue
            area = "waste" if "waste" in action or "leftover" in action else (
                "system" if r["item_type"] == "system" else "stock")
            rows.append({"id": r["id"], "created_at": r["created_at"], "username": r["action_by"], "action": action,
                         "area": area, "details": r["item_name"] or "", "source": "stock"})
        rows.sort(key=lambda r: r["created_at"] or "", reverse=True)
        return rows

    def _log_start(self):
        if not hasattr(self, "_first"):
            r = self.db.fetch_one("SELECT MIN(created_at) AS m FROM activity_log")
            self._first = r["m"] if r and r["m"] else "9999"
        return self._first

    def load_logs(self, *_):
        if self.db.is_closed():
            return
        self._load_glance()
        rows = self._fetch()
        who = self.person.currentText()
        q = self.search.text().strip().lower()
        if self._type:
            rows = [r for r in rows if r["area"] == self._type or (self._type == "stock" and r["area"] == "waste")]
        if who != "Everyone":
            rows = [r for r in rows if r["username"] == who]
        if q:
            rows = [r for r in rows if q in f"{r['username']} {r['action']} {r['details']}".lower()]
        if self.only_warn.isChecked():
            rows = [r for r in rows if r["action"] in WARNING_ACTIONS]
        self.rows = rows
        self._shown = self.PAGE
        self._render()

    def _render(self):
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        rows = self.rows[:self._shown]
        self.count_lbl.setText(f"{len(self.rows):,} record{'s' if len(self.rows) != 1 else ''}")
        if not rows:
            empty = QWidget(); el = QVBoxLayout(empty); el.setContentsMargins(0, 40, 0, 40)
            el.addWidget(icon_label("check_circle", T["muted"], 36), alignment=Qt.AlignmentFlag.AlignCenter)
            m = QLabel("Nothing found for this choice."); m.setStyleSheet(f"color: {T['muted']}; font-size: 13px;")
            el.addWidget(m, alignment=Qt.AlignmentFlag.AlignCenter)
            self.list_lay.addWidget(empty)
        last_day = None
        for r in rows:
            day = _day_title(r["created_at"])
            if day != last_day:
                h = QLabel(day.upper())
                h.setStyleSheet(f"color: {T['brown']}; background: {T['cream']}; font-size: 11px; font-weight: bold; "
                                f"letter-spacing: 1px; padding: 7px 14px; border-bottom: 1px solid {T['line']};")
                self.list_lay.addWidget(h)
                last_day = day
            self.list_lay.addWidget(_Row(r, self._show_row))
        if len(self.rows) > self._shown:
            more = button(f"Show more ({len(self.rows) - self._shown:,} left)", "ghost", icon="chevron_down", h=40)
            more.clicked.connect(self._more)
            self.list_lay.addWidget(more)
        self.list_lay.addStretch()

    def _more(self):
        self._shown += self.PAGE
        self._render()

    def _load_glance(self):
        def n(sql):
            r = self.db.fetch_one(sql)
            return r[0] if r else 0
        today = "date(created_at) = date('now','localtime')"
        vals = {"signins": n(f"SELECT COUNT(*) FROM activity_log WHERE action = 'signed in' AND {today}"),
                "failed": n(f"SELECT COUNT(*) FROM activity_log WHERE action IN ('sign-in failed','account locked','sign-in blocked') AND {today}"),
                "sales": n(f"SELECT COUNT(DISTINCT created_at) FROM sales WHERE COALESCE(is_voided,0) = 0 AND {today}"),
                "voids": n(f"SELECT COUNT(*) FROM void_logs WHERE {today}"),
                "changes": n(f"SELECT COUNT(*) FROM activity_log WHERE (action = 'price changed' OR area = 'account') AND {today}")}
        for k, v in vals.items():
            self.glance[k].setText(f"{v:,}")
            self.glance[k].setStyleSheet(f"color: {T['red'] if v and k in ('failed', 'voids') else T['text']};")
        warn = n(f"SELECT COUNT(*) FROM activity_log WHERE action IN ({','.join(repr(a) for a in WARNING_ACTIONS)}) AND {today}")
        if warn:
            self.banner.setStyleSheet(f"QFrame#banner {{ background: {T['red_bg']}; border: 1px solid #F1C2BE; border-radius: 10px; }}")
            self.banner_icon.setPixmap(svg_icon("alert", T["red"], 22).pixmap(22, 22))
            self.banner_text.setText(f"<b>{warn} thing{'s' if warn != 1 else ''} to check today</b> "
                                     "(wrong passwords, voids, short cash or account changes).")
            self.banner_text.setStyleSheet(f"color: {T['text']}; font-size: 13px; background: transparent;")
            self.banner_btn.show()
        else:
            self.banner.setStyleSheet(f"QFrame#banner {{ background: {T['green_bg']}; border: 1px solid #BFE3CB; border-radius: 10px; }}")
            self.banner_icon.setPixmap(svg_icon("check_circle", T["green"], 22).pixmap(22, 22))
            self.banner_text.setText("<b>Nothing unusual today.</b> No wrong passwords, voids or short cash.")
            self.banner_text.setStyleSheet(f"color: {T['text']}; font-size: 13px; background: transparent;")
            self.banner_btn.hide()

    # ── actions ───────────────────────────────────────────────────────────
    def _show_row(self, r):
        details = {"When": f"{_day_title(r['created_at'])}, {_time(r['created_at'])}", "Who": r["username"] or "System",
                   "Type": AREAS.get(r["area"], r["area"].capitalize()), "What happened": r["action"].capitalize()}
        if r["details"]:
            details["Details"] = r["details"]
        details["Record"] = f"#{r['id']} ({'secure log' if r['source'] == 'log' else 'stock log'})"
        BakeSyncAlert.show_info(self, "Activity record", "Everything saved about this action:", details=details)

    def _check(self):
        ok, n, bad = verify_log(self.db)
        log_activity(self.db, self.current_user, "records checked", "system",
                     f"{n} records checked - {'all untouched' if ok else f'problem found at record #{bad}'}")
        if ok:
            BakeSyncAlert.show_success(self, "Records are safe",
                                       f"All {n:,} records were checked.\nNone of them were changed or deleted.")
        else:
            BakeSyncAlert.show_error(self, "Records were changed",
                                     f"Record #{bad} (or one just before it) was changed or removed outside BakeSync.\n\n"
                                     "Ask the Administrator to check who had access to the computer, and keep a backup.")
        self.load_logs()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save audit log for Excel",
                                              f"BakeSync_AuditLog_{datetime.now():%Y%m%d}.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["When", "Who", "Type", "What happened", "Details"])
                for r in self.rows:
                    w.writerow([r["created_at"], r["username"] or "System", AREAS.get(r["area"], r["area"]),
                                r["action"], r["details"]])
            log_activity(self.db, self.current_user, "audit log saved", "system", f"{len(self.rows)} records saved to a file")
            BakeSyncAlert.show_success(self, "Saved", f"Saved as:\n{os.path.basename(path)}")
        except OSError as e:
            BakeSyncAlert.show_error(self, "Could not save", str(e))
