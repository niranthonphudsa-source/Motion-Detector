@echo off
setlocal

REM ==================================================
REM กำหนด path ของโปรเจกต์
REM ==================================================
set "PROJECT_DIR=C:\Users\Niran_t\Desktop\file_work\ProjectDetection\Motion-Detector"
set "SCRIPT_DIR=%PROJECT_DIR%\script_run"
set "SCRIPT_FILE=%SCRIPT_DIR%venv\Scripts\activate.bat"

REM ==================================================
REM ใช้ Python จาก .venv1
REM ==================================================
set "PYTHON_EXE=%PROJECT_DIR%\main\mian.py"

REM ==================================================
REM เพิ่ม path สำหรับ import module
REM - root project
REM - โฟลเดอร์ 00_setting
REM ==================================================
set "PYTHONPATH=%PROJECT_DIR%;%PROJECT_DIR%\setting\config.json;%PYTHONPATH%"

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
REM เข้าโฟลเดอร์ script ก่อนรัน
REM ==================================================
cd /d "%SCRIPT_DIR%"

REM ==================================================
REM รันโปรแกรม
REM ==================================================
"%PYTHON_EXE%" mian\main.py

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