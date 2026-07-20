# LIB/config_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import os
import glob
import threading

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

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
            return {"global": {}, "cameras": {}}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f, allow_unicode=True)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถบันทึกไฟล์ได้: {e}")
            return False

    def scan_models(self):
        files = glob.glob("models/*.pkl") + glob.glob("models/*.joblib") + glob.glob("*.pkl") + glob.glob("*.joblib")
        model_names = [os.path.basename(f) for f in files]
        if not model_names:
            model_names = ["pose_classifier_1.pkl"]
        return model_names

    def open_train_studio(self):
        train_win = tk.Toplevel(self.root)
        train_win.title("Pose Model Training Studio")
        train_win.geometry("450x320")
        train_win.resizable(False, False)

        tk.Label(train_win, text="🏋️‍♂️ AI Pose Training Studio", font=("Helvetica", 12, "bold")).pack(pady=10)

        info_frame = ttk.LabelFrame(train_win, text=" ไฟล์ที่กำลังใช้งานอยู่ ", padding=10)
        info_frame.pack(fill="x", padx=15, pady=5)

        dataset_path = self.config.get("global", {}).get("dataset_path", "dataset.csv")
        model_path = self.config.get("global", {}).get("model_path", "pose_classifier_1.pkl")

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

                joblib.dump(clf, model_path)
                abs_path = os.path.abspath(model_path)

                if hasattr(self, 'cb_model'):
                    self.cb_model['values'] = self.scan_models()

                train_win.after(0, lambda: success_callback(acc_score, abs_path))
            except Exception as e:
                train_win.after(0, lambda: fail_callback(str(e)))

        def success_callback(acc, path):
            progress.stop()
            btn_train.config(state=tk.NORMAL, text="🚀 เริ่มเทรนโมเดลใหม่")
            status_lbl.config(text="🟢 เทรนสำเร็จ!", fg="green")
            messagebox.showinfo("Train Success", f"🎉 เทรนโมเดลสำเร็จสมบูรณ์!\n\n🎯 Accuracy: {acc:.2f}%\n📂 PATH: {path}")
            train_win.destroy()

        def fail_callback(err):
            progress.stop()
            btn_train.config(state=tk.NORMAL, text="🚀 เริ่มเทรนโมเดลใหม่")
            status_lbl.config(text="❌ ล้มเหลว", fg="red")
            messagebox.showerror("Error", f"เกิดปัญหาขณะเทรนข้อมูล:\n{err}")

        btn_train = ttk.Button(train_win, text="🚀 เริ่มเทรนโมเดลใหม่ (Start Train)", command=start_train_thread)
        btn_train.pack(pady=10)

    # 🌟 เพิ่มพารามิเตอร์ current_cam_id มารองรับการจำหน้ากล้องล่าสุด
    def open_settings(self, current_cam_id=None, on_close_callback=None):
        """เปิดหน้าต่าง GUI สำหรับการ Setting เบื้องหลัง"""
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.lift()
                    return
            except Exception:
                self.root = None

        self.root = tk.Tk()
        self.root.title("System Configuration")
        self.root.geometry("480x630")
        self.root.resizable(False, False)

        # ─── โซนเลือกกล้อง ───
        frame_cam = ttk.LabelFrame(self.root, text=" การจัดการกล้อง ", padding=10)
        frame_cam.pack(fill="x", padx=15, pady=6)

        ttk.Label(frame_cam, text="เลือกกล้องที่ต้องการตั้งค่า:").grid(row=0, column=0, sticky="w", pady=5)
        
        camera_list = list(self.config.get("cameras", {}).keys())
        self.cam_var = tk.StringVar()
        self.cb_camera = ttk.Combobox(frame_cam, textvariable=self.cam_var, values=camera_list, state="readonly")
        self.cb_camera.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 🌟 แก้ไข: ตรวจเช็กและกระโดดไปล็อกค่าที่กล้องตัวปัจจุบันทันทีเมื่อเปิดขึ้นมา
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

        # ─── 🤖 โซนการตั้งค่าและเลือกโมเดล AI ───
        frame_model = ttk.LabelFrame(self.root, text=" การตั้งค่าโมเดล AI (Model Settings) ", padding=10)
        frame_model.pack(fill="x", padx=15, pady=6)

        ttk.Label(frame_model, text="โมเดลที่ต้องการใช้งาน:").grid(row=0, column=0, sticky="w", pady=5)

        self.available_models = self.scan_models()
        current_model_path = self.config.get("global", {}).get("model_path", "pose_classifier_1.pkl")
        current_model_name = os.path.basename(current_model_path)
        
        self.model_var = tk.StringVar(value=current_model_name)
        self.cb_model = ttk.Combobox(frame_model, textvariable=self.model_var, values=self.available_models, state="readonly", width=25)
        self.cb_model.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        def browse_model_file():
            file_path = filedialog.askopenfilename(
                title="เลือกไฟล์โมเดล AI",
                filetypes=[("Model Files", "*.pkl *.joblib"), ("All Files", "*.*")]
            )
            if file_path:
                # แปลงให้เป็นระบบ Path มาตรฐานเพื่อป้องกันปัญหาเรื่องเครื่องหมาย / กับ \
                file_path = os.path.normpath(file_path)
                filename = os.path.basename(file_path)
                
                # 🌟 เช็กว่าไฟล์นี้ถูกเลือกมาจากโฟลเดอร์ models ในโปรแกรมของเราหรือไม่
                # ค้นหาคำว่า "models" ในเส้นทางไฟล์ย่อย
                current_dir = os.getcwd()
                models_dir = os.path.join(current_dir, "models")
                
                if file_path.startswith(models_dir):
                    # ถ้าดึงมาจากโฟลเดอร์ models ให้ใช้เป็น "models/filename.pkl"
                    final_path_or_name = os.path.join("models", filename)
                else:
                    # ถ้าดึงมาจากที่อื่นนอกโปรแกรม ให้ใช้ Path เต็มของไฟล์นั้นเลย เพื่อความปลอดภัย
                    final_path_or_name = file_path

                # อัปเดตตัวเลือกใน Dropdown (แสดงแค่ชื่อไฟล์ให้ผู้ใช้เห็นเพื่อความสวยงามสะอาดตา)
                if filename not in self.available_models:
                    self.available_models.append(filename)
                    self.cb_model['values'] = self.available_models
                
                self.model_var.set(filename)
                
                # 🌟 เก็บค่า Path จริง (ที่มีโฟลเดอร์นำหน้า) ซ่อนไว้ในตัวแปรชั่วคราวของคลาส 
                # เพื่อเอาไปใช้ตอนกดปุ่มบันทึก (save_and_close)
                self.selected_model_full_path = final_path_or_name

        btn_browse = ttk.Button(frame_model, text="📁 ค้นหา...", command=browse_model_file, width=8)
        btn_browse.grid(row=0, column=2, padx=5, pady=5)

        btn_go_train = tk.Button(
            frame_model, 
            text="🏋️‍♂️ เปิดสตูดิโอเทรนโมเดล (Train AI)", 
            command=self.open_train_studio,
            bg="#f39c12", 
            fg="white",
            font=("Helvetica", 9, "bold")
        )
        btn_go_train.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # 🌟 แก้ไข: ตรรกะปุ่มกากบาท X ให้ส่งคืนค่ากล้องตัวเดิมตัวล่าสุด (ไม่ดีดกลับไปกล้องแรก)
        def on_window_close():
            # 1. โหลดคอนฟิกเดิมจากไฟล์กลับมาทับ เพื่อล้างค่าเก่าที่อาจจะเปลี่ยนเล่นใน GUI แต่ไม่ได้กดเซฟ
            self.config = self.load_config() 
            
            # 2. ปิดหน้าต่าง GUI
            if self.root:
                self.root.destroy()
            self.root = None  
            
            # 3. บังคับส่งชื่อกล้องเริ่มต้น (หน้าปัจจุบัน) กลับไปที่โปรแกรมหลักเสมอ
            if on_close_callback and current_cam_id:
                on_close_callback(current_cam_id)

        self.root.protocol("WM_DELETE_WINDOW", on_window_close)

        # ─── ปุ่มบันทึกข้อมูลหลัก ───
        def save_and_close():
            # ─── ปุ่มบันทึกข้อมูลหลัก (save_and_close ใน LIB/config_gui.py) ───
            cam_id = self.cam_var.get()
            selected_model = self.model_var.get()

            # 🌟 แก้ไขตรงนี้: ตรวจสอบว่าผู้ใช้กด Browse มาหรือไม่ 
            # ถ้ามีให้ใช้พิกัดเต็มที่เซ็ตไว้ แต่ถ้าไม่ได้กด (เลือกจาก dropdown ปกติ) ให้คำนวณหาโฟลเดอร์ตามระบบเดิม
            if hasattr(self, 'selected_model_full_path') and self.selected_model_full_path and os.path.basename(self.selected_model_full_path) == selected_model:
                final_model_path = self.selected_model_full_path
            else:
                if os.path.exists(os.path.join("models", selected_model)):
                    final_model_path = os.path.join("model", selected_model)
                else:
                    final_model_path = selected_model

            if "global" not in self.config: 
                self.config["global"] = {}
            
            # บันทึกค่าที่มีโฟลเดอร์นำหน้า (หรือ Path เต็ม) ลงไฟล์ config.yml เรียบร้อย!
            self.config["global"]["model_path"] = final_model_path

            if cam_id:
                if "cameras" not in self.config: self.config["cameras"] = {}
                if cam_id not in self.config["cameras"]: self.config["cameras"][cam_id] = {}
                
                self.config["cameras"][cam_id]["save_ok"] = self.var_ok.get()
                self.config["cameras"][cam_id]["save_ng"] = self.var_ng.get()
                
                if self.save_config():
                    messagebox.showinfo("สำเร็จ", f"อัปเดตโมเดลเป็น: {selected_model}\nบันทึกค่ากล้อง {cam_id} เรียบร้อยแล้ว")
                    if self.root:
                        self.root.destroy()
                    self.root = None
                    if on_close_callback:
                        # ถ้ากดเซฟสำเร็จ ค่อยส่งกล้องตัวที่เลือกใหม่ใน GUI กลับไป
                        on_close_callback(cam_id)

        btn_save = ttk.Button(self.root, text="💾 บันทึกและปิดหน้าต่าง", command=save_and_close)
        btn_save.pack(pady=15)

        self.root.mainloop()