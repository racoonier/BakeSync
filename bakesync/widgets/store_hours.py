"""Store hours: a weekly schedule (open/close time per day, or closed), closed
days such as holidays, staying open longer today, and an End of Day reminder.

Saved in app_settings:
    hours_0 .. hours_6      "06:00-18:00" or "closed"   (0 = Monday)
    closed_dates            "2026-12-25,2027-01-01"
    closing_extend_date/_time   today's later closing time
    closing_reminder_min    minutes before closing to show End of Day tasks
Older databases only have closing_time; it is used as every day's closing time."""
from datetime import date, datetime, time, timedelta

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QTimeEdit, QCheckBox, QGridLayout, QDateEdit, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, QTime, QDate, QTimer
from PyQt6.QtGui import QFont

from bakesync.core.audit import log_activity
from bakesync.widgets.ui import (THEME as T, InfoIcon, ToggleSwitch, button, card, title_row, icon_label,
                               svg_icon, svg_pixmap)

DEFAULT_OPEN, DEFAULT_CLOSING = "06:00", "18:00"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BROWN, BROWN_DARK, MID, DARK, BORDER = "#6B3F27", "#693903", "#64748B", "#1F2937", "#E8E2D9"


def _t(text, fallback):
    try:
        h, m = (int(x) for x in text.split(":"))
        return time(h, m)
    except (ValueError, AttributeError):
        return fallback


def default_closing(db):
    return db.get_setting("closing_time", DEFAULT_CLOSING)


def day_hours(db, weekday):
    """(open, close) as datetime.time for a weekday, or None if closed that day."""
    value = db.get_setting(f"hours_{weekday}")
    if value == "closed":
        return None
    if not value:
        return _t(DEFAULT_OPEN, time(6, 0)), _t(default_closing(db), time(18, 0))
    o, c = (value.split("-") + [DEFAULT_CLOSING])[:2]
    return _t(o, time(6, 0)), _t(c, time(18, 0))


def closed_dates(db):
    return sorted(d for d in (db.get_setting("closed_dates", "") or "").split(",") if d)


def is_open_on(db, d):
    return d.isoformat() not in closed_dates(db) and day_hours(db, d.weekday()) is not None


def is_extended_today(db):
    return db.get_setting("closing_extend_date") == date.today().isoformat()


def opening_time_today(db):
    h = day_hours(db, date.today().weekday())
    return h[0] if h else _t(DEFAULT_OPEN, time(6, 0))


def closing_time_today(db):
    """Today's closing time (today's extension wins over the schedule)."""
    if is_extended_today(db):
        return _t(db.get_setting("closing_extend_time"), time(18, 0))
    h = day_hours(db, date.today().weekday())
    return h[1] if h else _t(default_closing(db), time(18, 0))


def reminder_minutes(db):
    try:
        return int(db.get_setting("closing_reminder_min", "30"))
    except ValueError:
        return 30


def end_of_day_from(db):
    """From this time on, the Dashboard shows the End of Day tasks."""
    start = datetime.combine(date.today(), closing_time_today(db)) - timedelta(minutes=reminder_minutes(db))
    return start.time() if start.date() == date.today() else time(0, 0)


def extend_today(db, hours=1):
    """Push today's closing time later (can be pressed more than once)."""
    current = datetime.combine(date.today(), closing_time_today(db)) + timedelta(hours=hours)
    if current.date() != date.today():
        current = datetime.combine(date.today(), time(23, 59))
    db.set_setting("closing_extend_date", date.today().isoformat())
    db.set_setting("closing_extend_time", current.strftime("%H:%M"))


def fmt(t):
    return datetime.combine(date.today(), t).strftime("%I:%M %p").lstrip("0")


def _in(minutes):
    h, m = divmod(max(0, int(minutes)), 60)
    return f"{h} h {m} min" if h else f"{m} min"


def store_status(db):
    """(is_open, title, detail) for right now."""
    now = datetime.now()
    today = now.date()
    if today.isoformat() in closed_dates(db):
        return False, "Closed today", "Today is marked as a closed day (holiday)."
    if day_hours(db, today.weekday()) is None:
        return False, "Closed today", f"The store is closed every {DAYS[today.weekday()]}."
    o, c = opening_time_today(db), closing_time_today(db)
    if now.time() < o:
        mins = (datetime.combine(today, o) - now).seconds // 60
        return False, "Not open yet", f"Opens at {fmt(o)} (in {_in(mins)}), closes at {fmt(c)}."
    if now.time() < c:
        mins = (datetime.combine(today, c) - now).seconds // 60
        extra = "  (staying open longer today)" if is_extended_today(db) else ""
        return True, "Open now", f"Closes at {fmt(c)} — in {_in(mins)}{extra}."
    return False, "Closed for today", f"Closed at {fmt(c)}. Don't forget the End of Day tasks on the Dashboard."


