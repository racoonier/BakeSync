"""One look for every dropdown (QComboBox) in BakeSync.

Many screens set their own combo styles, so instead of editing each one, an
application-wide event filter restyles every QComboBox the first time it is
polished. Widget-level styles win over app-level ones in Qt, which is why the
theme is applied to each combo directly.
"""
import os

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QComboBox, QListView

from bakesync.paths import IMAGES_DIR

_ARROW = os.path.join(IMAGES_DIR, "brown_arrow.svg").replace("\\", "/")

COMBO_STYLE = f"""
QComboBox {{
    background-color: #FFFFFF;
    border: 1px solid #D6CCC2;
    border-radius: 8px;
    padding: 5px 26px 5px 10px;
    font-family: 'Segoe UI';
    font-size: 13px;
    color: #1F2937;
    min-height: 22px;
}}
QComboBox:hover {{ border: 1px solid #A0785A; background-color: #FFFCF9; }}
QComboBox:focus, QComboBox:on {{ border: 1.5px solid #693903; }}
QComboBox:disabled {{ background-color: #F3F4F6; color: #9CA3AF; border: 1px solid #E5E7EB; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
}}
QComboBox::down-arrow {{ image: url("{_ARROW}"); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    border: 1px solid #D6CCC2;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    color: #1F2937;
    font-family: 'Segoe UI';
    font-size: 13px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 30px;
    padding: 4px 10px;
    border-radius: 6px;
    color: #1F2937;
}}
QComboBox QAbstractItemView::item:hover {{ background-color: #F5ECE5; color: #693903; }}
QComboBox QAbstractItemView::item:selected {{ background-color: #EBDCCF; color: #693903; }}
"""


class _ComboThemer(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish and isinstance(obj, QComboBox) and not obj.property("_bs_themed"):
            obj.setProperty("_bs_themed", True)
            if not obj.isEditable():
                # A plain list view lets the ::item rules above apply on Windows
                obj.setView(QListView())
            obj.setStyleSheet(COMBO_STYLE)
            # Combos given a fixed width elsewhere: widen them if the longest item would be cut off
            if obj.maximumWidth() < 16777215 and obj.count():
                fm = obj.fontMetrics()
                needed = max(fm.horizontalAdvance(obj.itemText(i)) for i in range(obj.count())) + 52
                if needed > obj.maximumWidth():
                    obj.setFixedWidth(needed)
        return False


_themer = None


def install_combo_theme(app):
    """Call once after creating the QApplication."""
    global _themer
    if _themer is None:
        _themer = _ComboThemer(app)
        app.installEventFilter(_themer)
