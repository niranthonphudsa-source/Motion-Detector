import csv
import datetime
import math
import os
import threading
import time
import tkinter as tk
import cv2
import joblib
import numpy as np
import pandas as pd
import serial

import callback_command.callback_command as clb
import mark_roi_polygon as mark_roi
import run_start.default_config_var as df
import show_mode_inDisplay as show_m
from app.data_viewer_gui import CheckLastID
from check_people_in_roi import (
    Check_where_inRectangle,
    CheckPeopleInRoi,
    RecordVedioDetect,
)
from LIB.Check_direction_of_Movement import Check_direction_of_Movement
from LIB.config_loader_start import AppConfig
from LIB.predict_frame_pose import ShowPredict
from LIB.roi_handler import ROIHandler
from LIB.stats_gui import StatsGUI, StatsManager
from LIB.user_manager import UserStateManager
from LIB.zoom_arae import AdvancedZoomArea
from rtspVideo import RTSPVideoGrabber
from search_keypoint import SearchKeypoint
from show_status_pose import ShowStatusPose
from ultralytics import YOLO

# ─── คำนวณหา PROJECT_ROOT ป้องกันปัญหา Working Directory เคลื่อน ───
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # อยู่ที่โฟลเดอร์ main
PROJECT_ROOT = os.path.dirname(
    CURRENT_DIR
)  # ถอย 1 ชั้นไปที่ Root ของ Project

# ─── โหลดและจัดการ CONFIG ───
CONFIG_FILE_PATH = os.path.join(PROJECT_ROOT, "setting", "config.yml")
app_config = AppConfig(
    CONFIG_FILE_PATH
    if os.path.exists(CONFIG_FILE_PATH)
    else r"setting\config.yml"
)

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
model_sklearn = app_config.model_sklearn
type = app_config.type

df.simulated_key

def resolve_model_path(path_str):
  """ช่วยแปลง Path ของโมเดลให้เป็น Absolute Path เสมอ"""
  if not path_str or not str(path_str).strip():
    return None

  path_str = str(path_str).strip()
  if os.path.isabs(path_str):
    return path_str

  # ถ้าเป็น Relative Path ให้ค้นหาจาก PROJECT_ROOT/model/filename
  filename = os.path.basename(path_str)
  return os.path.join(PROJECT_ROOT, "model", filename)


def reload_config_callback(new_camera_id, updated_config=None):
    global save_ok_flag, save_ng_flag, config, active_camera_id, camera, cap, window_name, roi, model_sklearn, pose_classifier, type, delay

    if updated_config:
        config = updated_config
        config_manager.config = updated_config
    else:
        config_manager.config = config_manager.load_config()
        config = config_manager.config

    try:
        model_info = config.get("model", {}).get("Model_path_1", {})
        new_model_path = (
            model_info.get("source", "")
            if isinstance(model_info, dict)
            else str(model_info)
        )

        full_path = resolve_model_path(new_model_path)
        if full_path and os.path.exists(full_path):
            model_sklearn = full_path
            ose_classifier = joblib.load(model_sklearn)
            print(f"🤖 [Model Reloaded] อัปเดตโมเดลเป็น: {model_sklearn}")
        else:
            print(
                f"⚠️ [Model Warning] ไม่พบไฟล์โมเดลที่ Path: {full_path or new_model_path}"
            )
    except Exception as e:
        print(f"❌ [Model Error] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")

    # 🔄 สลับกล้อง (Switch Camera)
    if active_camera_id != new_camera_id:
        print(
            f"🔄 [Switch Camera] ตรวจพบการเปลี่ยนกล้องจาก {active_camera_id} ➡️"
            f" {new_camera_id}"
        )
        old_cap = cap
        active_camera_id = new_camera_id
        camera = config.get("cameras", {}).get(active_camera_id, {})

        # ใช้ .get() เพื่อป้องกัน KeyError ทั้งหมด
        type = camera.get("Type", "")
        cam_reverse = camera.get("reverse_point", (0, 0))

        print(f"Type Main {type}  fps_limit={df.fps}")
        print(f"cam_reverse: {cam_reverse}")
        new_source = camera.get("source", 0)
        cap = RTSPVideoGrabber(df.fps, new_source)
        print(f"[RTSP] FPS ของ source: {cap.target_fps:.2f} FPS")

        if old_cap:
            if hasattr(old_cap, "stop"):
                old_cap.stop()
            elif hasattr(old_cap, "release"):
                old_cap.release()

            roi.clear()
            cam_mark = camera.get("mark_points", [])
            cam_start = camera.get("start_point", None)
            cam_reverse = camera.get("reverse_point", None)
            point_zoom = camera.get("point_zoom", None)
            (
                roi.mark_points,
                roi.start_point,
                roi.reverse_point,
                roi.point_zoom,
                roi.is_confirmed,
            ) = roi.update_roi_start_check(
                cam_mark, cam_start, cam_reverse, point_zoom
            )

    cam_data = config.get("cameras", {}).get(active_camera_id, {})
    save_ok_flag = cam_data.get("save_ok", True)
    save_ng_flag = cam_data.get("save_ng", True)

    print(
        f"⚙️ สเตตัสปัจจุบัน: Save OK={save_ok_flag}, Save"
        f" NG={save_ng_flag}, Model={model_sklearn}"
    )
    return cam_data, save_ok_flag, save_ng_flag


