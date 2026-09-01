# Motion Detector

Motion Detector เป็นระบบตรวจจับภาพและวิเคราะห์เหตุการณ์จากกล้องหลายตัว โดยมุ่งเน้นไปที่การตรวจจับการเคลื่อนไหว/การเข้าพื้นที่/สถานะวัตถุผ่านการประมวลผลภาพและโมเดล AI การทำงานเป็นระบบแบบเรียลไทม์ พร้อมการบันทึกสถิติและจัดการข้อมูลกล้อง/ROI/การรายงานผล

## ภาพรวมของโครงการ

โปรเจ็กต์นี้ประกอบด้วย 4 ส่วนหลัก ได้แก่

- กล้องและการแสดงผลแบบ real-time
- ROI และการกำหนดพื้นที่ตรวจจับ
- AI model / classification / detection
- Logging, dashboard, export data และการจัดการ config

โค้ดหลักอยู่ที่

- main/main.py
- main/LIB/
- setting/config.yml
- main/app/

## ฟีเจอร์หลัก

- ตรวจจับภาพแบบ real-time จาก RTSP / IP Camera / Webcam / Video File
- กำหนด ROI (Region of Interest) เพื่อจำกัดพื้นที่ที่ต้องตรวจจับ
- รองรับการตั้งค่า camera ประเภท LIVE_STREAM และ Video
- บันทึกภาพ/วิดีโอเมื่อมีเหตุการณ์ OK หรือ NG
- บันทึกสถิติและผลการตรวจเข้าฐานข้อมูล
- แสดง dashboard สถิติแบบกราฟและ KPI
- รองรับ export data เป็น Excel
- มีส่วนสำหรับ training โมเดล AI และ export โมเดล
- มี GUI สำหรับการตั้งค่า camera, config และการแสดงผล

## เทคโนโลยีที่ใช้

- Python 3.10+
- OpenCV
- Ultralytics YOLO
- PyTorch
- Tkinter (GUI)
- PyYAML
- pandas
- scikit-learn
- joblib
- pyodbc
- SQLite / SQL Server (ขึ้นกับการใช้งานจริง)
- OpenVINO

## โครงสร้างโปรเจ็กต์

```text
Motion-Detector/
├── README.md
├── setting/
│   └── config.yml
├── main/
│   ├── main.py
│   ├── app/
│   ├── LIB/
│   ├── display/
│   ├── callback_command/
│   ├── logs/
│   ├── run_start/
│   └── utils/
├── model/
├── yolo26n-pose_openvino_model/
├── datasets/
├── train_model/
├── output_videos/
├── video_ok/
├── video_ng/
├── db_config.json
├── db_config.txt
├── install_library.txt
├── pose_dataset_label.csv
└── pose_dataset_99.4_persent copy.csv
```

## การติดตั้ง

### 1) ติดตั้ง Python

แนะนำใช้ Python 3.10.x

### 2) สร้าง virtual environment

```bash
cd "path/to/Motion-Detector"
python -m venv venv
venv\Scripts\activate
```

### 3) ติดตั้งไลบรารีที่จำเป็น

```bash
pip install opencv-python Pillow PyYAML pyodbc
pip install ultralytics pandas joblib pyserial
pip install tkcalendar
pip install scikit-learn
pip install openvino
pip install openpyxl
```

หากต้องการติดตั้งเพิ่มเติมจากไฟล์แนะนำใน project สามารถดูได้ที่

- install_library.txt

## การตั้งค่า config

### 1) ไฟล์ config หลัก

โปรเจ็กต์ใช้ไฟล์ YAML เป็น config หลักที่อยู่ที่

- setting/config.yml

ตัวอย่างโครงสร้างที่ Project ใช้งานจริงมีข้อมูลเช่น

```yaml
cameras:
  Camera_1:
    Type: LIVE_STREAM
    enabled: true
    save_ok: false
    save_ng: false
    save_data: true
    source: rtsp://username:password@ip:port/...
    Display:
      Position_x: 0
      Position_y: 0
      Size_x: 1920
      Size_y: 1080
```

### 2) ตัวแปร DB สำหรับการเชื่อมต่อ

มีไฟล์ db_config.json ที่ใช้สำหรับการเชื่อมต่อฐานข้อมูลแบบบางส่วน เช่น SQL Server หรือการใช้งาน GUI ดูข้อมูล

ตัวอย่าง

