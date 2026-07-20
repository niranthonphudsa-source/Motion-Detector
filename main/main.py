import os
import shutil
import cv2
from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.file_manager import save_roi_to_txt, load_roi_from_txt
from LIB.user_manager import UserStateManager  # ✨ นำเข้าตัวจัดการที่เราสร้างขึ้น
from ultralytics import YOLO
import numpy as np
import joblib
import time
import yaml
import pandas as pd

# โหลด config.yml
with open(r"setting\config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

camera = config["cameras"]["Camera_3"]
model_sklearn = config["global"]["model_path"]
source = camera["source"]

# 1. ตั้งค่าเริ่มต้นและโหลดโมดูล
roi = ROIHandler()
window_name = "Mode Control ROI"
s = ShowPredict()

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
roi.mark_points = load_roi_from_txt()

model = YOLO('yolo26n-pose.pt')
pose_classifier = joblib.load(model_sklearn) 

check_pose = ["Right", "Left", "Front"]
ok_display_time = 5.0
SKIP_FRAMES = 1
predicted_label = "None"
confidence = 0.3

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]

cap = cv2.VideoCapture(source)
os.makedirs("video_ng", exist_ok=True)
os.makedirs("video_ok", exist_ok=True)
os.makedirs("video_center", exist_ok=True)

fourcc = cv2.VideoWriter_fourcc(*'XVID')

