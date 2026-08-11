@echo off
:: 1. เปลี่ยน Code Page ให้รองรับภาษาไทย / UTF-8
chcp 65001 > nul


:start_script
:: 3. ล็อก Location ให้อยู่ในโฟลเดอร์เดียวกับไฟล์ .bat นี้เสมอ
cd /d "%~dp0"

cd ..
set "PROJECT_DIR=%CD%"
echo %PROJECT_DIR%



set "SCRIPT_DIR=%PROJECT_DIR%\train_model"
echo %SCRIPT_DIR%

set "MAIN_DIR=%SCRIPT_DIR%\train_gui.py"
echo %MAIN_DIR%

:: ----------------------------------------------------
:: [พื้นที่เขียนคำสั่งของคุณ]
:: ----------------------------------------------------
echo ====================================================
echo  เริ่มทำงานสคริปต์...
echo ====================================================

:: ตัวอย่าง: รันไฟล์ Python หรือสั่งงานโปรแกรมในโฟลเดอร์เดียวกัน
python %MAIN_DIR%

echo.
echo ทำงานเสร็จสิ้นเรียบร้อยแล้ว!
pause