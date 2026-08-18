import cv2
import numpy as np
import csv
import os
from ultralytics import YOLO

# 1. ตั้งค่าไฟล์ CSV
csv_filename = "pose_dataset.csv"

headers = []
for i in range(17):
    headers.append(f"x_{i}")
    headers.append(f"y_{i}")
headers.append("label")

if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

# 2. โหลดโมเดล
model = YOLO('yolo26n-pose.pt') 
cap = cv2.VideoCapture(r"../../ProjectDetection/recordings/VideoTrain_20260817_153543.mp4")
# cap = cv2.VideoCapture(0)

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),      # หัว
    (5, 6),                              # ไหล่
    (5, 7), (7, 9), (6, 8), (8, 10),    # แขน
    (5, 11), (6, 12),                    # ลำตัว
    (11, 12),                            # สะโพก
    (11, 13), (13, 15), (12, 14), (14, 16) # ขา
]

print("=== เริ่มการบันทึกข้อมูลแบบแยก ID ===")
print("- กดเลข '1': บันทึก Right")
print("- กดเลข '2': บันทึก Left")
print("- กดเลข '3': บันทึก Front")
print("- กดเลข '4': บันทึก Nomal")
print("- กด 'q': ออกจากโปรแกรม")

window = "Label Pose"
cv2.namedWindow(window, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window, cv2.WINDOW_FULLSCREEN, cv2.WND_PROP_FULLSCREEN)

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret:
            print("file video not found")
            break

    frame = cv2.flip(frame, 1)
    # frame = cv2.resize(frame, cv2.Full)
    h, w = frame.shape[:2]
    
    # 🟢 เปลี่ยนใช้ track เพื่อดึง ID ของแต่ละคน
    results = model.track(source=frame, conf=0.5, persist=True, verbose=False, tracker="bytetrack.yaml")

    # ใช้ Dictionary เก็บพิกัดแยกตาม ID -> {track_id: features_34_values}
    current_frame_people = {} 

    for result in results:
        if result.keypoints is not None and result.boxes is not None and result.boxes.id is not None:
            keypoints_list = result.keypoints.xy.cpu().numpy()
            track_ids = result.boxes.id.int().cpu().numpy()

            for keypoints, track_id in zip(keypoints_list, track_ids):
                if len(keypoints) < 17:
                    continue
                
                pts = keypoints.astype(int)

                # วาดโครงกระดูก
                for start_idx, end_idx in SKELETON_CONNECTIONS:
                    if (pts[start_idx, 0] == 0 and pts[start_idx, 1] == 0) or \
                       (pts[end_idx, 0] == 0 and pts[end_idx, 1] == 0):
                        continue
                    cv2.line(frame, tuple(pts[start_idx]), tuple(pts[end_idx]), (0, 255, 0), 2)

                # Normalize พิกัด
                normalized_points = []
                for kp in keypoints:
                    kpx, kpy = int(kp[0]), int(kp[1])
                    if kpx == 0 and kpy == 0:
                        normalized_points.append((0.0, 0.0))
                        continue
                    
                    x_norm = kpx / w
                    y_norm = kpy / h
                    normalized_points.append((x_norm, y_norm))
                    cv2.circle(frame, (kpx, kpy), 4, (0, 0, 255), cv2.FILLED)

                # แสดง ID บนตัวคนในภาพ
                cv2.putText(frame, f"ID: {track_id}", (pts[0, 0], pts[0, 1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # บันทึกลง Dict โดยใช้ ID เป็น Key
                current_frame_people[track_id] = np.array(normalized_points).flatten()

    cv2.imshow(window, frame)
    key = cv2.waitKey(25) & 0xFF

    if key == ord('q'):
        break

    # 🟢 กดเซฟเมื่อมีคนที่ถูกตรวจจับอยู่ใน Dict
    elif key in [ord('1'), ord('2'), ord('3'), ord('4')] and len(current_frame_people) > 0:
        label = ""
        if key == ord('1'): label = "Right"
        elif key == ord('2'): label = "Left"
        elif key == ord('3'): label = "Front"
        elif key == ord('4'): label = "Nomal"

        # วนลูปบันทึกพิกัดของทุกคนในเฟรมนั้นลง CSV
        with open(csv_filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            for p_id, features in current_frame_people.items():
                row_data = list(features)
                row_data.append(label)
                writer.writerow(row_data)
                print(f"บันทึกข้อมูล ID {p_id} ท่าทาง '{label}' สำเร็จ!")

cap.release()
cv2.destroyAllWindows()