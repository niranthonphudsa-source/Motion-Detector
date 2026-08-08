import cv2
import numpy as np
import joblib  # ใช้สำหรับโหลดไฟล์ .pkl
from ultralytics import YOLO

# 1. โหลดโมเดลทั้งสองตัว
model = YOLO('yolo26n-pose.pt')          # โมเดล YOLO Pose สำหรับหาจุด
pose_classifier = joblib.load('pose_classifier.pkl')  # โมเดล Sklearn สำหรับจำแนกท่าทาง

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),      # หัว
    (5, 6),                              # ไหล่
    (5, 7), (7, 9), (6, 8), (8, 10),    # แขน
    (5, 11), (6, 12),                    # ลำตัว
    (11, 12),                            # สะโพก
    (11, 13), (13, 15), (12, 14), (14, 16) # ขา
]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    results = model.predict(source=frame, conf=0.8, verbose=False)

    for result in results:
        if result.keypoints is not None:
            keypoints_list = result.keypoints.xy.cpu().numpy()
            
            for keypoints in keypoints_list:
                if len(keypoints) < 17: 
                    continue
                
                pts = keypoints.astype(int)

                # 1. วาดเส้นโครงกระดูก
                for start_idx, end_idx in SKELETON_CONNECTIONS:
                    if (pts[start_idx, 0] == 0 and pts[start_idx, 1] == 0) or \
                       (pts[end_idx, 0] == 0 and pts[end_idx, 1] == 0):
                        continue
                    cv2.line(frame, tuple(pts[start_idx]), tuple(pts[end_idx]), (0, 255, 0), 2)

                # 2. ทำ Normalize พิกัดเพื่อเตรียมส่งให้โมเดลทายผล
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

                # แปลงข้อมูลเป็น 1D Array ขนาด 34 ค่า
                features = np.array(normalized_points).flatten()


                predicted_label = pose_classifier.predict([features])[0]
                
                # ดึงค่าความมั่นใจ (Probability) ออกมาแสดง (Optional)
                probabilities = pose_classifier.predict_proba([features])[0]
                confidence = np.max(probabilities) * 100

                # หาพิกัดตำแหน่งที่จะเขียนข้อความ (ใช้พิกัดของจุดจมูก Index 0 หรือไหล่ Index 5 ก็ได้)
                text_x = pts[5][0] if pts[5][0] > 0 else 50
                text_y = pts[5][1] - 30 if pts[5][1] > 30 else 50

                # นำชื่อท่าทางที่ทายได้ไปเขียนแสดงบนหน้าจอ OpenCV
                cv2.putText(frame, f"Pose: {predicted_label} ({confidence:.1f}%)", 
                            (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.8, (255, 255, 0), 2)

    cv2.imshow("Real-time Pose Classifier", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()