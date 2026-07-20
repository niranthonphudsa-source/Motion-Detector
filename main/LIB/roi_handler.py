# roi_handler.py
import cv2
from LIB.file_manager import save_roi_to_txt

class ROIHandler:
    def __init__(self):
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.cx, self.cy = -1, -1
        self.current_rect = None
        self.current_mode = 0  # 0 = Normal, 1 = Drawing
        self.mark_points = []  # ลิสต์สำหรับเก็บพิกัดพอยต์ [(x1, y1), (x2, y2), ...]
        self.is_confirmed = False  # ตัวแปรสถานะเพื่อบอกว่ากดยืนยันแล้วหรือยัง


    # 1. Callback ฟังก์ชันดักจับเมาส์
    def click_event(self, event, x, y, flags, param):
        # ถ้ายังไม่ได้กดยืนยัน และอยู่ในโหมดวาด (current_mode == 1) จะคลิกเพิ่มจุดได้เรื่อย ๆ
        if not self.is_confirmed and self.current_mode == 1:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.mark_points.append([x, y])
                print(f"📍 บันทึกจุดที่ {len(self.mark_points)}: ({x}, {y})")

    def draw_rectangle_callback(self):         
        if len(self.mark_points) >= 3:
            self.is_confirmed = True
            print(f"\n[ยืนยันพิกัดเรียบร้อย] รูปปิด (Polygon): {self.mark_points}")
        else:
            print("กรุณาคลิกอย่างน้อย 3 จุดก่อนกดยืนยันครับ")

    def clear(self):
        self.mark_points = []
        self.is_confirmed = False
        print("\nรีเซ็ตพิกัดเรียบร้อย เริ่มคลิกใหม่ได้เลยครับ")
        
    # 1. Callback ฟังก์ชันดักจับเมาส์
    def click_event(self, event, x, y, flags, param):
        # ถ้ายังไม่ได้กดยืนยัน จะสามารถคลิกเพิ่มจุดได้เรื่อย ๆ
        if not self.is_confirmed:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.mark_points.append((x, y))
                # print(f"บันทึกจุดที่ {len(self.mark_points)}: {x}, {y}")

    
    def draw_rectangle_callback(self):         
        if len(self.mark_points) > 2:
            # print(self.mark_points)
            self.is_confirmed = True
            # print("\n[ยืนยันพิกัดเรียบร้อย!]")
            # print(f"พิกัดรูปปิด (Polygon): {self.mark_points}")
        # else:
            # print("กรุณาคลิกอย่างน้อย 3 จุดก่อนกดยืนยันครับ")

    def clear(self):
        self.mark_points = []
        self.is_confirmed = False
        # print("\nรีเซ็ตพิกัดเรียบร้อย เริ่มคลิกใหม่ได้เลยครับ")