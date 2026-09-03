# Motion Detector

Motion Detector เป็นระบบตรวจจับความเคลื่อนไหวและสถานะคน/วัตถุแบบเรียลไทม์ โดยใช้กล้อง RTSP, webcam หรือวิดีโอเป็น Input และประยุกต์ใช้ YOLO + Pose-based inference เพื่อคัดกรองสถานะ OK / NG ภายใน ROI (Region of Interest)

โครงการนี้มีลักษณะเป็นระบบตรวจจับแบบแอปพลิเคชันเดสก์ท็อปบน Python และมี GUI สำหรับตั้งค่า ROI, กล้อง, กับดักข้อมูล, Dashboard และการจัดการอุปกรณ์ต่อ ESP32

## ภาพรวมของระบบ

ระบบหลักทำงานด้วยกระบวนการต่อไปนี้:

- รับสัญญาณจากกล้องหลายตัว (RTSP / Webcam / Video File)
- ตรวจจับคนหรือวัตถุในพื้นที่ ROI ที่กำหนดไว้
- วิเคราะห์สถานะการเคลื่อนไหวและความสัมพันธ์ระหว่างจุดสำคัญของร่างกายผ่านโมเดล pose
- ตรวจสอบ threshold ของ OK / NG และบันทึกเหตุการณ์เมื่อเกิดสัญญาณผิดพลาด
- เมื่อเงื่อนไข NG เกิดขึ้นและคนออกจาก ROI จะส่งคำสั่งไปยัง ESP32 หรือบอร์ดควบคุมภายนอก
- บันทึกวิดีโอ + ข้อมูลสถิติ และสามารถเรียกดูผ่าน GUI / export ข้อมูลได้

## โครงสร้างโปรเจ็กต์ที่ใช้งานจริง

```text
Motion-Detector/
├── README.md
├── setting/
│   └── config.yml
├── main/
│   ├── main.py                   # จุดเริ่มต้นโปรแกรมหลัก
│   ├── app/                     # GUI สำหรับดูข้อมูล/ตั้งค่าข้อมูล
│   ├── callback_command/        # callback/command ของระบบ
│   ├── display/                 # GUI แสดงผลหลัก
│   ├── LIB/                     # โมดูลช่วยต่าง ๆ (ROI, prediction, config, stats, user manager)
│   ├── logs/                    # ไฟล์ heartbeat, log ต่าง ๆ
│   ├── run_start/               # default config / runtime setup
│   ├── setting_esp32/           # GUI และ config สำหรับ ESP32
│   ├── utils/                   # helper functions
│   ├── yolo26n-pose_openvino_model/
│   ├── mark_roi_polygon.py
│   ├── rtspVideo.py
│   ├── videoWrite.py
│   ├── check_people_in_roi.py
│   ├── show_status_pose.py
│   └── ...
├── model/
├── train_model/
├── yolo26n-pose_openvino_model/
├── datasets/
├── output_videos/
├── video_ok/
├── video_ng/
├── db_config.json
├── db_config.txt
├── install_library.txt
├── esp32_ng_controller.py
├── pose_dataset_label.csv
├── pose_dataset_99.4_persent copy.csv
├── TEST/
├── delete/
└── ...
```

> หมายเหตุ: โฟลเดอร์ `TEST/` และ `delete/` เป็นไฟล์สำหรับทดสอบ/สคริปต์เก่า อาจไม่ใช่ส่วนสำคัญของ runtime หลัก

## จุดเริ่มต้นโปรแกรม

โปรแกรมหลักเริ่มจาก:

- `main/main.py`

เมื่อรันไฟล์นี้ โปรแกรมจะทำการ:

1. โหลด config จาก `setting/config.yml`
2. ตั้งค่า camera ที่ active อยู่
3. โหลดโมเดล YOLO Pose หรือ model classifier ที่ใช้ในระบบ
4. ตั้งค่า ROI และ reverse point
5. เปิดกล้อง/RTSP stream
6. เริ่มแสดง GUI และประมวลผลภาพแบบ real-time

## ฟีเจอร์หลัก

- รองรับกล้องหลายตัวและหลายชนิด input
  - RTSP stream
  - Webcam
  - Video file
- ROI-based detection เพื่อจำกัดพื้นที่ตรวจจับ
- การตรวจจับแบบ realtime ผ่าน YOLO Pose
- ระบบนับเหตุการณ์/threshold และจัดการ OK / NG
- บันทึกวิดีโอและข้อมูลเมื่อ trigger เกิดขึ้น
- GUI สำหรับดูข้อมูล / ตรวจสถิติ / ตั้งค่า config
- รองรับการทำงานร่วมกับ ESP32 เพื่อส่งสัญญาณเตือนหรือรีเซ็ต
- สามารถ export ข้อมูลเชิงสถิติต่าง ๆ ได้

