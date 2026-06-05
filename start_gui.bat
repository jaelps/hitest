@echo off
rem -------------------------------------------------
rem  Launch HITEST with pythonw (no console window)
rem -------------------------------------------------

rem Change to the directory of this script
cd /d "%~dp0"

rem Activate a virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

rem Run the application using the window‑less interpreter
.venv\Scripts\pythonw.exe main.py

rem (optional) pause to keep the window open if you need diagnostics
rem pause
