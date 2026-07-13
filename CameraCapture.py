import cv2
import time
from ultralytics import YOLO
import numpy as np  
import os
import threading

# สร้างโฟลเดอร์ images หากยังไม่มี
if not os.path.exists('images'):
    os.makedirs('images')

# ฟังก์ชันสำหรับเซฟรูปภาพในเธรดแยก
def save_image_worker(frame_to_save, filename):
    cv2.imwrite(filename, frame_to_save)
    print(f" Saved: {filename}")

# โหลดโมเดล (แนะนำเช็กชื่อไฟล์ให้ถูก เช่น yolov8n-pose.pt หรือ yolo11n-pose.pt)
model = YOLO('yolov8n-pose.pt') 
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# --- แยกตัวแปรจับเวลาให้ชัดเจน ---
prev_fps_time = time.time()
last_save_time = 0

is_capturing = False  # สถานะเปิด/ปิดการเซฟภาพ (กด s เพื่อเปลี่ยนสถานะ)
count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # สร้างตัวแปรเริ่มต้นเผื่อกรณีไม่เจอใครเลย โปรแกรมจะได้ไม่แครช
    frame_pose = frame.copy()
 
    # รัน YOLO เพียงรอบเดียว (ส่งภาพแบบประหยัดแรมและปิด verbose)
    results = model.predict(source=frame, stream=True, conf=0.5, verbose=False)


    for r in results:
        # วาดเส้น Pose ลงบนเฟรม
        frame_pose = r.plot(boxes=False, kpt_radius=10, kpt_line=True)

    current_time = time.time()

    # --- ส่วนที่ 1: ตรวจสอบการบันทึกภาพอัตโนมัติ (ทำงานเมื่อเปิดโหมดและครบ 1 วินาที) ---
    if is_capturing:
        if current_time - last_save_time >= 1.0:
            last_save_time = current_time
            
            filename = f"images/shot_{int(current_time)}.jpg"
            
            # ทำการ copy เฟรมที่มีเส้น Pose ไปเซฟ (หรือเปลี่ยนเป็น frame เฉพาะภาพดิบได้ครับ)
            frame_copy = frame_pose.copy()
            
            # ส่งไปเซฟใน background thread ไม่ดึงเฟรมหลัก
            threading.Thread(target=save_image_worker, args=(frame_copy, filename), daemon=True).start()
            count += 1

    # --- ส่วนที่ 2: คำนวณ FPS แยกอิสระ ---
    time_diff = current_time - prev_fps_time
    fps = 1 / time_diff if time_diff > 0 else 0
    prev_fps_time = current_time    

    # --- ส่วนที่ 3: แสดงข้อมูลบนหน้าจอ ---
    status_text = "Status: CAPTURING..." if is_capturing else "Status: IDLE (Press 's' to Start)"
    
    cv2.putText(frame_pose, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame_pose, status_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame_pose, f"Count: {count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)

    cv2.imshow("Camera Capture", frame_pose)
    
    # --- ส่วนที่ 4: ดักจับการกดปุ่มเพียงที่เดียวในลูป ---
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('s'):
        is_capturing = not is_capturing  # สลับสถานะ เปิด/ปิด
        if is_capturing:
            last_save_time = time.time() # รีเซ็ตเวลาเริ่มต้นเซฟทันทีที่กด
            
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()