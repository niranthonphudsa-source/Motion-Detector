import cv2
import os
import time

folder_save_images = "images"

if not os.path.exists(folder_save_images):
    os.makedirs(folder_save_images)
    print(f"Build Folder Successfully: {folder_save_images}")

cap = cv2.VideoCapture(0)
img_counter = 0

# ตัวแปรควบคุมสถานะ
is_saving = False
last_save_time = 0  # เก็บเวลาที่เซฟรูปล่าสุด
fps_start_time = time.time()
fps_counter = 0
fps = 0

print("กด 's' เพื่อเริ่ม/หยุด แคปรูปทุก 1 วินาที | กด 'q' เพื่อออก")

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)  # พลิกภาพแนวนอนเพื่อให้เหมือนกระจก
    # --- ส่วนคำนวณ FPS จริงแบบลื่นๆ ---
    fps_counter += 1
    if (time.time() - fps_start_time) > 1:
        fps = fps_counter / (time.time() - fps_start_time)
        fps_counter = 0
        fps_start_time = time.time()
    cv2.putText(frame, f"fps: {fps:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # --- ส่วนเช็กสถานะการเซฟรูป ---
    if is_saving:
        cv2.putText(frame, "Status: Auto Saving (Every 1s)...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # เช็กว่าเวลาผ่านไปครบ 1 วินาทีหรือยัง โดยไม่ทำให้เฟรมค้าง
        current_time = time.time()
        if current_time - last_save_time >= 1.0:
            img_name = f"screenshot_{img_counter}.png"
            full_path = os.path.join(folder_save_images, img_name)
            
            # บันทึกรูปภาพ
            cv2.imwrite(full_path, frame)
            print(f"บันทึกรูปภาพสำเร็จที่: {full_path}")
            
            img_counter += 1
            last_save_time = current_time  # อัปเดตเวลาล่าสุด
    else:
        cv2.putText(frame, "Press 's' to START auto save", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # แสดงผลหน้าจอ (ต้องอยู่นอกสุดเพื่อให้แสดงผลตลอดเวลา)
    cv2.imshow('Camera', frame) 

    # --- ดักจับปุ่มกด (เรียกใช้แค่ครั้งเดียวต่อ 1 ลูป) ---
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):  # กด q เพื่อออก
        break
    elif key == ord('s'):  # กด s เพื่อ เปิด หรือ ปิด ระบบแคปภาพอัตโนมัติ
        is_saving = not is_saving
        last_save_time = 0  # รีเซ็ตเวลาเพื่อให้เริ่มแคปทันทีที่กด

cap.release()
cv2.destroyAllWindows()