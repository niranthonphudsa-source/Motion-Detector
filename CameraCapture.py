import cv2
import time
from ultralytics import YOLO
import numpy as np  
import os
import csv

# ==========================================
# SETUP & CONFIGURATION
# ==========================================
DATASET_FILE = 'pose_dataset.csv'
CURRENT_LABEL = 'Stand'  # เปลี่ยนชื่อท่าตรงนี้ตอนเก็บข้อมูล (เช่น Sit, Walk, Fall)

# โหลดโมเดล และเปิดกล้อง (ใช้ DSHOW เพื่อเปิดกล้องไวบน Windows)
model = YOLO('yolov8n-pose.pt') 
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# 1. สร้างหัวคอลัมน์ (Header) สำหรับไฟล์ CSV หากยังไม่มีไฟล์นี้มาก่อน
if not os.path.exists(DATASET_FILE):
    with open(DATASET_FILE, mode='w', newline='') as f:
        csv_writer = csv.writer(f)
        header = []
        for i in range(17):
            header.extend([f'x{i}', f'y{i}'])
        header.append('label')
        csv_writer.writerow(header)

# ค่าคอนฟิกการแสดงผลโครงกระดูก (สีเขียวล้วน ไร้กรอบ)
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),           # ใบหน้า
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # แขนและไหล่
    (5, 11), (6, 12), (11, 12),               # ลำตัว
    (11, 13), (13, 15), (12, 14), (14, 16)    # ช่วงขา
]
POSE_COLOR = (0, 255, 0)

# ตัวแปรควบคุมระบบจับเวลา
prev_fps_time = time.time()
last_save_time = 0
is_capturing = False  # สลับสถานะ บันทึก/หยุดบันทึก (กด 's' บนคีย์บอร์ด)
count = 0

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def preprocess_keypoints(person_kpts):
    """
    ฟังก์ชันทำ Normalization ปรับพิกัดดิบให้อยู่ในรูปแบบสัมพันธ์กับตัวบุคคล
    โดยใช้จุดจมูก (Index 0) เป็นจุดศูนย์กลางอ้างอิง (0,0) ของร่างกาย
    """
    # 1. หาพิกัดของจุดจมูกเพื่อใช้เป็นจุดกำเนิด (Origin)
    origin_x, origin_y = person_kpts[0] 
    
    # 2. คัดลอกพิกัดมาหักลบค่า Origin ออก
    normalized_kpts = person_kpts.copy()
    normalized_kpts[:, 0] = normalized_kpts[:, 0] - origin_x
    normalized_kpts[:, 1] = normalized_kpts[:, 1] - origin_y
    
    # 3. แปลงอาร์เรย์มิติ (17, 2) ให้เป็นแถวเดี่ยว 1 มิติ (34 ค่า)
    return normalized_kpts.flatten()

# ==========================================
# MAIN LOOP
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_pose = frame.copy()
    current_time = time.time()

    # รัน YOLO ตรวจจับท่วงท่า
    results = model(frame, stream=True, conf=0.8, verbose=False)

    for r in results:
        if r.keypoints is not None:
            keypoints_data = r.keypoints.xy.cpu().numpy()
            
            for person_kpts in keypoints_data:
                # ตรวจสอบว่าในเฟรมนี้ตรวจเจอคนจริงๆ (พิกัดต้องไม่ใช่ 0 ทั้งหมด)
                if np.any(person_kpts):
                    
                    # --- ส่วนที่ 1: การประมวลผลข้อมูลและบันทึกลง CSV ทุกๆ 1 วินาที ---
                    if is_capturing and (current_time - last_save_time >= 1.0):
                        # ทำ Normalization ดึงค่า 34 Features ออกมา
                        flat_features = preprocess_keypoints(person_kpts)
                        
                        # บันทึกข้อมูลต่อท้ายลงไฟล์ CSV ทันที
                        with open(DATASET_FILE, mode='a', newline='') as f:
                            csv_writer = csv.writer(f)
                            csv_writer.writerow(list(flat_features) + [CURRENT_LABEL])
                        
                        # อัปเดตเวลาการบันทึกล่าสุดและเพิ่มจำนวนนับ
                        last_save_time = current_time
                        count += 1
                        print(f" Recorded data rows: {count} for label '{CURRENT_LABEL}'")

                # --- ส่วนที่ 2: วาดเส้นโครงกระดูกแสดงผลบนจอภาพ ---
                int_kpts = person_kpts.astype(int)
                # วาดเส้นเชื่อมต่อ
                for start, end in SKELETON_CONNECTIONS:
                    pt1 = tuple(int_kpts[start])
                    pt2 = tuple(int_kpts[end])
                    if pt1 != (0, 0) and pt2 != (0, 0):
                        cv2.line(frame_pose, pt1, pt2, POSE_COLOR, 2, cv2.LINE_AA)
                # วาดจุดวงกลม
                for kp in int_kpts:
                    pt = tuple(kp)
                    if pt != (0, 0):
                        cv2.circle(frame_pose, pt, 5, POSE_COLOR, -1, cv2.LINE_AA)

    # --- ส่วนที่ 3: คำนวณความเร็วเฟรมเรต (FPS) ---
    time_diff = current_time - prev_fps_time
    fps = 1 / time_diff if time_diff > 0 else 0
    prev_fps_time = current_time    

    # --- ส่วนที่ 4: แสดงสถานะบนหน้าจอภาพ ---
    status_text = f"Status: RECORDING ({CURRENT_LABEL})" if is_capturing else "Status: IDLE (Press 's' to Record)"
    
    cv2.putText(frame_pose, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame_pose, status_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame_pose, f"Saved Rows: {count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)

    cv2.imshow("Pose Data Collector", frame_pose)
    
    # --- ส่วนที่ 5: ดักจับการกดคีย์บอร์ด ---
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        is_capturing = not is_capturing  # กด 's' เพื่อเปิด/ปิดการบันทึกข้อมูล
        if is_capturing:
            last_save_time = time.time() - 1.0  # ให้เริ่มบันทึกทันทีกดวินาทีแรก
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()