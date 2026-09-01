import os
import sys
import cv2
import math
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# ✅ ดักจับและแมป np.row_stack ไปหา np.vstack ก่อนที่ไลบรารีอื่นจะเรียกใช้
if not hasattr(np, "row_stack"):
    np.row_stack = np.vstack
import joblib
import time
import pandas as pd
import threading
import tkinter as tk
import serial
import mark_roi_polygon as mark_roi
import run_start.default_config_var as df
import callback_command.callback_command as clb
import show_mode_inDisplay as show_m
import csv
import datetime
import videoWrite
import queue
import torch
import subprocess
from display.display_gui import DisplayGui
from app.data_viewer_gui import CheckLastID
from check_people_in_roi import CheckPeopleInRoi, Check_where_inRectangle, RecordVedioDetect
# from search_keypoint import SearchKeypoint
from LIB.roi_handler import ROIHandler
from LIB.predict_frame_pose import ShowPredict
from LIB.user_manager import UserStateManager  
from LIB.stats_gui import StatsGUI, StatsManager
from LIB.config_loader_start import AppConfig
from ultralytics import YOLO
from rtspVideo import RTSPVideoGrabber
from LIB.zoom_arae import AdvancedZoomArea
from show_status_pose import ShowStatusPose
from LIB.Check_direction_of_Movement import Check_direction_of_Movement
from esp32_ng_controller import ESP32SerialController, NGThresholdController

# Keep CPU workloads bounded on mini PCs and avoid thread oversubscription.
CPU_THREADS = max(1, min(4, (os.cpu_count() or 2) - 1))
os.environ.setdefault("OMP_NUM_THREADS", str(CPU_THREADS))
torch.set_num_threads(CPU_THREADS)
cv2.setNumThreads(1)

HEARTBEAT_FILE = os.path.join(PROJECT_ROOT, "main", "logs", "heartbeat.txt")
SELECTED_CAMERA_FILE = os.path.join(PROJECT_ROOT, "main", "logs", "selected_camera.txt")


def update_heartbeat():
    os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
    with open(HEARTBEAT_FILE, "a", encoding="utf-8"):
        os.utime(HEARTBEAT_FILE, None)


def resolve_classifier_path(configured_path, config_data):
    candidates = [configured_path]
    for model_config in config_data.get("model", {}).values():
        if isinstance(model_config, dict):
            candidates.append(model_config.get("source", ""))

    candidates.append(os.path.join("model", "pose_classifier.pkl"))
    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = candidate if os.path.isabs(candidate) else os.path.join(PROJECT_ROOT, candidate)
        if os.path.exists(candidate_path):
            return candidate_path
    return ""


def heartbeat_loop():
    while True:
        try:
            update_heartbeat()
        except OSError:
            pass
        time.sleep(5)


update_heartbeat()
threading.Thread(target=heartbeat_loop, daemon=True).start()

