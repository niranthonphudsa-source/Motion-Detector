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
- pyserial (สำหรับ ESP32 / Serial Communication)

## ลำดับการทำงานหลักของระบบ

ระบบนี้ทำงานแบบ real-time ดังนี้

1. โหลดกล้อง / RTSP stream / video source
2. ตรวจจับคนหรือวัตถุใน ROI
3. คำนวณสถานะลำดับท่าทาง / การยืนยันผล OK / NG
4. ถ้าคนออกจาก ROI และสถานะเป็น NG ให้ส่งสัญญาณไปยัง ESP32 ทันที
5. เริ่มนับเวลารักษาวิดีโอแถมท้ายแบบ buffer output
6. เมื่อครบเวลาที่กำหนดแล้ว จึงปิดวิดีโอ ย้ายไฟล์ไปยัง video_ok หรือ video_ng และบันทึกสถิติ

### Flow ของ NG Trigger

```text
คนเข้าพื้นที่ -> ตรวจท่าทาง -> สถานะ OK / NG
      |                         |
      |                         └── ถ้าเป็น NG และออกจาก ROI
      |                               ↓
      └────────────── ส่งคำสั่งไป ESP32: CMD_NG ───────► เสียง/ไฟเตือน
                                                       ↓
                                           เริ่มนับถอยหลังบันทึกแถมท้าย
                                                       ↓
                               เมื่อครบเวลา -> ปิดไฟล์ / ย้ายไป video_ng / บันทึก DB
```

## ESP32 Controller / GPIO I/O

โปรเจ็กต์นี้มีการเชื่อมต่อกับ ESP32 เพื่อควบคุมสัญญาณภายนอก เช่น

- ไฟ OK (Green LED)
- ไฟ NG (Red LED)
- Buzzer / เสียงเตือน
- Reset สถานะหลังการ Trigger

### ไฟล์ที่เกี่ยวข้อง

- main/setting_esp32/esp32_pin_config.json
- main/setting_esp32/esp32_pin_config_gui.py
- esp32/esp32_controller.py
- esp32_ng_controller.py

### คำสั่งที่ใช้กับ ESP32

ตัวอย่างคำสั่งที่ส่งผ่าน Serial เช่น

- `CMD_OK` → เปิดสถานะ OK
- `CMD_NG` → เปิดสถานะ NG / Trigger Error
- `CMD_CHECK_START` → เริ่มการตรวจสอบคนอยู่ในพื้นที่
- `CMD_RESET` → รีเซ็ตสถานะทั้งหมด
- `CONFIG:PIN_OK=2,PIN_NG=4,PIN_BUZZER=5` → ตั้งค่าพิน GPIO ให้ ESP32

### การเชื่อมต่อ ESP32

1. เปิด GUI ในส่วนการตั้งค่า ESP32 หรือเรียกใช้งาน script ที่เกี่ยวข้อง
2. เลือก COM Port และ Baud Rate ที่ตรงกัน
3. กด Connect
4. ระบบจะส่ง `CONNECT_DETECT` และโหลดค่า PIN จากไฟล์ config

> ค่าพินและพอร์ตจะถูกบันทึกลงไฟล์ JSON เพื่อให้ระบบหลักอ่านและใช้งานต่อได้

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

สำหรับการตั้งค่าทั่วไปของโปรแกรมและกล้อง ให้แก้ไขไฟล์

- setting/config.yml

ถ้าต้องการตั้งค่ากล้อง หรือ ROI หรือค่าเช็ก state ต่าง ๆ ให้ทำผ่าน config หรือ GUI ตามโมดูลที่มีให้ใช้งาน

### 2) ไฟล์ config สำหรับ ESP32

ไฟล์ที่ใช้บันทึกพอร์ต Serial และพิน GPIO ของ ESP32 อยู่ที่

- main/setting_esp32/esp32_pin_config.json

ตัวอย่าง

