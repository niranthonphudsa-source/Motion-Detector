import cv2
import numpy
class AdvancedZoomArea:
    def __init__(self, zoom_factor=1.5):
        self.zoom_factor = zoom_factor

    def apply(self, frame, center_pt=None):
        """
        center_pt: (x, y) พิกัดเป้าหมายที่ต้องการซูมเจาะจง เช่น จุด start_point (ถ้าไม่ใส่จะใช้กลางภาพ)
        """
        if self.zoom_factor <= 1.0:
            return frame

        height, width = frame.shape[:2]

        # ถ้าไม่ระบุจุด พิกัดศูนย์กลางจะใช้กลางภาพ
        if center_pt is None:
            cx, cy = width // 2, height // 2
        else:
            cx, cy = center_pt

        new_w = int(width / self.zoom_factor)
        new_h = int(height / self.zoom_factor)

        # ป้องกันไม่ให้ขอบ Crop ทะลุออกนอกเฟรมภาพ
        x1 = max(0, min(width - new_w, cx - new_w // 2))
        y1 = max(0, min(height - new_h, cy - new_h // 2))
        x2 = x1 + new_w
        y2 = y1 + new_h

        cropped = frame[y1:y2, x1:x2]
        return cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LANCZOS4)