## เทคโนโลยีและไลบรารีที่ใช้

- Python 3.10+
- OpenCV
- PyTorch
- Ultralytics YOLO
- NumPy
- Pandas
- scikit-learn
- joblib
- PyYAML
- Tkinter
- PySerial
- PyODBC
- OpenVINO
- SQLite / SQL Server (ตามการใช้งานจริง)
- Matplotlib (สำหรับ dashboard / chart)

## การติดตั้ง

### 1) ติดตั้ง Python

แนะนำให้ใช้ Python 3.10 หรือ 3.11

### 2) สร้าง Virtual Environment

```bash
cd "path/to/Motion-Detector"
python -m venv venv
```

บน Windows:

```bash
venv\Scripts\activate
```

### 3) ติดตั้งไลบรารีที่จำเป็น

สามารถติดตั้งด้วยคำสั่งต่อไปนี้:

```bash
pip install opencv-python
pip install numpy
pip install pandas
pip install pyyaml
pip install ultralytics
pip install torch
pip install joblib
pip install pyserial
pip install pyodbc
pip install scikit-learn
pip install openpyxl
pip install matplotlib
pip install pillow
```

สำหรับคู่มือการติดตั้งเบื้องต้นใน project ยังมีไฟล์:

- `install_library.txt`

> โปรดสังเกตว่าโครงการนี้มีการใช้ไลบรารีหลายตัวตามโมดูลที่ทำงานจริง หากเครื่องใช้ Windows + SQL Server อาจต้องติดตั้ง ODBC Driver เพิ่มเติมด้วย

## การตั้งค่าโปรแกรม

### 1) การตั้งค่า Camera และ ROI

ไฟล์ config หลักอยู่ที่:

- `setting/config.yml`

นี่เป็นไฟล์ที่ใช้กำหนดกล้องที่ใช้งาน, source, Type, ROI, save_ok, save_ng, save_data, point_zoom และค่าต่าง ๆ ที่เกี่ยวกับการตรวจจับ

ตัวอย่าง YAML:

```yaml
cameras:
  Camera_1:
    Type: LIVE_STREAM
    enabled: true
    source: rtsp://username:password@ip:port/...
    save_ok: false
    save_ng: false
    save_data: true
    mark_points:
      - [582, 681]
      - [1148, 699]
    start_point:
      - 872
      - 758
    reverse_point:
      - 956
      - 1034
    ng_trigger_count: 1
    person_limit: 5
```

### 2) การตั้งค่า ESP32 / Serial

โครงการมีโมดูลการตั้งค่า ESP32 ที่อยู่ใน:

- `main/setting_esp32/`
- `main/setting_esp32/setting_esp32.py`
- `main/setting_esp32/esp32_pin_config.json`
- `main/setting_esp32/esp32_pin_config_gui.py`
- `esp32_ng_controller.py`

บางส่วนของ project ยังมีไฟล์ JSON อื่น ๆ เช่น `main/hardware_config.json` ซึ่งเป็นไฟล์เก่าหรือใช้สำหรับการทดสอบ/การตั้งค่า hardware แบบต่าง ๆ

### 3) การตั้งค่าฐานข้อมูล

มีไฟล์:

- `db_config.json`
- `db_config.txt`

ใช้สำหรับการเชื่อมต่อฐานข้อมูลที่โปรแกรมอาจเรียกใช้ผ่าน GUI / report / export data

ตัวอย่าง:

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

## การติดตั้ง ODBC สำหรับ SQL Server (ถ้าจำเป็น)

หากใช้ SQL Server Authentication บน Windows และต้องการใช้งาน `pyodbc` ร่วมกับ Driver 18 ให้รันคำสั่งนี้ใน PowerShell:

```powershell
Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/?linkid=2249006" -OutFile "msodbcsql18.msi"; Start-Process msiexec.exe -ArgumentList '/i msodbcsql18.msi /qn IACCEPTMSODBCSQLLICENSETERMS=YES' -Wait; Remove-Item "msodbcsql18.msi"
```

## วิธีการรันโปรเจ็กต์

จาก root ของโปรเจ็กต์:

```bash
python main/main.py
```

หรือถ้าอยู่ใน venv แล้ว:

```bash
venv\Scripts\activate
python main/main.py
```

## การทำงานของระบบในเชิงลำดับ

```text
เปิดโปรแกรม
   ↓
โหลด config.yml
   ↓
เลือก Camera ปัจจุบัน
   ↓
โหลดโมเดลและ ROI
   ↓
เปิดกล้อง/RTSP
   ↓
ตรวจจับคน/วัตถุในพื้นที่ ROI
   ↓
ประเมินสถานะ OK / NG
   ↓
ถ้า trigger NG และออกจาก ROI => ส่งคำสั่ง ESP32 / เตือน
   ↓
บันทึกวิดีโอและข้อมูลสถิติ
   ↓
แสดงผลบน GUI / Dashboard
```

