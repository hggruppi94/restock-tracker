@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during setup.
  pause
  exit /b
)
rem Serve the dashboard at http://localhost:8765 so "Use my location" works
rem and restock info saves to store-notes.json.
start "Tracker web page" /min python server.py
timeout /t 2 >nul
start "" "http://localhost:8765/index.html"
python checker.py --loop
pause
