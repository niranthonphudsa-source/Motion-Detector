@echo off
echo "Start Connect Database.....!"

cd /d "%~dp0"
cd..

call venv\Scripts\activate.bat

python main\app\app.py

pause