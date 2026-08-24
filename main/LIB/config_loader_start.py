# setting/config_loader_start.py
import os
from LIB.config_gui import ConfigGUI

base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
grandparent_dir = os.path.dirname(parent_dir)

root_path = grandparent_dir
config_dir = os.path.join(root_path, "setting", "config.yml")
class AppConfig:
    def __init__(self, config_path=config_dir):
        self.config_path = config_path
        self.config_manager = ConfigGUI()
        self.config = self.config_manager.config
        
        # ตัวแปรที่จะดึงไปใช้งานหลัก
        self.active_camera_id = ""
        self.camera = {}
        self.source = 0
        self.save_ok_flag = False
        self.save_ng_flag = False
        self.model_sklearn = ""
        self.type = None
        self.reverse_point = None
        # รันการตั้งค่าเริ่มต้นทันทีที่เรียกใช้ Class
        self.load_initial_settings()

    def load_initial_settings(self):
        """โหลดและเตรียมค่า Config ทั้งหมด"""
        cameras_dict = self.config.get("cameras", {})
        
        if not cameras_dict:
            self.active_camera_id = "Camera_1"
            self.config["cameras"] = {
                self.active_camera_id: {
                    "source": 0, 
                    "save_ok": False, 
                    "save_ng": False, 
                    "mark_points": [],
                    "start_point": None,
                    "reverse_point": None,
                    "Type": "Video"
                }
            }
        else:
            configured_camera_id = self.config.get("global", {}).get("default_camera_id")
            if configured_camera_id in cameras_dict:
                self.active_camera_id = configured_camera_id
            else:
                # รองรับ config เก่าที่ยังไม่มี default_camera_id
                self.active_camera_id = list(cameras_dict.keys())[0]

        self.camera = self.config["cameras"][self.active_camera_id]
        self.source = self.camera.get("source", 0)
        self.type = self.camera.get("Type", 0)
        self.reverse_point = self.camera.get("reverse_point", None)

        # อ่านค่าการบันทึกวิดีโอ
        self.save_ok_flag = self.camera.get("save_ok", False)
        self.save_ng_flag = self.camera.get("save_ng", False)

        # โหลดโมเดล AI
        model_path = self.config.get("model", {}).get("Model_path_1", {})
        raw_model_path = model_path.get("source", "")

        if raw_model_path:
            # ถ้าเป็น Absolute Path อยู่แล้วให้ใช้ค่านั้น แต่ถ้าเป็น Relative Path ให้เอามาต่อกับ PROJECT_ROOT
            if os.path.isabs(raw_model_path):
                self.model_sklearn = raw_model_path
            else:
                self.model_sklearn = os.path.abspath(os.path.join(root_path, raw_model_path))
        else:
            self.model_sklearn = ""

        # ปริ้นท์สรุปสถานะเมื่อเริ่มโปรแกรม
        self.print_status()

    def print_status(self):
        """แสดงสถานะระบบบน Terminal"""
        print("=" * 50)
        print(f"🚀 [System Starting] กำลังเปิดกล้อง: {self.active_camera_id}")
        print(f"📹 Source: {self.source}")
        print(f"⚙️ สเตตัสการบันทึก: Save OK={self.save_ok_flag}, Save NG={self.save_ng_flag}")
        print(f"🤖 Model Path: {self.model_sklearn}")
        print(f"🤖 Type Camera: {self.type}")
        print(f"🤖 Reverse Camera: {self.reverse_point}")
        
        print("=" * 50) 