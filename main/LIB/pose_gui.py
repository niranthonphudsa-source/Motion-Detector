import tkinter as tk
from tkinter import ttk
import cv2
import time
from PIL import Image, ImageTk
from ultralytics import YOLO
import numpy as np
from main.LIB.video_thread import VideoCaptureThread
import csv

class PoseTkinterGUI:
    def __init__(self, window, filename="pose_coordinates.csv"):
        self.window = window
        self.window.title("YOLO Pose - CSV Recording System")
        self.window.geometry("800x700") 

        self.model = YOLO('yolo26n-pose.pt')
        self.filename = filename

        # ✅ เขียน Header CSV พร้อม label
        with open(self.filename, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            header = []
            for i in range(17):  # 17 keypoints
                header.extend([f"X{i}", f"Y{i}"])
            writer.writerow(header)

        self.current_camera_index = 1
        self.cam_thread = VideoCaptureThread(self.current_camera_index)
        
        self.prev_time = 0
        self.frame_count = 0

        # ค่า label ปัจจุบัน (default = Normal)
        self.current_label = tk.StringVar()

        self.SKELETON_CONNECTIONS = [
            (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), 
            (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), 
            (13, 15), (12, 14), (14, 16)
        ]

        # Layout UI
        self.left_frame = tk.Frame(self.window)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20)

        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack()

        self.right_frame = tk.Frame(self.window)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="n")

        self.control_title = tk.Label(self.right_frame, text="แผงควบคุมระบบ", font=('Helvetica', 16, 'bold'))
        self.control_title.pack(pady=(0, 20))

        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 11), padding=10)
        
        self.btn_switch = ttk.Button(
            self.right_frame, 
            text="🔄 สลับไปกล้องถัดไป", 
            command=self.switch_camera,
            style='TButton'
        )
        self.btn_switch.pack(pady=10, fill='x')

        # # ✅ ปุ่มเลือก Label
        # ttk.Button(self.right_frame, text="Set Label: Right", 
        #            command=lambda: self.current_label.set("Right")).pack(pady=5, fill='x')
        # ttk.Button(self.right_frame, text="Set Label: Left", 
        #            command=lambda: self.current_label.set("Left")).pack(pady=5, fill='x')
        # ttk.Button(self.right_frame, text="Set Label: Normal", 
        #            command=lambda: self.current_label.set("Normal")).pack(pady=5, fill='x')

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cam_thread.get_frame()
        
        if ret and frame is not None:
            frame = cv2.resize(frame, (640, 600))
            h, w = frame.shape[:2]
            self.frame_count += 1

            current_time = time.time()
            fps = 1 / (current_time - self.prev_time) if (current_time - self.prev_time) > 0 else 0
            self.prev_time = current_time

            results = self.model(frame, imgsz=480, conf=0.8, verbose=False, stream=True)
            
            for result in results:
                if result.keypoints is not None:
                    keypoints_list = result.keypoints.xy.cpu().numpy()
                    for keypoints in keypoints_list:
                        if len(keypoints) < 17: continue
                        
                        # ✅ Normalize พิกัด
                        normalized_points = []
                        for kp in keypoints:
                            kpx, kpy = int(kp[0]), int(kp[1])
                            if kpx > 0 and kpy > 0:
                                x_norm = kpx / w
                                y_norm = kpy / h
                                normalized_points.append((x_norm, y_norm))
                                cv2.circle(frame, (kpx, kpy), 5, (255, 255, 255), cv2.FILLED)

                        # ✅ บันทึกลง CSV พร้อม label
                        row = []
                        for (x_norm, y_norm) in normalized_points:
                            row.extend([x_norm, y_norm])
                        row.append(self.current_label.get())  # ใส่ label ปัจจุบัน
                        
                        with open(self.filename, mode='a', newline='', encoding='utf-8-sig') as file:
                            writer = csv.writer(file)
                            writer.writerow(row)

                        # วาด skeleton
                        for connection in self.SKELETON_CONNECTIONS:
                            pt1_idx, pt2_idx = connection
                            x1, y1 = int(keypoints[pt1_idx][0]), int(keypoints[pt1_idx][1])
                            x2, y2 = int(keypoints[pt2_idx][0]), int(keypoints[pt2_idx][1])
                            if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                                cv2.line(frame, (x1, y1), (x2, y2), (0,255,0), 2, cv2.LINE_AA)

            cv2.putText(frame, f"FPS: {fps:.1f}", (480, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"CAM: {self.current_camera_index}", (480, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Label: {self.current_label.get()}", (20, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            
            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            imgtk = ImageTk.PhotoImage(image=pil_image)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.update_frame)

    def switch_camera(self):
        self.current_camera_index = 0 if self.current_camera_index == 1 else 1
        self.cam_thread.change_src(self.current_camera_index)
        print(f"สลับระบบ Thread ไปที่กล้องไอดี: {self.current_camera_index}")

    def on_close(self):
        self.cam_thread.release()
        self.window.destroy()
