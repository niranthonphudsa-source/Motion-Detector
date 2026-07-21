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

        # ดึงไฟล์ที่มีบันทึกไว้ใน config.yml ด้วย
        if "model" in self.config and isinstance(self.config["model"], dict):
            for k, v in self.config["model"].items():
                if isinstance(v, dict) and "source" in v:
                    model_names.append(os.path.basename(v["source"]))
                elif isinstance(v, str):
                    model_names.append(os.path.basename(v))

        # ลบชื่อซ้ำ และเรียงลำดับ
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

        # ─── 🤖 โซนการเลือกไฟล์โมเดล AI (Dropdown เดียวเหมือนเลือกกล้อง) ───
        frame_model = ttk.LabelFrame(self.root, text=" การตั้งค่าโมเดล AI (Model Settings) ", padding=10)
        frame_model.pack(fill="x", padx=15, pady=6)

        ttk.Label(frame_model, text="ไฟล์โมเดลที่ใช้งาน:").grid(row=0, column=0, sticky="w", pady=5)

        self.available_models = self.scan_models()
        
        # ดึงไฟล์โมเดลตัวแรกสุดที่พบบันทึกอยู่ใน config เป็นค่าเริ่มต้น
        default_model_name = self.available_models[0] if self.available_models else ""
        if "model" in self.config and isinstance(self.config["model"], dict):
            for k, v in self.config["model"].items():
                if isinstance(v, dict) and "source" in v:
                    default_model_name = os.path.basename(v["source"])
                    break

        self.model_var = tk.StringVar(value=default_model_name)
        self.cb_model = ttk.Combobox(frame_model, textvariable=self.model_var, values=self.available_models, state="readonly", width=25)
        self.cb_model.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # ตัวแปรเก็บ Full path ชั่วคราวกรณีเปิดไฟล์ผ่าน Browse
        self.custom_model_full_path = None

        def browse_model_file():
            """เปิดหน้าต่างเลือกไฟล์โมเดลภายนอกเข้ามาเพิ่มในตัวเลือก"""
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

                # เพิ่มชื่อไฟล์เข้า Dropdown ถ้ายังไม่มี
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

            # คำนวณหา Path ที่จะบันทึกลงไฟล์ config.yml
            if self.custom_model_full_path and os.path.basename(self.custom_model_full_path) == selected_file:
                final_model_path = self.custom_model_full_path
            else:
                if os.path.exists(os.path.join("model", selected_file)):
                    final_model_path = os.path.join("model", selected_file)
                else:
                    final_model_path = selected_file

            # 🌟 อัปเดตไฟล์โมเดลลงใน config
            if "model" not in self.config or not isinstance(self.config["model"], dict):
                self.config["model"] = {}

            # ค้นหาว่าไฟล์นี้ตรงกับ key ไหนใน config หรือไม่ ถ้าตรงให้อัปเดต ถ้าไม่ตรงให้สร้าง key ใหม่เพิ่มเข้าไป
            found_key = None
            for key, val in self.config["model"].items():
                if isinstance(val, dict) and os.path.basename(val.get("source", "")) == selected_file:
                    found_key = key
                    break

            if found_key:
                self.config["model"][found_key]["source"] = final_model_path
            else:
                # ถ้าเป็นโมเดลใหม่ที่เพิ่ง Browse เข้ามา หรือเพิ่งเพิ่ม ให้สร้าง key ใหม่ลง config
                new_key = f"model_path_{len(self.config['model']) + 1}"
                self.config["model"][new_key] = {"source": final_model_path}

            # บันทึกค่ากล้อง
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