## ข้อควรระวังเมื่อใช้งาน

- ตรวจสอบว่า path ของ model ถูกต้องก่อนเปิดโปรแกรม
- หากเปิดใช้งาน RTSP ให้ตรวจสอบ username/password และ URL ให้ถูกต้อง
- หากมีกล้องหลายตัว ให้เลือก Camera ID ที่ถูกต้องใน config หรือ GUI
- หากไม่มี hardware ESP32 ให้ลดส่วนที่เกี่ยวกับ serial หรือปิดการใช้งานออกได้
- ไฟล์ใน `TEST/` และ `delete/` ไม่ใช่ส่วนหลักของระบบและใช้สำหรับการทดลองเท่านั้น

## การแก้ไขหรือปรับแต่งต่อ

หากต้องการปรับแต่งฟังก์ชันหลัก เช่น ROI, threshold, กล้อง, model path, หรือ logic ของ NG trigger สามารถแก้ไขได้ที่:

- `setting/config.yml`
- `main/main.py`
- `main/LIB/config_loader_start.py`
- `main/LIB/roi_handler.py`
- `main/check_people_in_roi.py`
- `main/setting_esp32/`

## สรุป

โครงการนี้เป็นระบบตรวจจับความเคลื่อนไหวและสถานะด้านความปลอดภัยตามบริเวณ ROI ที่กำหนดไว้ ซึ่งใช้ภาพจากกล้องจริงและโมเดล YOLO/pose เป็นข้อมูลเชิงวิเคราะห์ การทำงานมีความซับซ้อนและจำเป็นต้องกำหนด config ให้ถูกต้องก่อนใช้งานจริง

ถ้าต้องการ ผมสามารถช่วยต่อได้อีก 2 แบบได้ทันที:

1. ปรับ README ให้เป็นเวอร์ชันภาษาอังกฤษแบบโปรเจ็กต์สาธารณะ
2. สร้าง `requirements.txt` ให้ตรงกับ library ที่โปรเจ็กต์นี้ใช้งานจริง

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

## การตั้งค่า NG และภาพครอปใบหน้า

สามารถตั้งค่าได้จาก GUI ตั้งค่ากล้อง หรือแก้ไขใน `setting/config.yml` ภายใต้กล้องที่ต้องการ:

```yaml
cameras:
   Camera_1:
      ng_trigger_count: 1
      esp32_light_enabled: false
      show_ng_head_overlay: true
      esp32_reset_after_sec: 10
```

ความหมายของค่า:

- `ng_trigger_count`: จำนวนเหตุการณ์ NG ที่ต้องสะสมก่อนสั่งงาน ESP32
- `esp32_light_enabled`: ถ้าเป็น `true` ระบบจึงจะส่ง `CMD_NG` ไป ESP32; ถ้าเป็น `false` จะไม่ส่งคำสั่งไฟ
- `show_ng_head_overlay`: ถ้าเป็น `true` จะแสดงภาพครอปใบหน้าของคนที่เป็น NG บนภาพหลัก; ถ้าเป็น `false` จะไม่แสดง
- `esp32_reset_after_sec`: เวลาหน่วงก่อนส่ง `CMD_RESET` กลับไปยัง ESP32

การแสดงภาพครอปไม่ขึ้นกับการเปิดไฟ ESP32 สามารถเปิด `show_ng_head_overlay` ได้แม้ตั้ง `esp32_light_enabled: false` ภาพจะแสดงเมื่อคน NG เดินออกจาก ROI และระบบครอปศีรษะได้ โดยแสดงภาพล่าสุดได้สูงสุด 5 คน

> ค่า `true/false` ใน YAML เทียบเท่ากับเปิด/ปิด หรือ `1/0` ตามลำดับ ควรใช้ `true` และ `false` เพื่อให้อ่านค่าได้ชัดเจน

## การเปิดใช้งานระบบบน Windows

รันจากโฟลเดอร์ root ของโปรเจ็กต์:

```powershell
python main\main.py
```

หรือใช้ supervisor ซึ่งจะตรวจสอบ heartbeat และเริ่มระบบใหม่เมื่อโปรแกรมหลักหยุดทำงาน:

```text
script_run\run_detected_pose.bat
```

ไฟล์ heartbeat อยู่ที่ `main/logs/heartbeat.txt` และระบบจะสร้างโฟลเดอร์ `main/logs` ให้อัตโนมัติ หากไม่สามารถเขียน heartbeat ได้ ระบบจะแจ้งเตือนและพยายามทำงานต่อ แต่ supervisor อาจมองว่าโปรแกรมไม่ตอบสนองเมื่อ heartbeat ไม่ถูกอัปเดต

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
