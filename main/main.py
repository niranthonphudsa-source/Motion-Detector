import os
import shutil
import cv2
from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.file_manager import save_roi_to_txt, load_roi_from_txt
from LIB.user_manager import UserStateManager  
from LIB.config_gui import ConfigGUI  # ✨ นำเข้าตัวจัดการ GUI หลังบ้าน
from ultralytics import YOLO
import numpy as np
import joblib
import time
import yaml
import pandas as pd

# ─── โหลดและจัดการ CONFIG แยกตามกล้อง ───
config_manager = ConfigGUI(r"setting\config.yml")
config = config_manager.config

# 🌟 กำหนดชื่อกล้องเริ่มต้นที่ต้องการรันในไฟล์นี้
active_camera_id = "Camera_3" 

if active_camera_id not in config.get("cameras", {}):
    print(f"❌ ไม่พบข้อมูลกล้อง '{active_camera_id}' ในไฟล์ config.yml กรุณาเปิดหน้าตั้งค่าเพื่อเพิ่มข้อมูล")
    if "cameras" not in config: config["cameras"] = {}
    config["cameras"][active_camera_id] = {"source": 0, "save_ok": True, "save_ng": True, "mark_points": []}

camera = config["cameras"][active_camera_id]
model_sklearn = config["global"]["model_path"]
source = camera["source"]

# ตัวแปรสถานะการบันทึกไฟล์ที่ซิงค์มาจาก GUI
save_ok_flag = camera.get("save_ok", True)
save_ng_flag = camera.get("save_ng", True)

# ─── ตั้งค่าเริ่มต้นและโหลดโมดูลตรวจจับ ───
roi = ROIHandler()
window_name = f"Mode Control ROI - {active_camera_id}"
s = ShowPredict()

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
cv2.setMouseCallback(window_name, roi.click_event)

# ดึงจุดมาร์กตามกล้องปัจจุบันใน config.yml
roi.mark_points = camera.get("mark_points", [])
if len(roi.mark_points) > 0:
    roi.is_confirmed = True

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

# เรียกใช้งานตัวจัดการสถานะ ID และวิดีโอ
manager = UserStateManager(check_pose, fourcc, ok_display_time=5.0, max_lost_time=2.0, max_distance=80, buffer_output_time=10.0)


def reload_config_callback(new_camera_id):
    """✨ ฟังก์ชันปิดกล้องเก่า สลับกล้องใหม่ และโหลดจุดมาร์กใหม่ทันทีหลังจากปิด GUI"""
    global save_ok_flag, save_ng_flag, config, active_camera_id, camera, cap, window_name, roi
    
    # โหลดคอนฟิกใหม่
    config_manager.config = config_manager.load_config()
    config = config_manager.config
    
    # เช็คว่าผู้ใช้สลับกล้องใน GUI หรือไม่
    if active_camera_id != new_camera_id:
        print(f"🔄 [Switch Camera] ตรวจพบการเปลี่ยนกล้องจาก {active_camera_id} ➡️ {new_camera_id}")
        
        # 1. ปิดหน้าต่าง OpenCV ตัวเดิม และปิดสตรีมกล้องเดิม
        cv2.destroyWindow(window_name)
        if 'cap' in globals() and cap.isOpened():
            cap.release()
            
        # 2. อัปเดตชื่อกล้องตัวใหม่เข้าไปในระบบหลัก
        active_camera_id = new_camera_id
        camera = config["cameras"][active_camera_id]
        
        # 3. ตั้งชื่อหน้าต่างใหม่ เปิด OpenCV ตัวใหม่
        window_name = f"Mode Control ROI - {active_camera_id}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, roi.click_event)
        # 4. โหลดพิกัด ROI ประจำกล้องใหม่ตัวนี้เข้ามา
        roi.clear()
        roi.mark_points = camera.get("mark_points", [])
        if len(roi.mark_points) > 0:
            roi.is_confirmed = True
            
        # 5. เปิดสตรีมวิดีโอจากแหล่งข้อมูลใหม่
        new_source = camera["source"]
        cap = cv2.VideoCapture(new_source)
        print(f"🎥 เริ่มต้นสตรีมกล้องใหม่เรียบร้อย: {new_source}")
        
    # อัปเดตสถานะการบันทึกวิดีโอของกล้องตัวนั้นๆ
    cam_data = config["cameras"][active_camera_id]
    save_ok_flag = cam_data.get("save_ok", True)
    save_ng_flag = cam_data.get("save_ng", True)
    print(f"⚙️ สเตตัสการบันทึกปัจจุบัน: Save OK={save_ok_flag}, Save NG={save_ng_flag}")

