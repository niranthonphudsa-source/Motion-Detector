import cv2
from LIB.file_manager import save_roi_to_txt

class ROIHandler:
    def __init__(self):
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.cx, self.cy = -1, -1
        self.current_rect = None
        
        # ─── โหมดการมาร์ก ───
        # 0 = Normal, 1 = วาด Polygon ROI, 2 = มาร์กจุด Start (จุดที่ 1), 3 = มาร์กจุด Reverse (จุดที่ 2)
        self.current_mode = 0  
        
        # ─── พิกัดที่บันทึก ───
        self.mark_points = []      # ลิสต์เก็บพิกัดรูปปิด [(x1, y1), (x2, y2), ...]
        self.start_point = None    # พิกัดจุดที่ 1: Start Check (x, y)
        self.reverse_point = None  # พิกัดจุดที่ 2: Reverse Check (x, y)
        
        self.is_confirmed = False  # สถานะยืนยัน Polygon ROI

    # 1. Callback ฟังก์ชันดักจับเมาส์
    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # 🟢 โหมดที่ 1: วาดรูปปิด Polygon (ต้องกดยืนยันก่อนถึงจะหยุด)
            if self.current_mode == 1 and not self.is_confirmed:
                self.mark_points.append((x, y))
                print(f"📍 [ROI Polygon] บันทึกจุดที่ {len(self.mark_points)}: ({x}, {y})")

            # 🟢 โหมดที่ 2: มาร์กจุดที่ 1 (Start Check Point)
            elif self.current_mode == 2:
                self.start_point = (x, y)
                print(f"🟢 [Point 1 - Start] บันทึกจุดเริ่มเช็ก: ({x}, {y})")

            # 🔴 โหมดที่ 3: มาร์กจุดที่ 2 (Reverse Check Point)
            elif self.current_mode == 3:
                self.reverse_point = (x, y)
                print(f"🔴 [Point 2 - Reverse] บันทึกจุดดักเดินสวน: ({x}, {y})")

    # 2. ยืนยันพิกัด Polygon ROI
    def draw_rectangle_callback(self):        
        if len(self.mark_points) >= 3:
            self.is_confirmed = True
            print(f"\n✅ [ยืนยัน ROI เรียบร้อย] พิกัด Polygon: {self.mark_points}")
        else:
            print("⚠️ กรุณาคลิกอย่างน้อย 3 จุดก่อนกดยืนยัน Polygon ครับ")

    # 3. ล้างค่าพิกัดทั้งหมด
    def clear(self):
        self.mark_points = []
        self.start_point = None
        self.reverse_point = None
        self.is_confirmed = False
        self.current_mode = 0
        print("\n🧹 รีเซ็ตพิกัดทั้งหมดเรียบร้อยแล้ว")

    # 4. ฟังก์ชันวาด Marker บนเฟรมพรีวิว (สำหรับนำไปเรียกใน OpenCV Loop)
    def draw_indicators(self, frame):
        """วาดจุดมาร์ก และ เส้น Polygon ลงบน Frame เพื่อให้ผู้ใช้เห็นบน UI"""
        # วาด จุดที่ 1 (Start Point) - สีเขียว 🟢
        if self.start_point:
            cv2.circle(frame, self.start_point, 8, (0, 255, 0), -1)
            cv2.putText(frame, "1: START", (self.start_point[0] + 10, self.start_point[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # วาด จุดที่ 2 (Reverse Point) - สีแดง 🔴
        if self.reverse_point:
            cv2.circle(frame, self.reverse_point, 8, (0, 0, 255), -1)
            cv2.putText(frame, "2: REVERSE", (self.reverse_point[0] + 10, self.reverse_point[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # ถ้ามีทั้ง 2 จุด ให้วาดเส้นเชื่อมพร้อมลูกศรชี้ทิศทางที่ถูกต้อง (จาก 1 -> 2)
        if self.start_point and self.reverse_point:
            cv2.arrowedLine(frame, self.start_point, self.reverse_point, (255, 255, 0), 2, tipLength=0.2)

        return frame