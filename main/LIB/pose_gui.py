import tkinter as tk
from tkinter import ttk
import yaml

class CameraSelectorGUI:
    def __init__(self, master, config_path="setting/config.yml"):
        self.master = master
        self.master.title("Camera Selector")

        # โหลด config.yml
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # ดึงข้อมูลกล้องทั้งหมด
        self.cameras = self.config["cameras"]

        # Label
        tk.Label(master, text="เลือกกล้องที่ต้องการ:").pack(pady=10)

        # Combobox สำหรับเลือกกล้อง
        self.camera_names = list(self.cameras.keys())
        self.combo = ttk.Combobox(master, values=self.camera_names, state="readonly")
        self.combo.pack(pady=5)
        self.combo.current(0)

        # ปุ่มยืนยัน
        tk.Button(master, text="เลือกกล้อง", command=self.select_camera).pack(pady=10)

        # แสดงจำนวนกล้องทั้งหมด
        tk.Label(master, text=f"จำนวนกล้องทั้งหมด: {len(self.camera_names)}").pack(pady=5)

        # Label สำหรับแสดงผลลัพธ์
        self.result_label = tk.Label(master, text="")
        self.result_label.pack(pady=10)

    def select_camera(self):
        selected = self.combo.get()
        camera_info = self.cameras[selected]
        self.result_label.config(
            text=f"คุณเลือก {selected}\nSource: {camera_info['source']}\nEnabled: {camera_info['enabled']}"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraSelectorGUI(root)
    root.mainloop()
