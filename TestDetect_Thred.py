import tkinter as tk
from tkinter import ttk
import cv2
import time
import threading
from PIL import Image, ImageTk
from ultralytics import YOLO
import numpy as np

class VideoCaptureThread:
    def __init__(self, src=1):
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

    def change_src(self, src):
        self.release()
        self.cap = cv2.VideoCapture(src)
        self.is_running = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()


class PoseTkinterGUI:
    def __init__(self, window):
        self.window = window
        self.window.title("YOLO Pose - Fixed Layout System")
        
        # ขยายขนาดหน้าต่างให้กว้างขึ้น เพื่อแบ่งฝั่งซ้าย-ขวา
        self.window.geometry("800x700") 

        self.model = YOLO('yolo26n-pose.pt')
        
        self.current_camera_index = 1
        self.cam_thread = VideoCaptureThread(self.current_camera_index)
        
        self.prev_time = 0
        self.SKELETON_CONNECTIONS = [
            (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), 
            (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), 
            (13, 15), (12, 14), (14, 16)
        ]

        # =========================================================
        # 🛠️ จัดโครงสร้างหน้าจอใหม่ด้วยระบบ Grid (แบ่งซ้าย-ขวา)
        # =========================================================
        
        # ฝั่งซ้าย: สำหรับแสดงผลภาพวิดีโอจากกล้อง
        self.left_frame = tk.Frame(self.window)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20)

        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack()

        # ฝั่งขวา: สำหรับวางปุ่มควบคุมและสถานะระบบ
        self.right_frame = tk.Frame(self.window)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="n")

        # เพิ่มข้อความหัวข้อตรงฝั่งขวา
        self.control_title = tk.Label(self.right_frame, text="แผงควบคุมระบบ", font=('Helvetica', 16, 'bold'))
        self.control_title.pack(pady=(0, 20))

        # ปุ่มสลับกล้อง (ย้ายมาอยู่ฝั่งขวา ไม่โดนภาพบังแน่นอน)
        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 11), padding=10)
        
        self.btn_switch = ttk.Button(
            self.right_frame, 
            text="🔄 สลับไปกล้องถัดไป", 
            command=self.switch_camera,
            style='TButton'
        )
        self.btn_switch.pack(pady=10, fill='x')

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cam_thread.get_frame()
        
        if ret and frame is not None:
            # frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (640, 640))

            current_time = time.time()
            fps = 1 / (current_time - self.prev_time) if (current_time - self.prev_time) > 0 else 0
            self.prev_time = current_time

            results = self.model(frame, imgsz=480, verbose=False, stream=True)
            for result in results:
                if result.keypoints is not None:
                    keypoints_list = result.keypoints.xy.cpu().numpy()
                    for keypoints in keypoints_list:
                        if len(keypoints) < 11: continue
                        
                        # ดึงพิกัดจุดที่ต้องใช้ (X, Y)
                        left_shoulder = keypoints[5]   # จุดที่ 5 = ไหล่ซ้าย
                        right_shoulder = keypoints[6]  # จุดที่ 6 = ไหล่ขวา
                        right_wrist = keypoints[10]    # จุดที่ 10 = ข้อมือขวา
                        left_wrist = keypoints[9]
                        
                        status_text = "Normal"
                        theme_color = (0, 255, 0) # สีเขียวสถานะปกติ
                        
                        # ตรวจสอบก่อนว่าโมเดลตรวจเจอจุดทั้ง 3 จุดนี้จริงๆ (ค่าต้องไม่เป็น 0)
                        if left_shoulder[0] > 0 and right_shoulder[0] > 0 and right_wrist[0] > 0 and left_wrist[0] > 0:
                            
                            # 1. คำนวณความกว้างไหล่ของคนๆ นั้น (ใช้เป็นระยะอ้างอิงอัจฉริยะ)
                            shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
                            
                            # 2. คำนวณระยะห่างจริงระหว่าง "ข้อมือขวา" กับ "ไหล่ซ้าย"
                            distance_right_wrist_to_shoulder = np.linalg.norm(right_wrist - left_shoulder)
                            distance_left_wrist_to_shoulder = np.linalg.norm(right_wrist + right_shoulder)
                            

                            # 🎯 3. เช็คเงื่อนไข: ถ้าระยะห่างน้อยกว่า 60% ของความกว้างไหล่ตัวเอง (ปรับตัวเลข 0.6 ได้ตามใจชอบ)
                            if distance_right_wrist_to_shoulder < (shoulder_width * 0.6):
                                status_text = "POINT LEFT!"
                                theme_color = (255, 0, 0) # เปลี่ยนเป็นสีน้ำเงินเมื่อชี้ไปทางซ้าย

                            if distance_left_wrist_to_shoulder < (shoulder_width * 0.6):
                                status_text = "POINT RIGHT!"
                                theme_color = (255, 0, 0) # เปลี่ยนเป็นสีน้ำเงินเมื่อชี้ไปทางซ้าย
                                
                            # (Option) วาดเส้นเชื่อมพิเศษจาก ข้อมือขวา ไป ไหล่ซ้าย เพื่อให้เห็นระยะที่วัด
                            cv2.line(frame, (int(right_wrist[0]), int(right_wrist[1])), 
                                     (int(left_shoulder[0]), int(left_shoulder[1])), (0, 255, 255), 1, cv2.LINE_AA)


                        
                        # วาดเส้นโครงกระดูกมาตรฐาน
                        for connection in self.SKELETON_CONNECTIONS:
                            pt1_idx, pt2_idx = connection
                            x1, y1 = int(keypoints[pt1_idx][0]), int(keypoints[pt1_idx][1])
                            x2, y2 = int(keypoints[pt2_idx][0]), int(keypoints[pt2_idx][1])
                            if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                                cv2.line(frame, (x1, y1), (x2, y2), theme_color, 2, cv2.LINE_AA)

                        # วาดจุดข้อต่อ
                        for kp in keypoints:
                            x, y = int(kp[0]), int(kp[1])
                            if x > 0 and y > 0:
                                cv2.circle(frame, (x, y), 5, (255, 255, 255), cv2.FILLED)
                                cv2.circle(frame, (x, y), 5, theme_color, 1)

                        # วาดป้ายข้อความแสดงสถานะมุมบนซ้าย
                        cv2.rectangle(frame, (20, 20), (250, 80), theme_color, cv2.FILLED)
                        cv2.putText(frame, status_text, (25, 60), cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(frame, f"FPS: {fps:.1f}", (480, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"CAM: {self.current_camera_index}", (480, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)

            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv2_image)
            imgtk = ImageTk.PhotoImage(image=pil_image)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.update_frame)
    def switch_camera(self):
        if self.current_camera_index == 1:
            self.current_camera_index = 0
        else:
            self.current_camera_index = 1
            
        self.cam_thread.change_src(self.current_camera_index)
        print(f"สลับระบบ Thread ไปที่กล้องไอดี: {self.current_camera_index}")

    def on_close(self):
        self.cam_thread.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PoseTkinterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()