@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo Updating SessionCountdown...
git pull origin agent/controller-display-v2
if errorlevel 1 (
  echo.
  echo Update failed. Check the Git message above.
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
)

echo.
echo Update complete.
pause
