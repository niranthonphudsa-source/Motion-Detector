import tkinter as tk
from tkinter import ttk
import cv2
import time
import threading
import numpy as np
import os
from PIL import Image, ImageTk
from ultralytics import YOLO

class VideoCaptureThread:
    def __init__(self, src=1): # เปลี่ยนเป็น 0 สำหรับกล้องหลักเริ่มต้น
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = False, None
        self.is_running = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.is_running:
            self.ret, self.frame = self.cap.read()
            time.sleep(0.01)

    def get_frame(self):
        return self.ret, self.frame

    def release(self):
        self.is_running = False
        self.cap.release()


class MultiPoseTkinterGUI:
    def __init__(self, window):
        self.window = window
        self.window.title("Multi-Person Pose Tracker & Recorder")
        self.window.geometry("1100x700") 

        # โหลดโมเดล YOLO Pose
        self.model = YOLO('yolo26n-pose.pt')
        self.cam_thread = VideoCaptureThread(0)
        self.prev_time = 0

        # ค่าคู่ลำดับจุดเชื่อมต่อร่างกาย (Skeleton Connections) ทั้ง 17 จุด ของ COCO dataset
        self.SKELETON_EDGES = [
            (0, 1), (0, 2), (1, 3), (2, 4),      # ส่วนใบหน้า (ตา, หู, จมูก)
            (5, 6),                              # ไหล่ซ้าย - ไหล่ขวา
            (5, 7), (7, 9),                      # แขนซ้าย (ไหล่ -> ศอก -> ข้อมือ)
            (6, 8), (8, 10),                     # แขนขวา (ไหล่ -> ศอก -> ข้อมือ)
            (5, 11), (6, 12), (11, 12),          # ลำตัว (ไหล่ไปสะโพก)
            (11, 13), (13, 15),                  # ขาซ้าย (สะโพก -> เข่า -> ข้อเท้า)
            (12, 14), (14, 16)                   # ขาขวา (สะโพก -> เข่า -> ข้อเท้า)
        ]

        # --- 🎯 ส่วนควบคุมข้อมูลหลายคน (Multi-Person Tracking Data) ---
        self.video_writer = None
        self.is_recording = False
        self.temp_video_filename = 'temp_full_frame.mp4'
        
        # Dictionary เก็บข้อมูลท่าทางแยกตาม ID ของแต่ละคน เช่น { 1: {"Left", "Right"}, 2: {"Front"} }
        self.people_tracks = {} 
        self.required_poses = {"Right", "Left", "Front"}
        
        # เก็บรายชื่อ ID ที่ปรากฏในเฟรมปัจจุบันเพื่อเช็คว่าใครเดินออกจากกล้องไปแล้ว
        self.current_frame_ids = set()

        # จัดหน้าจอ GUI
        self.left_frame = tk.Frame(self.window)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20)
        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack()

        self.right_frame = tk.Frame(self.window)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="n")

        self.control_title = tk.Label(self.right_frame, text="ระบบตรวจจับท่าทางรายบุคคล", font=('Helvetica', 14, 'bold'))
        self.control_title.pack(pady=(0, 10))

        # สรุปสถานะของแต่ละคนบน GUI
        self.status_text = tk.Text(self.right_frame, height=15, width=40, font=('Helvetica', 10))
        self.status_text.pack(pady=5)

        self.rec_status_label = tk.Label(self.right_frame, text="🔴 ไม่มีการบันทึก", font=('Helvetica', 12), fg="gray")
        self.rec_status_label.pack(pady=10)

        self.update_frame()

    def check_pose(self, keypoints):
        """ ตรวจสอบการชี้ โดยใช้พิกัด 'ข้อมือขวา' เทียบกับจุดอื่น """
        if len(keypoints) < 11:
            return None

        left_sholder = keypoints[5]   # ไหล่ซ้าย
        right_sholder = keypoints[6]   # ไหล่ขวา
        right_wrist = keypoints[10]  # ข้อมือขวา

        conf_threshold = 0.5
        
        if right_wrist[2] > conf_threshold and right_sholder[2] > conf_threshold and left_sholder[2] > conf_threshold:
            right_wrist_x, right_wrist_y = right_wrist[0], right_wrist[1]
            right_sholder_x, right_sholder_y = right_sholder[0], right_sholder[1]
            left_sholder_x, left_sholder_y = left_sholder[0], left_sholder[1]

            shoulder_width = abs(left_sholder_x - right_sholder_x)
            # 1. ชี้ไปทางขวา
            offset_side = shoulder_width * 0.4
            if right_wrist_x > right_sholder_x + offset_side and abs(right_wrist_y - right_sholder_y) < shoulder_width:
                return "Right"

            # 2. ชี้ไปทางซ้าย (ข้อมือขวายื่นตัดข้ามลำตัวไปทางซ้าย)
            if right_wrist_x < left_sholder_x - offset_side and abs(right_wrist_y - left_sholder_y) < shoulder_width:
                return "Left"

            # 🎯 3. ชี้มาข้างหน้า: เช็คว่าใกล้เคียงกึ่งกลางอก (Chest Center)
            # หาจุดกึ่งกลางระหว่างไหล่ซ้ายและไหล่ขวา (พิกัดหน้าอกโดยประมาณ)
            chest_x = (left_sholder_x + right_sholder_x) / 2
            chest_y = (left_sholder_y + right_sholder_y) / 2

            # กำหนดระยะบวกลบ (Tolerance) ตามความกว้างของไหล่
            # เช่น ยอมให้เบี่ยงซ้าย-ขวา ได้ 35% และ สูง-ต่ำ (บน-ล่าง) ได้ 40% ของความกว้างไหล่
            x_tolerance = shoulder_width * 0.35
            y_tolerance = shoulder_width * 0.40

            # ตรวจสอบว่า ข้อมือขวา (right_wrist) อยู่ในขอบเขตบวกลบของกึ่งกลางอกหรือไม่
            if (chest_x - x_tolerance < right_wrist_x < chest_x + x_tolerance) and \
               (chest_y - y_tolerance < right_wrist_y < chest_y + y_tolerance):
                return "Front"

        return None
    def update_frame(self):
        ret, frame = self.cam_thread.get_frame()
        
        if ret and frame is not None:
            current_time = time.time()
            fps = 1 / (current_time - self.prev_time) if (current_time - self.prev_time) > 0 else 0
            self.prev_time = current_time
            
            frame_resized = cv2.resize(frame, (640, 640))

            # 🎯 เปลี่ยนมาใช้ .track() เพื่อเปิดระบบ Tracking ระบุ ID ให้กับคนในกล้อง
            results = self.model.track(frame_resized, imgsz=480, persist=True, verbose=False, stream=True)
            
            self.current_frame_ids.clear()
            any_person_in_frame = False

            for result in results:
                # ตรวจสอบว่าตรวจเจอคนและมีตาราง ID หรือไม่
                if result.boxes is not None and result.boxes.id is not None and result.keypoints is not None:
                    any_person_in_frame = True
                    
                    boxes = result.boxes.xyxy.cpu().numpy()
                    ids = result.boxes.id.int().cpu().numpy()
                    keypoints_all = result.keypoints.data.cpu().numpy()

                    for box, idx, keypoints in zip(boxes, ids, keypoints_all):
                        self.current_frame_ids.add(idx)
                        
                        # ถ้าเป็นคนใหม่ที่เพิ่งเคยเจอ ให้สร้างเซตเก็บท่าทางว่างๆ ไว้
                        if idx not in self.people_tracks:
                            self.people_tracks[idx] = set()

                        # ตรวจสอบท่าทางจากข้อมือขวา
                        current_pose = self.check_pose(keypoints)
                        if current_pose:
                            self.people_tracks[idx].add(current_pose)

                        # วาดกล่องข้อความและเลข ID บนตัวคนในเฟรมหลัก
                        is_complete = self.required_poses.issubset(self.people_tracks[idx])
                        box_color = (0, 255, 0) if is_complete else (0, 165, 255) # เขียวถ้าครบ ส้มถ้ายังไม่ครบ
                        
                        cv2.rectangle(frame_resized, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), box_color, 2)
                        
                        status_str = f"ID:{idx} {'[COMPLETE]' if is_complete else 'Incomplete'}"
                        cv2.putText(frame_resized, status_str, (int(box[0]), int(box[1]) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

                        # 🌐 --- เพิ่มส่วนการวาดโครงกระดูกและจุดร่างกาย 17 จุด ---
                        conf_threshold = 0.5
                        
                        # 1. วาดเส้นเชื่อมต่อ (Skeleton)
                        for edge in self.SKELETON_EDGES:
                            p1_idx, p2_idx = edge
                            p1 = keypoints[p1_idx]
                            p2 = keypoints[p2_idx]
                            
                            # วาดเส้นก็ต่อเมื่อทั้งสองจุดมีความแม่นยำ (Confidence) เกินเกณฑ์
                            if p1[2] > conf_threshold and p2[2] > conf_threshold:
                                cv2.line(frame_resized, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255, 255, 255), 2)

                        # 2. วาดจุดร่างกายทั้ง 17 จุด
                        for i, kp in enumerate(keypoints):
                            x, y, conf = kp
                            if conf > conf_threshold:
                                # ไฮไลต์ข้อมือขวา (จุดที่ 10) เป็นสีแดงพิเศษ ส่วนจุดอื่นเป็นสีน้ำเงินสว่าง
                                circle_color = (0, 0, 255) if i == 10 else (255, 255, 0)
                                circle_radius = 5 if i == 10 else 4
                                cv2.circle(frame_resized, (int(x), int(y)), circle_radius, circle_color, -1)

            # --- 📝 อัปเดตตารางสถานะทุกคนลงบนหน้าจอ GUI ---
            self.status_text.delete('1.0', tk.END)
            self.status_text.insert(tk.END, " สรุปผลรายบุคคล (ID):\n")
            self.status_text.insert(tk.END, "----------------------------------------\n")
            for p_id, poses in self.people_tracks.items():
                done = self.required_poses.issubset(poses)
                check_mark = "✅ ครบแล้ว (ผ่าน)" if done else f"❌ ยังขาดอยู่ {list(self.required_poses - poses)}"
                self.status_text.insert(tk.END, f"👤 Person ID {p_id}: {check_mark}\n")

            # --- 💾 ลอจิกการบันทึกวิดีโอแบบเต็มเฟรมตามเงื่อนไข ---
            if any_person_in_frame:
                if not self.is_recording:
                    # เปิดไฟล์บันทึกภาพขนาดเต็มเฟรม (640x640) ไว้ล่วงหน้า
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self.video_writer = cv2.VideoWriter(self.temp_video_filename, fourcc, 20.0, (640, 640))
                    self.is_recording = True
                    self.rec_status_label.config(text="⏺️ กำลังบันทึกเหตุการณ์รวม...", fg="orange")
                
                # เขียนเฟรมเต็มลงไป
                self.video_writer.write(frame_resized)
            else:
                # เมื่อกล้องว่างเปล่า (ไม่มีใครอยู่เลย) -> ประเมินผลลัพธ์วิดีโอทันที
                if self.is_recording:
                    self.video_writer.release()
                    self.is_recording = False
                    self.evaluate_video_saving()

            # แสดงผลภาพบน GUI
            cv2.putText(frame_resized, f"FPS: {fps:.1f}", (480, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            cv2_image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            imgtk = ImageTk.PhotoImage(image=pil_image)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.update_frame)

    def evaluate_video_saving(self):
        """ ตรวจสอบว่าในบรรดาคนทั้งหมดที่เคยเข้ามา มีใครทำไม่ครบ 3 ท่าทางหรือไม่ """
        if not self.people_tracks:
            if os.path.exists(self.temp_video_filename): os.remove(self.temp_video_filename)
            return

        all_completed = True
        for p_id, poses in self.people_tracks.items():
            if not self.required_poses.issubset(poses):
                all_completed = False
                break

        if all_completed:
            if os.path.exists(self.temp_video_filename):
                os.remove(self.temp_video_filename)
            self.rec_status_label.config(text="✅ ทุกคนทำครบเงื่อนไข: ไม่บันทึกวิดีโอ", fg="green")
        else:
            final_filename = f"failed_poses_session_{int(time.time())}.mp4"
            if os.path.exists(self.temp_video_filename):
                os.rename(self.temp_video_filename, final_filename)
            self.rec_status_label.config(text=f"⚠️ มีคนทำไม่ครบ! เซฟไฟล์ {final_filename}", fg="red")
        
        self.people_tracks.clear()

    def on_close(self):
        if self.is_recording and self.video_writer is not None:
            self.video_writer.release()
            if os.path.exists(self.temp_video_filename):
                os.remove(self.temp_video_filename)
        self.cam_thread.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiPoseTkinterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()