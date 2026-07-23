import cv2
import joblib
import numpy as np
import yaml
import tkinter as tk
from PIL import Image, ImageTk
from LIB.multi_cam_helper import MultiCameraManager

# ─── 1. ตัวอย่างไฟล์การตั้งค่า (Config Mockup) ───
config_data = {
    "cameras": {
        "Camera_1": {"source": 0},          # Webcam เครื่องหลัก
        "Camera_2": {"source": 1},          # Webcam ตัวที่ 2 หรือไฟล์วิดีโอ
        "Camera_3": {"source": "test.mp4"}, # ไฟล์ วิดีโอ หรือ RTSP Stream
    }
}

class MultiCamApp:
    def __init__(self, root, config):
        self.root = root
        self.root.title("Multi-Camera AI Pose Detection Studio")
        self.root.geometry("1024x600")

        # โหลดโมเดล AI ที่เทรนไว้ (ถ้าไม่มีจะรันแบบดึงภาพเปล่า)
        try:
            self.model = joblib.load("pose_classifier_1.pkl")
            print("🟢 [AI] โหลดโมเดล pose_classifier_1.pkl สำเร็จ")
        except Exception as e:
            self.model = None
            print(f"⚠️ [AI] ไม่พบไฟล์โมเดล: {e} (รันโหมดดึงภาพปกติ)")

        # เรียกใช้งาน MultiCameraManager จากคลาสที่คุณสร้างขึ้น
        self.cam_manager = MultiCameraManager(config)
        
        # ตั้งค่าผูกกล้องลง Grid Slot (เช่น ช่อง 1 ใช้ Camera_1, ช่อง 2 ใช้ Camera_2)
        self.cam_manager.update_grid_slots(["Camera_1", "Camera_2", "None", "None"])

        # UI Element สำหรับแสดงผล Grid 2x2
        self.lbl_video = tk.Label(self.root, bg="black")
        self.lbl_video.pack(fill="both", expand=True, padx=10, pady=10)

        # จัดการเมื่อปิดหน้าต่าง ให้ release กล้องทั้งหมด
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # เริ่ม Main Loop การอ่านเฟรม
        self.update_frame()

    def process_ai_detection(self, raw_frames):
        """
        นำเฟรมแต่ละกล้องมาประมวลผลผ่าน AI Detect ก่อนส่งเข้า Grid
        """
        processed_frames = {}
        for cam_id, frame in raw_frames.items():
            if frame is None:
                processed_frames[cam_id] = None
                continue

            # คัดลอกภาพมาวาดผลลัพธ์
            annotated_frame = frame.copy()

            # ----------------------------------------------------
            # 🤖 [พื้นที่ใส่ Logic AI Pose Detection]
            # 1. สกัด Keypoints พิกัดโครงกระดูก (เช่น Mediapipe Pose)
            # 2. ทำ Prediction ด้วยโมเดล: pred = self.model.predict(X_keypoints)
            # 3. วาด Bounding Box / Text บน annotated_frame
            # ----------------------------------------------------
            if self.model is not None:
                cv2.putText(
                    annotated_frame, f"AI Status: Active [{cam_id}]", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )

            processed_frames[cam_id] = annotated_frame

        return processed_frames

    def update_frame(self):
        """อ่านเฟรมจาก Manager -> ส่งประมวลผล AI -> สร้าง Grid -> แสดงบน Tkinter"""
        # 1. อ่านเฟรมจากกล้องทุกตัว
        raw_frames = self.cam_manager.read_frames()

        # 2. ส่งเฟรมเข้าประมวลผลด้วย AI
        ai_frames = self.process_ai_detection(raw_frames)

        # 3. รวมเฟรมเป็น Grid 2x2 ผ่านเมธอด create_grid ของคุณ
        grid_view = self.cam_manager.create_grid(ai_frames, target_size=(480, 270))

        # 4. แปลงภาพ OpenCV (BGR) เป็น ImageTk
        grid_rgb = cv2.cvtColor(grid_view, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(grid_rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        self.lbl_video.imgtk = imgtk
        self.lbl_video.configure(image=imgtk)

        # วนรอบการทำงานทุก 30 Milliseconds (~33 FPS)
        self.root.after(30, self.update_frame)

    def on_closing(self):
        """ปิดการเชื่อมต่อกล้องอย่างปลอดภัยก่อนปิดโปรแกรม"""
        print("🛑 กำลังปิดการเชื่อมต่อกล้องทั้งหมด...")
        self.cam_manager.release_all()
        self.root.destroy()

# ─── 🚀 สั่งรันแอปพลิเคชัน ───
if __name__ == "__main__":
    root = tk.Tk()
    app = MultiCamApp(root, config_data)
    root.mainloop()