import cv2
import tkinter as tk
import numpy as np

from PIL import Image, ImageTk

class DisplayGui:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Detection GUI")
        self.root.geometry("1920x1080")

        self.source = None
        self.cap = None

        
        # Label สำหรับวางภาพวิดีโอ
        self.lbs = tk.Label(self.root)
        self.lbs.pack(padx=10, pady=10)

        # ปุ่มกดปิดโปรแกรม
        btn_close = tk.Button(self.root, text="Exit", command=self.close_app)
        btn_close.pack(pady=10)

    def getSource(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        # สั่งประมวลผลเฟรมแรก
        self.getFrame()

    def getFrame(self):
        ret, frame = self.cap.read()
        if ret:
            self.showFrame(frame)

    def showFrame(self, frame):
        if frame is not None: 
            print(f"welcom display_gui {frame.shape}")
            frame = np.ascontiguousarray(frame, dtype=np.uint8)

            # 1. แปลง BGR เป็น RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 2. แปลงเป็น Image และ PhotoImage เพื่อแสดงบน Tkinter
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # 3. อัปเดตภาพลง Label
            self.lbs.imgtk = imgtk
            self.lbs.configure(image=imgtk)

            # 4. วนลูปเรียกตัวเองทุกๆ 15ms (ไม่ต้องใช้ while True)
            self.root.after(15, self.getFrame)
        else:
            self.close_app()

    def close_app(self):
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()

    def run(self):
        # เมธอดสำหรับเริ่มทำงาน GUI
        self.root.mainloop()
if __name__ == "__main__":
    rtsp_url = "rtsp://admin:Aoyama456@10.17.7.246:554/cam/realmonitor?channel=1&subtype=0"
    
    app = DisplayGui()
    app.getSource(rtsp_url)

    # จัดการการกดปิดหน้าต่างผ่านปุ่ม X มุมขวาบน
    # root.protocol("WM_DELETE_WINDOW", app.close_app)
    app.run()