# ─── ตั้งค่าเริ่มต้นและโหลดโมดูลตรวจจับ ───
roi = ROIHandler()
window_name = f"Mode Control ROI - {active_camera_id}"
s = ShowPredict()
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
)
cv2.setMouseCallback(window_name, roi.click_event)

# ดึงจุดมาร์กตามกล้องปัจจุบันใน config.yml
cam_mark = camera.get("mark_points", [])
cam_start = camera.get("start_point", None)
cam_reverse = camera.get("reverse_point", (0, 0))
point_zoom = camera.get("point_zoom", None)

if len(roi.mark_points) > 0:
  roi.is_confirmed = True

(
    roi.mark_points,
    roi.start_point,
    roi.reverse_point,
    roi.point_zoom,
    roi.is_confirmed,
) = roi.update_roi_start_check(cam_mark, cam_start, cam_reverse, point_zoom)

# โหลด YOLO Model (ใช้ Absolute Path หากมีไฟล์ในโฟลเดอร์หลัก)
yolo_model_path = os.path.join(PROJECT_ROOT, "yolo26n-pose.pt")
model = YOLO(
    yolo_model_path if os.path.exists(yolo_model_path) else "yolo26n-pose.pt"
)

cap = RTSPVideoGrabber(df.fps, source)
print(f"[RTSP] FPS ของ source: {cap.target_fps:.2f} FPS")
zoom_tool = AdvancedZoomArea(zoom_factor=2)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
manager = UserStateManager(
    df.check_pose,
    fourcc,
    df.ok_display_time,
    max_lost_time=2.0,
    max_distance=80,
    buffer_output_time=5,
)

direction_tracker = {}

# ─── Safe Load Pose Classifier Model (บรรทัดที่ 157) ───
pose_classifier = None
target_model_path = resolve_model_path(model_sklearn)

if target_model_path and os.path.exists(target_model_path):
  try:
    pose_classifier = joblib.load(target_model_path)
    model_sklearn = target_model_path
    print(f"✅ โหลด Sklearn Model สำเร็จจาก: {target_model_path}")
  except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในการโหลด Sklearn Model: {e}")
else:
  print(
      "⚠️ [Warning] ไม่พบไฟล์ Sklearn Model หรือค่าใน config.yml เป็นค่าว่าง!"
  )
  print(f"   Path ที่พยายามค้นหา: {target_model_path or model_sklearn}")

# โหลดไฟล์ Database แบบ Absolute Path
DB_FILE_PATH = os.path.join(PROJECT_ROOT, "setting", "inspection_stats.db")
stats_manager = StatsManager(
    db_path=DB_FILE_PATH
    if os.path.exists(DB_FILE_PATH)
    else r"setting\inspection_stats.db"
)

latest_frame = None

prev_frame_time = 0
new_frame_time = 0

