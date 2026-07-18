# roi_handler.py
import cv2

class ROIHandler:
    def __init__(self):
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.cx, self.cy = -1, -1
        self.current_rect = None
        self.current_mode = 0  # 0 = Normal, 1 = Drawing

    def draw_rectangle_callback(self, event, x, y, flags, param):
        if self.current_mode == 1:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drawing = True
                self.ix, self.iy = x, y
                self.cx, self.cy = x, y

            elif event == cv2.EVENT_MOUSEMOVE:
                if self.drawing:
                    self.cx, self.cy = x, y

            elif event == cv2.EVENT_LBUTTONUP:
                self.drawing = False
                self.current_rect = (self.ix, self.iy, x, y)
                print(f"ลากพื้นที่เสร็จสิ้น: {self.current_rect} (กด '2' เพื่อบันทึกค่า)")

    def clear(self):
        self.current_rect = None
        self.current_mode = 0
        self.drawing = False