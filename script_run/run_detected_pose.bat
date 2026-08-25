@echo off
echo "Start Connect Main Programe!"

cd /d "%~dp0"
cd..

call venv\Scripts\activate.bat

@REM echo.
@REM echo ===================================================
@REM echo [2/3] Starting Time Logger in Background...
@REM echo ===================================================
@REM :: รัน logger.py ในหน้าต่างเบื้องหลัง/แยกหน้าต่าง โดยไม่หยุดรอ
@REM start "Time Logger" /min python main\display_error_reset.py



echo "Start Pose Detect"
python main\main.py

:: เมื่อปิด main.py ให้ปิดหน้าต่าง logger.py ตามไปด้วยอัตโนมัติ
@REM taskkill /FI "WINDOWTITLE eq Time Logger*" /F > nul 2>&1

pause


@REM @echo off
@REM setlocal
@REM chcp 65001 > nul 


@REM REM ==================================================
@REM REM กำหนด path ของโปรเจกต์
@REM REM ==================================================
@REM cd /d  "%~dp0"
@REM cd ..
@REM set "PROJECT_DIR=%CD%"
@REM set "SCRIPT_DIR=%PROJECT_DIR%\main"
@REM set "SCRIPT_FILE=%SCRIPT_DIR%\main.py"


@REM REM ==================================================
@REM REM ใช้ Python จาก .venv1
@REM REM ==================================================
@REM set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"

@REM REM ==================================================
@REM REM เพิ่ม path สำหรับ import module
@REM REM - root project
@REM REM - โฟลเดอร์ 00_setting
@REM REM ==================================================
@REM set "PYTHONPATH=%PROJECT_DIR%\setting\config.yml%PYTHONPATH%"


@REM REM ==================================================
@REM REM ตรวจสอบไฟล์สำคัญ
@REM REM ==================================================
@REM if not exist "%PYTHON_EXE%" (
@REM     echo ERROR: ไม่พบ Python interpreter
@REM     echo %PYTHON_EXE%
@REM     echo.
@REM     pause
@REM     exit /b 1
@REM )

@REM if not exist "%SCRIPT_FILE%" (
@REM     echo ERROR: ไม่พบไฟล์ script
@REM     echo %SCRIPT_FILE%
@REM     echo.
@REM     pause
@REM     exit /b 1
@REM )

@REM REM ==================================================
@REM REM แสดงข้อมูลก่อนรัน
@REM REM ==================================================
@REM echo ==========================================
@REM echo Project Dir : %PROJECT_DIR%
@REM echo Python Used : %PYTHON_EXE%
@REM echo Script File : %SCRIPT_FILE%
@REM echo PYTHONPATH  : %PYTHONPATH%
@REM echo ==========================================
@REM echo.

@REM REM ==================================================
@REM REM เข้าโฟลเดอร์ script ก่อนรัน
@REM REM ==================================================
@REM cd /d "%SCRIPT_DIR%"

@REM REM ==================================================
@REM REM รันโปรแกรม
@REM REM ==================================================
@REM "%PYTHON_EXE%" main.py

@REM REM ==================================================
@REM REM แสดง exit code
@REM REM ==================================================
@REM set "EXIT_CODE=%ERRORLEVEL%"

@REM echo.
@REM echo ==========================================
@REM echo Program finished with exit code: %EXIT_CODE%
@REM echo ==========================================
@REM pause

@REM endlocal