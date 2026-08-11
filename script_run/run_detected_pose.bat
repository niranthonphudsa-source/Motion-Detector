@echo off
echo "Start Connect Main Programe!"

cd /d "%~dp0"
cd..

call venv\Scripts\activate.bat

python main\main.py

pause


@REM @echo off
@REM setlocal
@REM :: 1. เปลี่ยน Code Page ให้รองรับภาษาไทย / UTF-8
@REM chcp 65001 > nul


@REM cd /d "%~dp0"
@REM :: ออกจาก Script_Run
@REM cd ..
@REM REM ==================================================
@REM REM กำหนด path ของโปรเจกต์
@REM REM ==================================================
@REM set "PROJECT_DIR=%CD%"
@REM set "SCRIPT_DIR=%PROJECT_DIR%\main"
@REM set "SCRIPT_FILE=%SCRIPT_DIR%\main.py"

@REM REM ==================================================
@REM REM ใช้ Python จาก .venv1
@REM REM ==================================================
@REM set "PYTHON_EXE=%SCRIPT_FILE%"

@REM REM ==================================================
@REM REM เพิ่ม path สำหรับ import module
@REM REM ==================================================
@REM set "PYTHONPATH=%PROJECT_DIR%\setting\config.yaml;%PYTHONPATH%"

@REM REM ==================================================
@REM REM ตรวจสอบไฟล์สำคัญ
@REM REM ==================================================
@REM if not exist "%PYTHON_EXE%" (
@REM     echo ERROR: IS NOT Python interpreter
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
@REM REM รันโปรแกรม
@REM REM ==================================================
@REM python "%PYTHON_EXE%" main\main.py

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