# file_manager.py
import os

def save_roi_to_txt(rect, filename="saved_roi.txt"):
    """บันทึกค่าพิกัดลงไฟล์ TXT"""
    if rect is not None:
        x1, y1, x2, y2 = rect
        with open(filename, "w") as f:
            f.write(f"{x1},{y1},{x2},{y2}")
        return True
    return False

def load_roi_from_txt(filename="saved_roi.txt"):
    """(เพิ่มเติมให้) โหลดพิกัดเดิมกลับมาใช้เมื่อเปิดโปรแกรมใหม่"""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = f.read().split(',')
                return tuple(map(int, data))
        except Exception:
            return None
    return None