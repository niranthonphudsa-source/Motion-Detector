@echo off
setlocal EnableDelayedExpansion

:: ---------------------------------------------------------
:: การตั้งค่าพื้นฐาน (Configuration)
:: ---------------------------------------------------------
set "PROJECT_TITLE=YOLO Vision Application"
set "MAIN_SCRIPT=main.py"
set "VENV_DIR=venv"
set "LOG_DIR=logs"

:: สร้างโฟลเดอร์ Log ถ้ายังไม่มี
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\app_run.log"

:: เซ็ตการแสดงผลสี (ใช้รหัส ANSI Color)
set "ESC=esc"
set "COLOR_GREEN=%ESC%[92m"
set "COLOR_RED=%ESC%[91m"
set "COLOR_YELLOW=%ESC%[93m"
set "COLOR_RESET=%ESC%[0m"

:: ---------------------------------------------------------
:: เปลี่ยนชื่อหน้าต่าง และกำหนดตำแหน่งอ้างอิงให้แม่นยำ
:: ---------------------------------------------------------
title %PROJECT_TITLE% - Running

:: ย้ายไปที่โฟลเดอร์ปัจจุบันที่ไฟล์ .bat อยู่
cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

echo %COLOR_GREEN%================================================%COLOR_RESET%
echo %COLOR_GREEN%    Starting %PROJECT_TITLE%                    %COLOR_RESET%
echo %COLOR_GREEN%================================================%COLOR_RESET%
echo [INFO] Working Directory: %CD% | tee -a "%LOG_FILE%"

:: ---------------------------------------------------------
:: ตรวจสอบความพร้อมของระบบ
:: ---------------------------------------------------------
:: 1. ตรวจสอบว่ามีไฟล์ main.py หรือไม่
if not exist "%MAIN_SCRIPT%" (
    echo %COLOR_RED%[ERROR] Main script '%MAIN_SCRIPT%' not found!%COLOR_RESET%
    echo [ERROR] Main script '%MAIN_SCRIPT%' not found! >> "%LOG_FILE%"
    goto :ErrorExit
)

:: 2. ตรวจสอบว่ามี Virtual Environment หรือไม่
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo %COLOR_RED%[ERROR] Virtual environment '%VENV_DIR%' not found or invalid!%COLOR_RESET%
    echo [ERROR] Virtual environment '%VENV_DIR%' not found! >> "%LOG_FILE%"
    goto :ErrorExit
)

:: ---------------------------------------------------------
:: เริ่มการทำงาน (Execution)
:: ---------------------------------------------------------
echo %COLOR_YELLOW%[INFO] Activating Virtual Environment...%COLOR_RESET% | tee -a "%LOG_FILE%"
call "%VENV_DIR%\Scripts\activate.bat"

echo %COLOR_YELLOW%[INFO] Launching Python Application...%COLOR_RESET% | tee -a "%LOG_FILE%"
echo ------------------------------------------------------

:: รันโปรแกรม Python พร้อมส่งข้อความออกทั้งหน้าจอและไฟล์ Log 
:: (2>&1 คือจับทั้ง Output ปกติและข้อความ Error ลง Log ด้วย)
python "%MAIN_SCRIPT%" 2>&1 | tee -a "%LOG_FILE%"

:: ---------------------------------------------------------
:: ตรวจสอบสถานะเมื่อโปรแกรมปิด/แครช
:: ---------------------------------------------------------
if %errorlevel% neq 0 (
    echo ------------------------------------------------------
    echo %COLOR_RED%[CRITICAL] Application crashed or terminated with error (Code: %errorlevel%).%COLOR_RESET%
    echo [CRITICAL] Application crashed (Code: %errorlevel%). >> "%LOG_FILE%"
    goto :ErrorExit
)

echo ------------------------------------------------------
echo %COLOR_GREEN%[SUCCESS] Application exited gracefully.%COLOR_RESET%
echo [SUCCESS] Application exited gracefully. >> "%LOG_FILE%"
pause
exit /b 0

:: ---------------------------------------------------------
:: กรณีเกิดข้อผิดพลาด
:: ---------------------------------------------------------
:ErrorExit
echo %COLOR_RED%================================================%COLOR_RESET%
echo %COLOR_RED%    System encountered an error.                %COLOR_RESET%
echo %COLOR_RED%    Check the logs at: %LOG_FILE%               %COLOR_RESET%
echo %COLOR_RED%================================================%COLOR_RESET%
pause
exit /b 1