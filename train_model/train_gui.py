import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import yaml
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

class TrainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pose Model Training Studio")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # โหลดค่าคอนฟิกเพื่อเอา Path มาแสดงผลและใช้งาน
        self.config_path = r"setting\config.yaml"
        self.config = self.load_config()
        
        self.setup_ui()

    def load_config(self):
        """โหลดไฟล์ config เพื่อดึง Path ปัจจุบัน"""
        if not os.path.exists(self.config_path):
            messagebox.showerror("Error", f"ไม่พบไฟล์คอนฟิกที่: {self.config_path}")
            return {"global": {"dataset_path": "dataset.csv", "model_path": "pose_classifier_1.pkl"}}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def setup_ui(self):
        """สร้างหน้าต่าง UI สำหรับโหมดเทรนโดยเฉพาะ"""
        # ส่วนหัวข้อ
        header_label = tk.Label(self.root, text="🏋️‍♂️ AI Pose Training Studio", font=("Helvetica", 14, "bold"))
        header_label.pack(pady=15)

        # กรอบแสดงรายละเอียด Path ปัจจุบัน
        info_frame = tk.LabelFrame(self.root, text=" สถาะนะไฟล์เชื่อมต่อปัจจุบัน ", font=("Helvetica", 9, "bold"), padx=10, pady=10)
        info_frame.pack(fill="x", padx=20, pady=5)

        dataset_path = self.config["global"]["dataset_path"]
        model_path = self.config["global"]["model_path"]

        tk.Label(info_frame, text=f"📊 Dataset: {os.path.basename(dataset_path)}", fg="blue").pack(anchor="w")
        tk.Label(info_frame, text=f"🤖 Model Output: {os.path.basename(model_path)}", fg="green").pack(anchor="w")

        # ส่วนแสดง Progress หน่วงเวลา (ตอนเทรนจะหมุนๆ วิ่งๆ)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        self.progress.pack(pady=20)

        # ข้อความสถานะด้านล่างโปรแกรม
        self.status_lbl = tk.Label(self.root, text="🔴 Ready to Train", font=("Helvetica", 10), fg="gray")
        self.status_lbl.pack(pady=5)

        # ปุ่มกดเริ่มกระบวนการเทรน
        self.btn_train = tk.Button(
            self.root, 
            text="🚀 เริ่มเทรนโมเดลใหม่ (Start Training)", 
            command=self.start_training_thread,
            bg="#2ecc71", 
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=5
        )
        self.btn_train.pack(pady=10)

    def start_training_thread(self):
        """สั่งเริ่ม Thread สำหรับเทรน เพื่อไม่ให้หน้าต่าง Windows ขึ้น Not Responding"""
        self.btn_train.config(state=tk.DISABLED, bg="#95a5a6", text="⏳ กำลังประมวลผล...")
        self.status_lbl.config(text="⚙️ กำลังอ่านข้อมูลและเทรนโมเดลหลังบ้าน...", fg="#d35400")
        self.progress.start(10) # ให้แอนิเมชันแถบโหลดวิ่ง

        # แยกทำงานไปไว้หลังบ้าน
        t = threading.Thread(target=self.train_process, daemon=True)
        t.start()

    def train_process(self):
        """ตรรกะหลังบ้านสำหรับการประมวลผลโมเดล AI"""
        try:
            dataset_path = self.config["global"]["dataset_path"]
            model_output_path = self.config["global"]["model_path"]

            if not os.path.exists(dataset_path):
                self.root.after(0, lambda: messagebox.showerror("Error", f"❌ ไม่พบไฟล์ Dataset ที่พิกัด:\n{dataset_path}"))
                return

            # 1. โหลดและจัดการข้อมูล
            df = pd.read_csv(dataset_path)
            X = df.drop(columns=['label'])
            y = df['label']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # 2. เทรนโมเดล
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train, y_train)

            # 3. คำนวณความแม่นยำ
            y_pred = clf.predict(X_test)
            acc_score = accuracy_score(y_test, y_pred) * 100

            # 4. บันทึกผลลัพธ์ไฟล์ pkl ทับที่เดิมตามคอนฟิก
            joblib.dump(clf, model_output_path)
            abs_path = os.path.abspath(model_output_path)

            # 5. แจ้งเตือนเมื่อจบขั้นตอนสำเร็จ (ส่งสัญญานกลับเข้า GUI หน้าต่างหลัก)
            self.root.after(0, lambda: self.training_success(acc_score, abs_path))

        except Exception as e:
            self.root.after(0, lambda: self.training_failed(str(e)))

    def training_success(self, accuracy, path):
        """เมื่อเทรนสำเร็จ คืนค่า UI และโชว์ Message Box"""
        self.progress.stop()
        self.btn_train.config(state=tk.NORMAL, bg="#2ecc71", text="🚀 เริ่มเทรนโมเดลใหม่ (Start Training)")
        self.status_lbl.config(text="🟢 Train Success!", fg="green")
        
        messagebox.showinfo(
            "Train Status", 
            f"🎉 Train Success!\n\n"
            f"🎯 Accuracy: {accuracy:.2f}%\n"
            f"📂 PATH: {path}"
        )

    def training_failed(self, error_msg):
        """เมื่อเทรนล้มเหลว คืนค่า UI และแจ้งเตือนข้อผิดพลาด"""
        self.progress.stop()
        self.btn_train.config(state=tk.NORMAL, bg="#2ecc71", text="🚀 เริ่มเทรนโมเดลใหม่ (Start Training)")
        self.status_lbl.config(text="❌ Train Failed", fg="red")
        messagebox.showerror("Train Error", f"เกิดข้อผิดพลาดระหว่างเทรน:\n{error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrainGUI(root)
    root.mainloop()