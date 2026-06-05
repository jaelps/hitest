@echo off
rem Change to the directory of this script
cd /d "%~dp0"

rem Ensure the virtual environment (if any) is activated
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

rem Run the application using Python
.venv\Scripts\python.exe main.py

rem Pause to keep the window open after the program exits
pause
