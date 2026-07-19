import cv2
from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.file_manager import save_roi_to_txt, load_roi_from_txt
from ultralytics import YOLO
from sklearn.linear_model import LinearRegression
import numpy as np
import joblib
import time
import yaml
import pandas as pd

# โหลด config.yml
with open("setting\config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# ดึงข้อมูลกล้อง
camera = config["cameras"]["Camera_3"]
model_sklearn = config["global"]["model_path"]
print(f"Loaded model from: {model_sklearn}")




# ตัวอย่างการเข้าถึงค่า
enabled = camera["enabled"]
source = camera["source"]
person_limit = camera["person_limit"]
display = camera["Display"]


# 1. ตั้งค่าเริ่มต้นและโหลดโมดูล
roi = ROIHandler()
window_name = "Mode Control ROI"

s = ShowPredict()
# เปลี่ยนเป็น WINDOW_NORMAL เพื่อให้สามารถย่อ-ขยายหน้าต่างได้ ขอบภาพจะไม่ล้นจอ
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
cv2.setMouseCallback(window_name, roi.draw_rectangle_callback)

# โหลดพิกัดเก่าที่เคยบันทึกไว้ (ถ้ามี)
roi.current_rect = load_roi_from_txt()

model = YOLO('yolo26n-pose.pt')
pose_classifier = joblib.load(model_sklearn)  # โมเดล Sklearn สำหรับจำแนกท่าทาง

check_people = "None People"

print("=== คู่มือการใช้งาน ===")
print("กด '1' : เปิดโหมดลากกล่อง (ลากเมาส์ซ้ายค้าง)")
print("กด '2' : บันทึกค่าพิกัดล่าสุดที่ลากไว้")
print("กด 'c' : ล้างพิกัดที่เลือกไว้")
print("กด 'q' : ออกจากโปรแกรม")
print("====================")

check_pose = ["Right", "Left", "Front"]
ok_display_time = 5.0  # ต้องการให้แสดงคำว่า "OK" ค้างไว้บนจอกี่วินาที


SKIP_FRAMES = 1

# ค่าเริ่มต้นสำหรับกรณีไม่ได้ทำนายท่าทาง
predicted_label = "None"
confidence = 0.3

# Dictionary สำหรับเก็บสถานะนับท่าทางแยกตาม ID คน
user_states = {} 
# โครงสร้างภายใน: user_states[p_id] = {"valaus_last": [], "confirm": "NG", "is_ok_holding": False, "ok_start_time": 0}

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),      # หัว
    (5, 6),                               # ไหล่
    (5, 7), (7, 9), (6, 8), (8, 10),    # แขน
    (5, 11), (6, 12),                    # ลำตัว
    (11, 12),                            # สะโพก
    (11, 13), (13, 15), (12, 14), (14, 16) # ขา
]

cap = cv2.VideoCapture(source)


