@echo off
echo Stopping Python Application...

:: สั่งปิด Process ของ Python ทั้งหมดบังคับปิดด้วย /F
taskkill /F /IM python.exe /T

echo Application Stopped!
timeout /t 3