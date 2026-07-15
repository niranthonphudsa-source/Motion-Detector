import cv2
import numpy as np
import csv
import os
from ultralytics import YOLO

# 1. ตั้งค่าไฟล์ CSV สำหรับบันทึกข้อมูล
csv_filename = "pose_dataset.csv"

# สร้าง Header ของ CSV (มีทั้งหมด 34 พิกัด + 1 คอลัมน์สำหรับชื่อท่าทาง)
# x0, y0, x1, y1, ..., x16, y16, label
headers = []
for i in range(17):
    headers.append(f"x_{i}")
    headers.append(f"y_{i}")
headers.append("label")

# หากยังไม่มีไฟล์ ให้สร้างและเขียน Header ลงไปก่อน
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

# 2. โหลดโมเดล YOLO Pose
model = YOLO('yolo26n-pose.pt') 
# cap = cv2.VideoCapture("Screen Recording 2026-07-14 111101.mp4")
cap = cv2.VideoCapture("videoTrain1.mp4")

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),      # หัว
    (5, 6),                              # ไหล่
    (5, 7), (7, 9), (6, 8), (8, 10),    # แขน
    (5, 11), (6, 12),                    # ลำตัว
    (11, 12),                            # สะโพก
    (11, 13), (13, 15), (12, 14), (14, 16) # ขา
]

print("=== เริ่มการบันทึกข้อมูล ===")
print("วิธีใช้งาน:")
print("- ทำท่าทางหน้ากล้อง")
print("- กดเลข '1' ค้างไว้เพื่อบันทึกท่าที่ 1 (เช่น 'Righht')")
print("- กดเลข '2' ค้างไว้เพื่อบันทึกท่าที่ 2 (เช่น 'Left')")
print("- กดเลข '3' ค้างไว้เพื่อบันทึกท่าที่ 3 (เช่น 'Front')")
print("- กด 'q' เพื่อออกจากโปรแกรม")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.resize(frame, (640, 540))
    h, w = frame.shape[:2]
    results = model.predict(source=frame, conf=0.8, verbose=False)

    features_to_save = None  # ตัวแปรชั่วคราวเก็บพิกัดในเฟรมนี้

    for result in results:
        if result.keypoints is not None:
            keypoints_list = result.keypoints.xy.cpu().numpy()
            
            for keypoints in keypoints_list:
                if len(keypoints) < 17: 
                    continue
                
                pts = keypoints.astype(int)

                # วาดโครงกระดูก
                for start_idx, end_idx in SKELETON_CONNECTIONS:
                    if (pts[start_idx, 0] == 0 and pts[start_idx, 1] == 0) or \
                       (pts[end_idx, 0] == 0 and pts[end_idx, 1] == 0):
                        continue
                    cv2.line(frame, tuple(pts[start_idx]), tuple(pts[end_idx]), (0, 255, 0), 2)

                # ทำ Normalize พิกัด
                normalized_points = []
                for kp in keypoints:
                    kpx, kpy = int(kp[0]), int(kp[1])
                    
                    if kpx == 0 and kpy == 0:
                        normalized_points.append((0.0, 0.0))
                        continue
                    
                    x_norm = kpx / w
                    y_norm = kpy / h
                    normalized_points.append((x_norm, y_norm))
                    
                    cv2.circle(frame, (kpx, kpy), 5, (0, 0, 255), cv2.FILLED)

                # แปลงเป็น 1D Array ขนาด 34 ค่า
                features_to_save = np.array(normalized_points).flatten()

    cv2.imshow("Skeleton Tracking & Data Collector", frame)

    # 3. ส่วนของการตรวจจับการกดปุ่มเพื่อบันทึกพิกัดลง CSV
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    
    # ตรวจสอบการกดเลข 1, 2, 3 เพื่อเลือกป้ายกำกับ (Label)
    elif key in [ord('1'), ord('2'), ord('3')] and features_to_save is not None:
        label = ""
        if key == ord('1'):
            # key = '1'
            label = "Right"
        elif key == ord('2'):
            # key = '2'
            label = "Left"
        elif key == ord('3'):
            # key = '3'
            label = "Front"

        # แปลง features เป็น list และต่อท้ายด้วยชื่อท่าทาง
        row_data = list(features_to_save)
        row_data.append(label)

        # บันทึกข้อมูลลง CSV ทันที
        with open(csv_filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)
            
        print(f"บันทึกข้อมูลท่าทาง '{label}' สำเร็จ! (แถวข้อมูลสะสม)")

cap.release()
cv2.destroyAllWindows()