while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    
    s.current_frame_poses = [] 
    s.current_frame_ids = [] 

    # --- ส่วนที่ 1: การหาพิกัด Keypoints (YOLO หรือ Linear Regression พยากรณ์เฟรมข้าม) ---
    if s.frame_count % SKIP_FRAMES == 0:
        predict_frame = model.track(source=frame, conf=0.5, persist=True, verbose=False)
        s.update_pose_history(predict_frame)    
        # s.current_frame_poses, s.current_frame_ids
        
    else:
        active_ids = list(s.pose_history.keys())
        s.predicted_people_kp = []
        s.predicted_people_ids = []
        
        s.predict_keypoints_from_history(s.pose_history, s.frame_count, SKIP_FRAMES)
        
        if len(s.predicted_people_kp) > 0:
            s.current_frame_poses = np.array(s.predicted_people_kp)
            s.current_frame_ids = np.array(s.predicted_people_ids)

    # --- ส่วนที่ 2: วาดผลลัพธ์ จำแนกท่าทาง และคำนวณตรรกะแยกรายบุคคล (ยุบรวมเหลือลูปเดียว) ---
    any_people_inside = False
    
    for point_pose, s.p_id in zip(s.current_frame_poses, s.current_frame_ids):
        if len(point_pose) < 17: 
            continue
        
        # สร้างสถานะเริ่มต้นให้ ID ใหม่ (ถ้ายังไม่มีในระบบ)
        if s.p_id not in user_states:
            user_states[s.p_id] = {
                "valaus_last": [],
                "confirm": "NG",
                "is_ok_holding": False,
                "ok_start_time": 0
            }
            
        # ดึงสถานะปัจจุบันของ ID นี้ขึ้นมาใช้
        state = user_states[s.p_id]
        
        people_in_rectangle = False
        if roi.current_rect is not None:
            x1, y1, x2, y2 = roi.current_rect
            xmin, xmax = min(x1, x2), max(x1, x2)
            ymin, ymax = min(y1, y2), max(y1, y2)
            
            foot_inside_count = 0
            for s.idx in (15, 16):
                hpx, hpy = int(point_pose[s.idx][0]), int(point_pose[s.idx][1])
                if (xmin <= hpx <= xmax) and (ymin <= hpy <= ymax):
                    foot_inside_count += 1
            
            if foot_inside_count > 0:
                people_in_rectangle = True
                any_people_inside = True  # ใช้สำหรับเปลี่ยนสีกล่อง ROI รวม

        # วาดจุดใบหน้าสีเหลือง
        for s.idx in range(5):
            hpx, hpy = int(point_pose[s.idx][0]), int(point_pose[s.idx][1])
            if hpx > 0 and hpy > 0:
                cv2.circle(frame, (hpx, hpy), 3, (0, 255, 255), cv2.FILLED)

        # วาดเส้นกระดูก
        point_skel = point_pose.astype(int)
        for start_idx, end_idx in SKELETON_CONNECTIONS:
            if (point_skel[start_idx, 0] == 0 and point_skel[start_idx, 1] == 0) or \
               (point_skel[end_idx, 0] == 0 and point_skel[end_idx, 1] == 0):
                continue
            cv2.line(frame, tuple(point_skel[start_idx]), tuple(point_skel[end_idx]), (0, 255, 0), 2)



        # ทำงานเมื่อหัวอยู่ใน ROI
        if people_in_rectangle:
            normalized_points = []
            for kp in point_pose:
                kpx, kpy = int(kp[0]), int(kp[1])
                if kpx == 0 and kpy == 0:
                    normalized_points.append((0.0, 0.0))
                    continue
                
                x_norm = kpx / w
                y_norm = kpy / h
                normalized_points.append((x_norm, y_norm))
                cv2.circle(frame, (kpx, kpy), 5, (0, 0, 255), cv2.FILLED)


            # ใช้ชื่อคอลัมน์ตรงกับตอน train
            feature_names = []
            for i in range(17):
                feature_names.append(f"x_{i}")
                feature_names.append(f"y_{i}")
                       
            features = np.array(normalized_points).flatten()

            if len(features) == 34:
                features_df = pd.DataFrame([features], columns=feature_names)
                predicted_label = pose_classifier.predict(features_df)[0]
                probabilities = pose_classifier.predict_proba(features_df)[0]
                confidence = np.max(probabilities) * 100
                # --- ตรรกะล็อกสถานะ OK ค้างไว้ และตรวจจับแบบ Strict ลำดับขวา -> ซ้าย -> หน้า ---
                if state["is_ok_holding"]:
                    if time.time() - state["ok_start_time"] < ok_display_time:
                        state["confirm"] = "OK"
                    else:
                        state["is_ok_holding"] = False
                        state["confirm"] = "NG"
                        state["valaus_last"] = []  # เริ่มนับศูนย์ใหม่จาก Right เท่านั้น
                else:
                    expected_pose_idx = len(state["valaus_last"])
                    if expected_pose_idx < len(check_pose):
                        expected_pose = check_pose[expected_pose_idx]
                        if predicted_label == expected_pose:
                            if not state["valaus_last"] or predicted_label != state["valaus_last"][-1]:
                                state["valaus_last"].append(predicted_label)

                    if state["valaus_last"] == check_pose:
                        state["confirm"] = "OK"
                        state["is_ok_holding"] = True
                        state["ok_start_time"] = time.time()

        # --- ส่วนที่ 3: จัดการแสดงผลเว้นบรรทัดแบบสวยงามใต้หัวไหล่ของแต่ละบุคคล ---
        text_x = int(point_pose[5][0]) if point_pose[5][0] > 0 else 50
        text_y_start = int(point_pose[5][1]) - 80 if point_pose[5][1] > 80 else 50
        line_height = 18 
        
        status_color = (0, 255, 0) if state["confirm"] == "OK" else (0, 0, 255)
        
        display_lines = [
            f"ID: {s.p_id}",
            f"Pose: {predicted_label} ({confidence:.1f}%)",
            f"Progress: {len(state['valaus_last'])}/{len(check_pose)} {state['valaus_last']}",
            f"STATUS: {state['confirm']}"
        ]
        
        for i, line_text in enumerate(display_lines):
            current_y = text_y_start + (i * line_height)
            if "STATUS" in line_text:
                cv2.putText(frame, line_text, (text_x, current_y + 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            else:
                cv2.putText(frame, line_text, (text_x, current_y + 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, 3)

    # --- ส่วนที่ 4: วาดอินเตอร์เฟซระบบ ROI รวม ---
    check_people = "People in Rectangle" if any_people_inside else "None People"
    box_color = (0, 0, 255) if any_people_inside else (0, 255, 0)
    
    if roi.current_rect is not None:
        cv2.rectangle(frame, (roi.current_rect[0], roi.current_rect[1]), 
                      (roi.current_rect[2], roi.current_rect[3]), box_color, 2)
        cv2.putText(frame, check_people, (roi.current_rect[0], roi.current_rect[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    if roi.current_mode == 1 and roi.drawing:
        cv2.rectangle(frame, (roi.ix, roi.iy), (roi.cx, roi.cy), (0, 0, 255), 2)

    mode_text = "Mode: DRAWING (Press Mouse & Drag)" if roi.current_mode == 1 else "Mode: NORMAL (Press '1' to Edit)"
    mode_color = (0, 0, 255) if roi.current_mode == 1 else (255, 0, 0)
    cv2.putText(frame, mode_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)

    cv2.imshow(window_name, frame)
    s.frame_count += 1 

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        roi.current_mode = 1
        print(">> เข้าสู่โหมด: ลากวาง (กดเมาส์ซ้ายค้างเพื่อวาดขอบเขต)")
    elif key == ord('2'):
        if save_roi_to_txt(roi.current_rect):
            print(f"Successfully Saved! บันทึกพิกัด {roi.current_rect} เรียบร้อย")
            roi.current_mode = 0
        else:
            print("❌ ยังไม่ได้ลากกล่องพิกัด กรุณากด 1 แล้วลากกล่องก่อน")
    elif key == ord('c'):
        roi.clear()
        print("ล้างค่าพิกัดและกลับสู่โหมดปกติ")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()