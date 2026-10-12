"""Default picture for products without a photo: a simple bread or shopping-bag icon."""
from PyQt6.QtCore import Qt, QByteArray, QRectF
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

_ICONS = {
    # Loaf of bread with scoring lines
    "bread": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <path d="M9 29c0-9.4 10.3-16.5 23-16.5S55 19.6 55 29c0 3.2-2 5.4-4.5 6V49.5A4.5 4.5 0 0 1 46 54H18a4.5 4.5 0 0 1-4.5-4.5V35C11 34.4 9 32.2 9 29z"
              fill="#EBC890" stroke="#7A4A1E" stroke-width="2.6" stroke-linejoin="round"/>
        <path d="M14 35h36" stroke="#7A4A1E" stroke-width="2" stroke-linecap="round" opacity="0.35"/>
        <path d="M23 22.5l4 6.5M31 21l4 6.5M39 22.5l4 6.5" stroke="#7A4A1E" stroke-width="2.6" stroke-linecap="round"/>
    </svg>""",
    # Shopping bag for retail items
    "retail": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <path d="M13 23h38l-2.6 29.2A3.5 3.5 0 0 1 44.9 55H19.1a3.5 3.5 0 0 1-3.5-2.8z"
              fill="#EBC890" stroke="#7A4A1E" stroke-width="2.6" stroke-linejoin="round"/>
        <path d="M24 28v-7a8 8 0 0 1 16 0v7" fill="none" stroke="#7A4A1E" stroke-width="2.6" stroke-linecap="round"/>
        <circle cx="24" cy="29" r="2" fill="#7A4A1E"/><circle cx="40" cy="29" r="2" fill="#7A4A1E"/>
    </svg>""",
}
_cache = {}


def kind_for(product_type):
    return "bread" if (product_type or "bread") == "bread" else "retail"


def default_product_pixmap(width, height, kind="bread"):
    """A transparent width x height pixmap with the default icon centred at about 55% size."""
    kind = kind if kind in _ICONS else "bread"
    key = (width, height, kind)
    if key not in _cache:
        pm = QPixmap(width, height)
        pm.fill(Qt.GlobalColor.transparent)
        side = min(width, height) * 0.55
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(QByteArray(_ICONS[kind].encode("utf-8"))).render(
            painter, QRectF((width - side) / 2, (height - side) / 2, side, side))
        painter.end()
        _cache[key] = pm
    return _cache[key]
