@echo off
echo "Start Config Pin Esp32......!"

cd /d "C:\Users\Niran_t\Desktop\file_work\ProjectDetection\Motion-Detector\main"

call venv\Scripts\activate.bat

python setting_esp32\setting_esp32.py
pause