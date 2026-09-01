from __future__ import annotations
import time
from esp32_helpers import (
    make_client, relay_on, relay_off, relay_all_on,
    relay_all_off, relay_pulse, relay_status
)
from esp32_client import ESP32Error

# ESP32_BASE_URL = "http://"
ESP32_BASE_URL = "http://"


def demo_basic():
    client = make_client(ESP32_BASE_URL, timeout=3.0)

    # 1) รอให้บอร์ดพร้อม (เช่น หลังรีบูต หรือ Wi-Fi เพิ่งเชื่อม)
    if not client.wait_ready(timeout_total=12.0, interval=1.0):
        print("ESP32 ยังไม่พร้อมใช้งานในเวลาที่กำหนด — ข้ามการทดสอบ")
        return

    # 2) เริ่มใช้งาน พร้อมจับ ESP32Error รายคำสั่ง (อ่านง่ายกว่า)
    try:
        print("Initial:", relay_status(client))

        print("Relay1 ON :", relay_on(client, 1));  time.sleep(1.0)
        print("Relay1 OFF:", relay_off(client, 1))

        print("Relay2 PULSE 3s:", relay_pulse(client, 2, 3000))

        print("ALL ON :", relay_all_on(client)); time.sleep(2.0)
        print("Status :", relay_status(client))

        print("ALL OFF:", relay_all_off(client))
        print("Final  :", relay_status(client))

    except ESP32Error as e:
        # ข้อผิดพลาดจากฝั่งเครือข่าย/HTTP ที่แปลงแล้วให้อ่านง่าย
        print("[ESP32Error]", e)
    except Exception as ex:
        # กรณีอื่น ๆ (โค้ดผิดพลาด, พารามิเตอร์ไม่ถูกต้อง ฯลฯ)
        print("[General Error]", ex)


if __name__ == "__main__":
    demo_basic()
