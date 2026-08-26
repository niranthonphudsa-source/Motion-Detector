@echo off
setlocal
echo Starting Python Application...

for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"
set "SCRIPT_FILE=%PROJECT_DIR%\main\LIB\config_gui.py"

if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
	set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
	set "PYTHON_ARGS="
) else if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
	set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
	set "PYTHON_ARGS="
) else (
	where py >nul 2>&1
	if not errorlevel 1 (
		set "PYTHON_EXE=py"
		set "PYTHON_ARGS=-3"
	) else (
		where python >nul 2>&1
		if not errorlevel 1 (
			set "PYTHON_EXE=python"
			set "PYTHON_ARGS="
		)
	)
)

if not defined PYTHON_EXE (
	echo ERROR: Python interpreter not found.
	echo Install Python or create venv in: %PROJECT_DIR%
	pause
	exit /b 1
)

if not exist "%SCRIPT_FILE%" (
	echo ERROR: Script not found: %SCRIPT_FILE%
	pause
	exit /b 1
)

cd /d "%PROJECT_DIR%"
echo Python command: %PYTHON_EXE% %PYTHON_ARGS%

:: รันโปรแกรม Python
"%PYTHON_EXE%" %PYTHON_ARGS% "%SCRIPT_FILE%"

:: ปิดการทำงาน (ถ้าค้างไว้ดู Log/Error ให้ใส่ pause)
pause
endlocal