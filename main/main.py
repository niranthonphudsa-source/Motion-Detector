import os
import cv2
import math
import numpy as np
import joblib
import time
import pandas as pd
import threading
import tkinter as tk
import serial

from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.file_manager import save_roi_to_txt, load_roi_from_txt
from LIB.user_manager import UserStateManager  
from LIB.config_gui import ConfigGUI
from app.app import TableViewerWindow, SSMSConnectGUI, ConfigManager
from LIB.stats_gui import StatsGUI, StatsManager
from LIB.config_loader_start import AppConfig
from ultralytics import YOLO
from LIB.help_gui import HelpGUI
from setting_esp32.setting_esp32 import PinConfigGUI
from rtspVideo import RTSPVideoGrabber

# ─── โหลดและจัดการ CONFIG ───
app_config = AppConfig(r"setting\config.yml")

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
model_sklearn = app_config.model_sklearn

# ─── ตั้งค่าเริ่มต้นและโหลดโมดูลตรวจจับ ───
roi = ROIHandler()
window_name = f"Mode Control ROI - {active_camera_id}"
s = ShowPredict()

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) 
cv2.setMouseCallback(window_name, roi.click_event)

# ดึงจุดมาร์กตามกล้องปัจจุบันใน config.yml
roi.mark_points = camera.get("mark_points", [])
roi.start_point = camera.get("start_point", None)
roi.reverse_point = camera.get("reverse_point", None)

if len(roi.mark_points) > 0:
    roi.is_confirmed = True

model = YOLO('yolo26n-pose.pt')

check_pose = ["Right", "Left", "Front"]
ok_display_time = 5.0
SKIP_FRAMES = 1
predicted_label = "None"
confidence = 0.0
any_people_inside = False
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]

cap = RTSPVideoGrabber(source)

os.makedirs("video_ng", exist_ok=True)
os.makedirs("video_ok", exist_ok=True)
os.makedirs("video_center", exist_ok=True)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
manager = UserStateManager(check_pose, fourcc, ok_display_time=5.0, max_lost_time=2.0, max_distance=80, buffer_output_time=3)

direction_tracker = {}
pose_classifier = joblib.load(model_sklearn) 

def get_distance(p1, p2):
    if p1 is None or p2 is None: return 999999
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def reload_config_callback(new_camera_id, updated_config=None):
    global save_ok_flag, save_ng_flag, config, active_camera_id, camera, cap, window_name, roi, model_sklearn, pose_classifier
    
    if updated_config:
        config = updated_config
        config_manager.config = updated_config
    else:
        config_manager.config = config_manager.load_config()
        config = config_manager.config
    
    try:
        model_info = config.get("model", {}).get("Model_path_1", {})
        new_model_path = model_info.get("source", "") if isinstance(model_info, dict) else str(model_info)

        if new_model_path and os.path.exists(new_model_path):
            model_sklearn = new_model_path
            pose_classifier = joblib.load(model_sklearn)
            print(f"🤖 [Model Reloaded] อัปเดตโมเดลเป็น: {model_sklearn}")
        else:
            print(f"⚠️ [Model Warning] ไม่พบไฟล์โมเดลที่ Path: {new_model_path}")
    except Exception as e:
        print(f"❌ [Model Error] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")

    # 🔄 สลับกล้อง (Switch Camera)
    if active_camera_id != new_camera_id:
        print(f"🔄 [Switch Camera] ตรวจพบการเปลี่ยนกล้องจาก {active_camera_id} ➡️ {new_camera_id}")
        
        old_cap = cap
        active_camera_id = new_camera_id
        camera = config["cameras"][active_camera_id]
        
        new_source = camera["source"]
        cap = RTSPVideoGrabber(new_source)
        
        # ป้องกัน AttributeError ด้วยการเรียก stop() หรือ release() แบบปลอดภัย
        if old_cap:
            if hasattr(old_cap, 'stop'):
                old_cap.stop()
            elif hasattr(old_cap, 'release'):
                old_cap.release()

        # อัปเดตพิกัด ROI & จุดมาร์ก
        roi.clear()
        roi.mark_points = camera.get("mark_points", [])
        roi.start_point = camera.get("start_point", None)
        roi.reverse_point = camera.get("reverse_point", None)
        if len(roi.mark_points) > 0:
            roi.is_confirmed = True

    cam_data = config["cameras"].get(active_camera_id, {})
    save_ok_flag = cam_data.get("save_ok", True)
    save_ng_flag = cam_data.get("save_ng", True)
    
    print(f"⚙️ สเตตัสปัจจุบัน: Save OK={save_ok_flag}, Save NG={save_ng_flag}, Model={model_sklearn}")

