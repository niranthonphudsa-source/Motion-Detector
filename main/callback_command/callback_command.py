import tkinter as tk
import threading
import serial
import os
import joblib
import run_start.default_config_var as df

from rtspVideo import RTSPVideoGrabber
from app.app import SSMSConnectGUI, TableViewerWindow
# from app.data_viewer_gui import SSTableViewerGUI
from LIB.help_gui import HelpGUI
from setting_esp32.setting_esp32 import PinConfigGUI
from setting_esp32 import esp32_pin_config_gui
from LIB.config_loader_start import AppConfig
from LIB.roi_handler import ROIHandler
from LIB.stats_gui import StatsGUI, StatsManager
# ─── โหลดและจัดการ CONFIG ───

base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
config_dir = os.path.join(parent_dir, "setting", "config.yml")
app_config = AppConfig(config_dir)

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
stats_manager = StatsManager(db_path=r"setting\inspection_stats.db")

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
# pose_classifier = joblib.load(model_sklearn) 


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


# def checkKey(key):
#     global config_manager
#     if key == 'q':
#         return False
#     elif key == 'h':  # 🌟 เพิ่มปุ่ม H สำหรับเปิด Help GUI
#         print("💡 กำลังเปิดหน้าต่างคู่มือช่วยเหลือ (Help GUI)...")
#         open_help_window()
#     elif key == '1':  # โหมดมาร์กพิกัดพื้นที่ Polygon
#         roi.clear_roi()
#         roi.current_mode = 1
#         print("✏️ เปิดโหมดวาด Polygon ROI: คลิกสร้างรูปปิด...")
#         # return roi.current_mode
#     elif key == '2':  # 🌟 โหมดมาร์กจุดเริ่มเช็ก (Start Point)
#         roi.current_mode = 2
#         print("🟢 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 1: Start Check Point]")
#         # return roi.current_mode
#     elif key == '3':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
#         roi.current_mode = 3
#         print("🔴 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 2: Reverse Check Point]")
#         # return roi.current_mode
#     elif key == '5':  # 🌟 โหมดมาร์กจุด Zoom
#         roi.current_mode = 5
#         print("🔴 คลิกบนหน้าจอเพื่อกำหนด [Mark Point Zoom]")
#         # return roi.current_mode
#     elif key == '6':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
#         roi.clear_point_zoom()
#         print("🔴[Cancle Mark Point Zoom]")
#         # return roi.current_mode

#     elif key == '0':  # บันทึกพิกัดจุดมาร์กเข้า config.yml
#         roi.is_confirmed = True
#         roi.current_mode = 0
        
#         if "cameras" not in config_manager.config: config_manager.config["cameras"] = {}
#         if active_camera_id not in config_manager.config["cameras"]: config_manager.config["cameras"][active_camera_id] = {}
        
#         config_manager.config["cameras"][active_camera_id]["mark_points"] = roi.mark_points
#         config_manager.config["cameras"][active_camera_id]["start_point"] = roi.start_point
#         config_manager.config["cameras"][active_camera_id]["reverse_point"] = roi.reverse_point
#         config_manager.config["cameras"][active_camera_id]["point_zoom"] = roi.point_zoom 
        
#         config_manager.save_config()
#         print(f"💾 [Config Saved] บันทึก ROI ({len(roi.mark_points)} จุด), Start Pt {roi.start_point}, Reverse Pt {roi.reverse_point} ของกล้อง '{active_camera_id}' เรียบร้อย!")
#         # return roi.current_mode    
#     elif key == 'c':  # ล้างพิกัดหน้าจอ
#         roi.clear()
        
#     elif key == 's':  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
#         print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
#         gui_thread = threading.Thread(
#             target=config_manager.open_settings,
#             kwargs={
#                 "current_cam_id": active_camera_id, 
#                 "on_close_callback":reload_config_callback
#             },
#             daemon=True
#         )
#         gui_thread.start()

#     # 4. เพิ่มปุ่มลัด 'D' บน Keyboard เพื่อเปิดหน้า Dashboard
#     # ⭕ เปลี่ยนเป็นชื่อฟังก์ชันจริงในคลาส StatsGUI เช่น:
#     elif key == 'd':
#         print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
#         stats_manager.open_dashboard() # เปิด UI ขึ้นมาโดยไม่บล็อก Main Loop  

#     elif key == 'o':
#         print("📊 กำลังเปิดหน้าต่าง Connect Database...")
#         open_ssms_gui()

#     return roi.current_mode