import os
import threading
import tkinter as tk
import joblib
import serial
import run_start.default_config_var as df

from app.app import SSMSConnectGUI, TableViewerWindow
from LIB.config_loader_start import AppConfig
from LIB.help_gui import HelpGUI
from LIB.roi_handler import ROIHandler
from LIB.stats_gui import StatsGUI, StatsManager
from rtspVideo import RTSPVideoGrabber
from setting_esp32 import esp32_pin_config_gui
from setting_esp32.setting_esp32 import PinConfigGUI

# ─── คำนวณหา PROJECT_ROOT เพื่อป้องกันปัญหา PATH เคลื่อน ───
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# ปรับระดับชั้นถอยหลังตามโครงสร้างจริง เช่น ถอย 1 หรือ 2 ชั้น
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# ─── โหลดและจัดการ CONFIG ───
# แนะนำสร้าง Path แบบ Absolute ป้องกัน Supervisor หาลำดับชั้นไม่เจอ
CONFIG_FILE_PATH = os.path.join(PROJECT_ROOT, "setting", "config.yml")
app_config = AppConfig(
    CONFIG_FILE_PATH
    if os.path.exists(CONFIG_FILE_PATH)
    else r"setting\config.yml"
)

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
model_sklearn = app_config.model_sklearn
type = app_config.type

roi = ROIHandler()
DB_FILE_PATH = os.path.join(PROJECT_ROOT, "setting", "inspection_stats.db")
stats_manager = StatsManager(
    db_path=DB_FILE_PATH
    if os.path.exists(DB_FILE_PATH)
    else r"setting\inspection_stats.db"
)

check_pose = df.check_pose
ok_display_time = df.ok_display_time
SKIP_FRAMES = df.SKIP_FRAMES
predicted_label = df.predicted_label
confidence = df.confidence
any_people_inside = df.any_people_inside
fps = df.fps
SKELETON_CONNECTIONS = df.SKELETON_CONNECTIONS
lastID = df.lastID

direction_tracker = {}

# ─── Safe Load Model (ป้องกัน Error ค่าว่าง หรือ FileNotFoundError) ───
pose_classifier = None

if model_sklearn and str(model_sklearn).strip():
    # หากเป็น Relative Path ให้ปรับเปลี่ยนชี้ไปที่ PROJECT_ROOT/model/...
    if not os.path.isabs(model_sklearn):
        model_filename = os.path.basename(model_sklearn)
        target_model_path = os.path.join(
            PROJECT_ROOT, "model", model_filename
        )
    else:
        target_model_path = model_sklearn

    if os.path.exists(target_model_path):
        try:
            pose_classifier = joblib.load(target_model_path)
            print(f"✅ โหลดโมเดลสำเร็จจาก: {target_model_path}")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะโหลดโมเดล: {e}")
    else:
        print(f"❌ หาไฟล์โมเดลไม่พบที่ Path: {target_model_path}")
else:
    print(
        "⚠️ คำเตือน: model_sklearn เป็นค่าว่าง (Empty String) หรืออ่านค่าจาก config.yml ไม่ได้"
    )


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


df.simulated_key = -1


def trigger_key_from_gui(key_code):
    df.simulated_key = key_code
    return df.simulated_key


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
            ser.write(command.encode("utf-8"))
            print(
                f"📡 ส่งคำสั่งตั้งค่า Pin ไปยัง {port}: {command.strip()}"
            )
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อกับ {port} ได้: {e}")


# 🔴 เปิด PinConfigGUI แบบ Threading ไม่ให้บล็อก OpenCV
def open_pin_config_window():
    def run_gui():
        app = PinConfigGUI(on_save_callback=apply_pin_config_to_mcu)
        app.run()

    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()