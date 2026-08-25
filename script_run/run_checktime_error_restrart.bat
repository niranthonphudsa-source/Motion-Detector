@echo off
setlocal
chcp 65001 > nul
chcp 874 > nul
REM ==================================================
REM ????? path ???????????
REM ==================================================
cd /d "%~dp0"
cd ..
set "PROJECT_DIR=%CD%"
set "SCRIPT_DIR=%PROJECT_DIR%\main"
set "SCRIPT_FILE=%SCRIPT_DIR%\LIB\checktime_error_restart.py"

REM ==================================================
REM ??? Python ??? .venv1
REM ==================================================
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
set "PYTHON_CONFIG=%PROJECT_DIR%\setting\config.yml"
REM ==================================================

REM =======================================================================
echo PROJECT DIR : %PROJECT_DIR%
echo SCRIPT_DIR : %SCRIPT_DIR%
echo SCRIPT_FILE : %SCRIPT_FILE%
echo PYTHON_EXE : %PYTHON_EXE%
echo PYTHON_CONFIG :%PYTHON_CONFIG%

REM =======================================================================
if not exist "%PYTHON_EXE%" (
    echo ERROR: ????? Python interpreter
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%PYTHON_CONFIG%" (
    echo ERROR: ????? Python Config
    echo %PYTHON_CONFIG%
    pause
    exit /b 1
)

if not exist "%SCRIPT_FILE%" (
    echo ERROR: ????????? script
    echo %SCRIPT_FILE%
    pause
    exit /b 1
)

cd /d "%SCRIPT_DIR%"
@REM cd ..
"%PYTHON_EXE%" %SCRIPT_FILE%

echo ===========================================
cd /d "%PROJECT_DIR%"
set "last_dir=%CD%"
echo last_dir: %last_dir% 
echo ===========================================
pause
endlocal