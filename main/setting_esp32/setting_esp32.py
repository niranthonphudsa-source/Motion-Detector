import sys
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports
import serial

CONFIG_FILE = "hardware_config.json"

class PinConfigGUI:
    def __init__(self, on_save_callback=None):
        self.on_save_callback = on_save_callback
        self.root = tk.Tk()
        self.root.title("⚙️ Hardware & Pin Configuration")
        self.root.geometry("400x480")
        self.root.attributes("-topmost", True)

        # โหลด Config เดิมถ้ามี
        self.config_data = self.load_config()

        # สร้าง UI Component
        self._create_widgets()

    def _create_widgets(self):
        title = ttk.Label(self.root, text="🎛️ ตั้งค่าพอร์ตและ Pin สัญญาณ", font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill="both", expand=True)

        # --- 1. เลือก Serial Port & Baud Rate ---
        ttk.Label(main_frame, text="Serial Port:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        # ดึงรายชื่อ COM Port บนเครื่อง
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        if not available_ports:
            available_ports = ["COM1", "COM3", "COM4"] # Default fallback
            
        self.port_combo = ttk.Combobox(main_frame, values=available_ports, width=15)
        self.port_combo.set(self.config_data.get("port", available_ports[0]))
        self.port_combo.grid(row=0, column=1, sticky="e", pady=5)

        ttk.Label(main_frame, text="Baud Rate:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.baud_combo = ttk.Combobox(main_frame, values=["9600", "115200"], width=15)
        self.baud_combo.set(self.config_data.get("baudrate", "115200"))
        self.baud_combo.grid(row=1, column=1, sticky="e", pady=5)

        ttk.Separator(main_frame, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=15)

        # --- 2. ตั้งค่า GPIO Pins ---
        ttk.Label(main_frame, text="📍 กำหนดขา GPIO (Pin Assignment)", font=("Helvetica", 11, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        # Pin 1: Trigger / Sensor Pin
        ttk.Label(main_frame, text="Trigger / Sensor Pin:").grid(row=4, column=0, sticky="w", pady=5)
        self.trig_pin_entry = ttk.Entry(main_frame, width=10)
        self.trig_pin_entry.insert(0, str(self.config_data.get("trig_pin", 26)))
        self.trig_pin_entry.grid(row=4, column=1, sticky="e", pady=5)

        # Pin 2: Echo / Input Pin
        ttk.Label(main_frame, text="Echo / Input Pin:").grid(row=5, column=0, sticky="w", pady=5)
        self.echo_pin_entry = ttk.Entry(main_frame, width=10)
        self.echo_pin_entry.insert(0, str(self.config_data.get("echo_pin", 27)))
        self.echo_pin_entry.grid(row=5, column=1, sticky="e", pady=5)

        # Pin 3: Relay / Output Control Pin
        ttk.Label(main_frame, text="Relay / Control Pin:").grid(row=6, column=0, sticky="w", pady=5)
        self.relay_pin_entry = ttk.Entry(main_frame, width=10)
        self.relay_pin_entry.insert(0, str(self.config_data.get("relay_pin", 12)))
        self.relay_pin_entry.grid(row=6, column=1, sticky="e", pady=5)

        # --- 3. ปุ่ม Save & Test ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)

        save_btn = ttk.Button(btn_frame, text="💾 บันทึกการตั้งค่า", command=self.save_settings)
        save_btn.pack(side="left", padx=5)

    def load_config(self):
        """โหลดค่า Config จากไฟล์ JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"port": "COM3", "baudrate": 115200, "trig_pin": 26, "echo_pin": 27, "relay_pin": 12}

    def save_settings(self):
        """บันทึกการตั้งค่าลงไฟล์ และส่ง Callback ต่อไปยังสคริปต์หลัก"""
        try:
            new_config = {
                "port": self.port_combo.get(),
                "baudrate": int(self.baud_combo.get()),
                "trig_pin": int(self.trig_pin_entry.get()),
                "echo_pin": int(self.echo_pin_entry.get()),
                "relay_pin": int(self.relay_pin_entry.get())
            }

            # 1. เขียนลงไฟล์ json
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=4)

            # 2. เรียกใช้ Callback ถ้าเชื่อมต่อกับสคริปต์หลักไว้
            if self.on_save_callback:
                self.on_save_callback(new_config)

            messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่า Pin และ Port เรียบร้อยแล้ว!")
            self.root.destroy()

        except ValueError:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกเลข Pin และ Baud Rate เป็นตัวเลขเท่านั้น!")

    def run(self):
        self.root.mainloop()

# =========================================================
# 🚀 ทดสอบรันหน้าต่างตั้งค่า GUI แบบ Standalone
# =========================================================
if __name__ == "__main__":
    def my_callback(updated_config):
        print("🔄 [System Updated] ค่า Config ใหม่ถูกปรับใช้แล้ว:")
        print(updated_config)

    app = PinConfigGUI(on_save_callback=my_callback)
    app.run()