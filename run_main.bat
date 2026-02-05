@echo off
REM ==========================================================
REM Windows launcher for running the package in src/
REM Place this file in the project root next to main.py
REM Usage: double-click or run from PowerShell/CMD: .\run_main.bat [args]
REM ==========================================================

:: 1) Navigate to the folder where this script lives
cd /d "%~dp0"

:: 2) Activate local virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment: venv\Scripts\activate.bat
    call "venv\Scripts\activate.bat"
) else (
    echo No virtual environment found at "%~dp0venv\Scripts\activate.bat"
    echo Continuing with system Python (ensure correct Python is on PATH)...
)

:: 3) Ensure Python can import packages from src/ and run module
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
echo Using PYTHONPATH=%~dp0src
python -m titan_guardian %*

:: Optional: Verify it finished (visible when run manually)
echo Script finished.

:: Force the window to close immediately when launched by double-click
exit
