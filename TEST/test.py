import cv2
import numpy as np

# ตัวแปร Global สำหรับพิกัดและสถานะเมาส์
drawing = False      
ix, iy = -1, -1      
cx, cy = -1, -1      

# ตัวแปรเก็บพิกัดล่าสุด (x1, y1, x2, y2)
current_rect = None

# สถานะของโปรแกรม: 0 = โหมดปกติ, 1 = โหมดพร้อมลาก (เมื่อกด 1)
current_mode = 0

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, cx, cy, drawing, current_rect, current_mode

    # ทำงานเฉพาะเมื่ออยู่ในโหมด 1 (กดปุ่ม 1 แล้ว) เท่านั้น
    if current_mode == 1:
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
            cx, cy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                cx, cy = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            current_rect = (ix, iy, x, y)
            print(f"ลากพื้นที่เสร็จสิ้น: {current_rect} (กด '2' เพื่อบันทึกค่า)")

window_name = "Mode Control ROI"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, draw_rectangle)

print("=== คู่มือการใช้งาน ===")
print("กด '1' : เปิดโหมดลากกล่อง (ลากเมาส์ซ้ายค้าง)")
print("กด '2' : บันทึกค่าพิกัดล่าสุดที่ลากไว้")
print("กด 'c' : ล้างพิกัดที่เลือกไว้")
print("กด 'q' : ออกจากโปรแกรม")
print("====================")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. วาดกล่องที่เลือกค้างไว้บนหน้าจอ (ถ้ามี)
    if current_rect is not None:
        cv2.rectangle(frame, (current_rect[0], current_rect[1]), 
                      (current_rect[2], current_rect[3]), (0, 255, 0), 2)
        cv2.putText(frame, "Selected ROI", (current_rect[0], current_rect[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # 2. แสดงกล่องสีแดงแบบ Real-time ขณะที่ผู้ใช้กำลังลากเมาส์
    if current_mode == 1 and drawing:
        cv2.rectangle(frame, (ix, iy), (cx, cy), (0, 0, 255), 2)

    # 3. แสดงสถานะโหมดปัจจุบันบนหน้าจอให้เห็นชัดเจน
    mode_text = "Mode: DRAWING (Press Mouse & Drag)" if current_mode == 1 else "Mode: NORMAL (Press '1' to Edit)"
    mode_color = (0, 0, 255) if current_mode == 1 else (255, 0, 0)
    cv2.putText(frame, mode_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)

    cv2.imshow(window_name, frame)
    
    # รับปุ่มกดจากคีย์บอร์ด
    key = cv2.waitKey(1) & 0xFF

    # กด '1' เพื่อเปิดโหมดลากวาง
    if key == ord('1'):
        current_mode = 1
        print(">> เข้าสู่โหมด: ลากวาง (กดเมาส์ซ้ายค้างเพื่อวาดขอบเขต)")

    # กด '2' เพื่อบันทึกค่า
    elif key == ord('2'):
        if current_rect is not None:
            # ดึงพิกัดออกมา
            x1, y1, x2, y2 = current_rect
            
            # ตัวอย่างการบันทึกค่าลงไฟล์ txt
            with open("saved_roi.txt", "w") as f:
                f.write(f"{x1},{y1},{x2},{y2}")
                
            print(f"Successfully Saved! บันทึกพิกัด {current_rect} ลงไฟล์ saved_roi.txt เรียบร้อย")
            current_mode = 0  # บันทึกเสร็จแล้วดีดกลับไปโหมดปกติ
        else:
            print("❌ ยังไม่ได้ลากกล่องพิกัด กรุณากด 1 แล้วลากกล่องก่อนกดบันทึก")

    # กด 'c' เพื่อเคลียร์ค่า
    elif key == ord('c'):
        current_rect = None
        current_mode = 0
        print("ล้างค่าพิกัดและกลับสู่โหมดปกติ")

    # กด 'q' เพื่อออก
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()