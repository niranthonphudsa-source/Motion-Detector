import os
import cv2
import math
import numpy as np
import joblib
import time
import pandas as pd
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
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
import sys

# เพิ่มโฟลเดอร์ setting เข้าไปในระบบค้นหาโมดูลของ Python
sys.path.append(os.path.join(os.path.dirname(__file__), "setting"))

from app.data_viewer_gui import CheckLastID
from check_people_in_roi import CheckPeopleInRoi, Check_where_inRectangle, RecordVedioDetect
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


# ==========================================
# 🎨 PALETTE COLOR (โทนสีขาว-ฟ้า Clean Tech)
# ==========================================
BG_MAIN = "#F4F7FB"          # พื้นหลังหลัก (ขาวอมฟ้าอ่อน)
BG_CARD = "#FFFFFF"          # พื้นหลังการ์ด/พาเนล (ขาวบริสุทธิ์)
PRIMARY_BLUE = "#0288D1"     # ฟ้าหลัก (Medium Blue)
PRIMARY_HOVER = "#0277BD"    # ฟ้าเข้มตอนโฮเวอร์
PRIMARY_LIGHT = "#E1F5FE"    # ฟ้าอ่อนรองพื้นปุ่ม
ACCENT_BLUE = "#03A9F4"     # ฟ้าสว่างสำหรับไฮไลต์
TEXT_DARK = "#1E293B"       # สีตัวหนังสือหลัก (เทาเข้มเกือบดำ อ่านง่าย)
TEXT_MUTED = "#64748B"      # สีตัวหนังสือรอง
SUCCESS_GREEN = "#2E7D32"   # เขียว OK
DANGER_RED = "#D32F2F"      # แดง NG/Stop
BORDER_COLOR = "#E2E8F0"    # สีเส้นขอบ


class ModernButton(tk.Button):
    """ปุ่มกดสไตล์โมเดิร์นพร้อม Hover Effect"""
    def __init__(self, parent, text, command=None, bg_color=PRIMARY_BLUE, fg_color="#FFFFFF", hover_bg=PRIMARY_HOVER, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_bg,
            activeforeground=fg_color,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            **kwargs
        )
        self.bg_color = bg_color
        self.hover_bg = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))