def open_ssms_gui():
    def run_gui():
        db_root = tk.Tk()
        app = SSMSConnectGUI(db_root)
        db_root.mainloop()

    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()

simulated_key = -1
def trigger_key_from_gui(key_code):
    global simulated_key
    simulated_key = key_code

help_gui = HelpGUI(key_callback=trigger_key_from_gui)

def open_help_window():
    gui_thread = threading.Thread(target=help_gui.open_window, daemon=True)
    gui_thread.start()

def apply_pin_config_to_mcu(config_data):
    port = config_data["port"]
    baud = config_data["baudrate"]
    
    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            command = f"SETPIN:TRIG={config_data['trig_pin']},ECHO={config_data['echo_pin']},RELAY={config_data['relay_pin']}\n"
            ser.write(command.encode('utf-8'))
            print(f"📡 ส่งคำสั่งตั้งค่า Pin ไปยัง {port}: {command.strip()}")
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อกับ {port} ได้: {e}")

# 🔴 แก้ไข: เปิด PinConfigGUI แบบ Threading ไม่ให้บล็อก OpenCV
def open_pin_config_window():
    def run_gui():
        app = PinConfigGUI(on_save_callback=apply_pin_config_to_mcu)
        app.run()

    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()

stats_db = StatsGUI(db_path=r"setting\inspection_stats.db")
stats_manager = StatsManager(db_path=r"setting\inspection_stats.db")

config_manager.open_settings(current_cam_id=active_camera_id, on_close_callback=reload_config_callback)  
latest_frame = None

