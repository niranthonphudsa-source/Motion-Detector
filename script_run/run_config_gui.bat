@echo off
echo Starting Python Application...

:: ย้ายไดเรกทอรีไปยังโฟลเดอร์ของโปรเจกต์
cd /d "%~dp0"
cd ..
:: เปิดใช้งาน Virtual Environment
call venv\Scripts\activate.bat

:: รันโปรแกรม Python
python main\LIB\config_gui.py

