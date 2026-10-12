@echo off
:: Builds BakeSync.exe and puts the ready-to-use app in release\BakeSync
:: Requires: pip install -r requirements.txt pyinstaller
setlocal
cd /d "%~dp0.."

echo [1/4] Building BakeSync.exe with PyInstaller...
python -m PyInstaller --noconfirm --clean --distpath packaging\dist --workpath packaging\build packaging\BakeSync.spec
if errorlevel 1 goto :error

echo [2/4] Copying app to release\BakeSync (existing data\ folder is kept)...
robocopy "packaging\dist\BakeSync" "release\BakeSync" /MIR /XD data /XF config.local.json "Create Desktop Shortcut.bat" config.example.json /NFL /NDL /NJH /NJS /NP
if %ERRORLEVEL% GEQ 8 goto :error
copy /Y "config.example.json" "release\BakeSync\" >nul
copy /Y "packaging\Create Desktop Shortcut.bat" "release\BakeSync\" >nul

echo [3/4] Preparing data folder...
:: The development database (data\) is never copied: a new install always starts empty.
if not exist "release\BakeSync\data\bakesync.db" (
    echo        No database yet: BakeSync will create a fresh one with the default accounts on first start.
) else (
    echo        Existing app data found - left untouched.
)
if exist "config.local.json" if not exist "release\BakeSync\config.local.json" copy /Y "config.local.json" "release\BakeSync\" >nul

echo [4/4] Creating release\BakeSync.lnk shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$app = (Resolve-Path 'release\BakeSync').Path;" ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Resolve-Path 'release').Path + '\BakeSync.lnk');" ^
  "$s.TargetPath = $app + '\BakeSync.exe'; $s.WorkingDirectory = $app;" ^
  "$s.IconLocation = $app + '\BakeSync.exe,0'; $s.Description = 'BakeSync - Bakery Management System'; $s.Save()"

echo.
echo Done! Open the app with release\BakeSync.lnk (or release\BakeSync\BakeSync.exe).
exit /b 0

:error
echo.
echo BUILD FAILED - see the messages above.
exit /b 1
