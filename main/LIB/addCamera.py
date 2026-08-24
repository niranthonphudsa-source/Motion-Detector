import os
import tkinter as tk
from tkinter import messagebox, ttk
import yaml


class ConfigEditorGui:

  def __init__(self, master, config_path=r"setting\config.yml"):
    self.master = master
    self.master.title("Camera Config Manager")
    self.master.geometry("820x540")
    self.master.resizable(False, False)

    self.config_path = config_path
    self.config = self.load_yaml()
    self.cameras = self.config.get("cameras", {})

    # 🎨 Palette โทน Dark Industrial / Tech UI
    self.BG_DARK = "#222831"  # พื้นหลังหลัก
    self.BG_PANEL = "#393E46"  # พื้นหลังการ์ด/เฟรม
    self.TEXT_COLOR = "#EEEEEE"  # ตัวหนังสือหลัก
    self.ACCENT_COLOR = "#00ADB5"  # ปุ่มไฮไลต์/จุดสำคัญ
    self.ACCENT_HOVER = "#008B92"  # Hover state
    self.INPUT_BG = "#2D3238"  # พื้นหลัง ช่องกรอกข้อความ

    self.master.configure(bg=self.BG_DARK)
    self.setup_styles()

    # ─── Main Container ───
    main_container = tk.Frame(self.master, bg=self.BG_DARK)
    main_container.pack(fill="both", expand=True, padx=15, pady=15)

    # หัวข้อใหญ่
    lbl_title = tk.Label(
        main_container,
        text="📷 Camera Configuration Editor",
        font=("Segoe UI", 14, "bold"),
        fg=self.ACCENT_COLOR,
        bg=self.BG_DARK,
    )
    lbl_title.pack(anchor="w", pady=(0, 10))

    # โครงสร้าง 2 คอลัมน์ (Left: Form Entry, Right: Selection & Controls)
    content_frame = tk.Frame(main_container, bg=self.BG_DARK)
    content_frame.pack(fill="both", expand=True)

    self.left_frame = tk.Frame(
        content_frame, bg=self.BG_PANEL, bd=1, relief="flat", padx=15, pady=15
    )
    self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

    self.right_frame = tk.Frame(
        content_frame, bg=self.BG_PANEL, bd=1, relief="flat", padx=15, pady=15
    )
    self.right_frame.pack(side="right", fill="both", expand=False, ipadx=10)

    # สร้าง UI Components
    self.build_left_form()
    self.build_right_controls()

  def setup_styles(self):
    """ตั้งค่าสไตล์สำหรับ TTK Components"""
    self.style = ttk.Style()
    self.style.theme_use("clam")

    # Style สำหรับ Combobox
    self.style.configure(
        "TCombobox",
        fieldbackground=self.INPUT_BG,
        background=self.BG_PANEL,
        foreground=self.TEXT_COLOR,
        darkcolor=self.BG_PANEL,
        lightcolor=self.BG_PANEL,
        insertcolor=self.TEXT_COLOR,
    )
    self.style.map(
        "TCombobox",
        fieldbackground=[("readonly", self.INPUT_BG)],
        selectbackground=[("readonly", self.INPUT_BG)],
        selectforeground=[("readonly", self.TEXT_COLOR)],
    )

  def load_yaml(self):
    """โหลดข้อมูลจากไฟล์ Config"""
    if os.path.exists(self.config_path):
      try:
        with open(self.config_path, "r", encoding="utf-8") as f:
          data = yaml.safe_load(f)
          return data if data else {"cameras": {}}
      except Exception as e:
        messagebox.showerror("Error", f"Failed to load config: {e}")
        return {"cameras": {}}
    return {"cameras": {}}

  def build_left_form(self):
    """สร้างส่วนฟอร์มป้อนข้อมูลกล้อง (ฝั่งซ้าย)"""
    lbl_section = tk.Label(
        self.left_frame,
        text="Camera Settings",
        font=("Segoe UI", 11, "bold"),
        fg=self.ACCENT_COLOR,
        bg=self.BG_PANEL,
    )
    lbl_section.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

    # Helper ในการสร้าง Label + Entry ให้สอดคล้องกัน
    def create_entry(parent, label_text, row, col):
      lbl = tk.Label(
          parent,
          text=label_text,
          font=("Segoe UI", 9),
          fg=self.TEXT_COLOR,
          bg=self.BG_PANEL,
          anchor="w",
      )
      lbl.grid(row=row, column=col, sticky="w", padx=5, pady=4)

      entry = tk.Entry(
          parent,
          bg=self.INPUT_BG,
          fg=self.TEXT_COLOR,
          insertbackground=self.TEXT_COLOR,
          relief="solid",
          bd=1,
          font=("Segoe UI", 9),
      )
      entry.grid(row=row + 1, column=col, sticky="ew", padx=5, pady=(0, 8))
      return entry

    self.left_frame.columnconfigure((0, 1, 2, 3), weight=1)

    # Row 1-2: Basic Info
    self.entry_name = create_entry(self.left_frame, "Camera Name ID", 1, 0)
    self.entry_type = create_entry(self.left_frame, "Type (e.g. RTSP)", 1, 1)
    self.entry_source = create_entry(
        self.left_frame, "Source (IP/ID)", 1, 2
    )
    self.entry_enable = create_entry(self.left_frame, "Enable (true/false)", 1, 3)

    # Row 3-4: Save Flags
    self.entry_ok = create_entry(self.left_frame, "Save OK (true/false)", 3, 0)
    self.entry_ng = create_entry(self.left_frame, "Save NG (true/false)", 3, 1)

    # Separator Line
    lbl_disp = tk.Label(
        self.left_frame,
        text="Display Coordinates & Size",
        font=("Segoe UI", 10, "bold"),
        fg=self.ACCENT_COLOR,
        bg=self.BG_PANEL,
    )
    lbl_disp.grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 5))

    # Row 6-7: Display Settings
    self.entry_pos_x = create_entry(self.left_frame, "Position X", 6, 0)
    self.entry_pos_y = create_entry(self.left_frame, "Position Y", 6, 1)
    self.entry_size_x = create_entry(self.left_frame, "Size X", 6, 2)
    self.entry_size_y = create_entry(self.left_frame, "Size Y", 6, 3)

    # Default values for quick setup
    self.set_default_entries()

  def build_right_controls(self):
    """สร้างส่วนการจัดการ เลือกแก้ไข และบันทึก (ฝั่งขวา)"""
    lbl_section = tk.Label(
        self.right_frame,
        text="Actions & Select",
        font=("Segoe UI", 11, "bold"),
        fg=self.ACCENT_COLOR,
        bg=self.BG_PANEL,
    )
    lbl_section.pack(anchor="w", pady=(0, 15))

    tk.Label(
        self.right_frame,
        text="Select Existing Camera:",
        font=("Segoe UI", 9),
        fg=self.TEXT_COLOR,
        bg=self.BG_PANEL,
    ).pack(anchor="w")

    self.camera_names = list(self.cameras.keys())
    self.combo = ttk.Combobox(
        self.right_frame,
        values=self.camera_names,
        state="readonly",
        width=22,
        style="TCombobox",
    )
    self.combo.pack(fill="x", pady=(5, 15))
    self.combo.bind("<<ComboboxSelected>>", self.load_camera_data)

    # Custom Action Buttons
    btn_save = tk.Button(
        self.right_frame,
        text="💾 Save / Update",
        font=("Segoe UI", 9, "bold"),
        bg=self.ACCENT_COLOR,
        fg="#FFFFFF",
        activebackground=self.ACCENT_HOVER,
        activeforeground="#FFFFFF",
        bd=0,
        cursor="hand2",
        command=self.save_camera_config,
    )
    btn_save.pack(fill="x", ipady=6, pady=(0, 8))

    btn_clear = tk.Button(
        self.right_frame,
        text="🧹 Clear Form",
        font=("Segoe UI", 9),
        bg="#525252",
        fg="#FFFFFF",
        activebackground="#3D3D3D",
        activeforeground="#FFFFFF",
        bd=0,
        cursor="hand2",
        command=self.clear_form,
    )
    btn_clear.pack(fill="x", ipady=5)

  def set_default_entries(self):
    """กำหนดค่าเริ่มต้นในช่องกรอก"""
    self.entry_enable.insert(0, "true")
    self.entry_ok.insert(0, "true")
    self.entry_ng.insert(0, "true")
    self.entry_pos_x.insert(0, "0")
    self.entry_pos_y.insert(0, "0")
    self.entry_size_x.insert(0, "640")
    self.entry_size_y.insert(0, "480")

  def clear_form(self):
    """ล้างข้อมูลออกจากช่องกรอก"""
    entries = [
        self.entry_name,
        self.entry_type,
        self.entry_source,
        self.entry_enable,
        self.entry_ok,
        self.entry_ng,
        self.entry_pos_x,
        self.entry_pos_y,
        self.entry_size_x,
        self.entry_size_y,
    ]
    for e in entries:
      e.delete(0, tk.END)
    self.set_default_entries()
    self.combo.set("")

  def load_camera_data(self, event=None):
    """ดึงข้อมูลของกล้องที่เลือกมาแสดงในฟอร์ม"""
    cam_id = self.combo.get()
    if cam_id in self.cameras:
      cam_data = self.cameras[cam_id]
      disp = cam_data.get("Display", {})

      self.clear_form()
      self.combo.set(cam_id)

      self.entry_name.insert(0, cam_id)
      self.entry_type.insert(0, str(cam_data.get("Type", "")))
      self.entry_source.insert(0, str(cam_data.get("source", "")))
      self.entry_enable.insert(0, str(cam_data.get("enabled", True)).lower())
      self.entry_ok.insert(0, str(cam_data.get("save_ok", True)).lower())
      self.entry_ng.insert(0, str(cam_data.get("save_ng", True)).lower())

      self.entry_pos_x.delete(0, tk.END)
      self.entry_pos_x.insert(0, str(disp.get("Position_x", 0)))
      self.entry_pos_y.delete(0, tk.END)
      self.entry_pos_y.insert(0, str(disp.get("Position_y", 0)))
      self.entry_size_x.delete(0, tk.END)
      self.entry_size_x.insert(0, str(disp.get("Size_x", 640)))
      self.entry_size_y.delete(0, tk.END)
      self.entry_size_y.insert(0, str(disp.get("Size_y", 480)))

  def save_camera_config(self):
    """บันทึกข้อมูลกล้องลงไฟล์ YAML"""
    c_name = self.entry_name.get().strip()

    if not c_name:
      messagebox.showwarning("Warning", "Please enter Camera Name ID!")
      return

    try:
      c_type = self.entry_type.get().strip()
      c_source_val = self.entry_source.get().strip()
      c_enable = self.entry_enable.get().strip().lower() == "true"
      c_ok = self.entry_ok.get().strip().lower() == "true"
      c_ng = self.entry_ng.get().strip().lower() == "true"

      pos_x = int(self.entry_pos_x.get().strip() or 0)
      pos_y = int(self.entry_pos_y.get().strip() or 0)
      size_x = int(self.entry_size_x.get().strip() or 640)
      size_y = int(self.entry_size_y.get().strip() or 480)

      c_source = (
          int(c_source_val) if c_source_val.isdigit() else c_source_val
      )

      # อัปเดต Dict
      if "cameras" not in self.config or not isinstance(
          self.config["cameras"], dict
      ):
        self.config["cameras"] = {}

      self.config["cameras"][c_name] = {
          "Display": {
              "Position_x": pos_x,
              "Position_y": pos_y,
              "Size_x": size_x,
              "Size_y": size_y,
          },
          "Type": c_type,
          "enabled": c_enable,
          "save_ng": c_ng,
          "save_ok": c_ok,
          "source": c_source,
      }

      # บันทึกลงไฟล์ YAML
      os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
      with open(self.config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            self.config, f, allow_unicode=True, default_flow_style=False
        )

      # อัปเดตรายชื่อใน Combobox
      self.cameras = self.config["cameras"]
      self.combo["values"] = list(self.cameras.keys())
      self.combo.set(c_name)

      messagebox.showinfo(
          "Success", f"Camera '{c_name}' saved successfully!"
      )

    except ValueError:
      messagebox.showerror(
          "Invalid Input",
          "Position and Size parameters must be numeric integers!",
      )
    except Exception as e:
      messagebox.showerror("Error", f"Failed to save YAML config: {e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = ConfigEditorGui(root)
  root.mainloop()