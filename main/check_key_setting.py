import threading

class KeyboardHandler:

    def __init__(
        self,
        roi,
        config_manager,
        stats_manager,
        active_camera_id,
        reload_config_callback,
        open_help_window,
        open_ssms_gui,
    ):
        self.roi = roi
        self.config_manager = config_manager
        self.stats_manager = stats_manager
        self.active_camera_id = active_camera_id
        self.reload_config_callback = reload_config_callback
        self.open_help_window = open_help_window
        self.open_ssms_gui = open_ssms_gui


    def check_key_setting(self, key):
        if key == ord('q'):
            return False
        elif key == ord('h'):  # 🌟 เพิ่มปุ่ม H สำหรับเปิด Help GUI
            print("💡 กำลังเปิดหน้าต่างคู่มือช่วยเหลือ (Help GUI)...")
            self.open_help_window()
            
        elif key == ord('1'):  # โหมดมาร์กพิกัดพื้นที่ Polygon
            self.roi.clear_roi()
            self.roi.current_mode = 1
            print("✏️ เปิดโหมดวาด Polygon ROI: คลิกสร้างรูปปิด...")

        elif key == ord('3'):  # 🌟 โหมดมาร์กจุดเริ่มเช็ก (Start Point)
            self.roi.current_mode = 2
            print("🟢 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 1: Start Check Point]")

        elif key == ord('4'):  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
            self.roi.current_mode = 3
            print("🔴 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 2: Reverse Check Point]")

        elif key == ord('5'):  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
            self.roi.current_mode = 5
            print("🔴 คลิกบนหน้าจอเพื่อกำหนด [Mark Point Zoom]")

        elif key == ord('6'):  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
            self.roi.clear_point_zoom()
            print("🔴[Cancle Mark Point Zoom]")


        elif key == ord('2'):  # บันทึกพิกัดจุดมาร์กเข้า config.yml
            self.roi.is_confirmed = True
            self.roi.current_mode = 0
            
            if "cameras" not in self.config_manager.config: self.config_manager.config["cameras"] = {}
            if self.active_camera_id not in self.config_manager.config["cameras"]: self.config_manager.config["cameras"][self.active_camera_id] = {}
            
            self.config_manager.config["cameras"][self.active_camera_id]["mark_points"] = self.roi.mark_points
            self.config_manager.config["cameras"][self.active_camera_id]["start_point"] = self.roi.start_point
            self.config_manager.config["cameras"][self.active_camera_id]["reverse_point"] = self.roi.reverse_point
            self.config_manager.config["cameras"][self.active_camera_id]["point_zoom"] = self.roi.point_zoom 
            
            self.config_manager.save_config()
            print(f"💾 [Config Saved] บันทึก ROI ({len(self.roi.mark_points)} จุด), Start Pt {self.roi.start_point}, Reverse Pt {self.roi.reverse_point} ของกล้อง '{self.active_camera_id}' เรียบร้อย!")
                
        elif key == ord('c'):  # ล้างพิกัดหน้าจอ
            self.roi.clear()
            
        elif key == ord('s'):  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
            print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
            gui_thread = threading.Thread(
                target=self.config_manager.open_settings,
                kwargs={
                    "current_cam_id": self.active_camera_id, 
                    "on_close_callback": self.reload_config_callback
                },
                daemon=True
            )
            gui_thread.start()
        # 4. เพิ่มปุ่มลัด 'D' บน Keyboard เพื่อเปิดหน้า Dashboard
        # ⭕ เปลี่ยนเป็นชื่อฟังก์ชันจริงในคลาส StatsGUI เช่น:
        elif key == ord('d'):
            print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
            self.stats_manager.open_dashboard() # เปิด UI ขึ้นมาโดยไม่บล็อก Main Loop  
    
        elif key == ord('o'):
            print("📊 กำลังเปิดหน้าต่าง Connect Database...")
            self.open_ssms_gui()

        return True