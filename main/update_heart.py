import os
import time

# กำหนด Path ให้ตรงกับที่ Supervisor รอตรวจ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HEARTBEAT_FILE = os.path.join(BASE_DIR, "LIB", "logs", "heartbeat.txt") # ปรับ Path ตามโครงสร้างจริง

def update_heartbeat():
    try:
        os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception as e:
        pass