```json
{
  "PORT": "COM3",
  "BAUD": 115200,
  "PIN_OK": "2",
  "PIN_NG": "4",
  "PIN_BUZZER": "5"
}
```

ตัวอย่างโครงสร้าง YAML ของโปรเจ็กต์

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

หรือติดตั้ง Environment และรันจาก venv ที่สร้างไว้ก่อนหน้า

```bash
venv\Scripts\activate
python main/main.py
```

หรือถ้าต้องการเปิดเฉพาะ GUI / ส่วนที่เกี่ยวกับการตั้งค่า camera สามารถเรียกใช้งานตามโมดูลใน main/LIB เช่น

- addCamera.py
- config_gui.py
- stats_gui.py
- train_gui.py
- esp32_pin_config_gui.py

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
- บันทึกวิดีโอแถมท้ายสำหรับผู้ที่ออกจาก ROI ระหว่างการตรวจจับ

### 4) ESP32 / สัญญาณผิดพลาด

- กรณีมีคนผิดปกติหรือ NG ระบบจะส่งสัญญาณไป ESP32 ทันที
- หลังจากให้สัญญาณแล้ว ระบบจะยังคงเก็บคลิปแถมท้ายตามระยะเวลาที่กำหนด
- หากต้องการรีเซ็ตสถานะหรือสัญญาณ ให้ใช้คำสั่ง `CMD_RESET`

### 5) รายงานและ explorer

- ดูประวัติเหตุการณ์
- ดูสถิติแบบรวม/รายวัน/รายเดือน
- จัดกลุ่มโดย camera_id และสถานะ

## ข้อควรระวัง

- ตรวจสอบให้ config.yml ถูกต้องก่อนรันโปรแกรม
- ถ้าใช้ RTSP ต้องตรวจสอบ username/password/IP/port ให้ถูกต้อง
- หากใช้โมเดล AI ให้ตรวจสอบ path ของโมเดลและการเตรียมไฟล์ model ให้ครบถ้วน
- การเชื่อมต่อ DB จำเป็นต้องมี driver ที่ถูกต้องและสิทธิ์เข้าถึง corresponding database
- ตรวจสอบ COM Port และ Baud Rate ของ ESP32 ให้ตรงกันก่อนใช้งานจริง
- หากใช้ไฟหรือ Buzzer ให้เช็คว่าพิน GPIO ที่กำหนดใน config ไม่ชนกับพินใช้งานจริงของบอร์ด
- หากต้องการปรับเวลา buffer_output_time ให้ตรวจสอบค่าที่ใช้ในการนับถอยหลังปิดวิดีโอเพื่อไม่ให้เกิดการตัดคลิปเร็วหรือช้าเกินความต้องการ

## Troubleshooting

### ปัญหา ESP32 ไม่ตอบ

- ตรวจสอบว่า COM Port ถูกต้อง
- ตรวจสอบว่าค่า Baud Rate ตรงกับ ESP32
- ตรวจสอบว่า serial cable / driver / port ถูกใช้งานอยู่หรือไม่
- ลองเปิด GUI ตั้งค่า ESP32 และกด Refresh COM Port

### ปัญหาโมเดลไม่โหลด

- ตรวจสอบ path ของโมเดลใน config.yml
- ตรวจสอบว่ามีไฟล์ model และ metadata อยู่ครบ
- หากใช้ OpenVINO ตรวจสอบว่าไฟล์ XML, bin หรือ metadata ถูกจัดเก็บตรงที่โปรแกรมต้องการ

### ปัญหาวิดีโอไม่ถูกเก็บ

- ตรวจสอบว่า save_ok / save_ng / save_data ถูกตั้งค่าสถานะให้ถูกต้อง
- ตรวจสอบโฟลเดอร์ video_ok / video_ng / temp_video ว่ามีสิทธิ์เขียนไฟล์หรือไม่
- ตรวจสอบว่า buffer_output_time ไม่ใช่ค่า 0 หรือติดลบ

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
