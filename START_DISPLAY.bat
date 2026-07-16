@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "CONFIG=.display_controller.txt"
set "DISPLAY_CONFIG=.display_name.txt"

if exist "%CONFIG%" set /p CONTROLLER=<"%CONFIG%"
if exist "%DISPLAY_CONFIG%" set /p DISPLAY_NAME=<"%DISPLAY_CONFIG%"

if not defined CONTROLLER (
  echo Enter the controller computer IP address or hostname.
  echo Example: 192.168.1.25
  set /p CONTROLLER=Controller address: 
  if not defined CONTROLLER exit /b 1
  >"%CONFIG%" echo !CONTROLLER!
)

if not defined DISPLAY_NAME (
  set /p DISPLAY_NAME=Display name [Test-PC]: 
  if not defined DISPLAY_NAME set "DISPLAY_NAME=Test-PC"
  >"%DISPLAY_CONFIG%" echo !DISPLAY_NAME!
)

set "URL=http://%CONTROLLER%:8080/display?display_id=%DISPLAY_NAME: =%%"
echo Opening %URL%

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "SessionCountdown Display" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --kiosk "%URL%"
  exit /b 0
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  start "SessionCountdown Display" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --kiosk "%URL%"
  exit /b 0
)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "SessionCountdown Display" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --kiosk "%URL%" --edge-kiosk-type=fullscreen
  exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  start "SessionCountdown Display" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --kiosk "%URL%" --edge-kiosk-type=fullscreen
  exit /b 0
)

start "SessionCountdown Display" "%URL%"
