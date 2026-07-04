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

rem Prefer .venv pythonw, otherwise try system pythonw, then python
if exist .venv\Scripts\pythonw.exe (
    .venv\Scripts\pythonw.exe main.py
) else (
    where pythonw >nul 2>&1
    if errorlevel 0 (
        pythonw main.py
    ) else (
        where python >nul 2>&1
        if errorlevel 1 (
            echo Nenhum interpretador encontrado (pythonw/python). Instale Python e recrie o ambiente .venv se necessario.
            pause
            exit /b 1
        ) else (
            echo pythonw nao encontrado, executando com python (uma janela de console aparecera)...
            python main.py
        )
    )
)
