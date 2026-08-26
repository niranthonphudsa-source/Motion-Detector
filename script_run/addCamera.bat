@echo off
echo Add Camera.....

:: ย้ายไดเรกทอรีไปยังโฟลเดอร์ของโปรเจกต์
cd /d "%~dp0"
cd /d "%~dp0.."
set "PYTHON_EXE=%CD%\venv\Scripts\python.exe"
set "SCRIPT_FILE=%CD%\main\LIB\addCamera.py"

:: รันโปรแกรม Python
"%PYTHON_EXE%" "%SCRIPT_FILE%"

:: ปิดการทำงาน (ถ้าค้างไว้ดู Log/Error ให้ใส่ pause)
pause