@echo off

:: Opens the BakeSync database in the Python sqlite3 console (needs Python 3.12+)
:: %~dp0 = folder ng .bat file (tools\), kaya ..\data ang database folder
SET DB_PATH="%~dp0..\data\bakesync.db"

echo Starting BakeSync SQLite Console...
echo Accessing the database at %DB_PATH%...

python -m sqlite3 %DB_PATH%

PAUSE
