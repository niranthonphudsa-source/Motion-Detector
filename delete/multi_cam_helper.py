# LIB/multi_cam_helper.py
import cv2
import numpy as np

class MultiCameraManager:
    def __init__(self, config):
        self.config = config
        self.grid_slots = ["Camera_1", "None", "None", "None"] # Default 4 ช่อง
        self.caps = {}
        
    def update_grid_slots(self, grid_slots, updated_config=None):
        """อัปเดต Mapping กล้องลงช่อง Grid (เช่น ['Camera_2', 'Camera_1', 'None', 'Camera_3'])"""
        if updated_config:
            self.config = updated_config

        self.grid_slots = (grid_slots + ["None"] * 4)[:4] # การันตีว่ามี 4 ช่องเสมอ
        all_cam_configs = self.config.get("cameras", {})

        # 1. รวบรวมกล้องทั้งหมดที่ต้องเปิดใช้งานจริง (ตัด 'None' ออก)
        active_cam_ids = set([cam_id for cam_id in self.grid_slots if cam_id != "None"])

        # 2. ปิดกล้องที่ไม่อยู่ใน grid_slots ใหม่แล้ว
        cams_to_remove = [cam_id for cam_id in self.caps.keys() if cam_id not in active_cam_ids]
        for cam_id in cams_to_remove:
            if self.caps[cam_id] and self.caps[cam_id].isOpened():
                self.caps[cam_id].release()
            del self.caps[cam_id]
            print(f"🛑 [MultiCam] ปิดการเชื่อมต่อ: {cam_id}")

        # 3. เปิดกล้องใหม่ที่ถูกระบุไว้ใน Slot
        for cam_id in active_cam_ids:
            if cam_id not in self.caps or not self.caps[cam_id].isOpened():
                cam_data = all_cam_configs.get(cam_id, {})
                source = cam_data.get("source", 0)
                
                if isinstance(source, str) and source.isdigit():
                    source = int(source)

                cap = cv2.VideoCapture(source)
                self.caps[cam_id] = cap
                print(f"🎥 [MultiCam] เปิดใช้งาน {cam_id} -> Source: {source}")

    def read_frames(self):
        """อ่านเฟรมแยกตาม ID กล้องที่มีการเชื่อมต่อไว้"""
        frames = {}
        for cam_id, cap in self.caps.items():
            if cap and cap.isOpened():
                ret, frame = cap.read()
                frames[cam_id] = frame if ret else None
            else:
                frames[cam_id] = None
        return frames
    
    def update_active_cameras(self, active_cams, config):
        """
        อัปเดตรายการกล้องที่ใช้งานอยู่ และโหลด Config ของกล้องใหม่
        """
        if isinstance(active_cams, list):
            self.active_cameras = active_cams
        else:
            self.active_cameras = [active_cams]
            
        # หากในคลาสมี Logic การเปิด/ปิด VideoCapture สามารถอัปเดตต่อตรงนี้ได้
        print(f"📷 [MultiCam] อัปเดตรายการกล้องเป็น: {self.active_cameras}")

    def create_grid(self, frame_dict, target_size=(640, 360)):
        """
        นำภาพประมวลผลแล้วมาจัดลงช่อง Grid ตามลำดับใน self.grid_slots (0 ถึง 3)
        """
        grid_frames = []

        for idx, cam_id in enumerate(self.grid_slots):
            if cam_id != "None":
                frame = frame_dict.get(cam_id)
                if frame is None:
                    # กรณีกล้องดับ/อ่านไม่ได้
                    blank = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                    cv2.putText(blank, f"Grid {idx+1} ({cam_id}): NO SIGNAL", (30, target_size[1]//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    grid_frames.append(blank)
                else:
                    resized = cv2.resize(frame, target_size)
                    grid_frames.append(resized)
            else:
                # กรณีปิดช่องนี้ไว้ (None)
                blank = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                cv2.putText(blank, f"Grid {idx+1}: [DISABLED]", (30, target_size[1]//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
                grid_frames.append(blank)

        # รวมเป็น 2x2 Grid
        top_row = np.hstack((grid_frames[0], grid_frames[1]))
        bottom_row = np.hstack((grid_frames[2], grid_frames[3]))
        grid_view = np.vstack((top_row, bottom_row))

        return grid_view

    def release_all(self):
        for cap in self.caps.values():
            if cap and cap.isOpened():
                cap.release()
        self.caps.clear()