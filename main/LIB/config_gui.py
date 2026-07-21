import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import os
import glob
import threading
import sys
import subprocess
import datetime
import shutil
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import time

# ─── 📁 คลาสหน้าต่างสำหรับจัดการวิดีโอ (Video Manager Window) ───
class VideoFolderManagerWindow:
    def __init__(self, parent, folder_path, title_name):
        self.folder_path = folder_path
        self.window = tk.Toplevel(parent)
        self.window.title(f"📁 จัดการวิดีโอ: {title_name} ({folder_path})")
        self.window.geometry("650x450")
        self.window.resizable(True, True)
        self.window.grab_set()  # ดึง โฟกัสมาที่หน้าต่างนี้ก่อน
        # ทำความสะอาดไฟล์เก่าอัตโนมัติทันทีเมื่อเปิดหน้าต่าง
        self.cleanup_old_videos(max_days=30, min_free_gb=1.0)
        # 🌟 เริ่มการทำความสะอาดเบื้องหลังอัตโนมัติ (เช็กทุกๆ 1 ชั่วโมง)
        self.start_auto_cleanup_thread(interval_seconds=3600, max_days=30, min_free_gb=1.0)
        # สร้างโฟลเดอร์ให้อัตโนมัติถ้ายังไม่มีในระบบ
        os.makedirs(self.folder_path, exist_ok=True)

        # Header Frame
        header_frame = ttk.Frame(self.window, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame, 
            text=f"📂 โฟลเดอร์: {folder_path}", 
            font=("Helvetica", 11, "bold")
        ).pack(side=tk.LEFT)

        btn_open_folder = ttk.Button(
            header_frame, 
            text="📂 เปิดใน File Explorer", 
            command=self.open_in_explorer
        )
        btn_open_folder.pack(side=tk.RIGHT)

        # Table (Treeview) สำหรับแสดงรายการวิดีโอ
        tree_frame = ttk.Frame(self.window, padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "size", "date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("name", text="ชื่อไฟล์")
        self.tree.heading("size", text="ขนาด")
        self.tree.heading("date", text="วันที่บันทึกล่าสุด")

        self.tree.column("name", width=280)
        self.tree.column("size", width=100, anchor="center")
        self.tree.column("date", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action Buttons Frame
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill=tk.X)

        btn_refresh = ttk.Button(btn_frame, text="🔄 รีเฟรช", command=self.load_files)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        btn_play = ttk.Button(btn_frame, text="▶️ เปิดเล่นวิดีโอ", command=self.play_video)
        btn_play.pack(side=tk.LEFT, padx=5)

        btn_delete = ttk.Button(btn_frame, text="🗑️ ลบไฟล์ที่เลือก", command=self.delete_video)
        btn_delete.pack(side=tk.RIGHT, padx=5)

        # โหลดข้อมูลไฟล์วิดีโอเข้าตารางครั้งแรก
        self.load_files()

    def load_files(self):
        """โหลดรายการไฟล์วิดีโอทั้งหมดในโฟลเดอร์ลงในตาราง"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(self.folder_path):
            return

        valid_extensions = ('.avi', '.mp4', '.mkv', '.mov')
        files = [f for f in os.listdir(self.folder_path) if f.lower().endswith(valid_extensions)]

        for f in sorted(files, reverse=True):  # เรียงไฟล์ใหม่สุดขึ้นก่อน
            full_path = os.path.join(self.folder_path, f)
            stat = os.stat(full_path)
            size_mb = f"{stat.st_size / (1024 * 1024):.2f} MB"
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            self.tree.insert("", tk.END, values=(f, size_mb, mod_time))

    def get_selected_file_path(self):
        """ดึง Path ของไฟล์วิดีโอที่ถูกคลิกเลือกในตาราง"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("แจ้งเตือน", "กรุณาคลิกเลือกไฟล์วิดีโอจากรายการก่อนครับ")
            return None
        
        filename = self.tree.item(selected_item[0])['values'][0]
        return os.path.join(self.folder_path, filename)

    def play_video(self):
        """เปิดวิดีโอด้วยโปรแกรมเล่นสื่อเริ่มต้นของเครื่อง"""
        file_path = self.get_selected_file_path()
        if file_path and os.path.exists(file_path):
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":  # macOS
                    subprocess.call(["open", file_path])
                else:  # Linux
                    subprocess.call(["xdg-open", file_path])
            except Exception as e:
                messagebox.showerror("Error", f"ไม่สามารถเปิดเล่นวิดีโอได้: {e}")

    def delete_video(self):
        """ลบไฟล์วิดีโอที่เลือก"""
        file_path = self.get_selected_file_path()
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            confirm = messagebox.askyesno(
                "ยืนยันการลบ", 
                f"คุณต้องการลบไฟล์ '{filename}' ใช่หรือไม่?\n(การลบนี้จะไม่สามารถกู้คืนได้)"
            )
            if confirm:
                try:
                    os.remove(file_path)
                    messagebox.showinfo("สำเร็จ", f"ลบไฟล์ '{filename}' เรียบร้อยแล้ว")
                    self.load_files()  # รีโหลดรายการในตารางใหม่
                except Exception as e:
                    messagebox.showerror("Error", f"ไม่สามารถลบไฟล์ได้: {e}")

    def open_in_explorer(self):
        """เปิดโฟลเดอร์ใน File Explorer"""
        os.makedirs(self.folder_path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.folder_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", self.folder_path])
        else:
            subprocess.call(["xdg-open", self.folder_path])

    def cleanup_old_videos(self, max_days=30, min_free_gb=1.0):
            """ฟังก์ชันลบไฟล์อัตโนมัติ (อายุเกิน 30 วัน หรือพื้นที่เหลือน้อยกว่า 1GB)"""
            if not os.path.exists(self.folder_path):
                return 0

            valid_extensions = ('.avi', '.mp4', '.mkv', '.mov')
            now = datetime.datetime.now().timestamp()
            max_age_seconds = max_days * 86400  # 30 วัน

            file_list = []
            for filename in os.listdir(self.folder_path):
                if filename.lower().endswith(valid_extensions):
                    full_path = os.path.join(self.folder_path, filename)
                    try:
                        mtime = os.path.getmtime(full_path)
                        file_list.append((full_path, mtime))
                    except Exception:
                        continue  # ถ้าดึงข้อมูลไฟล์ไม่ได้ (เช่น ไฟล์ถูกล็อกอยู่) ให้ข้ามไปก่อน

            # เรียงลำดับไฟล์จาก Oldest -> Newest (เก่าสุดขึ้นก่อน)
            file_list.sort(key=lambda x: x[1])

            deleted_count = 0

            # ─── เงื่อนไข 1: ลบไฟล์อายุเกิน max_days (30 วัน) ───
            remaining_files = []
            for full_path, mtime in file_list:
                if (now - mtime) > max_age_seconds:
                    try:
                        os.remove(full_path)
                        deleted_count += 1
                        print(f"🧹 [Auto Cleanup] ลบไฟล์หมดอายุ: {os.path.basename(full_path)}")
                    except PermissionError:
                        # ถ้าไฟล์กำลังถูกเขียน/เปิดใช้งานอยู่โดยโปรแกรมอื่น ให้เก็บไว้ก่อน
                        remaining_files.append((full_path, mtime))
                    except Exception as e:
                        print(f"Error removing aged file {full_path}: {e}")
                else:
                    remaining_files.append((full_path, mtime))

            # ─── เงื่อนไข 2: เช็กพื้นที่ดิสก์ หากเหลือน้อยกว่า min_free_gb (1 GB) ลบไฟล์เก่าสุด ───
            target_free_bytes = int(min_free_gb * 1024 * 1024 * 1024)

            for full_path, _ in remaining_files:
                total, used, free = shutil.disk_usage(self.folder_path)

                # ถ้าพื้นที่ว่างมากกว่าหรือเท่ากับ 1 GB แล้ว ให้หยุดลบ
                if free >= target_free_bytes:
                    break

                try:
                    os.remove(full_path)
                    deleted_count += 1
                    print(f"💾 [Space Cleanup] ลบไฟล์เก่าเพื่อคืนพื้นที่: {os.path.basename(full_path)}")
                except PermissionError:
                    continue  # ถ้าลบไม่ได้เพราะไฟล์ใช้งานอยู่ ให้ข้ามไปลบไฟล์ถัดไป
                except Exception as e:
                    print(f"Error removing file for space {full_path}: {e}")

            # ถ้ามีไฟล์ถูกลบ และหน้าจอ GUI ยังเปิดอยู่ ให้รีเฟรชตารางแสดงไฟล์
            if deleted_count > 0 and hasattr(self, 'window') and self.window.winfo_exists():
                # ใช้ root.after เพื่อสั่งอัปเดต UI จาก Thread หลักอย่างปลอดภัย
                self.window.after(0, self.load_files)

            return deleted_count

    def start_auto_cleanup_thread(self, interval_seconds=3600, max_days=30, min_free_gb=1.0):
            """เริ่ม Background Thread คอยตรวจเช็กไฟล์ขยะตามระยะเวลาที่กำหนด"""
            def cleanup_loop():
                # รันครั้งแรกทันทีที่เปิดโปรแกรม/เปิดหน้าต่าง
                self.cleanup_old_videos(max_days=max_days, min_free_gb=min_free_gb)
                
                while True:
                    time.sleep(interval_seconds)  # หน่วงเวลาตาม interval (เช่น 3600 วินาที = 1 ชม.)
                    
                    # เช็กว่าหากวัตถุถูกทำลายหรือหน้าต่างถูกปิดไปแล้ว ให้หยุดการทำงานของ Thread
                    if hasattr(self, 'window') and not self.window.winfo_exists():
                        break
                    
                    self.cleanup_old_videos(max_days=max_days, min_free_gb=min_free_gb)

            # สร้าง Thread เบื้องหลัง (daemon=True จะปิดตัวลงเองเมื่อโปรแกรมหลักปิด)
            cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
            cleanup_thread.start()

# ─── ⚙️ คลาสจัดการ GUI Setting หลัก ───
class ConfigGUI:
    def __init__(self, config_path=r"setting\config.yml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.root = None

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"global": {}, "cameras": {}, "model": {}}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f, allow_unicode=True)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถบันทึกไฟล์ได้: {e}")
            return False

    def scan_models(self):
        """สแกนไฟล์โมเดลในโฟลเดอร์ และดึงรายการโมเดลทั้งหมดที่มีอยู่ใน config"""
        files = glob.glob("model/*.pkl") + glob.glob("model/*.joblib") + glob.glob("*.pkl") + glob.glob("*.joblib")
        model_names = [os.path.basename(f) for f in files]

        if "model" in self.config and isinstance(self.config["model"], dict):
            for k, v in self.config["model"].items():
                if isinstance(v, dict) and "source" in v:
                    model_names.append(os.path.basename(v["source"]))
                elif isinstance(v, str):
                    model_names.append(os.path.basename(v))

        unique_models = list(set([m for m in model_names if m]))
        if not unique_models:
            unique_models = ["pose_classifier_1.pkl"]
        return sorted(unique_models)

    def open_train_studio(self, selected_model_file):
        train_win = tk.Toplevel(self.root)
        train_win.title("Pose Model Training Studio")
        train_win.geometry("450x320")
        train_win.resizable(False, False)

        tk.Label(train_win, text="🏋️‍♂️ AI Pose Training Studio", font=("Helvetica", 12, "bold")).pack(pady=10)

        info_frame = ttk.LabelFrame(train_win, text=" ไฟล์ที่กำลังใช้งานอยู่ ", padding=10)
        info_frame.pack(fill="x", padx=15, pady=5)

        dataset_path = self.config.get("global", {}).get("dataset_path", "dataset.csv")
        model_path = os.path.join("model", selected_model_file) if not os.path.isabs(selected_model_file) else selected_model_file

        ttk.Label(info_frame, text=f"📊 Dataset: {os.path.basename(dataset_path)}", foreground="blue").pack(anchor="w")
        ttk.Label(info_frame, text=f"🤖 Target Save: {os.path.basename(model_path)}", foreground="green").pack(anchor="w")

        progress = ttk.Progressbar(train_win, orient="horizontal", length=380, mode="indeterminate")
        progress.pack(pady=15)

        status_lbl = tk.Label(train_win, text="🔴 พร้อมทำการเทรนโมเดล", font=("Helvetica", 9), fg="gray")
        status_lbl.pack(pady=2)

        def start_train_thread():
            btn_train.config(state=tk.DISABLED, text="⏳ กำลังคำนวณโมเดล...")
            status_lbl.config(text="⚙️ กำลังประมวลผลอัลกอริทึม Random Forest...", fg="#d35400")
            progress.start(10)
            t = threading.Thread(target=run_training, daemon=True)
            t.start()

        def run_training():
            try:
                if not os.path.exists(dataset_path):
                    train_win.after(0, lambda: messagebox.showerror("Error", f"❌ ไม่พบไฟล์ Dataset ที่พิกัด:\n{dataset_path}"))
                    return

                df = pd.read_csv(dataset_path)
                X = df.drop(columns=['label'])
                y = df['label']
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                clf = RandomForestClassifier(n_estimators=100, random_state=42)
                clf.fit(X_train, y_train)

                y_pred = clf.predict(X_test)
                acc_score = accuracy_score(y_test, y_pred) * 100

                os.makedirs(os.path.dirname(model_path), exist_ok=True) if os.path.dirname(model_path) else None
                joblib.dump(clf, model_path)
                abs_path = os.path.abspath(model_path)

                train_win.after(0, lambda: success_callback(acc_score, abs_path))
            except Exception as e:
                train_win.after(0, lambda: fail_callback(str(e)))

        def success_callback(acc, path):
            progress.stop()
            btn_train.config(state=tk.NORMAL, text="🚀 เริ่มเทรนโมเดลใหม่")
            status_lbl.config(text="🟢 เทรนสำเร็จ!", fg="green")
            
            if hasattr(self, 'cb_model'):
                self.available_models = self.scan_models()
                self.cb_model['values'] = self.available_models
                
            messagebox.showinfo("Train Success", f"🎉 เทรนโมเดลสำเร็จสมบูรณ์!\n\n🎯 Accuracy: {acc:.2f}%\n📂 PATH: {path}")
            train_win.destroy()

        def fail_callback(err):
            progress.stop()
            btn_train.config(state=tk.NORMAL, text="🚀 เริ่มเทรนโมเดลใหม่")
            status_lbl.config(text="❌ ล้มเหลว", fg="red")
            messagebox.showerror("Error", f"เกิดปัญหาขณะเทรนข้อมูล:\n{err}")

        btn_train = ttk.Button(train_win, text="🚀 เริ่มเทรนโมเดลใหม่ (Start Train)", command=start_train_thread)
        btn_train.pack(pady=10)

    def open_settings(self, current_cam_id=None, on_close_callback=None):
        """เปิดหน้าต่าง GUI สำหรับการ Setting"""
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.lift()
                    return
            except Exception:
                self.root = None

        self.root = tk.Tk()
        self.root.title("System Configuration")
        self.root.geometry("500x720")  # ปรับเพิ่มความสูงรองรับโซนจัดการวิดีโอ
        self.root.resizable(False, False)

        # ─── โซนเลือกกล้อง ───
        frame_cam = ttk.LabelFrame(self.root, text=" การจัดการกล้อง ", padding=10)
        frame_cam.pack(fill="x", padx=15, pady=6)

        ttk.Label(frame_cam, text="เลือกกล้องที่ต้องการตั้งค่า:").grid(row=0, column=0, sticky="w", pady=5)
        
        camera_list = list(self.config.get("cameras", {}).keys())
        self.cam_var = tk.StringVar()
        self.cb_camera = ttk.Combobox(frame_cam, textvariable=self.cam_var, values=camera_list, state="readonly")
        self.cb_camera.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        if camera_list:
            if current_cam_id in camera_list:
                idx = camera_list.index(current_cam_id)
                self.cb_camera.current(idx)
            else:
                self.cb_camera.current(0)

        # ─── โซนตั้งค่าตัวเลือกการเซฟไฟล์ ───
        frame_save = ttk.LabelFrame(self.root, text=" การบันทึกวิดีโอ (Video Output) ", padding=10)
        frame_save.pack(fill="x", padx=15, pady=6)

        self.var_ok = tk.BooleanVar()
        self.var_ng = tk.BooleanVar()

        self.chk_ok = ttk.Checkbutton(frame_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น OK (video_ok)", variable=self.var_ok)
        self.chk_ok.pack(anchor="w", pady=5)

        self.chk_ng = ttk.Checkbutton(frame_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น NG (video_ng)", variable=self.var_ng)
        self.chk_ng.pack(anchor="w", pady=5)

        def on_camera_select(event=None):
            cam_id = self.cam_var.get()
            cam_data = self.config.get("cameras", {}).get(cam_id, {})
            self.var_ok.set(cam_data.get("save_ok", True))
            self.var_ng.set(cam_data.get("save_ng", True))

        self.cb_camera.bind("<<ComboboxSelected>>", on_camera_select)
        if camera_list: 
            on_camera_select()

        # ─── 🎥 เพิ่มใหม่: โซนจัดการวิดีโอบันทึก (Video Viewer & Manager) ───
        frame_video_manager = ttk.LabelFrame(self.root, text=" 🎥 คลังไฟล์วิดีโอบันทึก (Video Viewer) ", padding=10)
        frame_video_manager.pack(fill="x", padx=15, pady=6)

        def open_folder_manager(folder_path, title):
            VideoFolderManagerWindow(self.root, folder_path, title)

        btn_center = ttk.Button(
            frame_video_manager, 
            text="📂 video_center", 
            command=lambda: open_folder_manager("video_center", "วิดีโอระหว่างการตรวจ")
        )
        btn_center.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        btn_ok = ttk.Button(
            frame_video_manager, 
            text="✅ video_ok", 
            command=lambda: open_folder_manager("video_ok", "วิดีโอผ่านเกณฑ์ (OK)")
        )
        btn_ok.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        btn_ng = ttk.Button(
            frame_video_manager, 
            text="❌ video_ng", 
            command=lambda: open_folder_manager("video_ng", "วิดีโอไม่ผ่านเกณฑ์ (NG)")
        )
        btn_ng.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        # ─── รายละเอียดอื่นๆ ───
        frame_info = ttk.LabelFrame(self.root, text=" ข้อมูลกล้องปัจจุบัน ", padding=10)
        frame_info.pack(fill="x", padx=15, pady=5)
        
        self.lbl_source = ttk.Label(frame_info, text="")
        self.lbl_source.pack(anchor="w")
        self.lbl_pts = ttk.Label(frame_info, text="")
        self.lbl_pts.pack(anchor="w")

        def update_info_labels(*args):
            cam_id = self.cam_var.get()
            cam_data = self.config.get("cameras", {}).get(cam_id, {})
            self.lbl_source.config(text=f"Source: {cam_data.get('source', 'None')}")
            pts_count = len(cam_data.get("mark_points", []))
            self.lbl_pts.config(text=f"จำนวนจุดมาร์ก ROI ที่บันทึกไว้: {pts_count} จุด")

        self.cam_var.trace_add("write", update_info_labels)
        if camera_list:
            update_info_labels()

        # ─── 🤖 โซนการเลือกไฟล์โมเดล AI ───
        frame_model = ttk.LabelFrame(self.root, text=" การตั้งค่าโมเดล AI (Model Settings) ", padding=10)
        frame_model.pack(fill="x", padx=15, pady=6)

        ttk.Label(frame_model, text="ไฟล์โมเดลที่ใช้งาน:").grid(row=0, column=0, sticky="w", pady=5)

        self.available_models = self.scan_models()
        
        default_model_name = self.available_models[0] if self.available_models else ""
        if "model" in self.config and isinstance(self.config["model"], dict):
            for k, v in self.config["model"].items():
                if isinstance(v, dict) and "source" in v:
                    default_model_name = os.path.basename(v["source"])
                    break

        self.model_var = tk.StringVar(value=default_model_name)
        self.cb_model = ttk.Combobox(frame_model, textvariable=self.model_var, values=self.available_models, state="readonly", width=25)
        self.cb_model.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.custom_model_full_path = None

        def browse_model_file():
            file_path = filedialog.askopenfilename(
                title="เลือกไฟล์โมเดล AI เพิ่มเติม",
                filetypes=[("Model Files", "*.pkl *.joblib"), ("All Files", "*.*")]
            )
            if file_path:
                file_path = os.path.normpath(file_path)
                filename = os.path.basename(file_path)
                
                current_dir = os.getcwd()
                models_dir = os.path.join(current_dir, "model")
                
                if file_path.startswith(models_dir):
                    final_path = os.path.join("model", filename)
                else:
                    final_path = file_path

                if filename not in self.available_models:
                    self.available_models.append(filename)
                    self.cb_model['values'] = self.available_models
                
                self.model_var.set(filename)
                self.custom_model_full_path = final_path

        btn_browse = ttk.Button(frame_model, text="📁 ค้นหา...", command=browse_model_file, width=8)
        btn_browse.grid(row=0, column=2, padx=5, pady=5)

        btn_go_train = tk.Button(
            frame_model, 
            text="🏋️‍♂️ เปิดสตูดิโอเทรนโมเดล (Train AI)", 
            command=lambda: self.open_train_studio(selected_model_file=self.model_var.get()),
            bg="#f39c12", 
            fg="white",
            font=("Helvetica", 9, "bold")
        )
        btn_go_train.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # ─── ตรรกะปิดหน้าต่าง ───
        def on_window_close():
            self.config = self.load_config() 
            if self.root:
                self.root.destroy()
            self.root = None  
            if on_close_callback and current_cam_id:
                on_close_callback(current_cam_id)

        self.root.protocol("WM_DELETE_WINDOW", on_window_close)

        # ─── ปุ่มบันทึกข้อมูลหลัก ───
        def save_and_close():
            cam_id = self.cam_var.get()
            selected_file = self.model_var.get()

            if self.custom_model_full_path and os.path.basename(self.custom_model_full_path) == selected_file:
                final_model_path = self.custom_model_full_path
            else:
                if os.path.exists(os.path.join("model", selected_file)):
                    final_model_path = os.path.join("model", selected_file)
                else:
                    final_model_path = selected_file

            if "model" not in self.config or not isinstance(self.config["model"], dict):
                self.config["model"] = {}

            found_key = None
            for key, val in self.config["model"].items():
                if isinstance(val, dict) and os.path.basename(val.get("source", "")) == selected_file:
                    found_key = key
                    break

            if found_key:
                self.config["model"][found_key]["source"] = final_model_path
            else:
                new_key = f"model_path_{len(self.config['model']) + 1}"
                self.config["model"][new_key] = {"source": final_model_path}

            if cam_id:
                if "cameras" not in self.config: self.config["cameras"] = {}
                if cam_id not in self.config["cameras"]: self.config["cameras"][cam_id] = {}
                
                self.config["cameras"][cam_id]["save_ok"] = self.var_ok.get()
                self.config["cameras"][cam_id]["save_ng"] = self.var_ng.get()
                
            if self.save_config():
                messagebox.showinfo("สำเร็จ", f"อัปเดตโมเดลเป็น: {selected_file}\nบันทึกข้อมูลเรียบร้อยแล้ว")
                if self.root:
                    self.root.destroy()
                self.root = None
                if on_close_callback:
                    on_close_callback(cam_id)

        btn_save = ttk.Button(self.root, text="💾 บันทึกและปิดหน้าต่าง", command=save_and_close)
        btn_save.pack(pady=15)

        self.root.mainloop()