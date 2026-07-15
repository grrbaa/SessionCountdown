@echo off
cd /d "%~dp0"
del /q .display_controller.txt 2>nul
del /q .display_name.txt 2>nul
echo Display configuration cleared.
echo Run START_DISPLAY.bat to enter a new controller address and display name.
pause
