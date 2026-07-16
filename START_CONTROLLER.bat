@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo               SESSION COUNTDOWN CONTROLLER
echo ============================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3 from https://www.python.org/downloads/
  echo During installation, select "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)

echo Checking application dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Controller: http://localhost:8080
echo Network displays connect to: http://THIS-PC-IP:8080/display
echo.
start "SessionCountdown Controller" http://localhost:8080
".venv\Scripts\python.exe" -m uvicorn session_countdown.main:app --host 0.0.0.0 --port 8080
exit /b %errorlevel%

:fail
echo.
echo SessionCountdown could not start. Review the message above.
pause
exit /b 1
