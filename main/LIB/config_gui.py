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
        self.window.geometry("500x450")
        self.window.resizable(True, True)
        self.window.grab_set()  # ดึงโฟกัสมาที่หน้าต่างนี้ก่อน
        
        os.makedirs(self.folder_path, exist_ok=True)

        # ทำความสะอาดไฟล์เก่าอัตโนมัติทันทีเมื่อเปิดหน้าต่าง
        self.cleanup_old_videos(max_days=30, min_free_gb=1.0)
        # 🌟 เริ่มการทำความสะอาดเบื้องหลังอัตโนมัติ (เช็กทุกๆ 1 ชั่วโมง)
        self.start_auto_cleanup_thread(interval_seconds=3600, max_days=30, min_free_gb=1.0)

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
            try:
                stat = os.stat(full_path)
                size_mb = f"{stat.st_size / (1024 * 1024):.2f} MB"
                mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                self.tree.insert("", tk.END, values=(f, size_mb, mod_time))
            except Exception:
                continue

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
                    continue

        file_list.sort(key=lambda x: x[1])
        deleted_count = 0

        # ─── เงื่อนไข 1: ลบไฟล์อายุเกิน max_days ───
        remaining_files = []
        for full_path, mtime in file_list:
            if (now - mtime) > max_age_seconds:
                try:
                    os.remove(full_path)
                    deleted_count += 1
                    print(f"🧹 [Auto Cleanup] ลบไฟล์หมดอายุ: {os.path.basename(full_path)}")
                except PermissionError:
                    remaining_files.append((full_path, mtime))
                except Exception as e:
                    print(f"Error removing aged file {full_path}: {e}")
            else:
                remaining_files.append((full_path, mtime))

        # ─── เงื่อนไข 2: เช็กพื้นที่ดิสก์ หากเหลือน้อยกว่า min_free_gb ───
        target_free_bytes = int(min_free_gb * 1024 * 1024 * 1024)

        for full_path, _ in remaining_files:
            try:
                total, used, free = shutil.disk_usage(self.folder_path)
                if free >= target_free_bytes:
                    break

                os.remove(full_path)
                deleted_count += 1
                print(f"💾 [Space Cleanup] ลบไฟล์เก่าเพื่อคืนพื้นที่: {os.path.basename(full_path)}")
            except PermissionError:
                continue
            except Exception as e:
                print(f"Error removing file for space {full_path}: {e}")

        if deleted_count > 0 and hasattr(self, 'window') and self.window.winfo_exists():
            self.window.after(0, self.load_files)

        return deleted_count

    def start_auto_cleanup_thread(self, interval_seconds=3600, max_days=30, min_free_gb=1.0):
        """เริ่ม Background Thread คอยตรวจเช็กไฟล์ขยะตามระยะเวลาที่กำหนด"""
        def cleanup_loop():
            # รันครั้งแรกทันที
            self.cleanup_old_videos(max_days=max_days, min_free_gb=min_free_gb)
            
            # ใช้วงรอบย่อยเช็กแบบละเอียดทุก 1 วินาที เพื่อหลุดลูปได้ทันทีเมื่อปิดหน้าต่าง
            counter = 0
            while True:
                time.sleep(1)
                if not hasattr(self, 'window') or not self.window.winfo_exists():
                    break
                counter += 1
                if counter >= interval_seconds:
                    self.cleanup_old_videos(max_days=max_days, min_free_gb=min_free_gb)
                    counter = 0

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()


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
        BG_COLOR = "#F8FAFC"
        PANEL_COLOR = "#FFFFFF"
        BORDER_COLOR = "#E2E8F0"
        TEXT_MAIN = "#1E3A8A"

        train_win = tk.Toplevel(self.root)
        train_win.title("Pose Model Training Studio")
        train_win.geometry("500x380")
        train_win.configure(bg=BG_COLOR)
        train_win.resizable(True, True)

        try:
            train_win.iconbitmap(r"main\Logo\atc_logo.png")
        except Exception:
            pass

        # Title
        tk.Label(
            train_win, 
            text="🏋️‍♂️ AI Pose Training Studio", 
            font=("Segoe UI", 14, "bold"), 
            fg=TEXT_MAIN, 
            bg=BG_COLOR
        ).pack(pady=(15, 5))


        info_frame = tk.Frame(train_win, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        info_frame.pack(fill="x", padx=20, pady=10, ipady=5)

        info_frame.columnconfigure(0, weight=1)

        dataset_path = self.config.get("global", {}).get("dataset_path", "dataset.csv")
        model_path = os.path.join("model", selected_model_file) if not os.path.isabs(selected_model_file) else selected_model_file

        def browse_file():
            dataset_path = filedialog.askopenfilename(
                title="select_dataset",
                filetypes=[("Csv", "*.csv"), ("All file", "*.*")]
            )

            if dataset_path:
                file_path = os.path.basename(dataset_path)
                label_dataset.config(text=f"📊 Dataset: {file_path}")

                if hasattr(self, 'config') and "global" in self.config:
                    self.config["global"]["dataset_path"] = file_path

        label_dataset = tk.Label(info_frame,
                                    text=f"📊 Dataset: {os.path.basename(dataset_path)}",
                                    fg="#2563EB",            # กำหนดสีข้อความแทนการใช้ style
                                    bg=PANEL_COLOR,          # กำหนดสีพื้นหลัง
                                    font=("Segoe UI", 9, "bold")
                                )
        label_dataset.grid(row=0, column=0, sticky="w", pady=2)

        label_model = tk.Label(info_frame,
                                text=f"🤖 Target Save: {os.path.basename(model_path)}",
                                fg="#2563EB",            # กำหนดสีข้อความแทนการใช้ style
                                bg=PANEL_COLOR,          # กำหนดสีพื้นหลัง
                                font=("Segoe UI", 9, "bold")
                                )
        label_model.grid(row=1, column=0, sticky="w", pady=2)


        btn_searce = ttk.Button(info_frame,
                                 text="📁 ค้นหา...", 
                                 style="Action.TButton", 
                                 command=browse_file, width=8
                                )
        btn_searce.grid(row=0, column=1, rowspan=2, sticky="e",  padx=(5, 10))

        progress = ttk.Progressbar(train_win, orient="horizontal", mode="indeterminate")
        progress.pack(fill="x", padx=20, pady=15)

        status_lbl = tk.Label(train_win, text="🔴 พร้อมทำการเทรนโมเดล", font=("Segoe UI", 9, "bold"), fg="#64748B", bg=BG_COLOR)
        status_lbl.pack(pady=2)

        def start_train_thread():
            btn_train.config(state=tk.DISABLED, text="⏳ กำลังคำนวณโมเดล...")
            status_lbl.config(text="⚙️ กำลังประมวลผลอัลกอริทึม Random Forest...", fg="#D97706")
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
            status_lbl.config(text="🟢 เทรนสำเร็จ!", fg="#059669")
            
            if hasattr(self, 'cb_model'):
                self.available_models = self.scan_models()
                self.cb_model['values'] = self.available_models
                
            messagebox.showinfo("Train Success", f"🎉 เทรนโมเดลสำเร็จสมบูรณ์!\n\n🎯 Accuracy: {acc:.2f}%\n📂 PATH: {path}")
            train_win.destroy()

        def fail_callback(err):
            progress.stop()
            btn_train.config(state=tk.NORMAL, text="🚀 เริ่มเทรนโมเดลใหม่")
            status_lbl.config(text="❌ ล้มเหลว", fg="#DC2626")
            messagebox.showerror("Error", f"เกิดปัญหาขณะเทรนข้อมูล:\n{err}")

        btn_train = tk.Button(
            train_win, 
            text="🚀 เริ่มเทรนโมเดลใหม่ (Start Train)", 
            command=start_train_thread,
            bg="#2563EB", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        btn_train.pack(pady=15)

    def safe_close_app(self):
        if self.root:
            self.root.quit()
            self.root.destroy()

    def open_settings(self, current_cam_id=None, on_close_callback=None):
        """เปิดหน้าต่าง GUI สำหรับการ Setting (Light Mode - Blue Theme)"""
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.lift()
                    return
            except Exception:
                self.root = None

        # ─── โทนสีหลัก (White & Blue Theme) ───
        BG_COLOR = "#F8FAFC"        # พื้นหลังหลัก
        PANEL_COLOR = "#FFFFFF"     # พื้นหลังกล่องการ์ด
        BORDER_COLOR = "#E2E8F0"    # สีขอบกล่อง
        TEXT_MAIN = "#0F172A"       # สีข้อความหลัก
        TEXT_MUTED = "#64748B"      # สีข้อความรอง
        PRIMARY_BLUE = "#2563EB"    # สีน้ำเงินหลัก
        TITLE_BLUE = "#1E3A8A"      # สีกรมท่าสำหรับหัวข้อ

        self.root = tk.Tk()
        self.root.title("System Configuration")
        self.root.geometry("600x820")
        self.root.minsize(450, 750)      # รองรับการขยายและย่อหน้าจอ
        self.root.resizable(True, True)  # ✅ เปิดให้ลด-ขยายขนาดหน้าต่างได้
        self.root.configure(bg=BG_COLOR)

        # ตั้งค่า App Icon
        try:
            self.root.iconbitmap(r"main\Logo\atc_logo.png")
        except Exception:
            pass

        # 🎨 ตั้งค่า Styling สำหรับ TTK Widget ให้ตรงกับโทนสีขาว-น้ำเงิน
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 9))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TCombobox", fieldbackground=PANEL_COLOR, background=PANEL_COLOR, foreground=TEXT_MAIN, padding=4)
        style.configure("TCheckbutton", background=PANEL_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 9))
        
        # Style ปุ่มกดทั่วไป
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), background="#F1F5F9", foreground=TITLE_BLUE, padding=6)
        style.map("Action.TButton", background=[("active", "#E2E8F0")])

        # Scrollable Container หลักเพื่อรองรับการย่อหน้าต่าง
        main_canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=BG_COLOR)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        canvas_frame = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def _on_canvas_configure(event):
            main_canvas.itemconfig(canvas_frame, width=event.width)
        main_canvas.bind('<Configure>', _on_canvas_configure)

        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ─── 1. HEADER SECTION (มี LOGO) ───
        header_frame = tk.Frame(scrollable_frame, bg=BG_COLOR, padx=20, pady=15)
        header_frame.pack(fill="x")

        # แสดงรูป Logo
        try:
            self.logo_icon = tk.PhotoImage(file=r"main\Logo\atc_logo.png").subsample(2, 2)
            lbl_logo = tk.Label(header_frame, image=self.logo_icon, bg=BG_COLOR)
            lbl_logo.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด Icon ได้: {e}")

        title_box = tk.Frame(header_frame, bg=BG_COLOR)
        title_box.pack(side="left", fill="x", expand=True)

        lbl_title = tk.Label(title_box, text="System Configuration", font=("Segoe UI", 16, "bold"), fg=TITLE_BLUE, bg=BG_COLOR)
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Camera, Model & Output Settings Center", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_COLOR)
        lbl_sub.pack(anchor="w")

        # ฟังก์ชันสร้าง Card Container ให้ได้ขอบการ์ดขาวเรียบหรู
        def create_card_frame(parent, title_text):
            card = tk.Frame(parent, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", padx=20, pady=8)
            
            top_bar = tk.Frame(card, bg=PRIMARY_BLUE, height=3)
            top_bar.pack(fill="x", side="top")
            
            content = tk.Frame(card, bg=PANEL_COLOR, padx=15, pady=12)
            content.pack(fill="x", expand=True)
            
            tk.Label(content, text=title_text, font=("Segoe UI", 10, "bold"), fg=TITLE_BLUE, bg=PANEL_COLOR).pack(anchor="w", pady=(0, 8))
            return content

        # ─── 2. โซนเลือกกล้อง ───
        c_cam = create_card_frame(scrollable_frame, "📷 การจัดการกล้อง (Camera Settings)")
        
        cam_grid = tk.Frame(c_cam, bg=PANEL_COLOR)
        cam_grid.pack(fill="x")
        cam_grid.columnconfigure(1, weight=1)

        tk.Label(cam_grid, text="เลือกกล้องที่ต้องการตั้งค่า:", fg=TEXT_MAIN, bg=PANEL_COLOR, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)
        
        camera_list = list(self.config.get("cameras", {}).keys())
        self.cam_var = tk.StringVar()
        self.cb_camera = ttk.Combobox(cam_grid, textvariable=self.cam_var, values=camera_list, state="readonly")
        self.cb_camera.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        if camera_list:
            if current_cam_id in camera_list:
                idx = camera_list.index(current_cam_id)
                self.cb_camera.current(idx)
            else:
                self.cb_camera.current(0)

        # ─── 3. โซนตั้งค่าตัวเลือกการเซฟไฟล์ ───
        c_save = create_card_frame(scrollable_frame, "📹 การบันทึกวิดีโอ (Video Output)")

        self.var_ok = tk.BooleanVar()
        self.var_ng = tk.BooleanVar()

        self.chk_ok = ttk.Checkbutton(c_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น OK (video_ok)", variable=self.var_ok)
        self.chk_ok.pack(anchor="w", pady=4)

        self.chk_ng = ttk.Checkbutton(c_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น NG (video_ng)", variable=self.var_ng)
        self.chk_ng.pack(anchor="w", pady=4)

        def on_camera_select(event=None):
            cam_id = self.cam_var.get()
            cam_data = self.config.get("cameras", {}).get(cam_id, {})
            self.var_ok.set(cam_data.get("save_ok", True))
            self.var_ng.set(cam_data.get("save_ng", True))

        self.cb_camera.bind("<<ComboboxSelected>>", on_camera_select)
        if camera_list: 
            on_camera_select()

        # ─── 4. โซนจัดการวิดีโอบันทึก (Video Viewer & Manager) ───
        c_vm = create_card_frame(scrollable_frame, "🎥 คลังไฟล์วิดีโอบันทึก (Video Viewer)")

        def open_folder_manager(folder_path, title):
            VideoFolderManagerWindow(self.root, folder_path, title)

        btn_box = tk.Frame(c_vm, bg=PANEL_COLOR)
        btn_box.pack(fill="x", pady=5)
        for i in range(3): btn_box.columnconfigure(i, weight=1)

        btn_center = ttk.Button(btn_box, text="📂 video_center", style="Action.TButton", command=lambda: open_folder_manager("video_center", "วิดีโอระหว่างการตรวจ"))
        btn_center.grid(row=0, column=0, padx=3, sticky="ew")

        btn_ok = ttk.Button(btn_box, text="✅ video_ok", style="Action.TButton", command=lambda: open_folder_manager("video_ok", "วิดีโอผ่านเกณฑ์ (OK)"))
        btn_ok.grid(row=0, column=1, padx=3, sticky="ew")

        btn_ng = ttk.Button(btn_box, text="❌ video_ng", style="Action.TButton", command=lambda: open_folder_manager("video_ng", "วิดีโอไม่ผ่านเกณฑ์ (NG)"))
        btn_ng.grid(row=0, column=2, padx=3, sticky="ew")

        # ─── 5. รายละเอียดกล้องปัจจุบัน ───
        c_info = create_card_frame(scrollable_frame, "ℹ️ ข้อมูลกล้องปัจจุบัน")
        
        self.lbl_source = tk.Label(c_info, text="", fg=TEXT_MUTED, bg=PANEL_COLOR, font=("Segoe UI", 9))
        self.lbl_source.pack(anchor="w")
        self.lbl_pts = tk.Label(c_info, text="", fg=TEXT_MUTED, bg=PANEL_COLOR, font=("Segoe UI", 9))
        self.lbl_pts.pack(anchor="w", pady=(2, 0))

        def update_info_labels(*args):
            cam_id = self.cam_var.get()
            cam_data = self.config.get("cameras", {}).get(cam_id, {})
            self.lbl_source.config(text=f"Source: {cam_data.get('source', 'None')}")
            pts_count = len(cam_data.get("mark_points", []))
            self.lbl_pts.config(text=f"จำนวนจุดมาร์ก ROI ที่บันทึกไว้: {pts_count} จุด")

        self.cam_var.trace_add("write", update_info_labels)
        if camera_list:
            update_info_labels()

        # ─── 6. โซนการเลือกไฟล์โมเดล AI ───
        c_model = create_card_frame(scrollable_frame, "🤖 การตั้งค่าโมเดล AI (Model Settings)")

        model_grid = tk.Frame(c_model, bg=PANEL_COLOR)
        model_grid.pack(fill="x")
        model_grid.columnconfigure(1, weight=1)

        tk.Label(model_grid, text="ไฟล์โมเดลที่ใช้งาน:", fg=TEXT_MAIN, bg=PANEL_COLOR, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=5)

        self.available_models = self.scan_models()
        default_model_name = self.available_models[0] if self.available_models else ""
        if "model" in self.config and isinstance(self.config["model"], dict):
            for k, v in self.config["model"].items():
                if isinstance(v, dict) and "source" in v:
                    default_model_name = os.path.basename(v["source"])
                    break

        self.model_var = tk.StringVar(value=default_model_name)
        self.cb_model = ttk.Combobox(model_grid, textvariable=self.model_var, values=self.available_models, state="readonly")
        self.cb_model.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

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

        btn_browse = ttk.Button(model_grid, text="📁 ค้นหา...", style="Action.TButton", command=browse_model_file, width=8)
        btn_browse.grid(row=0, column=2, padx=(5, 0), pady=5)

        btn_go_train = tk.Button(
            c_model, 
            text="🏋️‍♂️ เปิดสตูดิโอเทรนโมเดล (Train AI Studio)", 
            command=lambda: self.open_train_studio(selected_model_file=self.model_var.get()),
            bg="#D97706", 
            fg="white",
            activebackground="#B45309",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=8,
            cursor="hand2"
        )
        # ✅ แก้ไข: แสดงผลปุ่มเปิดสตูดิโอเทรนโมเดล
        btn_go_train.pack(fill="x", pady=(10, 0))

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

            # 1. จัดการ Path ของโมเดลที่เลือก
            if self.custom_model_full_path and os.path.basename(self.custom_model_full_path) == selected_file:
                final_model_path = self.custom_model_full_path
            else:
                if os.path.exists(os.path.join("model", selected_file)):
                    final_model_path = os.path.join("model", selected_file)
                else:
                    final_model_path = selected_file

            if "model" not in self.config or not isinstance(self.config["model"], dict):
                self.config["model"] = {}

            # 2. อัปเดต Model_path_1 ให้เป็นโมเดลที่เลือกล่าสุด
            if "Model_path_1" not in self.config["model"]:
                self.config["model"]["Model_path_1"] = {}
            
            self.config["model"]["Model_path_1"]["source"] = final_model_path

            found_key = None
            for key, val in self.config["model"].items():
                if isinstance(val, dict) and os.path.basename(val.get("source", "")) == selected_file:
                    found_key = key
                    break

            if found_key and found_key != "Model_path_1":
                self.config["model"][found_key]["source"] = final_model_path

            # 3. บันทึกการตั้งค่ากล้อง (Save OK / Save NG)
            if cam_id:
                if "cameras" not in self.config: self.config["cameras"] = {}
                if cam_id not in self.config["cameras"]: self.config["cameras"][cam_id] = {}
                
                self.config["cameras"][cam_id]["save_ok"] = self.var_ok.get()
                self.config["cameras"][cam_id]["save_ng"] = self.var_ng.get()
                
            # 4. บันทึกลงไฟล์ YAML และส่ง Callback
            if self.save_config():
                messagebox.showinfo("สำเร็จ", f"อัปเดตโมเดลเป็น: {selected_file}\nบันทึกข้อมูลเรียบร้อยแล้ว")
                if self.root:
                    self.root.destroy()
                self.root = None
                
                if on_close_callback:
                    on_close_callback(cam_id, self.config)

        btn_save = tk.Button(
            scrollable_frame, 
            text="💾 บันทึกและปิดหน้าต่าง (Save & Close)", 
            command=save_and_close,
            bg=PRIMARY_BLUE,
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            pady=10,
            cursor="hand2"
        )
        btn_save.pack(fill="x", padx=20, pady=(10, 25))

        # ✅ แก้ไข: ปิดวงเล็บ mainloop
        self.root.mainloop()


# ─── ตัวอย่างการเรียกใช้งาน ───
if __name__ == "__main__":
    app = ConfigGUI()
    app.open_settings()