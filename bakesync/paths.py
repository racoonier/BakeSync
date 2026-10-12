"""Every file location BakeSync uses, in one place.

Works both when run from source (python run.py) and as the packaged
BakeSync.exe, where bundled assets are read-only and user data must live
in a writable folder next to the executable.
"""
import os
import sys

FROZEN = getattr(sys, "frozen", False)

if FROZEN:
    APP_ROOT = os.path.dirname(sys.executable)            # folder containing BakeSync.exe
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_ROOT)        # bundled, read-only files
else:
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    BUNDLE_DIR = APP_ROOT

# Read-only assets (icons, logos)
ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")

# Writable user data (database, backups, product photos)
DATA_DIR = os.environ.get("BAKESYNC_DATA_DIR") or os.path.join(APP_ROOT, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
PRODUCT_IMAGES_DIR = os.path.join(DATA_DIR, "product_images")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

CONFIG_FILE = os.path.join(APP_ROOT, "config.local.json")

for _d in (DATA_DIR, BACKUP_DIR, PRODUCT_IMAGES_DIR, CACHE_DIR):
    os.makedirs(_d, exist_ok=True)


def product_image(stored):
    """Full path of a product photo from the value saved in products.image_path,
    or None if there is no photo. Only the file name is used, so photos keep
    working after the app folder is moved to another computer."""
    if not stored:
        return None
    path = os.path.join(PRODUCT_IMAGES_DIR, os.path.basename(str(stored).replace("\\", "/")))
    return path if os.path.exists(path) else None