# ─── โหลดและจัดการ CONFIG ───
app_config = AppConfig(os.path.join(PROJECT_ROOT, "setting", "config.yml"))

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
save_data_flag = app_config.save_data_flag
model_sklearn = app_config.model_sklearn
type = app_config.type
df.simulated_key
def reload_config_callback(new_camera_id, updated_config=None):
    global save_ok_flag, save_ng_flag, save_data_flag, config, active_camera_id, camera, cap, window_name, roi, model_sklearn, pose_classifier, type, delay, last_valid_frame, cam_reverse, reverse_y
    
    if updated_config:
        config = updated_config
        config_manager.config = updated_config
    else:
        config_manager.config = config_manager.load_config()
        config = config_manager.config
    
    try:
        model_info = config.get("model", {}).get("Model_path_1", {})
        new_model_path = model_info.get("source", "") if isinstance(model_info, dict) else str(model_info)

        resolved_model_path = resolve_classifier_path(new_model_path, config)
        if resolved_model_path:
            model_sklearn = resolved_model_path
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
        type = camera.get("Type", "LIVE_STREAM")
        cam_reverse = camera.get("reverse_point")
        
        # fps = check_source_type(type)
        print(f"Type Main {type}  fps_limit={df.fps}")
        print(f"cam_reverse: {cam_reverse}")
        new_source = camera.get("source", 0)
        cap = RTSPVideoGrabber(df.fps, new_source)
        last_valid_frame = None
        reverse_y = 0

   
        # ป้องกัน AttributeError ด้วยการเรียก stop() หรือ release() แบบปลอดภัย
        if old_cap:
            if hasattr(old_cap, 'stop'):
                old_cap.stop()
            elif hasattr(old_cap, 'release'):
                old_cap.release()

        roi.clear()
        cam_mark = camera.get("mark_points", []); cam_start = camera.get("start_point", None); cam_reverse = camera.get("reverse_point", None)
        point_zoom = camera.get("point_zoom", None)
        (roi.mark_points, 
         roi.start_point, 
         roi.reverse_point, 
         roi.point_zoom, 
         roi.is_confirmed
         ) = roi.update_roi_start_check(cam_mark,
                                        cam_start,
                                        cam_reverse, 
                                        point_zoom
                                        )


    cam_data = config["cameras"].get(active_camera_id, {})
    save_ok_flag = cam_data.get("save_ok", True)
    save_ng_flag = cam_data.get("save_ng", True)
    save_data_flag = cam_data.get("save_data", True)
    ng_threshold_controller.set_threshold(int(cam_data.get("ng_trigger_count", 10)))
    manager.ng_threshold_controller = ng_threshold_controller
    
    print(f"⚙️ สเตตัสปัจจุบัน: Save OK={save_ok_flag}, Save NG={save_ng_flag}, Save_Data={save_data_flag}, NGTrigger={ng_threshold_controller.threshold},Model={model_sklearn}")
    return cam_data, save_ok_flag, save_ng_flag, save_data_flag


def sync_config_after_settings_closed():
    global config_process

    if config_process is None or config_process.poll() is None:
        return

    config_process = None
    updated_config = config_manager.load_config()
    cameras = updated_config.get("cameras", {})
    new_camera_id = None
    if os.path.exists(SELECTED_CAMERA_FILE):
        with open(SELECTED_CAMERA_FILE, "r", encoding="utf-8") as selected_file:
            new_camera_id = selected_file.read().strip()
        os.remove(SELECTED_CAMERA_FILE)

    if new_camera_id in cameras:
        reload_config_callback(new_camera_id, updated_config)
        print(f"✅ โหลด config ใหม่แล้ว: {new_camera_id}")


# ─── ตั้งค่าเริ่มต้นและโหลดโมดูลตรวจจับ ───
roi = ROIHandler()
# show_status = ShowStatusPose()
window_name = f"Mode Control ROI - {active_camera_id}"

# movement = Check_direction_of_Movement()
# ดึงจุดมาร์กตามกล้องปัจจุบันใน config.yml
cam_mark = camera.get("mark_points", [])
cam_start = camera.get("start_point", None)
cam_reverse = camera.get("reverse_point", (0, 0))
point_zoom = camera.get("point_zoom", None)


if len(roi.mark_points) > 0:
    roi.is_confirmed = True
    
(roi.mark_points, 
 roi.start_point, 
 roi.reverse_point, 
 roi.point_zoom, 
 roi.is_confirmed) = roi.update_roi_start_check(cam_mark,
                                                cam_start,
                                                cam_reverse, 
                                                point_zoom
                                            )
model = YOLO(os.path.join(PROJECT_ROOT, 'yolo26n-pose_openvino_model'), task='pose')

s = ShowPredict(df.SKIP_FRAMES, model, imgsz=640)


cap = RTSPVideoGrabber(df.fps, source)
display_frame_queue = queue.Queue(maxsize=1)
display_key_queue = queue.Queue(maxsize=20)
display_mouse_queue = queue.Queue(maxsize=100)
display_stop_event = threading.Event()

fps_per_sec = 0
def run_display_gui():
    DisplayGui(
        roi.current_mode,
        df.fps,
        fps_per_sec,
        frame_queue=display_frame_queue,
        key_queue=display_key_queue,
        mouse_queue=display_mouse_queue,
        stop_event=display_stop_event
    ).run()

