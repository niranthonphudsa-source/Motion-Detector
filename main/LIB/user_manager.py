# LIB/user_manager.py
import os
import shutil
import time
import cv2
import numpy as np

class UserStateManager:
    def __init__(self, check_pose, fourcc, ok_display_time, max_lost_time, max_distance, buffer_output_time):
        # """
        # คลาสสำหรับจัดการสถานะ, วิดีโอไรเตอร์, และตรรกะสวมรอย ID แบบ Multi-person
        # """
        self.user_states = {}
        self.check_pose = check_pose
        self.fourcc = fourcc
        self.ok_display_time = ok_display_time
        self.max_lost_time = max_lost_time
        self.max_distance = max_distance
        self.buffer_output_time = buffer_output_time # 👈 ผูกค่าไว้ใช้งาน

    def _safe_move_file(self, src, dst, retries=10, delay=0.5):
        """ พยายามย้ายไฟล์จนกว่าจะสำเร็จ เพื่อแก้ปัญหาไฟล์โดนล็อกขณะบันทึก """
        for i in range(retries):
            try:
                shutil.move(src, dst)
                print(f"✅ ย้ายไฟล์สำเร็จในความพยายามครั้งที่ {i+1}")
                return True
            except (OSError, PermissionError) as e:
                # ถ้าไฟล์ยังถูกล็อกอยู่ (OS กำลังเขียนไฟล์) ให้รอแล้วลองใหม่
                time.sleep(delay)
        print(f"❌ ย้ายไฟล์ไม่สำเร็จหลังจากพยายาม {retries} ครั้ง: {e}")
        return False

    def get_or_recover_id(self, current_id, current_frame_active_ids, point_pose):
        # """
        # ตรรกะกู้คืน ID: หากพบ ID ใหม่เข้ามา จะเช็คว่ามี ID เก่าที่เพิ่งหายไปในตำแหน่งใกล้เคียงกันหรือไม่
        # หากใช่ จะทำสวมรอยดึงประวัติเดิมกลับมาทันที
        # """
        # ป้องกันพิกัดข้อผิดพลาด
        if len(point_pose) < 17:
            return None

        current_time = time.time()
        curr_x, curr_y = int(point_pose[16][0]), int(point_pose[16][1]) # จุดอ้างอิง: เท้าข้อ 16

        # 1. เช็คว่า ID นี้มีอยู่แล้วในระบบหรือไม่
        if current_id in self.user_states:
            return self.user_states[current_id]

        # 2. กรณีเป็น ID ใหม่ -> ลองค้นหา ID เก่าที่หายไปเพื่อสวมรอย (Recover)
        reclaimed_id = None
        for old_id, old_state in self.user_states.items():
            # เงื่อนไขสำคัญ: ID เก่านั้นต้องไม่อยู่ในเฟรมปัจจุบัน (หายตัวไปแล้ว)
            if old_id not in current_frame_active_ids:
                if old_state.get("last_seen_time") is not None:
                    time_diff = current_time - old_state["last_seen_time"]
                    
                    # หายไปไม่เกินเวลาที่กำหนด และเฟรมสุดท้ายก่อนหายเคยอยู่ในจุดตรวจ (ROI)
                    if time_diff < self.max_lost_time and old_state["was_inside_last_frame"]:
                        if old_state.get("last_position") is not None:
                            old_x, old_y = old_state["last_position"]
                            
                            # คำนวณระยะห่าง Euclidean Distance
                            distance = np.sqrt((curr_x - old_x)**2 + (curr_y - old_y)**2)
                            if distance < self.max_distance:
                                reclaimed_id = old_id
                                break

        if reclaimed_id is not None:
            self.user_states[current_id] = self.user_states.pop(reclaimed_id)
            # 🌟 ถ้ากู้คืน ID กลับมาได้สำเร็จ ให้ยกเลิกการนับเวลาถอยหลังปิดไฟล์ทันที
            self.user_states[current_id]["is_terminating"] = False
            self.user_states[current_id]["termination_start_time"] = None
            print(f"🔄 [ID Recovered] กู้คืนข้อมูลสำเร็จ: ID {reclaimed_id} สลับเป็น ID ใหม่ {current_id}")
        else:
            self.user_states[current_id] = {
                "valaus_last": [],
                "confirm": "NG",
                "is_ok_holding": False,
                "ok_start_time": 0,
                "video_filename": None,
                "writer": None,
                "was_inside_last_frame": False,
                "last_seen_time": None,
                "last_position": None,
                "is_terminating": False,            # 👈 เช็คว่ากำลังอยู่ในช่วงหน่วงเวลาปิดไฟล์ไหม
                "termination_start_time": None     # 👈 เวลาที่เริ่มหน่วงเพื่อปิดไฟล์
            }
        return self.user_states[current_id]

    def update_tracking_data(self, state, people_in_rectangle, point_pose):
        """
        อัปเดตข้อมูลพิกัดและเวลาของเฟรมปัจจุบันฝังลงไปใน state เผื่อหลุดในเฟรมถัดไป
        """
        state["last_seen_time"] = time.time()
        if len(point_pose) >= 17:
            state["last_position"] = (int(point_pose[16][0]), int(point_pose[16][1]))
        state["was_inside_last_frame"] = people_in_rectangle

    def handle_lost_people(self, current_frame_active_ids):
        current_time = time.time()
        for active_id, active_state in list(self.user_states.items()):
            
            # ─── กรณีที่ 1: อยู่ในช่วงหน่วงเวลาอัดต่อหลังจากเดินออก (Buffer Time) ───
            if active_state["is_terminating"] and active_state["termination_start_time"] is not None:
                elapsed_time = current_time - active_state["termination_start_time"]
                
                if int(elapsed_time) % 2 == 0: 
                    remaining = max(0, self.buffer_output_time - elapsed_time)
                    print(f"⏳ ID {active_id} กำลังนับถอยหลังอัดแถมท้าย.. เหลืออีก {remaining:.1f} วินาที")

                if elapsed_time >= self.buffer_output_time:
                    if active_state["writer"] is not None:
                        active_state["writer"].release()
                        active_state["writer"] = None
                        
                        if active_state["video_filename"] and os.path.exists(active_state["video_filename"]):
                            base_filename = os.path.basename(active_state["video_filename"])
                            dest_folder = "video_ok" if active_state["confirm"] == "OK" else "video_ng"
                            dest_path = os.path.join(dest_folder, base_filename)
                            
                            # 🔄 เรียกใช้ฟังก์ชันย้ายไฟล์แบบเช็คสถานะล็อก (Retry Move)
                            self._safe_move_file(active_state["video_filename"], dest_path)
                        
                        # ล้างค่าหลังทำงานเสร็จ
                        active_state["video_filename"] = None
                        active_state["is_terminating"] = False
                        active_state["termination_start_time"] = None
                        if active_state["confirm"] != "OK":
                            active_state["valaus_last"] = []
                
                # บังคับข้ามการเช็ค Lost Timeout ด้านล่างเพื่อส่งผ่านการบันทึกแถมท้ายจนสมบูรณ์
                continue 
            
            # ─── กรณีที่ 2: คนหายตัวไปจากกล้องดื้อๆ (Lost Tracking Timeout) ───
            if active_id not in current_frame_active_ids:
                if active_state["last_seen_time"] is not None:
                    time_lost_duration = current_time - active_state["last_seen_time"]
                    
                    if time_lost_duration > self.max_lost_time and active_state["writer"] is not None:
                        active_state["writer"].release()
                        active_state["writer"] = None
                        
                        if active_state["video_filename"] and os.path.exists(active_state["video_filename"]):
                            base_filename = os.path.basename(active_state["video_filename"])
                            dest_folder = "video_ok" if active_state["confirm"] == "OK" else "video_ng"
                            dest_path = os.path.join(dest_folder, base_filename)
                            
                            # 🔄 เรียกใช้ฟังก์ชันย้ายไฟล์แบบเช็คสถานะล็อก (Retry Move)
                            self._safe_move_file(active_state["video_filename"], dest_path)
                        
                        # ล้างค่าสถานะป้องกันลูปค้างคาสมบูรณ์
                        active_state["video_filename"] = None
                        active_state["was_inside_last_frame"] = False
                        if active_state["confirm"] != "OK":
                            active_state["valaus_last"] = []

    def close_all_writers(self):
        """
        สั่งปิดฟังก์ชันการเขียนไฟล์ทั้งหมดเมื่อกดปิดโปรแกรม
        """
        for active_id, active_state in self.user_states.items():
            if active_state["writer"] is not None:
                active_state["writer"].release()