# ─── เริ่มต้นลูปประมวลผลวิดีโอ ───
while True:
    
    ret, frame = cap.read()
    if not ret:     
        break
        # continue
    frame = cv2.resize(frame, (640, 640))
    h, w = frame.shape[:2]
    # 🌟 อัปเดต Frame ล่าสุดเข้าตัวแปรแชร์ (ควร copy() เพื่อป้องกัน Thread Race Condition)
    latest_frame = frame.copy()

    # 1. รับคำสั่งจากแป้นคีย์บอร์ดจริง
    key = cv2.waitKey(1) & 0xFF

    # 2. ถ้ามีคำสั่งจำลองมาจาก GUI ให้ใช้ค่านั้นแทน
    if simulated_key != -1:
        key = simulated_key
        simulated_key = -1  # ล้างค่าเมื่อดึงไปใช้แล้ว
    
    s.current_frame_poses = [] 
    s.current_frame_ids = [] 
    num_pts = len(roi.mark_points)

    # --- ส่วนที่ 3: UI กล่อง ROI รวม และวาด Marker Indicators ---
    check_people = "People in Rectangle" if any_people_inside else "None People"
    box_color = (0, 0, 255) if any_people_inside else (0, 255, 0)

    # วาดจุดมาร์กและเส้นตาราง ROI Polygon
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

    # 🌟 วาดจุด Start (จุดที่ 1) และ Reverse (จุดที่ 2) บนหน้าจอ
    frame = roi.draw_indicators(frame)

    # --- ส่วนที่ 1: หาพิกัด Keypoints ---
    if s.frame_count % SKIP_FRAMES == 0:
        predict_frame = model.track(source=frame,
                                    conf=0.5, 
                                    persist=True, 
                                    verbose=False, 
                                    tracker="bytetrack.yaml")
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

        # ดึงพิกัดเท้าเพื่อใช้เช็กระยะกับจุดมาร์ก (Ankle: 15, 16)
        foot_x = int((point_pose[15][0] + point_pose[16][0]) / 2)
        foot_y = int((point_pose[15][1] + point_pose[16][1]) / 2)
        foot_pos = (foot_x, foot_y)

        # 🌟 ─── ตรวจสอบทิศทางการเดิน (Direction Check) ───
        if s.p_id not in direction_tracker:
            direction_tracker[s.p_id] = {'first_touch': None, 'is_reverse': False}

        person_dir = direction_tracker[s.p_id]

        # ถ้ายังไม่มีการระบุว่าเข้าจุดไหนก่อน ให้คำนวณระยะทางสัมผัสจุด (รัศมี 50px)
        if person_dir['first_touch'] is None:
            dist_to_start = get_distance(foot_pos, roi.start_point)
            dist_to_reverse = get_distance(foot_pos, roi.reverse_point)

            if dist_to_reverse < 50:
                person_dir['first_touch'] = 'REVERSE'
                person_dir['is_reverse'] = True
                print(f"🚫 ID {s.p_id}: เดินสวนทาง! (เข้าจุดที่ 2 ก่อน) -> ไม่ตรวจจับท่าทาง")
            elif dist_to_start < 50:
                person_dir['first_touch'] = 'START'
                person_dir['is_reverse'] = False
                print(f"✅ ID {s.p_id}: เดินถูกทิศทาง! (เข้าจุดที่ 1 ก่อน) -> เริ่มระบบตรวจจับ")

        # 🛑 หากเป็นคนที่เดินสวนทางมา ให้ข้ามตรรกะการตรวจท่าทางและการบันทึกไฟล์ไปเลย
        if person_dir['is_reverse']:
            cv2.putText(frame, f"ID: {s.p_id} [REVERSE - IGNORED]", (foot_x - 30, foot_y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            continue

        # --- ตรวจสอบว่าอยู่ในพื้นที่ ROI Polygon หรือไม่ ---
        if roi.mark_points and len(roi.mark_points) >= 2:
            contour = np.array(roi.mark_points, dtype=np.int32).reshape((-1, 1, 2))
            foot_inside_count = 0
            for idx in (15, 16):
                hpx, hpy = int(point_pose[idx][0]), int(point_pose[idx][1])
                inside = cv2.pointPolygonTest(contour, (hpx, hpy), False)
                if inside >= 0:
                    foot_inside_count += 1
            
            if foot_inside_count > 0:
                people_in_rectangle = True
                any_people_inside = True 

            for idx in range(17):
                hpx, hpy = int(point_pose[idx][0]), int(point_pose[idx][1])
                if hpx > 0 and hpy > 0:
                    cv2.circle(frame, (hpx, hpy), 3, (0, 255, 255), cv2.FILLED)

        # วาดเส้นกระดูก Skeleton
        point_skel = point_pose.astype(int)
        for start_idx, end_idx in SKELETON_CONNECTIONS:
            if (point_skel[start_idx, 0] == 0 and point_skel[start_idx, 1] == 0) or \
               (point_skel[end_idx, 0] == 0 and point_skel[end_idx, 1] == 0):
                continue
            cv2.line(frame, tuple(point_skel[start_idx]), tuple(point_skel[end_idx]), (0, 255, 0), 2)


        # ─── 📍 จุดที่ 1: ตรรกะเมื่ออยู่ใน ROI (เข้าจุดเช็ก) ───
        if people_in_rectangle:
            if state["is_terminating"]:
                state["is_terminating"] = False
                state["termination_start_time"] = None
                print(f"🏃‍♂️ ID {s.p_id} กลับเข้ามาในพื้นที่ตรวจ -> ยกเลิกการหน่วงเวลาปิดไฟล์")

            if state["writer"] is None:
                current_time_str = int(time.time())
                state["video_filename"] = f"video_center/violation_{s.p_id}_{current_time_str}.avi"
                state["writer"] = cv2.VideoWriter(state["video_filename"], fourcc, 20.0, (w, h))
                print(f"[Record] ID {s.p_id} เข้าจุด -> เริ่มบันทึกวิดีโอ: {state['video_filename']}")

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

        # ─── 📍 จุดที่ 2: ตรรกะเมื่อเดินออกจากจุดเช็ก (เริ่มนับถอยหลัง อัดวิดีโอแถม) ───
        if not people_in_rectangle and state["was_inside_last_frame"]:
            if state["writer"] is not None and not state["is_terminating"]:
                state["is_terminating"] = True
                state["termination_start_time"] = time.time()
                print(f"⏱️ ID {s.p_id} เดินออกจากจุดเช็ค -> เริ่มนับถอยหลังอัดแถมอีก {manager.buffer_output_time} วินาที...")

                
        # ─── 📍 จุดที่ 3: อัปเดตสถานะเข้า Manager และเขียน Frame ลงไฟล์วิดีโอ ───
        manager.update_tracking_data(state, people_in_rectangle, point_pose)

        # แสดงข้อความบนตัวบุคคล
        text_x = int(point_pose[5][0]) if point_pose[5][0] > 0 else 50
        text_y_start = int(point_pose[5][1]) - 80 if point_pose[5][1] > 80 else 50
        line_height = 20
        status_color = (0, 255, 0) if state["confirm"] == "OK" else (0, 0, 255)

        color_state1 = (0, 255, 0) if len(state['valaus_last']) >= 1 else (255, 255, 255)
        color_state2 = (0, 255, 0) if len(state['valaus_last']) >= 2 else (255, 255, 255)
        color_state3 = (0, 255, 0) if len(state['valaus_last']) >= 3 else (255, 255, 255)
            

        display_lines = [
            f"ID: {s.p_id}",
            f"Pose: {predicted_label} ({confidence:.1f}%)" if people_in_rectangle else "Pose: Outside ROI",
            # f"Progress Test: {len(state['valaus_last'])}/{len(check_pose)} {state['valaus_last']}",
            f"State Right",
            f"State Left",
            f"State Front",
            f"STATUS: {state['confirm']}"
        ]

        for i, line_text in enumerate(display_lines):
            current_y = text_y_start + (i * line_height)
            if "Pose" in line_text:
                cv2.putText(frame, line_text, (text_x + 40, current_y + 40), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255), 1, 3)
            elif "State Right" in line_text:
                cv2.putText(frame, line_text, (text_x + 40, current_y + 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, color_state1, 1, 3)

            elif "State Left" in line_text:
                cv2.putText(frame, line_text, (text_x + 40, current_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_state2, 1, 3)

            elif "State Front" in line_text:
                cv2.putText(frame, line_text, (text_x + 40, current_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_state3, 1, 3)

            elif "STATUS" in line_text:
                cv2.putText(frame, line_text, (text_x + 40, current_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            
            else:
                cv2.putText(frame, line_text, (text_x - 50, current_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, 3)

        if state["writer"] is not None:
            state["writer"].write(frame)
    # ─── 📍 จุดที่ 4: จัดการคนหลุดเฟรม / นับถอยหลังปิดวิดีโอ (วางไว้นอก for-loop บุคคล) ───
    manager.handle_lost_people(
        current_frame_active_ids, 
        save_ok=save_ok_flag, 
        save_ng=save_ng_flag,
        stats_db=stats_db,                # 👈 ส่งตัวบันทึกข้อมูลลง DB
        camera_id=active_camera_id        # 👈 ระบุ ID กล้อง
    )

    # ล้างข้อมูล direction_tracker สำหรับ ID ที่หลุดเฟรมไปนานแล้ว
    active_ids_list = list(direction_tracker.keys())
    for tid in active_ids_list:
        if tid not in current_frame_active_ids and tid not in manager.user_states:
            del direction_tracker[tid]


    # แสดงสถานะโหมดใช้งานบน UI
    mode_names = {0: "NORMAL", 1: "DRAW POLYGON", 2: "MARK POINT 1 (START)", 3: "MARK POINT 2 (REVERSE)"}
    status_text = f"MODE: {mode_names.get(roi.current_mode, 'NORMAL')}"
    cv2.putText(frame, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "1=Polygon | 3=Start Pt | 4=Reverse Pt | 2=Save Config | C=Clear | S=Settings | Q=Exit", 
                (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)


    # เรนเดอร์ภาพออกหน้าจอหลัก
    cv2.imshow(window_name, frame)
    s.frame_count += 1 
    
    # 2. 🌟 อัปเดต GUI ของ Dashboard (ถ้าหน้าต่างเปิดอยู่) ไม่ให้ค้าง
    stats_manager.update_window()

    # รับคำสั่งแป้นคีย์บอร์ด (Keyboard Actions)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('h'):  # 🌟 เพิ่มปุ่ม H สำหรับเปิด Help GUI
        print("💡 กำลังเปิดหน้าต่างคู่มือช่วยเหลือ (Help GUI)...")
        open_help_window()
        
    elif key == ord('1'):  # โหมดมาร์กพิกัดพื้นที่ Polygon
        roi.clear()
        roi.current_mode = 1
        print("✏️ เปิดโหมดวาด Polygon ROI: คลิกสร้างรูปปิด...")

    elif key == ord('3'):  # 🌟 โหมดมาร์กจุดเริ่มเช็ก (Start Point)
        roi.current_mode = 2
        print("🟢 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 1: Start Check Point]")

    elif key == ord('4'):  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
        roi.current_mode = 3
        print("🔴 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 2: Reverse Check Point]")
        
    elif key == ord('2'):  # บันทึกพิกัดจุดมาร์กเข้า config.yml
        roi.is_confirmed = True
        roi.current_mode = 0
        
        if "cameras" not in config_manager.config: config_manager.config["cameras"] = {}
        if active_camera_id not in config_manager.config["cameras"]: config_manager.config["cameras"][active_camera_id] = {}
        
        config_manager.config["cameras"][active_camera_id]["mark_points"] = roi.mark_points
        config_manager.config["cameras"][active_camera_id]["start_point"] = roi.start_point
        config_manager.config["cameras"][active_camera_id]["reverse_point"] = roi.reverse_point
        
        config_manager.save_config()
        print(f"💾 [Config Saved] บันทึก ROI ({len(roi.mark_points)} จุด), Start Pt {roi.start_point}, Reverse Pt {roi.reverse_point} ของกล้อง '{active_camera_id}' เรียบร้อย!")
            
    elif key == ord('c'):  # ล้างพิกัดหน้าจอ
        roi.clear()
        
    elif key == ord('s'):  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
        print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
        gui_thread = threading.Thread(
            target=config_manager.open_settings,
            kwargs={
                "current_cam_id": active_camera_id, 
                "on_close_callback": reload_config_callback
            },
            daemon=True
        )
        gui_thread.start()
    # 4. เพิ่มปุ่มลัด 'D' บน Keyboard เพื่อเปิดหน้า Dashboard
    # ⭕ เปลี่ยนเป็นชื่อฟังก์ชันจริงในคลาส StatsGUI เช่น:
    elif key == ord('d'):
        print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
        stats_manager.open_dashboard() # เปิด UI ขึ้นมาโดยไม่บล็อก Main Loop  
 
    elif key == ord('o'):
        print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
        open_ssms_gui()

manager.close_all_writers()
cap.release()
cv2.destroyAllWindows()

