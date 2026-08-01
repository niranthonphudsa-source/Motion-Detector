import threading
import callback_command.callback_command as clb

from LIB.config_loader_start import AppConfig
from LIB.roi_handler import ROIHandler
from LIB.stats_gui import StatsGUI, StatsManager

app_config = AppConfig(r"setting\config.yml")
config_manager = app_config.config_manager
active_camera_id = app_config.active_camera_id


roi = ROIHandler()

stats_manager = StatsManager(db_path=r"setting\inspection_stats.db")
class KeyboardHandler:

    def __init__(self, key):
        self.key = key

    def check_key_setting(self):
        if self.key == 'q':
            pass
        elif self.key == 'h':  # 🌟 เพิ่มปุ่ม H สำหรับเปิด Help GUI
            print("💡 กำลังเปิดหน้าต่างคู่มือช่วยเหลือ (Help GUI)...")
            clb.open_help_window()
            
        elif self.key == '1':  # โหมดมาร์กพิกัดพื้นที่ Polygon
            roi.clear_roi()
            roi.current_mode = 1
            print("✏️ เปิดโหมดวาด Polygon ROI: คลิกสร้างรูปปิด...")

        elif self.key == '3':  # 🌟 โหมดมาร์กจุดเริ่มเช็ก (Start Point)
            roi.current_mode = 2
            print("🟢 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 1: Start Check Point]")

        elif self.key == '4':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
            roi.current_mode = 3
            print("🔴 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 2: Reverse Check Point]")

        elif self.key == '5':  # 🌟 โหมดมาร์กจุด Zoom
            roi.current_mode = 5
            print("🔴 คลิกบนหน้าจอเพื่อกำหนด [Mark Point Zoom]")

        elif self.key == '6':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
            roi.clear_point_zoom()
            print("🔴[Cancle Mark Point Zoom]")


        elif self.key == '2':  # บันทึกพิกัดจุดมาร์กเข้า config.yml
            roi.is_confirmed = True
            roi.current_mode = 0
            
            if "cameras" not in config_manager.config: config_manager.config["cameras"] = {}
            if active_camera_id not in config_manager.config["cameras"]: config_manager.config["cameras"][active_camera_id] = {}
            
            config_manager.config["cameras"][active_camera_id]["mark_points"] = roi.mark_points
            config_manager.config["cameras"][active_camera_id]["start_point"] = roi.start_point
            config_manager.config["cameras"][active_camera_id]["reverse_point"] = roi.reverse_point
            config_manager.config["cameras"][active_camera_id]["point_zoom"] = roi.point_zoom 
            
            config_manager.save_config()
            print(f"💾 [Config Saved] บันทึก ROI ({len(roi.mark_points)} จุด), Start Pt {roi.start_point}, Reverse Pt {roi.reverse_point} ของกล้อง '{active_camera_id}' เรียบร้อย!")
                
        elif self.key == ord('c'):  # ล้างพิกัดหน้าจอ
            roi.clear()
            
        elif self.key == 's':  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
            print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
            gui_thread = threading.Thread(
                target=config_manager.open_settings,
                kwargs={
                    "current_cam_id": active_camera_id, 
                    "on_close_callback": reload_config_callback
                },
                daemon=True
            )
            gui_thread.start()
        # 4. เพิ่มปุ่มลัด 'D' บน Keyboard เพื่อเปิดหน้า Dashboard
        # ⭕ เปลี่ยนเป็นชื่อฟังก์ชันจริงในคลาส StatsGUI เช่น:
        elif self.key == 'd':
            print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
            stats_manager.open_dashboard() # เปิด UI ขึ้นมาโดยไม่บล็อก Main Loop  
    
        elif self.key == 'o':
            print("📊 กำลังเปิดหน้าต่าง Connect Database...")
            clb.open_ssms_gui()
        return True