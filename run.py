"""Start BakeSync from source:  python run.py
(Also the entry point PyInstaller uses for BakeSync.exe.)"""
import os
import sys

from bakesync import paths

if paths.FROZEN:
    # The packaged app has no console window, so keep printed errors in data/bakesync.log
    _log = open(os.path.join(paths.DATA_DIR, "bakesync.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log

from bakesync.main import main

if __name__ == "__main__":
    main()
