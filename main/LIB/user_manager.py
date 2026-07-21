import os
import shutil
import time
import cv2
import numpy as np

class UserStateManager:
    def __init__(self, check_pose, fourcc, ok_display_time, max_lost_time, max_distance, buffer_output_time=3):
        self.user_states = {}
        self.check_pose = check_pose
        self.fourcc = fourcc
        self.ok_display_time = ok_display_time
        self.max_lost_time = max_lost_time
        self.max_distance = max_distance
        self.buffer_output_time = buffer_output_time # 👈 กำหนดไว้เป็น 5 วินาที
        self.save_ng = False
        self.save_ok = False
    def get_or_recover_id(self, current_id, current_frame_active_ids, point_pose):
        if len(point_pose) < 17:
            return None

        current_time = time.time()
        curr_x, curr_y = int(point_pose[16][0]), int(point_pose[16][1])

        # 1. เช็กว่า ID นี้มีอยู่แล้วในระบบหรือไม่
        if current_id in self.user_states:
            return self.user_states[current_id]

        # 2. กรณีเป็น ID ใหม่ -> ลองค้นหา ID เก่าที่หายไปเพื่อสวมรอย (Recover)
        reclaimed_id = None
        for old_id, old_state in self.user_states.items():
            if old_id not in current_frame_active_ids:
                if old_state.get("last_seen_time") is not None:
                    time_diff = current_time - old_state["last_seen_time"]
                    if time_diff < self.max_lost_time and old_state["was_inside_last_frame"]:
                        if old_state.get("last_position") is not None:
                            old_x, old_y = old_state["last_position"]
                            distance = np.sqrt((curr_x - old_x)**2 + (curr_y - old_y)**2)
                            if distance < self.max_distance:
                                reclaimed_id = old_id
                                break

        if reclaimed_id is not None:
            self.user_states[current_id] = self.user_states.pop(reclaimed_id)
            # 🌟 หากกู้คืน ID ได้สำเร็จในระยะเวลา 5 วินาที ให้ยกเลิกการปิดไฟล์อัดวิดีโอเพื่ออัดต่อยาวๆ
            self.user_states[current_id]["is_terminating"] = False
            self.user_states[current_id]["termination_start_time"] = None
            print(f"🔄 [ID Recovered] กู้คืนข้อมูลสำเร็จ: ID {reclaimed_id} -> ID {current_id}")
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
                "is_terminating": False,          # สถานะว่ากำลังนับถอยหลัง 5 วินาทีเพื่อปิดไฟล์หรือไม่
                "termination_start_time": None,   # เวลาเริ่มนับถอยหลัง
                "last_logged_sec": -1             # ตัวแปรช่วยควบคุม log
            }
        return self.user_states[current_id]

    def update_user_video(self, user_id, frame, is_inside_roi):
        """
        🎬 ฟังก์ชันจัดการการเขียนวิดีโอ (ให้เรียกใช้งานทุกๆ เฟรมในลูปหลัก)
        """
        state = self.user_states.get(user_id)
        if not state:
            return

        current_time = time.time()
        height, width = frame.shape[:2]

        # ─── 1. จังหวะอยู่ในจุดเช็ก (ROI = True) ───
        if is_inside_roi:
            # ถ้าก้าวเข้ามาในจุดเช็กแล้วยังไม่มีการเปิดไฟล์วิดีโอ -> เริ่มสร้างไฟล์ทันที!
            if state["writer"] is None:
                os.makedirs("temp_video", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = os.path.join("temp_video", f"user_{user_id}_{timestamp}.mp4")
                
                # กำหนด FPS เช่น 20.0 (ให้ปรับตามกล้องจริง)
                state["writer"] = cv2.VideoWriter(filename, self.fourcc, 20.0, (width, height))
                state["video_filename"] = filename
                print(f"🎥 [Start Recording] ID {user_id} เข้าจุดเช็ก เริ่มบันทึกวิดีโอ -> {filename}")

            # ถ้าเคยออกไปแล้วเดินกลับเข้ามาใหม่ภายใน 5 วินาที -> ให้ยกเลิกการนับถอยหลังปิดไฟล์
            if state["is_terminating"]:
                state["is_terminating"] = False
                state["termination_start_time"] = None
                print(f"⏩ ID {user_id} กลับเข้ามาในจุดเช็กอีกครั้ง ยกเลิกการนับถอยหลัง 5 วินาที")

        # ─── 2. จังหวะก้าวออกจากจุดเช็ก (ROI = False) ───
        else:
            # ถ้าเคยมี่การอัดวิดีโออยู่ แล้วก้าวออกเป็นเฟรมแรก -> เริ่มนับถอยหลัง 5 วินาที
            if state["writer"] is not None and not state["is_terminating"]:
                state["is_terminating"] = True
                state["termination_start_time"] = current_time
                print(f"⏱️ ID {user_id} ออกจากจุดเช็ก เริ่มนับถอยหลังบันทึกแถมอีก {self.buffer_output_time} วินาที")

        # ─── 3. บันทึกภาพลงไฟล์ (ถ้ายังมี VideoWriter เปิดอยู่ ไม่ว่าจะอยู่ในจุดเช็ก หรืออยู่นอกจุดเช็กแถม 5 วินาที) ───
        if state["writer"] is not None:
            state["writer"].write(frame)

    def update_tracking_data(self, state, is_inside, point_pose):
        """อัปเดตสถานะและพิกัดล่าสุดของบุคคล"""
        state["was_inside_last_frame"] = is_inside
        state["last_seen_time"] = time.time()
        
        # คำนวณจุดศูนย์กลาง (เช่น จุดสะโพกหรือค่าเฉลี่ยร่าง) เพื่อใช้ในการคำนวณระยะทาง
        valid_pts = [pt for pt in point_pose if pt[0] > 0 and pt[1] > 0]
        if valid_pts:
            avg_x = sum(p[0] for p in valid_pts) / len(valid_pts)
            avg_y = sum(p[1] for p in valid_pts) / len(valid_pts)
            state["last_position"] = (avg_x, avg_y)

            
    def handle_lost_people(self, current_frame_active_ids, save_ok, save_ng, stats_db=None, camera_id="Camera_1"):
        self.save_ok = save_ok 
        self.save_ng = save_ng
        current_time = time.time()

        for active_id, active_state in list(self.user_states.items()):
            
            # ตรวจสอบคนที่อยู่ในช่วงนับถอยหลังปิดไฟล์
            if active_state["is_terminating"] and active_state["termination_start_time"] is not None:
                elapsed_time = current_time - active_state["termination_start_time"]
                remaining = max(0.0, self.buffer_output_time - elapsed_time)
                
                current_sec = int(elapsed_time)
                if current_sec != active_state.get("last_logged_sec", -1):
                    active_state["last_logged_sec"] = current_sec
                    print(f"⏳ ID {active_id} กำลังอัดวิดีโอแถมท้าย.. เหลืออีก {remaining:.1f} วินาที")

                # 🏁 เมื่อครบเวลาบันทึกแถมพอดี -> ปิดวิดีโอ ย้ายไฟล์ และบันทึก Log
                if elapsed_time >= self.buffer_output_time:
                    # 1. คืนทรัพยากร VideoWriter
                    if active_state["writer"] is not None:
                        active_state["writer"].release()
                        active_state["writer"] = None
                        print(f"🛑 [Stop Recording] บันทึกแถมครบ {self.buffer_output_time} วินาทีแล้ว ปิดไฟล์วิดีโอ ID {active_id}")

                    # 2. บันทึก LOG สถิติลง SQLite Database
                    if stats_db is not None:
                        final_status = active_state["confirm"]  # "OK" หรือ "NG"
                        stats_db.log_event(camera_id, final_status, active_id)
                        print(f"📊 [Stats Logged] Cam: {camera_id} | ID: {active_id} | Status: {final_status}")

                    # 3. ตรวจสอบเงื่อนไขการย้ายไฟล์วิดีโอ
                    # 3. ตรวจสอบเงื่อนไขการย้าย/คัดลอกไฟล์วิดีโอ
                    is_ok = (active_state["confirm"] == "OK")
                    should_save = self.save_ok if is_ok else self.save_ng

                    temp_file = active_state["video_filename"]

                    if temp_file and os.path.exists(temp_file):
                        base_filename = os.path.basename(temp_file)
                        dest_folder = "video_ok" if is_ok else "video_ng"
                        os.makedirs(dest_folder, exist_ok=True)
                        dest_path = os.path.join(dest_folder, base_filename)
                        
                        # คัดลอกไฟล์ไปยังโฟลเดอร์ปลายทาง โดยไม่ลบไฟล์ต้นฉบับเดิม
                        if should_save:
                            try:
                                shutil.copy(temp_file, dest_path)
                                print(f"📁 [SUCCESS] คัดลอกไฟล์วิดีโอสำเร็จไปที่: {dest_path}")
                            except Exception as e:
                                print(f"❌ [ERROR] ไม่สามารถคัดลอกไฟล์ได้: {e}")
                        else:
                            # ถ้าผู้ใช้สั่งไม่เซฟ (Flag = False) ให้ลบไฟล์ชั่วคราวทิ้งทันที ไม่ให้เปลืองพื้นที่ disk
                            try:
                                os.remove(temp_file)
                                print(f"🗑️ [CLEANUP] ลบไฟล์ชั่วคราวเนื่องจากตั้งค่าไม่บันทึก {dest_folder}: {temp_file}")
                            except Exception as e:
                                print(f"❌ [ERROR] ลบไฟล์ชั่วคราวไม่สำเร็จ: {e}")

                    # 4. Reset ค่าเพื่อเตรียมรับการทำงานรอบใหม่
                    active_state["video_filename"] = None
                    active_state["is_terminating"] = False
                    active_state["termination_start_time"] = None
                    active_state["last_logged_sec"] = -1
                    if active_state["confirm"] != "OK":
                        active_state["valaus_last"] = []
    
    def close_all_writers(self):
        """
        สั่งปิดฟังก์ชันการเขียนไฟล์ทั้งหมดเมื่อกดปิดโปรแกรม
        """
        for active_id, active_state in self.user_states.items():

            if active_state["writer"] is not None:

                active_state["writer"].release()