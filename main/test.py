import serial
import serial.tools.list_ports
import time
import sys


COMMANDS = [
    "CONNECT_DETECT",
    "CMD_OK",
    "CMD_NG",
    "CMD_CHECK_START",
    "CMD_RESET",
]


def find_esp32_port():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        print("⚠️ ไม่พบพอร์ต COM")
        return None

    print("📋 พอร์ตที่พบ:")
    for i, port in enumerate(ports, start=1):
        print(f"  {i}. {port}")

    choice = input(f"เลือกพอร์ต [1-{len(ports)}]: ").strip()
    try:
        idx = int(choice) - 1
        return ports[idx]
    except Exception:
        print(f"ใช้พอร์ตเริ่มต้น: {ports[0]}")
        return ports[0]


def send_command_loop():
    port = find_esp32_port()
    if not port:
        return

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"✅ เปิดพอร์ต {port} สำเร็จ")
    except Exception as e:
        print(f"❌ ไม่สามารถเปิดพอร์ต {port}: {e}")
        return

    try:
        index = 0
        while True:
            cmd = COMMANDS[index % len(COMMANDS)]
            payload = (cmd + "\n").encode("utf-8")
            ser.write(payload)
            ser.flush()

            print(f"📤 ส่ง: {cmd}")
            time.sleep(0.5)

            try:
                response = ser.readline().decode("utf-8", errors="ignore").strip()
                if response:
                    print(f"📥 ESP32 ตอบกลับ: {response}")
                else:
                    print("⚠️ ESP32 ไม่ตอบกลับ")
            except Exception as e:
                print(f"❌ อ่านข้อมูลไม่ได้: {e}")

            index += 1
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n🛑 หยุดการส่งข้อมูล")
    finally:
        ser.close()
        print("✅ ปิดพอร์ตแล้ว")


if __name__ == "__main__":
    print("ESP32 Serial Sender Test")
    print("จะส่งคำสั่งไป ESP32 ทุก 3 วินาที")
    send_command_loop()