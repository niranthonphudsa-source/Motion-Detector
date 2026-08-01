import tkinter as tk
import threading
import serial

from app.app import SSMSConnectGUI
from LIB.help_gui import HelpGUI
from setting_esp32.setting_esp32 import PinConfigGUI
from setting_esp32 import esp32_pin_config_gui

def open_ssms_gui():
    def run_gui():
        db_root = tk.Tk()
        app = SSMSConnectGUI(db_root)
        db_root.mainloop()

    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()

def set_esp32_pin():
    def run_gui():
        esp_root = tk.Tk()
        app = esp32_pin_config_gui(esp_root)
        esp_root.mainloop()
        
simulated_key = -1
def trigger_key_from_gui(key_code):
    global simulated_key
    simulated_key = key_code
    return simulated_key

help_gui = HelpGUI(key_callback=trigger_key_from_gui)

def open_help_window():
    gui_thread = threading.Thread(target=help_gui.open_window, daemon=True)
    gui_thread.start()

def apply_pin_config_to_mcu(config_data):
    port = config_data["port"]
    baud = config_data["baudrate"]
    
    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            command = f"SETPIN:TRIG={config_data['trig_pin']},ECHO={config_data['echo_pin']},RELAY={config_data['relay_pin']}\n"
            ser.write(command.encode('utf-8'))
            print(f"📡 ส่งคำสั่งตั้งค่า Pin ไปยัง {port}: {command.strip()}")
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อกับ {port} ได้: {e}")

# 🔴 แก้ไข: เปิด PinConfigGUI แบบ Threading ไม่ให้บล็อก OpenCV
def open_pin_config_window():
    def run_gui():
        app = PinConfigGUI(on_save_callback=apply_pin_config_to_mcu)
        app.run()

    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()