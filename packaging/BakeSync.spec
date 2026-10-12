# PyInstaller recipe for BakeSync.exe. Run packaging\build.bat instead of calling this directly.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "run.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "assets"), "assets")],
    hiddenimports=[],
    excludes=["tkinter", "matplotlib", "pandas", "numpy", "PIL", "reportlab", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BakeSync",
    icon=os.path.join(SPECPATH, "bakesync.ico"),
    console=False,          # windowed app, no black console box
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="BakeSync",
    upx=False,
)
