@echo off
echo "Start Help GUI....!"

cd /d "%~dp0.."
set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_FILE=%CD%\main\LIB\help_gui.py"

"%PYTHON_EXE%" "%SCRIPT_FILE%"
pause