type = camera.get("Type", None)
cam_reverse = camera.get("reverse_point", (0, 0))
reverse_y = 0
# ─── เริ่มต้นลูปประมวลผลวิดีโอ ───
while True:
    ret, frame = cap.read()
    if not ret:     
        break
        # continue
    # frame = cv2.resize(frame, (640, 640))
    h, w = frame.shape[:2]
    # 🌟 อัปเดต Frame ล่าสุดเข้าตัวแปรแชร์ (ควร copy() เพื่อป้องกัน Thread Race Condition)
    latest_frame = frame.copy()
    if roi.point_zoom is not None:
        zoomed_frame = zoom_tool.apply(frame, center_pt=roi.point_zoom)
        frame = zoomed_frame

    s.current_frame_poses = [] 
    s.current_frame_ids = [] 
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

    search_key = SearchKeypoint(df.SKIP_FRAMES, frame, model, s.frame_count)
    s.current_frame_poses, s.current_frame_ids =  search_key.searchKeypoint()

    # --- ส่วนที่ 2: ตรรกะประมวลผลแยกบุคคล ---
    df.any_people_inside = False
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
        cv2.line(frame, (0, foot_y), (w, foot_y), (0, 255, 255), 1, cv2.LINE_AA)
        # ถ้ายังไม่มีการระบุว่าเข้าจุดไหนก่อน ให้คำนวณระยะทางสัมผัสจุด (รัศมี 50px)
        if person_dir['is_reverse']:
            continue

        # ตรวจสอบคนอยู่ในกรอบที่กำหนดไว้
        checkInRoi = CheckPeopleInRoi(frame, roi.mark_points, point_pose)
        people_in_rectangle, df.any_people_inside = checkInRoi.checkPeopleInRoi()


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

    # ─── 📍 จุดที่ 4: จัดการคนหลุดเฟรม / นับถอยหลังปิดวิดีโอ (วางไว้นอก for-loop บุคคล) ───
    manager.handle_lost_people(
        current_frame_active_ids, 
        save_ok=save_ok_flag, 
        save_ng=save_ng_flag,
        # stats_db=stats_db,                # 👈 ส่งตัวบันทึกข้อมูลลง DB
        camera_id=active_camera_id        # 👈 ระบุ ID กล้อง
    )

    # ล้างข้อมูล direction_tracker สำหรับ ID ที่หลุดเฟรมไปนานแล้ว
    active_ids_list = list(direction_tracker.keys())
    for tid in active_ids_list:
        if tid not in current_frame_active_ids and tid not in manager.user_states:
            del direction_tracker[tid]

    last_x = w
    if reverse_y is not None and cam_reverse is not None:
        reverse_y = cam_reverse[1]
        # print(reverse_y)
        cv2.line(frame, (0, reverse_y), (last_x, reverse_y), (0, 255, 0), 2, cv2.LINE_AA)

    # show fps
    new_frame_time = time.time()
    fps_per_sec = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time

    fps_per_sec = int(fps_per_sec)
    show_m.showModeDisplay(frame, roi.current_mode, df.fps, fps_per_sec)

    # เรนเดอร์ภาพออกหน้าจอหลัก
    cv2.imshow(window_name, frame)
    s.frame_count += 1 
    # time.sleep(0.01)

    # 2. 🌟 อัปเดต GUI ของ Dashboard (ถ้าหน้าต่างเปิดอยู่) ไม่ให้ค้าง
    stats_manager.update_window()

    # รับคำสั่งแป้นคีย์บอร์ด (Keyboard Actions)
    key_input = cv2.waitKey(1) & 0xFF
    key = None
        # 2. ถ้ามีคำสั่งจำลองมาจาก GUI ให้ใช้ค่านั้นแทน
    if df.simulated_key != -1:
    # รองรับทั้งการส่งค่ามาเป็น String ('s') หรือ Integer (ord('s'))
        if isinstance(df.simulated_key, str):
            key = df.simulated_key.lower()
        else:
            key = chr(df.simulated_key).lower()

        df.simulated_key = -1  # ล้างค่าเมื่อดึงไปใช้แล้ว
    elif key_input != 255:
        key = chr(key_input).lower()
    # roi.current_mode =  clb.checkKey(key)
    # if roi.current_mode == False:
    #     break
    if key == 'q':
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
        # 🔍 เช็กค่า active_camera_id ก่อนเปิดหน้าต่าง
        # ป้องกันกรณี active_camera_id เป็น None
        cam_id_to_pass = active_camera_id if active_camera_id else "Camera_1"
        
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

