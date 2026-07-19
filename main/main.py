import os

import cv2
from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.file_manager import save_roi_to_txt, load_roi_from_txt
from LIB.pose_gui import CameraSelectorGUI
from ultralytics import YOLO
from sklearn.linear_model import LinearRegression
import numpy as np
import joblib
import time
import yaml
import pandas as pd
import tkinter as tk


# โหลด config.yml
with open("setting\config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# # ดึงข้อมูลกล้อง
camera = config["cameras"]["Camera_3"]
model_sklearn = config["global"]["model_path"]
print(f"Loaded model from: {model_sklearn}")


# # ตัวอย่างการเข้าถึงค่า
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

# โหลดพิกัดเก่าที่เคยบันทึกไว้ (ถ้ามี)
roi.mark_points = load_roi_from_txt()

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
os.makedirs("video_ng", exist_ok=True)

video_writer = None
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # หรือใช้ 'mp4v'

while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    
    s.current_frame_poses = [] 
    s.current_frame_ids = [] 

    num_pts = len(roi.mark_points)
            
    # 3. วาดเส้นและจุดบนจอ
    if num_pts > 0:
        # วาดวงกลมเล็ก ๆ ในทุกจุดที่คลิก
        for pt in roi.mark_points:
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            
        # ลากเส้นเชื่อมจาก จุด 1 -> 2 -> 3 ไปเรื่อย ๆ
        for i in range(num_pts - 1):
            cv2.line(frame, roi.mark_points[i], roi.mark_points[i+1], (0, 255, 255), 2)
            
        # ถ้ากดยืนยันแล้ว (is_confirmed == True) ให้ลากเส้นจาก จุดสุดท้าย กลับมา จุดแรก
        if roi.is_confirmed and num_pts > 2:
            cv2.line(frame, roi.mark_points[-1], roi.mark_points[0], (0, 255, 255), 2)


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
        if roi.mark_points is not None and len(roi.mark_points) >= 2:
        
            contour = np.array(roi.mark_points, dtype=np.int32)
            foot_inside_count = 0
            for s.idx in (15, 16):
                hpx, hpy = int(point_pose[s.idx][0]), int(point_pose[s.idx][1])
                inside = cv2.pointPolygonTest(contour, (hpx, hpy), False)
                if inside >= 0:  # อยู่ใน polygon
                    foot_inside_count += 1
            
            if foot_inside_count > 0:
                people_in_rectangle = True
                any_people_inside = True  # ใช้สำหรับเปลี่ยนสีกล่อง ROI รวม

            # วาดจุดใบหน้าสีเหลือง
            for s.idx in range(17):
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
        line_height = 20
        
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
                
            # ตรวจสอบเงื่อนไขการบันทึกวิดีโอ
        if state["confirm"] != "OK":
            if video_writer is None:
                filename = f"video_ng/violation_{s.p_id}_{int(time.time())}.avi"
                video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
                print(f"เริ่มบันทึกวิดีโอ: {filename}")

            # เขียนเฟรมหลังจากวาดเส้นครบแล้ว
            video_writer.write(frame)

        else:
            if video_writer is not None:
                video_writer.release()
                video_writer = None
                print("หยุดบันทึกวิดีโอ (ทำครบเงื่อนไข)")
                
    # --- ส่วนที่ 4: วาดอินเตอร์เฟซระบบ ROI รวม ---
    check_people = "People in Rectangle" if any_people_inside else "None People"
    box_color = (0, 0, 255) if any_people_inside else (0, 255, 0)
    
    if roi.mark_points is not None and len(roi.mark_points) >= 3:
        pts = np.array(roi.mark_points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], isClosed=True, color=box_color, thickness=2)
        cv2.putText(frame, check_people, (roi.mark_points[0][0], roi.mark_points[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    mode_text = "Mode: DRAWING (Press Mouse & Drag)" if roi.current_mode == 1 else "Mode: NORMAL (Press '1' to Edit)"
    mode_color = (0, 0, 255) if roi.current_mode == 1 else (255, 0, 0)
    cv2.putText(frame, mode_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)

    cv2.imshow(window_name, frame)
    s.frame_count += 1 

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        roi.current_mode = 1
        cv2.setMouseCallback(window_name, roi.click_event)
        # print(">> เข้าสู่โหมด: มาร์คจุด (กดเมาส์ซ้ายเพื่อมาร์คขอบเขต)")
    elif key == ord('2'):
        roi.is_confirmed = True
        save_roi_to_txt(roi.mark_points)
        # print(f"Successfully Saved! บันทึกพิกัด {roi.mark_points} เรียบร้อย")
        roi.current_mode = 0
    elif key == ord('c'):
        roi.clear()
        # print("ล้างค่าพิกัดและกลับสู่โหมดปกติ")
    elif key == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()

