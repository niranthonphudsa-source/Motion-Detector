import cv2
import tkinter as tk
import numpy as np
from tkinter import ttk
from PIL import Image, ImageTk

class DisplayGui:

    def __init__(self):
        # ─── โทนสีหลัก (White & Blue Theme) ───
        BG_COLOR = "#F8FAFC"        # พื้นหลังหลัก
        PANEL_COLOR = "#FFFFFF"     # พื้นหลังกล่องการ์ด
        BORDER_COLOR = "#E2E8F0"    # สีขอบกล่อง
        TEXT_MAIN = "#0F172A"       # สีข้อความหลัก
        TEXT_MUTED = "#64748B"      # สีข้อความรอง
        PRIMARY_BLUE = "#2563EB"    # สีน้ำเงินหลัก
        TITLE_BLUE = "#1E3A8A"      # สีกรมท่าสำหรับหัวข้อ

        # --- 1. การตั้งค่าหน้าต่างหลัก (Main Window) ---
        self.root = tk.Tk()
        self.root.title("Aoyama Detection System")
        self.root.geometry("1920x1080")
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        self.source = None
        self.cap = None

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
        try:
            self.logo_icon = tk.PhotoImage(file=r"main\Logo\atc_logo.png").subsample(2, 2)
            lbl_logo = tk.Label(header_content, image=self.logo_icon, bg=PANEL_COLOR)
            lbl_logo.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด Icon ได้: {e}")

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

        # แบ่ง Grid คอลัมน์ 0 และ 1 ให้กว้างเท่ากัน (50/50)
        main_container.grid_columnconfigure(0, weight=1, uniform="group1")
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
        lbl_card_left_title.pack(anchor="w")

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

        # --- 5. RIGHT CARD: Example Pose / Reference Image ---
        card_right = tk.Frame(
            main_container, 
            bg=PANEL_COLOR, 
            highlightbackground=BORDER_COLOR, 
            highlightthickness=1, 
            bd=0
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

        # จัดการการกดปิดหน้าต่างผ่านปุ่ม X มุมขวาบน
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def getSource(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        # สั่งประมวลผลเฟรมแรกและโหลดรูปภาพตัวอย่าง
        self.getFrame()
        self.imageExample()

    def getFrame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.showFrame(frame)
            else:
                print("⚠️ ไม่สามารถอ่านเฟรมจากกล้องได้")

    def imageExample(self):
        image_path = r"main\Logo\ImageExample.png"
        image = cv2.imread(image_path)
        
        # 🌟 เช็กว่าอ่านภาพสำเร็จหรือไม่
        if image is None:
            print(f"❌ Error: ไม่พบไฟล์ภาพที่ path: {image_path}")
            return
            
        # ปรับขนาดภาพตัวอย่างให้อยู่ในสัดส่วนที่เหมาะสม
        image = cv2.resize(image, (640, 320))
        image_unit8 = np.ascontiguousarray(image, dtype=np.uint8)
        image_rgb = cv2.cvtColor(image_unit8, cv2.COLOR_BGR2RGB)
        image_array = Image.fromarray(image_rgb)
        image_tk = ImageTk.PhotoImage(image=image_array)

        self.lb_examle.image_tk = image_tk
        self.lb_examle.configure(image=image_tk)

    def showFrame(self, frame):
        if frame is not None: 
            # ปรับขนาดเฟรมวิดีโอให้เข้ากับ Card
            frame = cv2.resize(frame, (920, 640))
            frame = np.ascontiguousarray(frame, dtype=np.uint8)

            # 1. แปลง BGR เป็น RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 2. แปลงเป็น Image และ PhotoImage เพื่อแสดงบน Tkinter
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # 3. อัปเดตภาพลง Label
            self.lbs.imgtk = imgtk
            self.lbs.configure(image=imgtk)

            # 4. วนลูปเรียกตัวเองทุกๆ 15ms
            self.root.after(15, self.getFrame)
        else:
            self.close_app()

    def close_app(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    rtsp_url = "rtsp://admin:Aoyama456@10.17.7.246:554/cam/realmonitor?channel=1&subtype=0"
    
    app = DisplayGui()
    app.getSource(rtsp_url)
    app.run()