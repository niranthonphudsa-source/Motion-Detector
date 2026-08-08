# file_manager.py
import os

def save_roi_to_txt(rect, filename="saved_roi.txt"):
    # """บันทึกค่าพิกัดลงไฟล์ TXT"""
    if rect is not None:
        for idx, point in enumerate(rect):
            if not isinstance(point, tuple) or len(point) != 2:
                # print(f"❌ Invalid point at index {idx}: {point}. Each point must be a tuple of (x, y).")
                return False
        with open(filename, "w") as f:
            for i, (x, y) in enumerate(rect):
                if i == len(rect) - 1:
                    f.write(f"{x},{y}")
                else:
                    f.write(f"{x},{y},")
        return True
    return False

def load_roi_from_txt(filename="saved_roi.txt"):
    # """โหลดพิกัดเดิมกลับมาใช้เมื่อเปิดโปรแกรมใหม่"""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = f.read().split(',')
                # แปลงเป็น list ของ tuple (x,y)
                converted_data = list(map(int, data))
                points = [(converted_data[i], converted_data[i+1]) for i in range(0, len(converted_data), 2)]
                return points
        except Exception:
            return None
    return None