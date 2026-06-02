@echo off
rem -------------------------------------------------
rem  Launch HITEST with pythonw (no console window)
rem -------------------------------------------------

rem Change to the directory of this script
cd /d "%~dp0"

rem Activate a virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

rem Run the application using the window‑less interpreter
rem   - If python is not on the system PATH, replace `pythonw.exe`
rem     with the full path, e.g. "C:\\Python311\\pythonw.exe"
pythonw.exe main.py

rem (optional) pause to keep the window open if you need diagnostics
rem pause
