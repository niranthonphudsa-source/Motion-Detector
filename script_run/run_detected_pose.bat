@echo off
echo Starting Python Application...

:: ย้ายไดเรกทอรีไปยังโฟลเดอร์ของโปรเจกต์
cd /d "C:\Users\Niran_t\Desktop\file_work\ProjectDetection\Motion-Detector"

:: เปิดใช้งาน Virtual Environment
call venv\Scripts\activate.bat

:: รันโปรแกรม Python
python main\main.py

:: ปิดการทำงาน (ถ้าค้างไว้ดู Log/Error ให้ใส่ pause)
pause