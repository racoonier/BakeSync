@echo off
:: Gumagawa ng "BakeSync" shortcut sa Desktop na nakaturo sa BakeSync.exe sa folder na ito.
:: Patakbuhin ulit ito kapag inilipat ang BakeSync folder sa ibang lugar o ibang PC.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\BakeSync.lnk');" ^
  "$s.TargetPath = '%~dp0BakeSync.exe';" ^
  "$s.WorkingDirectory = '%~dp0';" ^
  "$s.IconLocation = '%~dp0BakeSync.exe,0';" ^
  "$s.Description = 'BakeSync - Bakery Management System';" ^
  "$s.Save()"
if %ERRORLEVEL%==0 (echo Desktop shortcut created.) else (echo Could not create the shortcut.)
pause