class PoseDetectionApp:
    def __init__(self, root):
        self.root = root
        # 1. กำหนดข้อความ Title ให้ถูกต้อง
        self.root.title("AI Pose Detection & ROI Control System")
        self.root.geometry("1600x900")

        # 2. ตั้งค่า Icon โลโก้โปรแกรม (.png)
        logo_path = os.path.join("main", "Logo", "atc_logo.png")
        if os.path.exists(logo_path):
            try:
                # โหลดรูป PNG และตั้งเป็น Icon ของหน้าต่างหลัก
                logo_img = ImageTk.PhotoImage(Image.open(logo_path))
                self.root.iconphoto(False, logo_img)
            except Exception as e:
                print(f"⚠️ ไม่สามารถตั้งค่า Icon ได้: {e}")
        else:
            print(f"⚠️ ไม่พบไฟล์โลโก้ที่: {logo_path}")
        self.root.geometry("1600x900")
        self.root.configure(bg=BG_MAIN)
        # 🌟 [เพิ่มบรรทัดนี้] ผูกการกดคีย์บอร์ดเข้ากับฟังก์ชันจัดการคีย์
        self.root.bind("<Key>", self.on_key_press)
        # ─── 1. โหลด CONFIG และการตั้งค่าเริ่มต้น ───
        
        self.app_config = AppConfig(r"setting\config.yml")
        self.config_manager = self.app_config.config_manager
        self.config = self.app_config.config
        self.active_camera_id = self.app_config.active_camera_id
        self.camera = self.app_config.camera
        self.source = self.app_config.source
        self.save_ok_flag = self.app_config.save_ok_flag
        self.save_ng_flag = self.app_config.save_ng_flag
        self.save_data_flag = self.app_config.save_data_flag
        self.model_sklearn = self.app_config.model_sklearn
        self.type = self.app_config.type

        # ─── 2. โมดูลการทำงานหลัก ───
        self.roi = ROIHandler()
        self.cam_mark = self.camera.get("mark_points", [])
        self.cam_start = self.camera.get("start_point", None)
        self.cam_reverse = self.camera.get("reverse_point", None)
        self.point_zoom = self.camera.get("point_zoom", None)

        if len(self.roi.mark_points) > 0:
            self.roi.is_confirmed = True

        (self.roi.mark_points, 
         self.roi.start_point, 
         self.roi.reverse_point, 
         self.roi.point_zoom, 
         self.roi.is_confirmed) = self.roi.update_roi_start_check(
            self.cam_mark, self.cam_start, self.cam_reverse, self.point_zoom
        )

        self.model = YOLO('yolo26n-pose_openvino_model/', task='pose')
        self.s = ShowPredict(df.SKIP_FRAMES, self.model)
        self.cap = RTSPVideoGrabber(df.fps, self.source)
        self.zoom_tool = AdvancedZoomArea(zoom_factor=2)
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.manager = UserStateManager(df.check_pose, self.fourcc, df.ok_display_time, max_lost_time=2.0, max_distance=80, buffer_output_time=5)
        self.direction_tracker = {}
        self.pose_classifier = joblib.load(self.model_sklearn)
        self.stats_manager = StatsManager(db_path=r"setting\inspection_stats.db")

        # ตัวแปรสถานะ
        self.is_running = True
        self.prev_frame_time = 0
        self.fps_per_sec = 0
        self.current_frame = None

        # Create GUI Components
        self.setup_ui()

        # Binding Mouse Events สำหรับวาด ROI บน Video Canvas
        self.video_label.bind("<Button-1>", self.on_canvas_click)

        # Thread ประมวลผลวิดีโอ
        self.video_thread = threading.Thread(target=self.process_video_loop, daemon=True)
        self.video_thread.start()

        # Update GUI Loop (Tkinter Periodic Event)
        self.root.after(10, self.update_gui_dashboard)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        """สร้างเค้าโครง UI โทนสีขาว-ฟ้า"""
        # ─── TOP HEADER ───
        header_frame = tk.Frame(self.root, bg=BG_CARD, height=65, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header_frame.pack(side="top", fill="x")

        title_label = tk.Label(
            header_frame, 
            text="AI Pose & Motion Inspection System", 
            font=("Segoe UI", 16, "bold"), 
            bg=BG_CARD, 
            fg=PRIMARY_BLUE
        )
        title_label.pack(side="left", padx=20, pady=15)

        # Info Badges บน Header
        self.cam_badge = tk.Label(
            header_frame, 
            text=f"Camera: {self.active_camera_id}", 
            font=("Segoe UI", 10, "bold"), 
            bg=PRIMARY_LIGHT, 
            fg=PRIMARY_BLUE, 
            padx=12, pady=4
        )
        self.cam_badge.pack(side="right", padx=15)

        self.fps_badge = tk.Label(
            header_frame, 
            text="FPS: 0", 
            font=("Segoe UI", 10, "bold"), 
            bg="#E8F5E9", 
            fg=SUCCESS_GREEN, 
            padx=12, pady=4
        )
        self.fps_badge.pack(side="right", padx=5)

        # ─── MAIN CONTENT CONTAINER ───
        main_container = tk.Frame(self.root, bg=BG_MAIN)
        main_container.pack(side="top", fill="both", expand=True, padx=20, pady=15)

        # LEFT SIDE: Video Display Area (Card View)
        video_card = tk.Frame(main_container, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        video_card.pack(side="left", fill="both", expand=True, padx=(0, 15))

        video_header = tk.Frame(video_card, bg=BG_CARD)
        video_header.pack(fill="x", padx=15, pady=10)
        
        tk.Label(video_header, text="Live Camera Feed", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_DARK).pack(side="left")
        self.mode_status_label = tk.Label(video_header, text="Mode: Normal", font=("Segoe UI", 10, "bold"), bg=PRIMARY_LIGHT, fg=PRIMARY_BLUE, padx=8, pady=2)
        self.mode_status_label.pack(side="right")

        self.video_label = tk.Label(video_card, bg="#000000")
        self.video_label.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # RIGHT SIDE: Control Panel
        sidebar = tk.Frame(main_container, bg=BG_MAIN, width=340)
        sidebar.pack(side="right", fill="y")

        # --- Card 1: ROI & Point Controls ---
        roi_card = tk.Frame(sidebar, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        roi_card.pack(fill="x", pady=(0, 15))

        tk.Label(roi_card, text="🎯 ROI & Point Marking", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=12)

        ModernButton(roi_card, "1. Mark Polygon ROI", lambda: self.set_mode(1)).pack(fill="x", padx=15, pady=4)
        ModernButton(roi_card, "2. Mark Start Point", lambda: self.set_mode(2)).pack(fill="x", padx=15, pady=4)
        ModernButton(roi_card, "3. Mark Reverse Point", lambda: self.set_mode(3)).pack(fill="x", padx=15, pady=4)
        ModernButton(roi_card, "5. Mark Zoom Point", lambda: self.set_mode(5)).pack(fill="x", padx=15, pady=4)
        ModernButton(roi_card, "6. Clear Zoom Point", self.clear_zoom_point, bg_color="#ECEFF1", fg_color=TEXT_DARK, hover_bg="#CFD8DC").pack(fill="x", padx=15, pady=4)

        btn_grid_frame = tk.Frame(roi_card, bg=BG_CARD)
        btn_grid_frame.pack(fill="x", padx=15, pady=(8, 15))

        ModernButton(btn_grid_frame, "💾 Save (0)", self.save_roi_config, bg_color=SUCCESS_GREEN, hover_bg="#1B5E20").pack(side="left", expand=True, fill="x", padx=(0, 4))
        ModernButton(btn_grid_frame, "🧹 Clear All (C)", self.clear_all_roi, bg_color="#FF9800", hover_bg="#F57C00").pack(side="right", expand=True, fill="x", padx=(4, 0))

        # --- Card 2: System Actions ---
        sys_card = tk.Frame(sidebar, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sys_card.pack(fill="x", pady=(0, 15))

        tk.Label(sys_card, text="⚙️ System Controls", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=12)

        ModernButton(sys_card, "⚙️ Open Settings (S)", self.open_settings_gui, bg_color=PRIMARY_LIGHT, fg_color=PRIMARY_BLUE, hover_bg="#B3E5FC").pack(fill="x", padx=15, pady=4)
        ModernButton(sys_card, "🗄️ Database Center (O)", lambda: clb.open_ssms_gui(), bg_color=PRIMARY_LIGHT, fg_color=PRIMARY_BLUE, hover_bg="#B3E5FC").pack(fill="x", padx=15, pady=4)
        ModernButton(sys_card, "❓ Help Manual (H)", lambda: clb.open_help_window(), bg_color=PRIMARY_LIGHT, fg_color=PRIMARY_BLUE, hover_bg="#B3E5FC").pack(fill="x", padx=15, pady=4)

        # Exit Button
        ModernButton(sidebar, "🛑 Exit Application (Q)", self.on_close, bg_color=DANGER_RED, hover_bg="#B71C1C").pack(fill="x", side="bottom")

    # ─── ACTION HANDLERS ───
    def set_mode(self, mode_num):
        if mode_num == 1:
            self.roi.clear_roi()
        self.roi.current_mode = mode_num
        mode_names = {1: "Mark Polygon", 2: "Mark Start", 3: "Mark Reverse", 5: "Mark Zoom"}
        self.mode_status_label.config(text=f"Mode: {mode_names.get(mode_num, 'Normal')}")

    def clear_zoom_point(self):
        self.roi.clear_point_zoom()
        self.mode_status_label.config(text="Mode: Normal")

    def clear_all_roi(self):
        self.roi.clear()
        self.mode_status_label.config(text="Mode: Normal")

    def save_roi_config(self):
        self.roi.is_confirmed = True
        self.roi.current_mode = 0
        self.mode_status_label.config(text="Mode: Normal")

        if "cameras" not in self.config_manager.config: 
            self.config_manager.config["cameras"] = {}
        if self.active_camera_id not in self.config_manager.config["cameras"]: 
            self.config_manager.config["cameras"][self.active_camera_id] = {}

        self.config_manager.config["cameras"][self.active_camera_id]["mark_points"] = self.roi.mark_points
        self.config_manager.config["cameras"][self.active_camera_id]["start_point"] = self.roi.start_point
        self.config_manager.config["cameras"][self.active_camera_id]["reverse_point"] = self.roi.reverse_point
        self.config_manager.config["cameras"][self.active_camera_id]["point_zoom"] = self.roi.point_zoom

        self.config_manager.save_config()
        messagebox.showinfo("Config Saved", f"บันทึกค่า ROI ของกล้อง {self.active_camera_id} เรียบร้อยแล้ว!")
        
    def open_settings_gui(self):
        cam_id_to_pass = self.active_camera_id if self.active_camera_id else "Camera_1"
        gui_thread = threading.Thread(
            target=self.config_manager.open_settings,
            kwargs={
                "current_cam_id": cam_id_to_pass, 
                "on_close_callback": self.reload_config_callback
            },
            daemon=True
        )
        gui_thread.start()

    def reload_config_callback(self, new_camera_id, updated_config=None):
        # 1. อัปเดต Config ล่าสุด
        if updated_config:
            self.config = updated_config
            self.config_manager.config = updated_config
        else:
            self.config_manager.config = self.config_manager.load_config()
            self.config = self.config_manager.config

        # 2. โหลดโมเดล AI ใหม่
        try:
            model_info = self.config.get("model", {}).get("Model_path_1", {})
            new_model_path = model_info.get("source", "") if isinstance(model_info, dict) else str(model_info)

            if new_model_path and os.path.exists(new_model_path):
                self.model_sklearn = new_model_path
                self.pose_classifier = joblib.load(self.model_sklearn)
        except Exception as e:
            print(f"❌ [Model Error]: {e}")

        # 3. Validation ป้องกัน KeyError กรณี new_camera_id เป็นค่าว่าง หรือไม่มีใน Config
        cameras_dict = self.config.get("cameras", {})
        
        if not new_camera_id or new_camera_id not in cameras_dict:
            # Fallback: ลองใช้ default_camera_id หรือดึงกล้องตัวแรกในระบบมาแทน
            default_cam = self.config.get("global", {}).get("default_camera_id")
            if default_cam and default_cam in cameras_dict:
                new_camera_id = default_cam
            elif cameras_dict:
                new_camera_id = list(cameras_dict.keys())[0]
            else:
                new_camera_id = "Camera_1"

        # 4. ตรวจสอบการเปลี่ยนแปลงของกล้อง หรือ Source URL
        old_source = self.camera.get("source") if hasattr(self, "camera") and isinstance(self.camera, dict) else None
        
        # อัปเดต self.camera และ active_camera_id เสมอ (ใช้ .get() เพื่อความปลอดภัย)
        self.active_camera_id = new_camera_id
        self.camera = cameras_dict.get(self.active_camera_id, {})
        new_source = self.camera.get("source", "")
        self.type = self.camera.get("Type", "RTSP")

        # ตรวจสอบว่ามีการเปลี่ยนตัวกล้อง หรือเปลี่ยน RTSP URL หรือไม่
        is_camera_changed = (self.active_camera_id != new_camera_id)
        is_source_changed = (old_source != new_source)

        if is_camera_changed or is_source_changed or not getattr(self, "cap", None):
            # ปิด Stream เก่าก่อนเพื่อคืน Memory/Socket
            if hasattr(self, "cap") and self.cap:
                if hasattr(self.cap, 'stop'): 
                    self.cap.stop()
                elif hasattr(self.cap, 'release'): 
                    self.cap.release()
                self.cap = None

            # เชื่อมต่อ Stream ใหม่
            if new_source:
                self.cap = RTSPVideoGrabber(df.fps, new_source)

            # รีเซ็ต ROI และโหลดพิกัดใหม่
            if hasattr(self, "roi") and self.roi:
                self.roi.clear()
                cam_mark = self.camera.get("mark_points", [])
                cam_start = self.camera.get("start_point", None)
                cam_reverse = self.camera.get("reverse_point", None)
                point_zoom = self.camera.get("point_zoom", None)
                
                (self.roi.mark_points, self.roi.start_point, self.roi.reverse_point, 
                 self.roi.point_zoom, self.roi.is_confirmed) = self.roi.update_roi_start_check(
                    cam_mark, cam_start, cam_reverse, point_zoom
                )

        # 5. อัปเดต Flag และ UI Status
        self.save_ok_flag = self.camera.get("save_ok", True)
        self.save_ng_flag = self.camera.get("save_ng", True)
        self.save_data_flag = self.camera.get("save_data", True)
        
        if hasattr(self, "cam_badge") and self.cam_badge:
            self.cam_badge.config(text=f"Camera: {self.active_camera_id}")

        print(f"Camera Detail:{self.active_camera_id}, {self.camera}, OK:{self.save_ok_flag}, NG:{self.save_ng_flag}, DB:{self.save_data_flag}")
        return self.camera, self.save_ok_flag, self.save_ng_flag, self.save_data_flag

    def on_canvas_click(self, event):
        """แปลงพิกัดการคลิกบน Tkinter Canvas กลับไปยังขนาดดั้งเดิมของ Frame"""
        if self.current_frame is None: return
        lbl_w = self.video_label.winfo_width()
        lbl_h = self.video_label.winfo_height()
        
        if lbl_w > 0 and lbl_h > 0:
            frame_h, frame_w = self.current_frame.shape[:2]
            real_x = int(event.x * (frame_w / lbl_w))
            real_y = int(event.y * (frame_h / lbl_h))
            self.roi.click_event(cv2.EVENT_LBUTTONDOWN, real_x, real_y, None, None)

    # ─── THREAD LOGIC: PROCESS VIDEO ───
    def process_video_loop(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.resize(frame, (2560, 1440))
            h, w = frame.shape[:2]

            if self.roi.point_zoom is not None:
                zoomed_frame = self.zoom_tool.apply(frame, center_pt=self.roi.point_zoom)
                frame = zoomed_frame

            self.s.searchKeypoint(frame)
            self.s.current_frame_poses = [] 
            self.s.current_frame_ids = [] 
            num_pts = len(self.roi.mark_points)

            check_people = "People in Rectangle" if df.any_people_inside else "None People"
            box_color = (0, 0, 255) if df.any_people_inside else (0, 255, 0)

            mark_roi.mark_roi_polygon(num_pts, frame, self.roi.mark_points, check_people, box_color, self.roi.is_confirmed)
            frame = self.roi.draw_indicators(frame)

            self.s.current_frame_poses, self.s.current_frame_ids = self.s.searchKeypoint(frame)
            inside_roi_ids = set()
            current_frame_active_ids = set(self.s.current_frame_ids)

            for point_pose, p_id in zip(self.s.current_frame_poses, self.s.current_frame_ids):
                p_id += df.lastID
                if len(point_pose) < 17: continue

                state = self.manager.get_or_recover_id(p_id, current_frame_active_ids, point_pose)
                if state is None: continue

                people_in_rectangle = False
                foot_x = int((point_pose[15][0] + point_pose[16][0]) / 2)
                foot_y = int((point_pose[15][1] + point_pose[16][1]) / 2)
                foot_pos = (foot_x, foot_y)

                if p_id not in self.direction_tracker:
                    self.direction_tracker[p_id] = {'first_touch': None, 'is_reverse': False}

                # Skeleton Drawing
                point_skel = point_pose.astype(int)
                for start_idx, end_idx in df.SKELETON_CONNECTIONS:
                    if (point_skel[start_idx, 0] == 0 and point_skel[start_idx, 1] == 0) or \
                       (point_skel[end_idx, 0] == 0 and point_skel[end_idx, 1] == 0):
                        continue
                    cv2.line(frame, tuple(point_skel[start_idx]), tuple(point_skel[end_idx]), (0, 255, 0), 2)

                person_dir = self.direction_tracker[p_id]
                movement = Check_direction_of_Movement(
                    person_dir, foot_pos, foot_x, foot_y, 
                    self.roi.start_point, self.roi.reverse_point, p_id
                )
                person_dir['first_touch'], person_dir['is_reverse'] = movement.checkMovement(frame)

                if person_dir['is_reverse']: continue

                checkInRoi = CheckPeopleInRoi(frame, self.roi.mark_points, point_pose)
                people_in_rectangle, _ = checkInRoi.checkPeopleInRoi()
                if people_in_rectangle: inside_roi_ids.add(p_id)

                if people_in_rectangle and (self.save_ok_flag or self.save_ng_flag): 
                    recordVideo = RecordVedioDetect(
                        state["writer"], state["video_filename"], p_id, self.fourcc, w, h
                    )
                    state["writer"], state["video_filename"] = recordVideo.recordingVideo()

                cw_inRectangle = Check_where_inRectangle(
                    people_in_rectangle, state["is_terminating"], state["termination_start_time"],
                    state["is_ok_holding"], state["confirm"], state["valaus_last"],
                    state["ok_start_time"], point_pose, p_id, self.pose_classifier,
                    df.check_pose, df.keypoint_conf
                )
                (confidence, state["is_terminating"], state["termination_start_time"], 
                 state["is_ok_holding"], state["confirm"], state["valaus_last"], 
                 state["ok_start_time"]) = cw_inRectangle.check_where_inRectangle(frame, w, h, self.manager)

                if not people_in_rectangle and state["was_inside_last_frame"]:
                    if state["writer"] is not None and not state["is_terminating"]:
                        state["is_terminating"] = True
                        state["termination_start_time"] = time.time()

                self.manager.update_tracking_data(state, people_in_rectangle, point_pose)

                text_x = int(point_pose[5][0]) if point_pose[5][0] > 0 else 50
                text_y_start = int(point_pose[5][1]) - 80 if point_pose[5][1] > 80 else 50
                status_color = (0, 255, 0) if state["confirm"] == "OK" else (0, 0, 255)

                status_show = ShowStatusPose(
                    p_id, df.predicted_label, confidence, people_in_rectangle,
                    20, status_color, text_x, text_y_start, state["confirm"], state['valaus_last']
                )
                status_show.showStatus(frame)

                if state["writer"] is not None:
                    state["writer"].write(frame)

            df.any_people_inside = bool(inside_roi_ids)
            self.manager.handle_lost_people(current_frame_active_ids, save_ok=self.save_ok_flag, save_ng=self.save_ng_flag, camera_id=self.active_camera_id)

            # Cleanup direction trackers
            for tid in list(self.direction_tracker.keys()):
                if tid not in current_frame_active_ids and tid not in self.manager.user_states:
                    del self.direction_tracker[tid]

            cam_reverse = self.camera.get("reverse_point", (0, 0))
            if cam_reverse:
                cv2.line(frame, (0, cam_reverse[1]), (w, cam_reverse[1]), (0, 255, 0), 2, cv2.LINE_AA)

            # FPS Calculator
            new_frame_time = time.time()
            if new_frame_time - self.prev_frame_time > 0:
                self.fps_per_sec = int(1 / (new_frame_time - self.prev_frame_time))
            self.prev_frame_time = new_frame_time

            show_m.showModeDisplay(frame, self.roi.current_mode, df.fps, self.fps_per_sec)

            # ส่งเฟรมไปให้ Tkinter Display
            self.current_frame = frame
            self.s.frame_count += 1

    # ─── PERIODIC GUI UPDATE LOOP ───
    def update_gui_dashboard(self):
        if self.current_frame is not None:
            # แปลงภาพ BGR -> RGB สำหรับ PIL
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            # Resize ให้พอดีกับ Label Container
            lbl_w = max(self.video_label.winfo_width(), 100)
            lbl_h = max(self.video_label.winfo_height(), 100)
            img = img.resize((lbl_w, lbl_h), Image.Resampling.LANCZOS)

            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # อัปเดต FPS Badge
            self.fps_badge.config(text=f"FPS: {self.fps_per_sec}")

        self.stats_manager.update_window()
        
        if self.is_running:
            self.root.after(15, self.update_gui_dashboard)

    def on_close(self):
        """ปิดการทำงานอย่างปลอดภัย"""
        if messagebox.askokcancel("Quit", "คุณต้องการปิดโปรแกรมใช่หรือไม่?"):
            self.is_running = False
            self.manager.close_all_writers()
            if hasattr(self.cap, 'release'): self.cap.release()
            cv2.destroyAllWindows()
            self.root.destroy()

    def on_key_press(self, event):
        """รับค่าจากคีย์บอร์ดแล้วสั่งงานฟังก์ชันเหมือนการกดปุ่มบน GUI"""
        key = event.char.lower()
        
        if key == '1':
            print("⌨️ [Keyboard 1] เปิดโหมดวาด Polygon ROI")
            self.set_mode(1)
        elif key == '2':
            print("⌨️ [Keyboard 2] เปิดโหมดมาร์ก Start Point")
            self.set_mode(2)
        elif key == '3':
            print("⌨️ [Keyboard 3] เปิดโหมดมาร์ก Reverse Point")
            self.set_mode(3)
        elif key == '5':
            print("⌨️ [Keyboard 5] เปิดโหมดมาร์ก Zoom Point")
            self.set_mode(5)
        elif key == '6':
            print("⌨️ [Keyboard 6] ยกเลิกจุด Zoom Point")
            self.clear_zoom_point()
        elif key == '0':
            print("⌨️ [Keyboard 0] บันทึกพิกัด ROI")
            self.save_roi_config()
        elif key == 'c':
            print("⌨️ [Keyboard C] ล้างพิกัดทั้งหมด")
            self.clear_all_roi()
        elif key == 's':
            print("⌨️ [Keyboard S] เปิดหน้าต่าง Settings")
            self.open_settings_gui()
        elif key == 'o':
            print("⌨️ [Keyboard O] เปิดหน้าต่าง Database")
            clb.open_ssms_gui()
        elif key == 'h':
            print("⌨️ [Keyboard H] เปิดหน้าต่าง Help")
            clb.open_help_window()
        elif key == 'q':
            print("⌨️ [Keyboard Q] ปิดโปรแกรม")
            self.on_close()

# ─── MAIN EXECUTION ───
if __name__ == "__main__":
    root = tk.Tk()
    app = PoseDetectionApp(root)
    root.mainloop()