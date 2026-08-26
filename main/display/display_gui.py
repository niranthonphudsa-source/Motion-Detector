import cv2
import queue
import tkinter as tk
import numpy as np
import os

from tkinter import ttk
from PIL import Image, ImageOps, ImageTk

class DisplayGui:

    def __init__(self, current_mode, fps, fps_sec, frame_queue=None, key_queue=None, mouse_queue=None, stop_event=None):
        # ─── โทนสีหลัก (White & Blue Theme) ───
        BG_COLOR = "#F8FAFC"        # พื้นหลังหลัก
        PANEL_COLOR = "#FFFFFF"     # พื้นหลังกล่องการ์ด
        BORDER_COLOR = "#E2E8F0"    # สีขอบกล่อง
        TEXT_MAIN = "#0F172A"       # สีข้อความหลัก
        TEXT_MUTED = "#64748B"      # สีข้อความรอง
        PRIMARY_BLUE = "#2563EB"    # สีน้ำเงินหลัก
        TITLE_BLUE = "#1E3A8A"      # สีกรมท่าสำหรับหัวข้อ

        # --- 1. การตั้งค่าหน้าต่างหลัก (Main Window) ---
        # --- 1. การตั้งค่าหน้าต่างหลัก (Main Window) ---
        self.root = tk.Tk()
        self.root.title("Aoyama Detection System")
        self.root.geometry("1920x1080")
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        # สั่งให้เริ่มต้นด้วยโหมดเต็มจอ
        self.root.attributes('-fullscreen', True)

        # ผูกปุ่ม F11 สำหรับสลับเต็มจอ / ปุ่ม Esc สำหรับออกจากเต็มจอ
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", lambda event: self.root.attributes('-fullscreen', False))



        self.source = None
        self.cap = None
        self.example_image = None
        self.frame_queue = frame_queue
        self.key_queue = key_queue
        self.mouse_queue = mouse_queue
        self.stop_event = stop_event
        self._closing = False
        self.current_mode = current_mode
        self.fps = fps
        self.fps_sec = fps_sec

        # ใช้ StringVar สำหรับอัปเดตข้อความ FPS แบบ Dynamic บน UI
        self.fps_text_var = tk.StringVar()
        self.update_fps_text()
        
        # ตั้งค่า App Window Icon (.ico / .png)
        try:
            self.root.iconbitmap(r"main\Logo\atc_logo.ico")
        except Exception:
            pass

        # --- 2. HEADER SECTION (แถบหัวข้อด้านบน) ---
        header_frame = tk.Frame(self.root, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header_frame.pack(fill="x", side="top", ipady=5)

        header_content = tk.Frame(header_frame, bg=PANEL_COLOR, padx=25, pady=10)
        header_content.pack(fill="x")

        # โหลดโลโก้ใน Header
        base_path = os.path.dirname(os.path.abspath(__file__)) #r"main\Logo\atc_logo.png"
        parent_path = os.path.dirname(base_path)
        logo_path = os.path.join(parent_path, "Logo", "atc_logo.png")
        try:
            self.logo_icon = tk.PhotoImage(file=logo_path).subsample(2, 2)
            lbl_logo = tk.Label(header_content, image=self.logo_icon, bg=PANEL_COLOR)
            lbl_logo.pack(side="left", padx=(0, 15))
        except Exception as e:
            pass

        # ข้อความหัวข้อระบบ
        header_text_frame = tk.Frame(header_content, bg=PANEL_COLOR)
        header_text_frame.pack(side="left")

        self.lbh = tk.Label(
            header_text_frame, 
            text="AOYAMA DETECTION SYSTEM", 
            font=("Segoe UI", 10, "bold"), 
            fg=TITLE_BLUE, 
            bg=PANEL_COLOR
        )
        self.lbh.pack(anchor="w")

        sub_title = tk.Label(
            header_text_frame, 
            text="Real-time AI Video Processing & Monitoring", 
            font=("Segoe UI", 9), 
            fg=TEXT_MUTED, 
            bg=PANEL_COLOR
        )
        sub_title.pack(anchor="w")


        # --- 3. MAIN CONTENT CONTAINER (พื้นที่แสดงผลหลัก) ---
        main_container = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=20)
        main_container.pack(fill="both", expand=True)

        # แบ่งพื้นที่แสดงผลเป็นวิดีโอ 80% และรูปตัวอย่าง 20%
        main_container.grid_columnconfigure(0, weight=4, uniform="group1")
        main_container.grid_columnconfigure(1, weight=1, uniform="group1")
        main_container.grid_rowconfigure(0, weight=1)

        # --- 4. LEFT CARD: Live Camera Video Stream ---
        card_left = tk.Frame(
            main_container, 
            bg=PANEL_COLOR, 
            highlightbackground=BORDER_COLOR, 
            highlightthickness=1, 
            bd=0
        )
        card_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        left_title_frame = tk.Frame(card_left, bg=PANEL_COLOR, padx=15, pady=12)
        left_title_frame.pack(fill="x")

        lbl_card_left_title = tk.Label(
            left_title_frame, 
            text="📹 Live Camera Stream", 
            font=("Segoe UI", 12, "bold"), 
            fg=TEXT_MAIN, 
            bg=PANEL_COLOR
        )
        lbl_card_left_title.pack(anchor="nw")

        lb_fps_card = tk.Label(
            left_title_frame, 
            textvariable=self.fps_text_var,
            font=("Segoe UI", 12, "bold"), 
            fg=TEXT_MAIN, 
            bg=PANEL_COLOR
        )
        lb_fps_card.pack(anchor="ne")

        ttk.Separator(card_left, orient="horizontal").pack(fill="x")

        # Label สำหรับวางสตรีมวิดีโอ (lbs)
        self.lbs = tk.Label(
            card_left, 
            bg="#0F172A",
            text="Waiting for camera feed...", 
            fg="#94A3B8",
            font=("Segoe UI", 11)
        )
        self.lbs.pack(fill="both", expand=True, padx=15, pady=15)
        self.lbs.bind("<Configure>", self._refresh_video_size)

        # --- 5. RIGHT CARD: Example Pose / Reference Image ---
        card_right = tk.Frame(
            main_container, 
            bg=PANEL_COLOR, 
            highlightbackground=BORDER_COLOR, 
            highlightthickness=1, 
            bd=0,
            height=0
        )
        card_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        right_title_frame = tk.Frame(card_right, bg=PANEL_COLOR, padx=15, pady=12)
        right_title_frame.pack(fill="x")

        lbl_card_right_title = tk.Label(
            right_title_frame, 
            text="📌 Standard Reference Image", 
            font=("Segoe UI", 12, "bold"), 
            fg=TEXT_MAIN, 
            bg=PANEL_COLOR
        )
        lbl_card_right_title.pack(anchor="w")

        ttk.Separator(card_right, orient="horizontal").pack(fill="x")

        # Label สำหรับวางภาพตัวอย่าง (lb_examle)
        self.lb_examle = tk.Label(
            card_right, 
            bg="#F1F5F9", 
            text="No Reference Image Loaded", 
            fg="#94A3B8",
            font=("Segoe UI", 11)
        )
        self.lb_examle.pack(fill="both", expand=True, padx=15, pady=15)
        self.lb_examle.bind("<Configure>", self._refresh_example_size)
        self.imageExample()
        
        self.root.bind("<KeyPress>", self._handle_key)
        self.lbs.bind("<Button-1>", self._handle_mouse)
        self.root.focus_force()

        # จัดการการกดปิดหน้าต่างผ่านปุ่ม X มุมขวาบน
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

            # เพิ่มฟังก์ชันนี้ต่อท้ายใน Class DisplayGui
    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)

    def update_fps_text(self):
        """ฟังก์ชันอัปเดตข้อความลง StringVar"""
        self.fps_text_var.set(
            f"Mode: {self.current_mode} fps_limit: {self.fps}  fps_per_sec: {self.fps_sec}"
        )

    def showMode(self, current_mode, fps, fps_sec):
        """อัปเดตโหมดและค่า FPS พร้อมสั่งรีเฟรชหน้าจอ UI ทันที"""
        self.current_mode = current_mode
        self.fps = fps
        self.fps_sec = fps_sec
        self.update_fps_text()
        print(f"Mode: {self.current_mode}, Limit: {self.fps}, FPS: {self.fps_sec}")

    def getSource(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        self.getFrame()

    def getFrame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.showFrame(frame)
            else:
                print("⚠️ ไม่สามารถอ่านเฟรมจากกล้องได้")

    def imageExample(self):
        image_path = r"main\Logo\ImageExampleJpeg.jpg"
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"❌ Error: ไม่พบไฟล์ภาพที่ path: {image_path}")
            return
            
        image_unit8 = np.ascontiguousarray(image, dtype=np.uint8)
        image_rgb = cv2.cvtColor(image_unit8, cv2.COLOR_BGR2RGB)
        self.example_image = Image.fromarray(image_rgb)
        self._refresh_example_size()

    def _fit_image(self, image, label):
        width = label.winfo_width()
        height = label.winfo_height()
        if width <= 1 or height <= 1:
            return None
        return ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)

    def _cover_image(self, image, label):
        width = label.winfo_width()
        height = label.winfo_height()
        if width <= 1 or height <= 1:
            return None
        return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)

    def _refresh_example_size(self, event=None):
        if self.example_image is None:
            return

        image = self._fit_image(self.example_image, self.lb_examle)
        if image is not None:
            image_tk = ImageTk.PhotoImage(image=image)
            self.lb_examle.image_tk = image_tk
            self.lb_examle.configure(image=image_tk)

    def _refresh_video_size(self, event=None):
        if getattr(self, "current_frame", None) is not None:
            self.showFrame(self.current_frame, schedule=False)

    def showFrame(self, frame, schedule=True):
        if frame is not None: 
            self.current_frame = frame
            frame = np.ascontiguousarray(frame, dtype=np.uint8)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = self._cover_image(Image.fromarray(rgb_frame), self.lbs)
            if img is None:
                if schedule:
                    self.root.after(15, self.getFrame)
                return
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.lbs.imgtk = imgtk
            self.lbs.configure(image=imgtk)

            if schedule:
                self.root.after(15, self.getFrame)
        else:
            self.close_app()

    def close_app(self):
        if self._closing:
            return
        self._closing = True
        if self.stop_event is not None:
            self.stop_event.set()
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()

    def run(self):
        if self.frame_queue is not None:
            self.root.after(15, self._poll_frame_queue)
        self.root.mainloop()

    def _handle_key(self, event):
        if self.key_queue is None or not event.char:
            return

        try:
            self.key_queue.put_nowait(event.char.lower())
        except queue.Full:
            pass

        return "break"

    def _handle_mouse(self, event):
        if self.mouse_queue is None or getattr(self, "current_frame", None) is None:
            return

        frame_height, frame_width = self.current_frame.shape[:2]
        label_width = self.lbs.winfo_width()
        label_height = self.lbs.winfo_height()
        scale = max(label_width / frame_width, label_height / frame_height)
        scaled_width = frame_width * scale
        scaled_height = frame_height * scale
        crop_x = (scaled_width - label_width) / 2
        crop_y = (scaled_height - label_height) / 2
        frame_x = int((event.x + crop_x) / scale)
        frame_y = int((event.y + crop_y) / scale)
        frame_x = max(0, min(frame_x, frame_width - 1))
        frame_y = max(0, min(frame_y, frame_height - 1))

        try:
            self.mouse_queue.put_nowait((frame_x, frame_y))
        except queue.Full:
            pass

    def _poll_frame_queue(self):
        if self.frame_queue is None:
            return
        if self.stop_event is not None and self.stop_event.is_set():
            self.close_app()
            return

        latest_data = None
        try:
            while True:
                latest_data = self.frame_queue.get_nowait()
        except queue.Empty:
            pass

        if latest_data is not None:
            # รองรับทั้งกรณีส่งมาแค่ Frame หรือส่งมาแบบ Dictionary (เช่น {"frame": img, "fps_sec": 29.5})
            if isinstance(latest_data, dict):
                frame = latest_data.get("frame")
                new_fps_sec = latest_data.get("fps_sec")
                if new_fps_sec is not None:
                    self.fps_sec = new_fps_sec
                    self.update_fps_text()
                if frame is not None:
                    self.showFrame(frame, schedule=False)
            else:
                self.showFrame(latest_data, schedule=False)

        self.root.after(15, self._poll_frame_queue)

if __name__ == "__main__":
    rtsp_url = "rtsp://admin:Aoyama456@10.17.7.246:554/cam/realmonitor?channel=1&subtype=0"
    
    # กำหนดค่าเริ่มต้นตอนสร้าง Object ให้ครบถ้วนเพื่อป้องกัน Error
    app = DisplayGui(current_mode="Normal", fps=30, fps_sec=0.0)
    app.getSource(rtsp_url)
    app.run()