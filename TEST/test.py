import cv2
import numpy as np
from ultralytics import YOLO # สมมติฐานอินเทอร์เฟซของ YOLO26-Pose
from sklearn.linear_model import LinearRegression

# 1. โหลดโมเดล YOLO26 Pose (มีความเร็วสูงขึ้นเนื่องจากโครงสร้างไร้ NMS)
model = YOLO("yolo26n-pose.pt")

# cap = cv2.VideoCapture("Screen Recording 2026-07-14 111101.mp4")
# หากเป็นกล้องสด (Live Camera) แนะนำให้เคลียร์บัฟเฟอร์เพื่อลด Latency
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

frame_count = 0
SKIP_FRAMES = 3  # รัน YOLO-Pose ทุกๆ 4 เฟรม (เฟรมที่เหลือใช้ Sklearn ทำนาย)

# โครงสร้างประวัติคิว: [[frame_idx, keypoints_array], ...]
# keypoints_array จะมีมิติเป็น (17, 2) คือ พิกัด x, y ของข้อต่อ 17 จุดมาตรฐาน (COCO)
pose_history = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    current_keypoints = None

    # --- จังหวะที่ 1: เฟรมหลัก (Keyframe) -> รัน YOLO26-Pose ---
    if frame_count % SKIP_FRAMES == 0:
        results = model(frame, verbose=False)[0]
        
        # ตรวจสอบว่าเจอคนในภาพหรือไม่
        if results.keypoints is not None and len(results.keypoints.xy) > 0:
            # ดึงพิกัด (x, y) ของคนแรกที่พบในซีน (มิติ 17 x 2)
            keypoints = results.keypoints.xy[0].cpu().numpy()
            
            # เก็บข้อมูลลงประวัติ (กรองเอาเฉพาะพิกัดที่ไม่เป็น 0,0)
            pose_history.append([frame_count, keypoints])
            
            # รักษาขนาดประวัติย้อนหลังไว้ 4 จุดก็เพียงพอต่อการทำนายความเร็ว
            if len(pose_history) > 4:
                pose_history.pop(0)
                
            current_keypoints = keypoints
            is_yolo_frame = True
        else:
            is_yolo_frame = False

    # --- จังหวะที่ 2: เฟรมที่ข้าม -> ใช้ Sklearn ทำนายพิกัดข้อต่อ ---
    else:
        # ต้องมีประวัติจาก YOLO อย่างน้อย 2 เฟรมขึ้นไปถึงจะเริ่มคำนวณทิศทางได้
        if len(pose_history) >= 2:
            X_train = np.array([item[0] for item in pose_history]).reshape(-1, 1) # [frame_0, frame_4, ...]
            
            # สร้างตัวแปรเก็บผลลัพธ์การทำนายข้อต่อทั้ง 17 จุด
            predicted_keypoints = np.zeros((17, 2))
            
            # วนลูปเทรนและทำนายทีละข้อต่อ (ข้อต่อ 0 ถึง 16)
            for kp_idx in range(17):
                # ดึงพิกัด X และ Y ของข้อต่อตัวนี้จากประวัติที่ผ่านมา
                y_train_x = np.array([item[1][kp_idx][0] for item in pose_history])
                y_train_y = np.array([item[1][kp_idx][1] for item in pose_history])
                
                # ถ้าข้อต่อเคยตรวจจับได้จริง (ไม่ใช่พิกัด 0,0)
                if np.any(y_train_x > 0):
                    # ทำนายพิกัด X
                    reg_x = LinearRegression().fit(X_train, y_train_x)
                    pred_x = reg_x.predict(np.array([[frame_count]]))[0]
                    
                    # ทำนายพิกัด Y
                    reg_y = LinearRegression().fit(X_train, y_train_y)
                    pred_y = reg_y.predict(np.array([[frame_count]]))[0]
                    
                    predicted_keypoints[kp_idx] = [pred_x, pred_y]
            
            current_keypoints = predicted_keypoints
            is_yolo_frame = False
        else:
            # ถ้าประวัติยังไม่พอ ให้ดึงค่าจากเฟรมล่าสุดมาใช้ตรงๆ ไปก่อน
            if len(pose_history) > 0:
                current_keypoints = pose_history[-1][1]
            is_yolo_frame = False

    # --- จังหวะที่ 3: วาดโครงร่างร่างกายนมนุษย์ (Skeleton) ---
    if current_keypoints is not None:
        # เลือกสี: เฟรมจริงจาก YOLO เป็นสีเขียวเข้ม | เฟรมทำนายจาก Sklearn เป็นสีฟ้า Cyan
        color = (0, 255, 0) if is_yolo_frame else (255, 255, 0)
        
        # 1. วาดจุดข้อต่อ (Keypoints)
        for kp in current_keypoints:
            x, y = map(int, kp)
            if x > 0 and y > 0: # วาดเฉพาะจุดที่มีพิกัดอยู่จริงบนจอ
                cv2.circle(frame, (x, y), 5, color, -1)
        
        # 2. วาดเส้นเชื่อมกระดูก (Skeleton Links) มาตรฐาน COCO
        # คู่ตัวเลขแทนจุดเชื่อมต่อ เช่น (5, 7) คือ ไหล่ซ้ายไปข้อศอกซ้าย
        skeleton_connections = [
            (5, 7), (7, 9), (6, 8), (8, 10),   # แขนซ้าย-ขวา
            (11, 13), (13, 15), (12, 14), (14, 16), # ขาซ้าย-ขวา
            (5, 6), (5, 11), (6, 12), (11, 12)  # ลำตัว
        ]
        
        for start_idx, end_idx in skeleton_connections:
            start_pt = current_keypoints[start_idx]
            end_pt = current_keypoints[end_idx]
            
            x1, y1 = map(int, start_pt)
            x2, y2 = map(int, end_pt)
            
            if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    # แสดงผลและนับเฟรม
    cv2.imshow("YOLO26-Pose + Sklearn (Low Latency Tracking)", frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()