# ─── เริ่มต้นลูปประมวลผลวิดีโอ ───
while True:
    ret, frame = cap.read()
    if not ret:
        cv2.waitKey(30)
        continue
    h, w = frame.shape[:2]
    
    s.current_frame_poses = [] 
    s.current_frame_ids = [] 
    num_pts = len(roi.mark_points)

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
        
        state = manager.get_or_recover_id(s.p_id, current_frame_active_ids, point_pose)
        if state is None:
            continue

        people_in_rectangle = False

        if roi.mark_points and len(roi.mark_points) >= 2:
            contour = np.array(roi.mark_points, dtype=np.int32).reshape((-1, 1, 2))
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

            # ยุบตรรกะเปิดใช้งาน VideoWriter ไว้ที่จุดเดียว
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

        # จังหวะที่เดินออกจากจุดเช็ค
        if not people_in_rectangle and state["was_inside_last_frame"]:
            if state["writer"] is not None and not state["is_terminating"]:
                state["is_terminating"] = True
                state["termination_start_time"] = time.time()
                print(f"⏱️ ID {s.p_id} เดินออกจากจุดเช็ค -> เริ่มนับเวลาถอยหลังเพื่ออัดวิดีโอเพิ่ม {manager.buffer_output_time} วินาที...")

                if state["video_filename"] and os.path.exists(state["video_filename"]):
                    base_filename = os.path.basename(state["video_filename"])
                    dest_folder = "video_ok" if state["confirm"] == "OK" else "video_ng"
                    dest_path = f"{dest_folder}/{base_filename}"
                    
                    should_save = (state["confirm"] == "OK" and save_ok_flag) or (state["confirm"] != "OK" and save_ng_flag)
                    
                    if should_save:
                        try:
                            shutil.copy(state["video_filename"], dest_path)
                            print(f"💾 บันทึกคัดแยกไฟล์วิดีโอลง '{dest_folder}' สำเร็จ")
                        except Exception as e:
                            print(f"❌ คัดลอกไฟล์ผิดพลาด: {e}")
                    else:
                        print(f"🗑️ ข้ามการเซฟไฟล์วิดีโอลง '{dest_folder}' ตามคำสั่งใน Config ปัจจุบัน")

                state["video_filename"] = None
                if state["confirm"] != "OK":
                    state["valaus_last"] = []

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



    manager.handle_lost_people(current_frame_active_ids)

    # --- ส่วนที่ 3: UI กล่อง ROI รวม และโหมดวาด ---
    check_people = "People in Rectangle" if any_people_inside else "None People"
    box_color = (0, 0, 255) if any_people_inside else (0, 255, 0)
    
    # วาดจุดมาร์กและเส้นตาราง ROI
    if num_pts > 0:
        for idx, pt in enumerate(roi.mark_points):
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)
            cv2.putText(frame, str(idx + 1), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
        for i in range(num_pts - 1):
            cv2.line(frame, tuple(roi.mark_points[i]), tuple(roi.mark_points[i+1]), (0, 255, 255), 2)
            
        if roi.is_confirmed and num_pts > 2:
            contour = np.array(roi.mark_points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [contour], isClosed=True, color=box_color, thickness=2)
            cv2.putText(frame, check_people, (int(roi.mark_points[0][0]), int(roi.mark_points[0][1] - 10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    # วางสถานะโหมดและคู่มือปุ่มลัดการใช้งานบนหน้าจอหลัก
    status_text = "MODE: DRAWING (Press '2' to confirm)" if roi.current_mode == 1 else "MODE: NORMAL (Press '1' to draw, 's' to settings)"
    cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "1=Draw | 2=Save ROI | C=Clear | S=Settings | Q=Exit", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    if state["writer"] is not None:
        state["writer"].write(frame)   
    # เรนเดอร์ภาพออกหน้าจอหลัก
    cv2.imshow(window_name, frame)
    s.frame_count += 1 
    
    # รับคำสั่งแป้นคีย์บอร์ด (Keyboard Actions)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
        
    elif key == ord('1'):  # เปิดโหมดมาร์กพิกัดพื้นที่
        roi.clear()
        roi.current_mode = 1
        print("✏️ เปิดโหมดวาด: สามารถคลิกซ้ายมาร์กจุดพื้นที่ได้อย่างอิสระ...")
        
    elif key == ord('2'):  # บันทึกพิกัดจุดมาร์กเข้า config.yml ของกล้องปัจจุบัน
        if len(roi.mark_points) >= 3:
            roi.is_confirmed = True
            roi.current_mode = 0
            
            if "cameras" not in config_manager.config: config_manager.config["cameras"] = {}
            if active_camera_id not in config_manager.config["cameras"]: config_manager.config["cameras"][active_camera_id] = {}
            
            config_manager.config["cameras"][active_camera_id]["mark_points"] = roi.mark_points
            config_manager.save_config()
            print(f"💾 [ROI Saved] ทำการเซฟพื้นที่มาร์ก ({len(roi.mark_points)} จุด) ของกล้อง '{active_camera_id}' เรียบร้อยแล้ว!")
        else:
            print("⚠️ กรุณาคลิกมาร์กให้ได้อย่างน้อย 3 จุดก่อนกดยืนยันเซฟพื้นที่ครับ")
            
    elif key == ord('c'):  # ล้างพิกัดหน้าจอ
        roi.clear()
        
    elif key == ord('s'):  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
        print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
        config_manager.open_settings(on_close_callback=reload_config_callback)

# เคลียร์ทรัพยากรระบบทั้งหมดเมื่อปิดโปรแกรม
manager.close_all_writers()
cap.release()
cv2.destroyAllWindows()