```json
{
  "server": "localhost",
  "database": "databasename",
  "auth_type": "SQL Server Authentication",
  "username": "username",
  "password": "password",
  "driver": "ODBC Driver 18 for SQL Server"
}
```

> โปรดสังเกตว่าโครงการนี้ใช้ config.yml เป็น config หลักสำหรับกล้องและระบบตรวจจับ ส่วน db_config.json เป็น config สำหรับการเชื่อมต่อฐานข้อมูล ซึ่งอาจใช้งานร่วมกับ GUI ดูข้อมูล/รายงานต่าง ๆ

## การติดตั้ง ODBC สำหรับ SQL Server

ใน Windows หากใช้ SQL Server Authentication และต้องการเชื่อมต่อด้วย ODBC Driver 18 ให้รันคำสั่งต่อไปนี้ใน PowerShell

```powershell
Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/?linkid=2249006" -OutFile "msodbcsql18.msi"; Start-Process msiexec.exe -ArgumentList '/i msodbcsql18.msi /qn IACCEPTMSODBCSQLLICENSETERMS=YES' -Wait; Remove-Item "msodbcsql18.msi"
```

## วิธีการรันโปรเจ็กต์

จาก root ของโปรเจ็กต์

```bash
python main/main.py
```

หรือถ้าต้องการเปิดเฉพาะ GUI / ส่วนที่เกี่ยวกับการตั้งค่า camera สามารถเรียกใช้งานตามโมดูลใน main/LIB เช่น

- addCamera.py
- config_gui.py
- stats_gui.py
- train_gui.py

## การทำงานของระบบ

### 1) เริ่มต้นระบบ

- โหลด config จาก setting/config.yml
- เลือกกล้องเริ่มต้น
- เปิด Stream / Video Source
- โหลดโมเดล AI
- เริ่มประมวลผลภาพแบบ real-time

### 2) ตรวจจับ ROI

- ผู้ใช้กำหนดพื้นที่ตรวจจับผ่าน ROI
- ระบบคำนวณว่ามีวัตถุหรือคนเข้าไปในพื้นที่หรือไม่
- สถานะสามารถบันทึกเป็น OK / NG / Warning ตามเงื่อนไขของโปรแกรม

### 3) บันทึกข้อมูล

- บันทึกเหตุการณ์ลง log
- บันทึกสถิติและสถานะกล้อง
- ส่งออกเป็น Excel หรือแสดงผลบน dashboard

### 4) รายงานและ explorer

- ดูประวัติเหตุการณ์
- ดูสถิติแบบรวม/รายวัน/รายเดือน
- จัดกลุ่มโดย camera_id และสถานะ

## ข้อควรระวัง

- ตรวจสอบให้ config.yml ถูกต้องก่อนรันโปรแกรม
- ถ้าใช้ RTSP ต้องตรวจสอบ username/password/IP/port ให้ถูกต้อง
- หากใช้โมเดล AI ให้ตรวจสอบ path ของโมเดลและการเตรียมไฟล์ model ให้ครบถ้วน
- การเชื่อมต่อ DB จำเป็นต้องมี driver ที่ถูกต้องและสิทธิ์เข้าถึง corresponding database

## ประเด็นที่น่าสังเกต

โปรเจ็กต์นี้ไม่ได้เป็นแค่ระบบ CRUD ธรรมดา แต่เป็นระบบ AI Vision + Monitoring + Monitoring Dashboard + Logging ที่มีการบันทึกและรายงานข้อมูลเพิ่มเติม โดยมีความเหมาะสมกับการใช้งานในด้าน

- CCTV monitoring
- human/pose detection
- security surveillance
- event record and analytics
- visual inspection system

## สรุป

Motion Detector เป็นโปรเจ็กต์ที่รวมเอา

- camera management
- AI inference
- ROI configuration
- event logging
- statistics dashboard
- training/export model

เข้าด้วยกันในโครงงานเดียว เพื่อใช้งานในระบบตรวจจับภาพและรายงานผลแบบเรียลไทม์

## หมายเหตุ

โปรเจ็กต์นี้มีการพัฒนาต่อเนื่อง และบางส่วนอาจมีการใช้ไฟล์ config / db / GUI / training module ที่แตกต่างกันไปตามเวอร์ชันหรือการใช้งานจริง จึงควรเปิดอ่าน module ที่เกี่ยวข้องก่อนทำการปรับปรุงหรือใช้ต่อในสภาพแวดล้อมใหม่