# ✨ เรียกใช้งานตัวจัดการสถานะ ID และวิดีโอ (ตั้งค่าเวลารอ 2.0 วินาที ระยะสลับไม่เกิน 80 พิกเซล)
manager = UserStateManager(check_pose, fourcc, ok_display_time=5.0, max_lost_time=2.0, max_distance=80, buffer_output_time=10.0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    
    s.current_frame_poses = [] 
    s.current_frame_ids = [] 
    num_pts = len(roi.mark_points)
            
    if num_pts > 0:
        for pt in roi.mark_points:
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        for i in range(num_pts - 1):
            cv2.line(frame, roi.mark_points[i], roi.mark_points[i+1], (0, 255, 255), 2)
        if roi.is_confirmed and num_pts > 2:
            cv2.line(frame, roi.mark_points[-1], roi.mark_points[0], (0, 255, 255), 2)

    # --- ส่วนที่ 1: หาพิกัด Keypoints ---
    if s.frame_count % SKIP_FRAMES == 0:
        predict_frame = model.track(source=frame, conf=0.5, persist=True, verbose=False)
        s.update_pose_history(predict_frame)    
    else:
        s.predicted_people_kp = []
        s.predicted_people_ids = []
        s.predict_keypoints_from_history(s.pose_history, s.frame_count, SKIP_FRAMES)
        if len(s.predicted_people_kp) > 0:
            s.current_frame_poses = np.array(s.predicted_people_kp)
            s.current_frame_ids = np.array(s.predicted_people_ids)

    # --- ส่วนที่ 2: ตรรกะประมวลผลแยกบุคคล ---
    any_people_inside = False
    current_frame_active_ids = set(s.current_frame_ids)

    for point_pose, s.p_id in zip(s.current_frame_poses, s.current_frame_ids):
        if len(point_pose) < 17: 
            continue
        
        # ✨ เรียกใช้งานสิทธิ์ของ ID หรือกู้คืน ID ผิดพลาดผ่าน Manager
        state = manager.get_or_recover_id(s.p_id, current_frame_active_ids, point_pose)
        if state is None:
            continue

        people_in_rectangle = False

        if roi.mark_points and len(roi.mark_points) >= 2:
            roi.is_confirmed = True
            contour = np.array(roi.mark_points, dtype=np.int32)
            foot_inside_count = 0
            for s.idx in (15, 16):
                hpx, hpy = int(point_pose[s.idx][0]), int(point_pose[s.idx][1])
                inside = cv2.pointPolygonTest(contour, (hpx, hpy), False)
                if inside >= 0:
                    foot_inside_count += 1
            
            if foot_inside_count > 0:
                people_in_rectangle = True
                any_people_inside = True 

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

        # ตรรกะตรวจจับท่าทางเมื่ออยู่ใน ROI
        if people_in_rectangle:
            if state["is_terminating"]:
                state["is_terminating"] = False
                state["termination_start_time"] = None
                print(f"🏃‍♂️ ID {s.p_id} กลับเข้ามาในพื้นที่ตรวจ -> ยกเลิกการหน่วงเวลาปิดไฟล์")

            if state["writer"] is None:
                current_time_str = int(time.time())
                state["video_filename"] = f"video_center/violation_{s.p_id}_{current_time_str}.avi"
                state["writer"] = cv2.VideoWriter(state["video_filename"], fourcc, 20.0, (w, h))
                print(f"[Record] ID {s.p_id} เข้าจุด -> เปิดวิดีโอ: {state['video_filename']}")

            normalized_points = []
            for kp in point_pose:
                kpx, kpy = int(kp[0]), int(kp[1])
                if kpx == 0 and kpy == 0:
                    normalized_points.append((0.0, 0.0))
                    continue
                normalized_points.append((kpx / w, kpy / h))
                cv2.circle(frame, (kpx, kpy), 5, (0, 0, 255), cv2.FILLED)

            feature_names = [f"{axis}_{i}" for i in range(17) for axis in ("x", "y")]
            features = np.array(normalized_points).flatten()

            if len(features) == 34:
                features_df = pd.DataFrame([features], columns=feature_names)
                predicted_label = pose_classifier.predict(features_df)[0]
                probabilities = pose_classifier.predict_proba(features_df)[0]
                confidence = np.max(probabilities) * 100

                # ล็อกแสดงผล OK ค้าง
                if state["is_ok_holding"]:
                    if time.time() - state["ok_start_time"] < manager.ok_display_time:
                        state["confirm"] = "OK"
                    else:
                        state["is_ok_holding"] = False
                        state["confirm"] = "NG"
                        state["valaus_last"] = [] 
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

            # สั่งเริ่มบันทึกวิดีโอ
            if state["writer"] is None:
                current_time_str = int(time.time())
                state["video_filename"] = f"video_center/violation_{s.p_id}_{current_time_str}.avi"
                state["writer"] = cv2.VideoWriter(state["video_filename"], fourcc, 20.0, (w, h))
                print(f"[Record] ID {s.p_id} เข้าจุด -> เปิดวิดีโอ: {state['video_filename']}")

        # จังหวะที่เดินออกจากจุดเช็ค
        if not people_in_rectangle and state["was_inside_last_frame"]:
            if state["writer"] is not None and not state["is_terminating"]:
                # 🌟 แทนที่จะปิดไฟล์ทันที เราตั้งค่าให้ระบบรู้ว่า "เริ่มเข้าสู่ช่วงหน่วงเวลาอัดต่อ 1 วิ"
                state["is_terminating"] = True
                state["termination_start_time"] = time.time()
                print(f"⏱️ ID {s.p_id} เดินออกจากจุดเช็ค -> เริ่มนับเวลาถอยหลังเพื่ออัดวิดีโอเก็บสถานะเพิ่มอีก {manager.buffer_output_time} วินาที...")
            # if state["writer"] is not None:
            #     state["writer"].release()
            #     state["writer"] = None
            #     print(f"[Record] ID {s.p_id} เดินออก -> ปิดและคัดแยกไฟล์")

                if state["video_filename"] and os.path.exists(state["video_filename"]):
                    base_filename = os.path.basename(state["video_filename"])
                    dest_folder = "video_ok" if state["confirm"] == "OK" else "video_ng"
                    dest_path = f"{dest_folder}/{base_filename}"
                    
                    try:
                        shutil.copy(state["video_filename"], dest_path)
                    except Exception as e:
                        print(f"❌ คัดลอกไฟล์ผิดพลาด: {e}")

                state["video_filename"] = None
                if state["confirm"] != "OK":
                    state["valaus_last"] = []

        # ✨ อัปเดตข้อมูลพิกัด/เวลา ป้องกันหลุด และเขียนเฟรมลงวิดีโอ
        manager.update_tracking_data(state, people_in_rectangle, point_pose)

        # การแสดงผล Text บนตัวบุคคล
        text_x = int(point_pose[5][0]) if point_pose[5][0] > 0 else 50
        text_y_start = int(point_pose[5][1]) - 80 if point_pose[5][1] > 80 else 50
        line_height = 20
        status_color = (0, 255, 0) if state["confirm"] == "OK" else (0, 0, 255)
        
        display_lines = [
            f"ID: {s.p_id}",
            f"Pose: {predicted_label} ({confidence:.1f}%)" if people_in_rectangle else "Pose: Outside ROI",
            f"Progress: {len(state['valaus_last'])}/{len(check_pose)} {state['valaus_last']}",
            f"STATUS: {state['confirm']}"
        ]
        
        for i, line_text in enumerate(display_lines):
            current_y = text_y_start + (i * line_height)
            if "STATUS" in line_text:
                cv2.putText(frame, line_text, (text_x, current_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            else:
                cv2.putText(frame, line_text, (text_x, current_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, 3)

        if state["writer"] is not None:
            state["writer"].write(frame)
    # ✨ เรียกฟังก์ชันดักจับและปิดงาน ID ที่หายไปจากกล้องถาวร (เกิน 2 วินาที) ของ Manager
    manager.handle_lost_people(current_frame_active_ids)

    # --- ส่วนที่ 3: UI กล่อง ROI รวม ---
    check_people = "People in Rectangle" if any_people_inside else "None People"
    box_color = (0, 0, 255) if any_people_inside else (0, 255, 0)
    
    if roi.mark_points and len(roi.mark_points) >= 3:
        pts = np.array(roi.mark_points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], isClosed=True, color=box_color, thickness=2)
        cv2.putText(frame, check_people, (roi.mark_points[0][0], roi.mark_points[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    mode_text = "Mode: DRAWING (Press Mouse & Drag)" if roi.current_mode == 1 else "Mode: NORMAL (Press '1' to Edit)"
    mode_color = (0, 0, 255) if roi.current_mode == 1 else (255, 0, 0)
    cv2.putText(frame, mode_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
            
    cv2.imshow(window_name, frame)
    s.frame_count += 1 

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        roi.current_mode = 1
        cv2.setMouseCallback(window_name, roi.click_event)
    elif key == ord('2'):
        roi.is_confirmed = True
        save_roi_to_txt(roi.mark_points)
        roi.current_mode = 0
    elif key == ord('c'):
        roi.clear()
    elif key == ord('q'):
        break

# ✨ สั่งปิดงานวิดีโอที่อาจค้างอยู่ทั้งหมดตอนออกจากโปรแกรม
manager.close_all_writers()
cap.release()
cv2.destroyAllWindows()