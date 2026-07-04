@echo off
rem Change to the directory of this script
cd /d "%~dp0"

rem Activate the virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

rem Prefer .venv python, otherwise use system python if present
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe main.py
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python nao encontrado. Instale Python ou crie um ambiente virtual .venv
        pause
        exit /b 1
    ) else (
        python main.py
    )
)

rem Pause to keep the window open after the program exits
pause
