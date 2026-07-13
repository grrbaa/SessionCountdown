@echo off
setlocal
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\pip.exe install -r requirements.txt
)
start "SessionCountdown" http://localhost:8080
.venv\Scripts\python.exe -m uvicorn session_countdown.main:app --host 0.0.0.0 --port 8080
