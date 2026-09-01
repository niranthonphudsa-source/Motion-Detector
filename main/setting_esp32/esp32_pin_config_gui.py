import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import serial
import serial.tools.list_ports


class ESP32PinConfigGUI:

  def __init__(self, parent_or_root):

    
    # ถ้าส่ง parent มา ให้สร้างหน้าต่างแบบ Toplevel
    if isinstance(parent_or_root, tk.Tk):
      self.root = parent_or_root
    else:
      self.root = tk.Toplevel(parent_or_root)

    self.root.title("ESP32 Pin Configurator & IO Controller")
    self.root.geometry("750x680")
    self.root.minsize(700, 600)

    # Serial Object
    self.ser = None
    self.config_filename = os.path.join(os.path.dirname(__file__), "esp32_pin_config.json")

    # Default Pin Configuration (ขาสัญญาณเริ่มต้น)
    self.pins_config = {
        "PIN_OK": "2",  # ขาไฟ OK (เขียว)
        "PIN_NG": "4",  # ขาไฟ NG (แดง)
        "PIN_BUZZER": "5",  # ขา ลำโพง/Buzzer
    }

    # สี Theme หลัก
    self.BG_COLOR = "#F8FAFC"
    self.PANEL_BG = "#FFFFFF"
    self.PRIMARY_COLOR = "#2563EB"
    self.TEXT_COLOR = "#0F172A"

    self.root.configure(bg=self.BG_COLOR)
    self.load_config()

    # สร้าง UI Components
    self._build_header()
    self._build_serial_panel()
    self._build_pin_mapping_panel()
    self._build_control_test_panel()
    self._build_log_panel()

    self.refresh_com_ports()

  def _build_header(self):
    header = tk.Frame(self.root, bg=self.PRIMARY_COLOR, pady=12)
    header.pack(fill="x")
    tk.Label(
        header,
        text="⚙️ ESP32 GPIO & Serial Controller",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg=self.PRIMARY_COLOR,
    ).pack()

  def _build_serial_panel(self):
    frame = tk.LabelFrame(
        self.root,
        text="📡 1. การเชื่อมต่อ COM Port",
        font=("Segoe UI", 10, "bold"),
        bg=self.PANEL_BG,
        padx=10,
        pady=10,
    )
    frame.pack(fill="x", padx=15, pady=8)

    tk.Label(frame, text="COM Port:", bg=self.PANEL_BG).grid(
        row=0, column=0, sticky="w", padx=5
    )
    self.cb_ports = ttk.Combobox(frame, width=20, state="readonly")
    self.cb_ports.grid(row=0, column=1, padx=5)

    btn_refresh = ttk.Button(
        frame, text="🔄 Refresh", command=self.refresh_com_ports
    )
    btn_refresh.grid(row=0, column=2, padx=5)

    tk.Label(frame, text="Baud Rate:", bg=self.PANEL_BG).grid(
        row=0, column=3, sticky="w", padx=(15, 5)
    )
    self.cb_baud = ttk.Combobox(
        frame,
        values=["9600", "115200", "57600", "19200"],
        width=10,
        state="readonly",
    )
    self.cb_baud.set("115200")
    self.cb_baud.grid(row=0, column=4, padx=5)

    self.btn_connect = tk.Button(
        frame,
        text="🔌 Connect",
        command=self.toggle_connection,
        bg="#10B981",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=10,
    )
    self.btn_connect.grid(row=0, column=5, padx=(15, 5))

  def _build_pin_mapping_panel(self):
    frame = tk.LabelFrame(
        self.root,
        text="📌 2. ตั้งค่าการจับคู่ขา Output (ESP32 Pins Mapping)",
        font=("Segoe UI", 10, "bold"),
        bg=self.PANEL_BG,
        padx=10,
        pady=10,
    )
    frame.pack(fill="x", padx=15, pady=8)

    # Frame เก็บแถวของ Pin แบบ Dynamic
    self.pin_rows_frame = tk.Frame(frame, bg=self.PANEL_BG)
    self.pin_rows_frame.pack(fill="x", expand=True)

    self.pin_entries = {}
    self._render_pin_inputs()

    btn_box = tk.Frame(frame, bg=self.PANEL_BG)
    btn_box.pack(fill="x", pady=(10, 0))

    btn_add_pin = ttk.Button(
        btn_box, text="➕ เพิ่มขา Output ใหม่", command=self.add_custom_pin
    )
    btn_add_pin.pack(side="left")

    btn_save_pin = tk.Button(
        btn_box,
        text="💾 บันทึกการตั้งค่า Pin",
        command=self.save_pin_config,
        bg=self.PRIMARY_COLOR,
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=10,
    )
    btn_save_pin.pack(side="right")

  def _render_pin_inputs(self):
    for widget in self.pin_rows_frame.winfo_children():
      widget.destroy()

    self.pin_entries.clear()

    row = 0
    for key, pin_val in self.pins_config.items():
      lbl_name = tk.Label(
          self.pin_rows_frame,
          text=f"{key}:",
          bg=self.PANEL_BG,
          font=("Segoe UI", 9, "bold"),
      )
      lbl_name.grid(row=row, column=0, sticky="w", padx=5, pady=4)

      ent_val = ttk.Entry(self.pin_rows_frame, width=12)
      ent_val.insert(0, str(pin_val))
      ent_val.grid(row=row, column=1, padx=5, pady=4)
      self.pin_entries[key] = ent_val

      tk.Label(
          self.pin_rows_frame,
          text=f"(ESP32 GPIO Pin)",
          fg="#64748B",
          bg=self.PANEL_BG,
      ).grid(row=row, column=2, sticky="w", padx=5)
      row += 1

  def add_custom_pin(self):
    custom_name = f"PIN_EXTRA_{len(self.pins_config) - 2}"
    self.pins_config[custom_name] = "0"
    self._render_pin_inputs()

  def _build_control_test_panel(self):
    frame = tk.LabelFrame(
        self.root,
        text="🚨 3. ทดสอบส่งสัญญาณส่งค่า (Control & Test)",
        font=("Segoe UI", 10, "bold"),
        bg=self.PANEL_BG,
        padx=10,
        pady=10,
    )
    frame.pack(fill="x", padx=15, pady=8)

    btn_box = tk.Frame(frame, bg=self.PANEL_BG)
    btn_box.pack(fill="x")

    btn_ok = tk.Button(
        btn_box,
        text="✅ PASS / OK (ไฟเขียว)",
        command=lambda: self.send_command("CMD_OK"),
        bg="#10B981",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        pady=8,
        width=18,
    )
    btn_ok.pack(side="left", padx=5)

    btn_ng = tk.Button(
        btn_box,
        text="❌ FAIL / NG (ไฟแดง)",
        command=lambda: self.send_command("CMD_NG"),
        bg="#EF4444",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        pady=8,
        width=18,
    )
    btn_ng.pack(side="left", padx=5)

    # ปุ่มสำหรับสถานะมีคนอยู่ในพื้นที่ Check Start
    btn_person = tk.Button(
        btn_box,
        text="👤 Person In Zone (ลำโพงดัง)",
        command=lambda: self.send_command("CMD_CHECK_START"),
        bg="#F59E0B",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        pady=8,
        width=22,
    )
    btn_person.pack(side="left", padx=5)

    btn_reset = tk.Button(
        btn_box,
        text="🧹 Reset All",
        command=lambda: self.send_command("CMD_RESET"),
        bg="#64748B",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        pady=8,
        width=10,
    )
    btn_reset.pack(side="right", padx=5)

  def _build_log_panel(self):
    frame = tk.LabelFrame(
        self.root,
        text="📝 Live Serial Log",
        font=("Segoe UI", 10, "bold"),
        bg=self.PANEL_BG,
        padx=10,
        pady=5,
    )
    frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    self.txt_log = tk.Text(
        frame,
        height=8,
        bg="#0F172A",
        fg="#38BDF8",
        font=("Consolas", 9),
        state="disabled",
    )
    self.txt_log.pack(fill="both", expand=True)

  def log(self, message):
    self.txt_log.config(state="normal")
    self.txt_log.insert("end", f"{message}\n")
    self.txt_log.see("end")
    self.txt_log.config(state="disabled")

  def refresh_com_ports(self):
    ports = [port.device for port in serial.tools.list_ports.comports()]
    self.cb_ports["values"] = ports
    if ports:
      self.cb_ports.current(0)
      self.log(f"พบพอร์ตใช้งาน: {', '.join(ports)}")
    else:
      self.cb_ports.set("")
      self.log("⚠️ ไม่พบพอร์ต COM ที่เชื่อมต่ออยู่")

  def toggle_connection(self):
    if self.ser and self.ser.is_open:
      self.ser.close()
      self.ser = None
      self.btn_connect.config(text="🔌 Connect", bg="#10B981")
      self.log("ตัดการเชื่อมต่อ Serial Port แล้ว")
    else:
      port = self.cb_ports.get()
      baud = self.cb_baud.get()
      if not port:
        messagebox.showerror("Error", "กรุณาเลือก COM Port ก่อนครับ")
        return
      try:
        self.ser = serial.Serial(port, int(baud), timeout=1)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.btn_connect.config(text="🛑 Disconnect", bg="#EF4444")
        self.log(f"✅ เชื่อมต่อสำเร็จที่ {port} (Baud: {baud})")

        # บันทึกพอร์ตและ baud ลงไฟล์ config เพื่อให้โปรแกรมหลักใช้ได้
        self.save_runtime_port_config(port, int(baud))

        # ส่งโปรโตคอลตั้งค่า Pin ทันทีเมื่อต่อพอร์ตสำเร็จ
        self.send_pin_setup_to_esp32()
        self.send_raw("CONNECT_DETECT\n")
      except Exception as e:
        messagebox.showerror("Connection Error", f"ไม่สามารถเชื่อมต่อได้: {e}")

  def save_runtime_port_config(self, port, baud):
    config_data = {"PORT": port, "BAUD": baud}
    config_data.update(self.pins_config)
    try:
      with open(self.config_filename, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
    except Exception:
      pass

  def save_pin_config(self):
    for key, entry in self.pin_entries.items():
      self.pins_config[key] = entry.get().strip()

    try:
      config_data = {"PORT": self.cb_ports.get(), "BAUD": int(self.cb_baud.get())}
      config_data.update(self.pins_config)
      with open(self.config_filename, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
      self.log("💾 บันทึกค่า Pin ลงไฟล์เรียบร้อยแล้ว")
      messagebox.showinfo("Success", "บันทึกการตั้งค่า Pin เรียบร้อยแล้ว")

      # ส่งโปรโตคอลตั้งค่า Pin ใหม่ไปยัง ESP32
      if self.ser and self.ser.is_open:
        self.send_pin_setup_to_esp32()
    except Exception as e:
      messagebox.showerror("Save Error", f"ไม่สามารถเซฟไฟล์ได้: {e}")

  def load_config(self):
    if os.path.exists(self.config_filename):
      try:
        with open(self.config_filename, "r", encoding="utf-8") as f:
          data = json.load(f)
        if "PORT" in data:
          self.cb_ports = None
        for key, value in data.items():
          if key in {"PORT", "BAUD", "port", "baud", "baudrate"}:
            continue
          self.pins_config[key] = str(value)
      except Exception:
        pass

  def send_pin_setup_to_esp32(self):
    """ส่ง String สำหรับคอนฟิก Pin ให้ ESP32 ทราบเมื่อเชื่อมต่อ"""
    # ตัวอย่างรูปแบบแพ็กเกจ: CONFIG:PIN_OK=2,PIN_NG=4,PIN_BUZZER=5
    pin_str_list = [f"{k}={v}" for k, v in self.pins_config.items()]
    payload = f"CONFIG:{','.join(pin_str_list)}\n"
    self.send_raw(payload)

  def send_command(self, cmd_type):
    """ส่งคำสั่งเปลี่ยนสถานะการทำงาน"""
    if not self.ser or not self.ser.is_open:
      messagebox.showwarning(
          "Warning", "กรุณาเชื่อมต่อ COM Port ก่อนส่งสัญญาณ!"
      )
      return

    # รูปแบบคำสั่งส่งออก เช่น "CMD_OK\n", "CMD_NG\n", "CMD_CHECK_START\n"
    payload = f"{cmd_type}\n"
    self.send_raw(payload)

  def send_raw(self, payload):
    try:
      self.ser.write(payload.encode("utf-8"))
      self.log(f"📤 Sent: {payload.strip()}")
    except Exception as e:
      self.log(f"❌ Error sending data: {e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = ESP32PinConfigGUI(root)
  root.mainloop()