display_thread = threading.Thread(target=run_display_gui, daemon=True)
display_thread.start()
zoom_tool = AdvancedZoomArea(zoom_factor=2)


fourcc = cv2.VideoWriter_fourcc(*'mp4v')
manager = UserStateManager(df.check_pose, fourcc, df.ok_display_time, max_lost_time=2.0, max_distance=80, buffer_output_time=5)

direction_tracker = {}
ng_threshold_controller = NGThresholdController(threshold=app_config.ng_trigger_count)
manager.ng_threshold_controller = ng_threshold_controller

esp32_controller = ESP32SerialController(
    config_filename=os.path.join(PROJECT_ROOT, "main", "setting_esp32", "esp32_pin_config.json"),
    ng_threshold_controller=ng_threshold_controller
)
esp32_controller.set_light_enabled(app_config.esp32_light_enabled)
esp32_controller.set_reset_after_sec(app_config.esp32_reset_after_sec)

try:
    connect_reply = esp32_controller.connect_detect()
    if connect_reply:
        print(f"✅ [ESP32] Connected: {connect_reply}")
    else:
        print("⚠️ [ESP32] ไม่พบการตอบกลับจาก ESP32 หรือยังไม่ได้ต่อพอร์ต")
except Exception as e:
    print(f"⚠️ [ESP32] connect_detect error: {e}")


def handle_ng_threshold_trigger():
    try:
        esp32_controller.set_light_enabled(app_config.esp32_light_enabled)
        esp32_controller.set_reset_after_sec(app_config.esp32_reset_after_sec)
        result = esp32_controller.trigger_ng(status="NG")
        print(f"[ESP32] Trigger result: {result}")
    except Exception as e:
        print(f"⚠️ [ESP32 NG Trigger Error] {e}")

ng_threshold_controller.on_trigger = handle_ng_threshold_trigger

model_sklearn = resolve_classifier_path(model_sklearn, config)
if not model_sklearn:
    raise FileNotFoundError("ไม่พบ classifier model ใน config.yml หรือโฟลเดอร์ model")
pose_classifier = joblib.load(model_sklearn)


# cam_data, save_ok_flag, save_ng_flag = clb.reload_config_callback(active_camera_id, updated_config=None)#new_camera_id=None, updated_config=None
# stats_db = StatsGUI(db_path=r"setting\inspection_stats.db")
stats_manager = StatsManager(db_path=r"setting\inspection_stats.db")
config_process = None

# config_manager.open_settings(current_cam_id=active_camera_id, on_close_callback=reload_config_callback)  
latest_frame = None
last_valid_frame = None

# ตัวแปรคำนวณ fps
prev_frame_time = 0
new_frame_time = 0

type = camera.get("Type", None)
cam_reverse = camera.get("reverse_point", (0, 0))
reverse_y = 0


