@echo off
setlocal
:: 1. เปลี่ยน Code Page ให้รองรับภาษาไทย / UTF-8
chcp 65001 > nul


cd /d "%~dp0"
:: ออกจาก Script_Run
cd ..
REM ==================================================
REM กำหนด path ของโปรเจกต์
REM ==================================================
set "PROJECT_DIR=%CD%"
set "SCRIPT_DIR=%PROJECT_DIR%\main"
set "SCRIPT_FILE=%SCRIPT_DIR%\main.py"

REM ==================================================
REM ใช้ Python จาก .venv1
REM ==================================================
set "PYTHON_EXE=%SCRIPT_FILE%"

REM ==================================================
REM เพิ่ม path สำหรับ import module
REM ==================================================
set "PYTHONPATH=%PROJECT_DIR%\setting\config.yaml;%PYTHONPATH%"

REM ==================================================
REM ตรวจสอบไฟล์สำคัญ
REM ==================================================
if not exist "%PYTHON_EXE%" (
    echo ERROR: IS NOT Python interpreter
    echo %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_FILE%" (
    echo ERROR: ไม่พบไฟล์ script
    echo %SCRIPT_FILE%
    echo.
    pause
    exit /b 1
)

REM ==================================================
REM แสดงข้อมูลก่อนรัน
REM ==================================================
echo ==========================================
echo Project Dir : %PROJECT_DIR%
echo Python Used : %PYTHON_EXE%
echo Script File : %SCRIPT_FILE%
echo PYTHONPATH  : %PYTHONPATH%
echo ==========================================
echo.


REM ==================================================
REM รันโปรแกรม
REM ==================================================
python "%PYTHON_EXE%" main\main.py

REM ==================================================
REM แสดง exit code
REM ==================================================
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ==========================================
echo Program finished with exit code: %EXIT_CODE%
echo ==========================================
pause

endlocal