TIME_CHOICES = [f"{h:02d}:{m:02d}" for h in range(4, 24) for m in (0, 30)] + ["23:59"]


def _label(hhmm):
    return datetime.strptime(hhmm, "%H:%M").strftime("%I:%M %p").lstrip("0")


class StoreHoursWidget(QWidget):
    """Full Store Hours page inside Settings."""

    def __init__(self, db, current_user=""):
        super().__init__()
        self.db = db
        self.current_user = current_user or "Unknown"
        self.setStyleSheet(f"background: {T['cream']};")
        self._build()
        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.isVisible() and self._refresh_status())
        self.timer.start(60000)

    def stop_timers(self):
        self.timer.stop()

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()

    def _time_combo(self):
        cb = QComboBox()
        for t in TIME_CHOICES:
            cb.addItem(_label(t), t)
        cb.setFixedHeight(34); cb.setMinimumWidth(118)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        return cb

    @staticmethod
    def _set_combo(cb, t):
        hhmm = t.strftime("%H:%M")
        i = cb.findData(hhmm)
        if i < 0:                       # not on the half hour: add it so nothing is lost
            cb.addItem(_label(hhmm), hhmm); i = cb.count() - 1
        cb.setCurrentIndex(i)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(32, 16, 32, 16); root.setSpacing(14)

        # right now
        self.status_card = QFrame(); self.status_card.setObjectName("status")
        sl = QHBoxLayout(self.status_card); sl.setContentsMargins(20, 14, 18, 14); sl.setSpacing(16)
        self.st_icon = QLabel(); self.st_icon.setFixedSize(54, 54); self.st_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self.st_icon)
        col = QVBoxLayout(); col.setSpacing(2)
        self.st_title = QLabel(""); self.st_title.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold))
        self.st_detail = QLabel(""); self.st_detail.setStyleSheet(f"color: {T['text']}; font-size: 13px;")
        col.addWidget(self.st_title); col.addWidget(self.st_detail)
        sl.addLayout(col, 1)
        ext = QVBoxLayout(); ext.setSpacing(6)
        er_t = QHBoxLayout(); er_t.setSpacing(4)
        el = QLabel("Stay open longer today"); el.setStyleSheet(f"color: {T['text']}; font-size: 12px; font-weight: 600;")
        er_t.addWidget(el)
        er_t.addWidget(InfoIcon("Open later than usual today only. Tomorrow goes back to the normal schedule by itself.",
                                "Stay open longer"))
        er_t.addStretch()
        ext.addLayout(er_t)
        er = QHBoxLayout(); er.setSpacing(6)
        for text, hours in (("+30 min", 0.5), ("+1 hour", 1), ("+2 hours", 2)):
            b = button(text, "secondary", icon="clock", h=34)
            b.clicked.connect(lambda _, n=hours: self._extend(n))
            er.addWidget(b)
        ext.addLayout(er)
        self.reset_btn = button("Back to normal hours", "ghost", icon="undo", h=28)
        self.reset_btn.clicked.connect(self._clear_extension)
        ext.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignRight)
        sl.addLayout(ext)
        root.addWidget(self.status_card)

        row = QHBoxLayout(); row.setSpacing(14)

        # weekly schedule
        week = card(14, name="week")
        wl = QVBoxLayout(week); wl.setContentsMargins(20, 14, 20, 14); wl.setSpacing(6)
        t, _ = title_row("Weekly schedule", icon="calendar", size=14, color=T["brown_dark"],
                         info="Turn a day OFF if the store is closed that day. Pick the opening and closing time for each open day, "
                              "then click Save.")
        wl.addWidget(t)
        self.day_rows = []
        today = date.today().weekday()
        for i, name in enumerate(DAYS):
            r = QFrame(); r.setObjectName("dr")
            r.setStyleSheet(f"QFrame#dr {{ background: {T['cream'] if i == today else 'transparent'}; border-radius: 8px; }}")
            h = QHBoxLayout(r); h.setContentsMargins(8, 3, 8, 3); h.setSpacing(10)
            lbl = QLabel(name + ("  (today)" if i == today else ""))
            lbl.setFixedWidth(130)
            lbl.setStyleSheet(f"color: {T['text']}; font-size: 13px; font-weight: {'bold' if i == today else 600};")
            sw = ToggleSwitch()
            state = QLabel("Open"); state.setFixedWidth(50)
            o, c = self._time_combo(), self._time_combo()
            to = QLabel("to"); to.setStyleSheet(f"color: {T['mid']}; font-size: 12px;")

            def toggled(on, a=o, b=c, s=state, tl=to):
                a.setVisible(on); b.setVisible(on); tl.setVisible(on)
                s.setText("Open" if on else "Closed")
                s.setStyleSheet(f"color: {T['green'] if on else T['muted']}; font-size: 12px; font-weight: 600;")
            sw.toggled.connect(toggled)
            for w in (lbl, sw, state, o, to, c):
                h.addWidget(w)
            h.addStretch()
            wl.addWidget(r)
            self.day_rows.append((sw, o, c, toggled))
        wb = QHBoxLayout(); wb.setSpacing(8)
        copy = button("Copy Monday to every day", "ghost", icon="copy", h=36)
        copy.clicked.connect(self._copy_monday)
        wb.addWidget(copy); wb.addStretch()
        self.week_msg = QLabel(""); self.week_msg.setStyleSheet(f"color: {T['green']}; font-size: 12px;")
        wb.addWidget(self.week_msg)
        save = button("Save schedule", "primary", icon="check", h=38)
        save.clicked.connect(self._save_week)
        wb.addWidget(save)
        wl.addSpacing(4)
        wl.addLayout(wb)
        row.addWidget(week, 3)

        side = QVBoxLayout(); side.setSpacing(14)
        # closed days
        hol = card(14, name="hol")
        hl = QVBoxLayout(hol); hl.setContentsMargins(20, 14, 20, 14); hl.setSpacing(8)
        t, _ = title_row("Closed days", icon="calendar_x", size=14, color=T["brown_dark"],
                         info="Holidays or days off. On these days the Dashboard will not remind you to close the store.")
        hl.addWidget(t)
        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self.hol_date = QDateEdit(); self.hol_date.setCalendarPopup(True); self.hol_date.setDisplayFormat("MMM d, yyyy")
        self.hol_date.setDate(QDate.currentDate()); self.hol_date.setMinimumDate(QDate.currentDate()); self.hol_date.setFixedHeight(36)
        self.hol_date.setStyleSheet(f"QDateEdit {{ border: 1px solid #D6CCC2; border-radius: 8px; padding: 0 10px; font-size: 13px; color: {T['text']}; background: white; }}")
        add_row.addWidget(self.hol_date, 1)
        add = button("Add", "primary", icon="plus", h=36)
        add.clicked.connect(self._add_holiday)
        add_row.addWidget(add)
        hl.addLayout(add_row)
        self.hol_list = QVBoxLayout(); self.hol_list.setSpacing(4)
        hl.addLayout(self.hol_list)
        side.addWidget(hol)

        # reminder
        rem = card(14, name="rem")
        rl = QVBoxLayout(rem); rl.setContentsMargins(20, 14, 20, 14); rl.setSpacing(8)
        t, _ = title_row("End of Day reminder", icon="bell", size=14, color=T["brown_dark"],
                         info="When to show the closing tasks on the Dashboard: close the POS, count the cash, "
                              "and decide what to do with leftover bread.")
        rl.addWidget(t)
        rr = QHBoxLayout(); rr.setSpacing(8)
        rr.addWidget(QLabel("Remind me"))
        self.rem_combo = QComboBox()
        for text, mins in (("at closing time", 0), ("15 minutes before closing", 15),
                           ("30 minutes before closing", 30), ("1 hour before closing", 60)):
            self.rem_combo.addItem(text, mins)
        self.rem_combo.setFixedHeight(36); self.rem_combo.setMinimumWidth(210)
        self.rem_combo.currentIndexChanged.connect(self._save_reminder)
        rr.addWidget(self.rem_combo); rr.addStretch()
        rl.addLayout(rr)
        side.addWidget(rem)
        side.addStretch()
        row.addLayout(side, 2)
        root.addLayout(row, 1)

    # ── data ──────────────────────────────────────────────────────────────
    def refresh(self):
        for i, (sw, o, c, toggled) in enumerate(self.day_rows):
            h = day_hours(self.db, i)
            oh, ch = h if h else (_t(DEFAULT_OPEN, time(6, 0)), _t(default_closing(self.db), time(18, 0)))
            self._set_combo(o, oh); self._set_combo(c, ch)
            sw.setChecked(h is not None)
            toggled(h is not None)
        self.rem_combo.blockSignals(True)
        idx = self.rem_combo.findData(reminder_minutes(self.db))
        self.rem_combo.setCurrentIndex(idx if idx >= 0 else 2)
        self.rem_combo.blockSignals(False)
        self._load_holidays()
        self._refresh_status()

    def _refresh_status(self):
        is_open, title, detail = store_status(self.db)
        bg, border, fg, icon = ((T["green_bg"], "#BFE3CB", T["green"], "store") if is_open
                                else ("#F4F1EE", T["line"], "#6B5E54", "moon"))
        self.status_card.setStyleSheet(f"QFrame#status {{ background: {bg}; border: 1px solid {border}; border-radius: 16px; }}"
                                       "QLabel { background: transparent; border: none; }")
        self.st_icon.setPixmap(svg_pixmap(icon, "white", 28))
        self.st_icon.setStyleSheet(f"background: {fg}; border-radius: 27px;")
        self.st_title.setText(title); self.st_title.setStyleSheet(f"color: {fg};")
        self.st_detail.setText(detail)
        self.reset_btn.setVisible(is_extended_today(self.db))

    def _load_holidays(self):
        while self.hol_list.count():
            it = self.hol_list.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        upcoming = [d for d in closed_dates(self.db) if d >= date.today().isoformat()]
        if not upcoming:
            l = QLabel("No closed days yet."); l.setStyleSheet(f"color: {T['muted']}; font-size: 12px;")
            self.hol_list.addWidget(l)
        for d in upcoming:
            w = QFrame(); w.setObjectName("chip")
            w.setStyleSheet(f"QFrame#chip {{ background: {T['cream']}; border: 1px solid {T['line']}; border-radius: 9px; }}")
            h = QHBoxLayout(w); h.setContentsMargins(10, 4, 4, 4); h.setSpacing(8)
            h.addWidget(icon_label("calendar_x", T["brown"], 15))
            l = QLabel(date.fromisoformat(d).strftime("%A, %B %d, %Y")); l.setStyleSheet(f"color: {T['text']}; font-size: 13px;")
            rm = QPushButton(); rm.setIcon(svg_icon("x", T["red"], 14)); rm.setFixedSize(28, 28)
            rm.setCursor(Qt.CursorShape.PointingHandCursor); rm.setToolTip("Remove this closed day")
            rm.setStyleSheet(f"QPushButton {{ border: none; border-radius: 14px; background: transparent; }} QPushButton:hover {{ background: {T['red_bg']}; }}")
            rm.clicked.connect(lambda _, x=d: self._remove_holiday(x))
            h.addWidget(l); h.addStretch(); h.addWidget(rm)
            self.hol_list.addWidget(w)

    # ── actions ───────────────────────────────────────────────────────────
    def _extend(self, hours):
        extend_today(self.db, hours)
        log_activity(self.db, self.current_user, "store hours changed", "system",
                     f"Open longer today, until {fmt(closing_time_today(self.db))}")
        self._refresh_status()

    def _clear_extension(self):
        self.db.set_setting("closing_extend_date", "")
        log_activity(self.db, self.current_user, "store hours changed", "system", "Back to normal closing time today")
        self._refresh_status()

    def _copy_monday(self):
        sw0, o0, c0, _ = self.day_rows[0]
        for sw, o, c, toggled in self.day_rows[1:]:
            sw.setChecked(sw0.isChecked()); toggled(sw0.isChecked())
            o.setCurrentIndex(o.findData(o0.currentData())); c.setCurrentIndex(c.findData(c0.currentData()))
        self.week_msg.setText("Copied. Click Save to keep it.")
        self.week_msg.setStyleSheet(f"color: {T['amber']}; font-size: 12px;")

    def _save_week(self):
        for i, (sw, o, c, _) in enumerate(self.day_rows):
            if sw.isChecked() and c.currentData() <= o.currentData():
                self.week_msg.setText(f"{DAYS[i]}: closing must be later than opening.")
                self.week_msg.setStyleSheet(f"color: {T['red']}; font-size: 12px;")
                return
        summary = []
        for i, (sw, o, c, _) in enumerate(self.day_rows):
            value = f"{o.currentData()}-{c.currentData()}" if sw.isChecked() else "closed"
            self.db.set_setting(f"hours_{i}", value)
            summary.append(f"{DAYS[i][:3]} {value}")
        if self.day_rows[0][0].isChecked():
            self.db.set_setting("closing_time", self.day_rows[0][2].currentData())   # kept for older screens
        log_activity(self.db, self.current_user, "store hours changed", "system", "Weekly schedule: " + ", ".join(summary))
        self.week_msg.setText("Saved.")
        self.week_msg.setStyleSheet(f"color: {T['green']}; font-size: 12px; font-weight: 600;")
        self._refresh_status()

    def _add_holiday(self):
        d = self.hol_date.date().toPyDate().isoformat()
        days = closed_dates(self.db)
        if d not in days:
            self.db.set_setting("closed_dates", ",".join(sorted(days + [d])))
            log_activity(self.db, self.current_user, "store hours changed", "system", f"Closed day added: {d}")
        self._load_holidays(); self._refresh_status()

    def _remove_holiday(self, d):
        self.db.set_setting("closed_dates", ",".join(x for x in closed_dates(self.db) if x != d))
        log_activity(self.db, self.current_user, "store hours changed", "system", f"Closed day removed: {d}")
        self._load_holidays(); self._refresh_status()

    def _save_reminder(self):
        self.db.set_setting("closing_reminder_min", self.rem_combo.currentData())
        log_activity(self.db, self.current_user, "store hours changed", "system", f"End of Day reminder: {self.rem_combo.currentText()}")