# ─── เริ่มต้นลูปประมวลผลวิดีโอ ───
while not display_stop_event.is_set():

    sync_config_after_settings_closed()
    update_heartbeat()

    ret, frame = cap.read()
    if not ret or frame is None:
        if last_valid_frame is None:
            frame = np.zeros((1080, 1980, 3), dtype=np.uint8)
        else:
            frame = last_valid_frame.copy()
    else:
        last_valid_frame = frame.copy()
    frame = cv2.resize(frame, (1980, 1080))
    h, w = frame.shape[:2]
    try:
        while True:
            click_x, click_y = display_mouse_queue.get_nowait()
            roi.click_event(cv2.EVENT_LBUTTONDOWN, click_x, click_y, 0, None)
    except queue.Empty:
        pass

    # 🌟 อัปเดต Frame ล่าสุดเข้าตัวแปรแชร์ (ควร copy() เพื่อป้องกัน Thread Race Condition)
    latest_frame = frame.copy()
    if roi.point_zoom is not None:
        zoomed_frame = zoom_tool.apply(frame, center_pt=roi.point_zoom)
        frame = zoomed_frame

    num_pts = len(roi.mark_points)

    
    # --- ส่วนที่ 3: UI กล่อง ROI รวม และวาด Marker Indicators ---
    check_people = "People in Rectangle" if df.any_people_inside else "None People"
    box_color = (0, 0, 255) if df.any_people_inside else (0, 255, 0)


    # # วาดจุดมาร์กและเส้นตาราง ROI Polygon
    # สิ่งที่ต้องส่งเข้าฟังชันนี้ num_pts, roi.mark_point
    # mark_roi_polygon(num_pts, roi.mark_point)
    # return x, y

    mark_roi.mark_roi_polygon(num_pts, frame, roi.mark_points,  check_people, box_color, roi.is_confirmed)

    # 🌟 วาดจุด Start (จุดที่ 1) และ Reverse (จุดที่ 2) บนหน้าจอ
    frame = roi.draw_indicators(frame)

    # --- ส่วนที่ 1: หาพิกัด Keypoints ---
    # สิ่งที่ต้องส่งเข้า search_keypoint(s.frame_count, SKIP_FRAMES, model)

    s.current_frame_poses, s.current_frame_ids = s.searchKeypoint(frame)

    # --- ส่วนที่ 2: ตรรกะประมวลผลแยกบุคคล ---
    # ใช้ set ของ ID แทน boolean ทั่วทั้งเฟรม เพื่อรองรับหลายคนที่อยู่ใน ROI พร้อมกัน
    inside_roi_ids = set()
    current_frame_active_ids = set(s.current_frame_ids)

    for point_pose, s.p_id in zip(s.current_frame_poses, s.current_frame_ids):
        s.p_id += df.lastID
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

        # วาดเส้นกระดูก Skeleton
        point_skel = point_pose.astype(int)
        for start_idx, end_idx in df.SKELETON_CONNECTIONS:
            if (point_skel[start_idx, 0] == 0 and point_skel[start_idx, 1] == 0) or \
               (point_skel[end_idx, 0] == 0 and point_skel[end_idx, 1] == 0):
                continue
            cv2.line(frame, tuple(point_skel[start_idx]), tuple(point_skel[end_idx]), (0, 255, 0), 2)


        person_dir = direction_tracker[s.p_id]

        movement = Check_direction_of_Movement(
            person_dir,
            foot_pos,
            foot_x,
            foot_y,
            roi.start_point,
            roi.reverse_point,
            s.p_id
        )
        person_dir['first_touch'], person_dir['is_reverse'] = movement.checkMovement(frame)

        # print(len(w))
        # cv2.line(frame, (0, foot_y), (w, foot_y), (0, 255, 255), 1, cv2.LINE_AA)
        # ถ้ายังไม่มีการระบุว่าเข้าจุดไหนก่อน ให้คำนวณระยะทางสัมผัสจุด (รัศมี 50px)
        if person_dir['is_reverse']:
            continue

        # ตรวจสอบคนอยู่ในกรอบที่กำหนดไว้
        checkInRoi = CheckPeopleInRoi(frame, roi.mark_points, point_pose)
        people_in_rectangle, _ = checkInRoi.checkPeopleInRoi()
        if people_in_rectangle:
            inside_roi_ids.add(s.p_id)

        if people_in_rectangle and (save_ok_flag != False or save_ng_flag != False): 
            recordVideo = RecordVedioDetect(
                state["writer"],
                state["video_filename"],
                s.p_id,
                fourcc,
                w,
                h
                
            )
            state["writer"], state["video_filename"] = recordVideo.recordingVideo()


        # ─── 📍 จุดที่ 1: ตรรกะเมื่ออยู่ใน ROI (เข้าจุดเช็ก) ───
        cw_inRectangle = Check_where_inRectangle(
                                    people_in_rectangle,
                                    state["is_terminating"],
                                    state["termination_start_time"],
                                    state["is_ok_holding"],
                                    state["confirm"],
                                    state["valaus_last"],
                                    state["ok_start_time"],
                                    point_pose,
                                    s.p_id,
                                    pose_classifier,
                                    df.check_pose,
                                    df.keypoint_conf
                                    )
        (confidence, state["is_terminating"], 
            state["termination_start_time"], 
            state["is_ok_holding"], 
            state["confirm"], 
            state["valaus_last"], 
            state["ok_start_time"]
        ) = cw_inRectangle.check_where_inRectangle(frame, w, h, manager)


        # ─── 📍 จุดที่ 2: ตรรกะเมื่อเดินออกจากจุดเช็ก (เริ่มนับถอยหลัง อัดวิดีโอแถม) ───
        if not people_in_rectangle and state["was_inside_last_frame"] :
            if (state["writer"] is not None or save_data_flag) and not state["is_terminating"]:
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

        status_show = ShowStatusPose(s.p_id,
                                        df.predicted_label, 
                                        confidence,
                                        people_in_rectangle, 
                                        line_height,
                                        status_color, 
                                        text_x, 
                                        text_y_start, 
                                        state["confirm"], 
                                        state['valaus_last']
                                    )

        status_show.showStatus(frame)

        if state["writer"] is not None:
            state["writer"].write(frame)

    df.any_people_inside = bool(inside_roi_ids)

    # ─── 📍 จุดที่ 4: จัดการคนหลุดเฟรม / นับถอยหลังปิดวิดีโอ (วางไว้นอก for-loop บุคคล) ───
    manager.handle_lost_people(
        current_frame_active_ids, 
        save_ok=save_ok_flag, 
        save_ng=save_ng_flag,
        save_data=save_data_flag,
        # stats_db=stats_db,                # 👈 ส่งตัวบันทึกข้อมูลลง DB
        camera_id=active_camera_id        # 👈 ระบุ ID กล้อง
    )

    # ล้างข้อมูล direction_tracker สำหรับ ID ที่หลุดเฟรมไปนานแล้ว
    active_ids_list = list(direction_tracker.keys())
    for tid in active_ids_list:
        if tid not in current_frame_active_ids and tid not in manager.user_states:
            del direction_tracker[tid]

    active_ids_list_history = list(s.pose_history.keys())
    for tid in active_ids_list_history:
        if tid not in current_frame_active_ids and tid not in manager.user_states:
            del s.pose_history[tid]

    last_x = w
    if cam_reverse is not None and reverse_y is not None:
        reverse_y = cam_reverse[1]
        # print(reverse_y)
        cv2.line(frame, (0, reverse_y), (last_x, reverse_y), (0, 255, 0), 2, cv2.LINE_AA)
    else:
        pass
    # show fps
    new_frame_time = time.time()
    fps_per_sec = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time

    fps_per_sec = int(fps_per_sec)
    # ส่งเฟรมที่ประมวลผลแล้วให้หน้า Display โดยเก็บไว้เฉพาะเฟรมล่าสุด
    try:
        display_frame_queue.put_nowait({"frame": frame.copy(), "fps_sec": fps_per_sec})
    except queue.Full:
        try:
            display_frame_queue.get_nowait()
        except queue.Empty: 
            pass
        try:
            display_frame_queue.put_nowait({"frame": frame.copy(), "fps_sec": fps_per_sec})
        except queue.Full:
            pass
    # เรนเดอร์ภาพออกหน้าจอหลัก
    # cv2.imshow(window_name, frame)
    
    s.frame_count += 1 

    # time.sleep(0.01)

    # 2. 🌟 อัปเดต GUI ของ Dashboard (ถ้าหน้าต่างเปิดอยู่) ไม่ให้ค้าง
    stats_manager.update_window()

    # รับคำสั่งแป้นคีย์บอร์ด (Keyboard Actions)
    key_input = 255
    key = None
    try:
        key = display_key_queue.get_nowait()
    except queue.Empty:
        pass

        # 2. ถ้ามีคำสั่งจำลองมาจาก GUI ให้ใช้ค่านั้นแทน
    if df.simulated_key != -1:
    # รองรับทั้งการส่งค่ามาเป็น String ('s') หรือ Integer (ord('s'))
        if isinstance(df.simulated_key, str):
            key = df.simulated_key.lower()
        else:
            key = chr(df.simulated_key).lower()

        df.simulated_key = -1  # ล้างค่าเมื่อดึงไปใช้แล้ว
    elif key is None and key_input != 255:
        key = chr(key_input).lower()
    # roi.current_mode =  clb.checkKey(key)
    # if roi.current_mode == False:
    #     break
    if key == 'q':
        display_stop_event.set()
        break
    elif key == 'h':  # 🌟 เพิ่มปุ่ม H สำหรับเปิด Help GUI
        print("💡 กำลังเปิดหน้าต่างคู่มือช่วยเหลือ (Help GUI)...")
        clb.open_help_window()
        
    elif key == '1':  # โหมดมาร์กพิกัดพื้นที่ Polygon
        roi.clear_roi()
        roi.current_mode = 1
        print("✏️ เปิดโหมดวาด Polygon ROI: คลิกสร้างรูปปิด...")

    elif key == '2':  # 🌟 โหมดมาร์กจุดเริ่มเช็ก (Start Point)
        roi.current_mode = 2
        print("🟢 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 1: Start Check Point]")

    elif key == '3':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
        roi.current_mode = 3
        print("🔴 คลิกบนหน้าจอเพื่อกำหนด [จุดที่ 2: Reverse Check Point]")

    elif key == '5':  # 🌟 โหมดมาร์กจุด Zoom
        roi.current_mode = 5
        print("🔴 คลิกบนหน้าจอเพื่อกำหนด [Mark Point Zoom]")

    elif key == '6':  # 🌟 โหมดมาร์กจุดดักเดินสวน (Reverse Point)
        roi.clear_point_zoom()
        print("🔴[Cancle Mark Point Zoom]")

    elif key == 'c':  # ล้างพิกัดหน้าจอ
        roi.clear()
        
    elif key == 's':  # เรียกเปิดหน้าต่าง GUI ตั้งค่าระบบ
        print("⚙️ กำลังเปิดหน้าต่างตั้งค่าระบบ...")
        if config_process is not None and config_process.poll() is None:
            print("⚠️ หน้าต่างตั้งค่าเปิดอยู่แล้ว")
        else:
            config_script = os.path.join(PROJECT_ROOT, "main", "LIB", "config_gui.py")
            config_process = subprocess.Popen(
                [sys.executable, config_script],
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": PROJECT_ROOT}
            )
    # 4. เพิ่มปุ่มลัด 'D' บน Keyboard เพื่อเปิดหน้า Dashboard
    # ⭕ เปลี่ยนเป็นชื่อฟังก์ชันจริงในคลาส StatsGUI เช่น:
    # elif key == 'd':
    #     print("📊 กำลังเปิดหน้าต่างสถิติ Dashboard...")
    #     stats_manager.open_dashboard() # เปิด UI ขึ้นมาโดยไม่บล็อก Main Loop  
 
    elif key == 'o':
        print("📊 กำลังเปิดหน้าต่าง Connect Database...")
        clb.open_ssms_gui()
    
    elif key == '0':  # บันทึกพิกัดจุดมาร์กเข้า config.yml
        roi.is_confirmed = True
        roi.current_mode = 0
        
        if "cameras" not in config_manager.config: config_manager.config["cameras"] = {}
        if active_camera_id not in config_manager.config["cameras"]: config_manager.config["cameras"][active_camera_id] = {}
        
        config_manager.config["cameras"][active_camera_id]["mark_points"] = roi.mark_points
        config_manager.config["cameras"][active_camera_id]["start_point"] = roi.start_point
        config_manager.config["cameras"][active_camera_id]["reverse_point"] = roi.reverse_point
        config_manager.config["cameras"][active_camera_id]["point_zoom"] = roi.point_zoom 
        
        config_manager.save_config()
        print(f"💾 [Config Saved] บันทึก ROI ({len(roi.mark_points)} จุด), Start Pt {roi.start_point}, Reverse Pt {roi.reverse_point} ของกล้อง '{active_camera_id}' เรียบร้อย!")
            

manager.close_all_writers()
cap.release()
cv2.destroyAllWindows()

