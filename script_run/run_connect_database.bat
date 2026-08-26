@echo off
echo "Start Connect Database.....!"

cd /d "%~dp0"
cd /d "%~dp0.."

set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_FILE=%CD%\main\app\app.py"

"%PYTHON_EXE%" "%SCRIPT_FILE%"

pause