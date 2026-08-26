@echo off
echo "Start Config Pin Esp32......!"

cd /d "%~dp0.."
set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_FILE=%CD%\main\setting_esp32\setting_esp32.py"

"%PYTHON_EXE%" "%SCRIPT_FILE%"
pause