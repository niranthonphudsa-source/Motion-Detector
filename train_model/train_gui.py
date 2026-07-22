import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import joblib
import yaml
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

class TrainGUI:
    def __init__(self, root=None, config_path=r"setting\config.yaml"):
        if root is None:
            self.root = tk.Tk()
            self.is_standalone = True
        else:
            self.root = root
            self.is_standalone = False

        self.config_path = config_path
        self.config = self.load_config()

        self.setup_ui()

    def load_config(self):
        """โหลดค่าตั้งต้นจาก config.yaml"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ ไม่สามารถอ่านไฟล์ Config ได้: {e}")
            return {"global": {"dataset_path": "dataset.csv"}}

    def browse_dataset_file(self):
        """ฟังก์ชันเปิด File Dialog สำหรับเลือกไฟล์ Dataset (CSV)"""
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ Dataset",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            norm_path = os.path.normpath(file_path)
            self.var_dataset.set(norm_path)

    def setup_ui(self):
        # ─── 🎨 โทนสีหลัก (White & Blue Theme) ───
        BG_COLOR = "#F8FAFC"
        PANEL_COLOR = "#FFFFFF"
        BORDER_COLOR = "#E2E8F0"
        TEXT_MAIN = "#0F172A"
        TEXT_MUTED = "#64748B"
        PRIMARY_BLUE = "#2563EB"
        TITLE_BLUE = "#1E3A8A"
        ACCENT_ORANGE = "#D97706"

        self.root.title("AI Pose Model Training Studio")
        self.root.geometry("750x850")
        self.root.minsize(600, 700)
        self.root.resizable(True, True)
        self.root.configure(bg=BG_COLOR)

        try:
            self.root.iconbitmap(r"main\Logo\atc_logo.png")
        except Exception:
            pass

        # ─── Scrollable Container ───
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

        try:
            self.logo_icon = tk.PhotoImage(file=r"main\Logo\atc_logo.png").subsample(2, 2)
            lbl_logo = tk.Label(header_frame, image=self.logo_icon, bg=BG_COLOR)
            lbl_logo.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด Logo ได้: {e}")

        title_box = tk.Frame(header_frame, bg=BG_COLOR)
        title_box.pack(side="left", fill="x", expand=True)

        lbl_title = tk.Label(title_box, text="Model Training Studio", font=("Segoe UI", 16, "bold"), fg=TITLE_BLUE, bg=BG_COLOR)
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(title_box, text="Random Forest Classifier Training & Evaluation", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_COLOR)
        lbl_sub.pack(anchor="w")

        # ฟังก์ชันสร้าง Card Frame
        def create_card_frame(parent, title_text):
            card = tk.Frame(parent, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", padx=20, pady=8)
            
            top_bar = tk.Frame(card, bg=PRIMARY_BLUE, height=3)
            top_bar.pack(fill="x", side="top")
            
            content = tk.Frame(card, bg=PANEL_COLOR, padx=15, pady=12)
            content.pack(fill="x", expand=True)
            
            tk.Label(content, text=title_text, font=("Segoe UI", 10, "bold"), fg=TITLE_BLUE, bg=PANEL_COLOR).pack(anchor="w", pady=(0, 8))
            return content

        # ─── 2. โซนพาธไฟล์ Dataset และ Output Model ───
        c_config = create_card_frame(scrollable_frame, "📁 การตั้งค่าแหล่งข้อมูลและไฟล์ผลลัพธ์")

        grid_cfg = tk.Frame(c_config, bg=PANEL_COLOR)
        grid_cfg.pack(fill="x")
        grid_cfg.columnconfigure(1, weight=1) # ให้ช่อง Entry ขยายเต็มความกว้าง

        # 2.1 Dataset Path (พร้อมปุ่มค้นหา)
        tk.Label(grid_cfg, text="Dataset Path (CSV):", fg=TEXT_MAIN, bg=PANEL_COLOR, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        default_ds = self.config.get("global", {}).get("dataset_path", "dataset.csv")
        self.var_dataset = tk.StringVar(value=default_ds)
        
        entry_ds = tk.Entry(grid_cfg, textvariable=self.var_dataset, font=("Segoe UI", 9), bg="#F8FAFC", bd=1, relief="solid")
        entry_ds.grid(row=0, column=1, padx=(10, 5), pady=5, sticky="ew")

        # ✅ ปุ่มกด Browse สำหรับเลือกไฟล์ CSV (ใส่ไว้ใน Grid แถวเดียวกัน)
        btn_browse = tk.Button(
            grid_cfg,
            text="📁 ค้นหา...",
            command=self.browse_dataset_file,
            bg=PRIMARY_BLUE,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2"
        )
        btn_browse.grid(row=0, column=2, padx=(0, 0), pady=5)

        # 2.2 Model Save Target Name
        tk.Label(grid_cfg, text="Save Model Name:", fg=TEXT_MAIN, bg=PANEL_COLOR, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        
        self.var_model_name = tk.StringVar(value="pose_classifier_1.pkl")
        entry_model = tk.Entry(grid_cfg, textvariable=self.var_model_name, font=("Segoe UI", 9), bg="#F8FAFC", bd=1, relief="solid")
        entry_model.grid(row=1, column=1, columnspan=2, padx=(10, 0), pady=5, sticky="ew")

        # ─── 3. โซนควบคุมการเทรนและ Progress Bar ───
        c_train = create_card_frame(scrollable_frame, "⚙️ สถานะและการประมวลผล (Training Control)")

        self.progress = ttk.Progressbar(c_train, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x", pady=(5, 10))

        self.lbl_status = tk.Label(c_train, text="🔴 พร้อมทำการเทรนโมเดล", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=PANEL_COLOR)
        self.lbl_status.pack(pady=2)

        self.btn_start = tk.Button(
            c_train,
            text="🚀 เริ่มการเทรนโมเดล (Start Train)",
            command=self.start_training_thread,
            bg=ACCENT_ORANGE,
            fg="white",
            activebackground="#B45309",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            pady=8,
            cursor="hand2"
        )
        self.btn_start.pack(fill="x", pady=(10, 5))

        # ─── 4. โซนแสดงรายงานผลลัพธ์ (Classification Report) ───
        c_result = create_card_frame(scrollable_frame, "📊 รายงานผลการทดสอบโมเดล (Training Report)")

        self.lbl_accuracy = tk.Label(c_result, text="Accuracy: - %", font=("Segoe UI", 12, "bold"), fg="#059669", bg=PANEL_COLOR)
        self.lbl_accuracy.pack(anchor="w", pady=(0, 5))

        report_frame = tk.Frame(c_result, bg=PANEL_COLOR)
        report_frame.pack(fill="both", expand=True)

        self.txt_report = tk.Text(
            report_frame, 
            height=12, 
            font=("Consolas", 9), 
            bg="#0F172A", 
            fg="#F8FAFC", 
            bd=0, 
            padx=10, 
            pady=10
        )
        report_scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.txt_report.yview)
        self.txt_report.configure(yscrollcommand=report_scrollbar.set)

        self.txt_report.pack(side="left", fill="both", expand=True)
        report_scrollbar.pack(side="right", fill="y")
        self.txt_report.insert("1.0", "กดปุ่ม 'เริ่มการเทรนโมเดล' เพื่อเริ่มต้นประมวลผล...")
        self.txt_report.config(state="disabled")

        if self.is_standalone:
            self.root.mainloop()

    def start_training_thread(self):
        """เริ่ม Thread แยกต่างหาก เพื่อไม่ให้ GUI ค้าง"""
        self.btn_start.config(state=tk.DISABLED, text="⏳ กำลังประมวลผล...")
        self.lbl_status.config(text="⚙️ กำลังอ่านข้อมูลและสร้างโมเดล Random Forest...", fg="#D97706")
        self.progress.start(10)

        t = threading.Thread(target=self.run_training_process, daemon=True)
        t.start()

    def run_training_process(self):
        """ลอจิกการเทรนโมเดล AI ตามสคริปต์หลัก"""
        try:
            dataset_path = self.var_dataset.get()
            model_save_name = self.var_model_name.get()

            if not os.path.exists(dataset_path):
                raise FileNotFoundError(f"ไม่พบไฟล์ Dataset: {dataset_path}")

            # 1. โหลดข้อมูลจาก CSV
            df = pd.read_csv(dataset_path)

            # 2. แยก X และ y
            X = df.drop(columns=['label'])
            y = df['label']

            # 3. แบ่งข้อมูลเป็น Train/Test (80/20)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # 4. เทรนโมเดล
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train, y_train)

            # 5. ประเมินผล
            y_pred = clf.predict(X_test)
            acc = accuracy_score(y_test, y_pred) * 100
            report = classification_report(y_test, y_pred)

            # 6. บันทึกโมเดล
            joblib.dump(clf, model_save_name)

            self.root.after(0, lambda: self.on_training_success(acc, report, model_save_name))

        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: self.on_training_failed(err_msg))

    def on_training_success(self, acc, report, model_name):
        """ทำงานเมื่อเทรนสำเร็จ"""
        self.progress.stop()
        self.btn_start.config(state=tk.NORMAL, text="🚀 เริ่มการเทรนโมเดล (Start Train)")
        self.lbl_status.config(text=f"🟢 เทรนสำเร็จ! เซฟโมเดลไว้ที่ '{model_name}' เรียบร้อย", fg="#059669")
        self.lbl_accuracy.config(text=f"Accuracy: {acc:.2f}%")

        self.txt_report.config(state="normal")
        self.txt_report.delete("1.0", tk.END)
        self.txt_report.insert("1.0", report)
        self.txt_report.config(state="disabled")

        messagebox.showinfo("Success", f"🎉 เซฟโมเดล '{model_name}' เรียบร้อย!\n🎯 Accuracy: {acc:.2f}%")

    def on_training_failed(self, error_message):
        """ทำงานเมื่อเกิดข้อผิดพลาด"""
        self.progress.stop()
        self.btn_start.config(state=tk.NORMAL, text="🚀 เริ่มการเทรนโมเดล (Start Train)")
        self.lbl_status.config(text="❌ เกิดข้อผิดพลาดขณะเทรนโมเดล", fg="#DC2626")

        messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการเทรนโมเดล:\n{error_message}")


if __name__ == "__main__":
    app = TrainGUI()