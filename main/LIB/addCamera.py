import os
import yaml
import tkinter as tk

from tkinter import ttk, messagebox


class ConfigEditorGui:
    def __init__(self, master, config_path=r"setting\config.yml"):
        self.master = master
        self.master.title("Camera Config Manager")
        self.master.geometry("900x620")
        self.master.minsize(620, 420)
        self.config_path = config_path

        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Card.TFrame", background="#f7f9fc")
        style.configure("TButton", padding=(10, 6))

        self.config = self._load_config()
        self.cameras = self.config.get("cameras", {})

        self.selected_camera_var = tk.StringVar()
        self.camera_fields = {}
        self.form_frame = None
        self.combo = None

        self.build_ui()
        self.refresh_camera_list()

    def _load_config(self):
        default_path = os.path.abspath(self.config_path)
        os.makedirs(os.path.dirname(default_path), exist_ok=True)

        if not os.path.exists(default_path):
            config = {"cameras": {}}
            with open(default_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
            return config

        with open(default_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            data = {}

        if "cameras" not in data or not isinstance(data["cameras"], dict):
            data["cameras"] = {}

        return data

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config, f, allow_unicode=True, sort_keys=False)

    def build_ui(self):
        main = ttk.Frame(self.master, padding=16)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Camera Configuration", style="Header.TLabel").pack(anchor="w")

        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="เลือกกล้อง:").pack(side="left", padx=(0, 8))
        self.combo = ttk.Combobox(top, textvariable=self.selected_camera_var, state="readonly", width=40)
        self.combo.pack(side="left", fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", self.on_select_camera)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(0, 12))

        ttk.Button(btn_frame, text="เพิ่มกล้อง", command=self.add_camera).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="บันทึกการแก้ไข", command=self.update_camera).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="ลบกล้อง", command=self.delete_camera).pack(side="left")

        card = ttk.Frame(main, padding=10)
        card.pack(fill="both", expand=True)

        canvas = tk.Canvas(card, height=450, highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.form_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.form_frame, anchor="nw", width=canvas.winfo_reqwidth())

        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=max(event.width, 760))

        canvas.bind("<Configure>", on_canvas_configure)
        self.form_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        self._build_fields()

    def _build_fields(self):
        for child in self.form_frame.winfo_children():
            child.destroy()

        fields = [
            ("ชื่อกล้อง", "name", "Entry"),
            ("Type", "type", "Combobox", ["LIVE_STREAM", "Video"]),
            ("Source / RTSP / URL", "source", "Entry"),
            ("IP / Device", "ip", "Entry"),
            ("Username", "username", "Entry"),
            ("Password", "password", "Entry"),
            ("Resolution Width", "width", "Entry"),
            ("Resolution Height", "height", "Entry"),
            ("FPS", "fps", "Entry"),
            ("Codec", "codec", "Entry"),
            ("Enabled", "enabled", "Combobox", ["true", "false"]),
            ("Save OK", "save_ok", "Combobox", ["true", "false"]),
            ("Save NG", "save_ng", "Combobox", ["true", "false"]),
            ("Save Data", "save_data", "Combobox", ["true", "false"]),
        ]

        for i, (label_text, key, field_type, *extra) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2

            ttk.Label(self.form_frame, text=label_text, width=18, justify="left").grid(
                row=row, column=col, sticky="w", padx=(10, 6), pady=8
            )

            if field_type == "Entry":
                entry = ttk.Entry(self.form_frame, width=38)
                entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=8)
                self.camera_fields[key] = entry
            elif field_type == "Combobox":
                values = extra[0]
                combo = ttk.Combobox(self.form_frame, values=values, state="readonly", width=35)
                combo.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=8)
                self.camera_fields[key] = combo

        self.form_frame.grid_columnconfigure(1, weight=1)
        self.form_frame.grid_columnconfigure(3, weight=1)
        self.form_frame.grid_columnconfigure(0, weight=0)

    def clear_form(self):
        for widget in self.camera_fields.values():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set("")

    def get_form_data(self):
        data = {
            "name": self.camera_fields["name"].get().strip(),
            "type": self.camera_fields["type"].get().strip(),
            "source": self.camera_fields["source"].get().strip(),
            "ip": self.camera_fields["ip"].get().strip(),
            "username": self.camera_fields["username"].get().strip(),
            "password": self.camera_fields["password"].get().strip(),
            "width": self.camera_fields["width"].get().strip(),
            "height": self.camera_fields["height"].get().strip(),
            "fps": self.camera_fields["fps"].get().strip(),
            "codec": self.camera_fields["codec"].get().strip(),
            "enabled": self.camera_fields["enabled"].get().strip().lower() == "true",
            "save_ok": self.camera_fields["save_ok"].get().strip().lower() == "true",
            "save_ng": self.camera_fields["save_ng"].get().strip().lower() == "true",
            "save_data": self.camera_fields["save_data"].get().strip().lower() == "true",
        }
        return data

    def set_form_data(self, camera_name):
        self.clear_form()
        if not camera_name or camera_name not in self.cameras:
            return

        cam = self.cameras[camera_name]

        self.camera_fields["name"].insert(0, camera_name)
        self.camera_fields["type"].set(cam.get("Type", "LIVE_STREAM"))
        self.camera_fields["source"].insert(0, str(cam.get("source", "")))
        self.camera_fields["ip"].insert(0, str(cam.get("ip", "")))
        self.camera_fields["username"].insert(0, str(cam.get("username", "")))
        self.camera_fields["password"].insert(0, str(cam.get("password", "")))

        display = cam.get("Display", {})
        self.camera_fields["width"].insert(0, str(display.get("Size_x", "")))
        self.camera_fields["height"].insert(0, str(display.get("Size_y", "")))
        self.camera_fields["fps"].insert(0, str(cam.get("fps", "")))
        self.camera_fields["codec"].insert(0, str(cam.get("codec", "")))

        self.camera_fields["enabled"].set("true" if cam.get("enabled") else "false")
        self.camera_fields["save_ok"].set("true" if cam.get("save_ok") else "false")
        self.camera_fields["save_ng"].set("true" if cam.get("save_ng") else "false")
        self.camera_fields["save_data"].set("true" if cam.get("save_data") else "false")

    def refresh_camera_list(self):
        names = list(self.cameras.keys())
        self.combo["values"] = names
        if names:
            self.combo.set(names[0])
            self.selected_camera_var.set(names[0])
            self.set_form_data(names[0])
        else:
            self.combo.set("")
            self.selected_camera_var.set("")
            self.clear_form()

    def on_select_camera(self, event=None):
        name = self.selected_camera_var.get()
        self.set_form_data(name)

    def _normalize_camera_payload(self, form_data, old_name=None):
        name = form_data["name"]
        width = form_data["width"]
        height = form_data["height"]

        if not name:
            raise ValueError("กรุณากรอกชื่อกล้อง")

        if width:
            try:
                width = int(width)
            except ValueError:
                width = None
        if height:
            try:
                height = int(height)
            except ValueError:
                height = None

        source_value = form_data["source"]
        if source_value.isdigit():
            try:
                source_value = int(source_value)
            except ValueError:
                pass

        payload = {
            "Display": {
                "Position_x": 0,
                "Position_y": 0,
                "Size_x": width if width is not None else 1920,
                "Size_y": height if height is not None else 1080,
            },
            "Type": form_data["type"] or "LIVE_STREAM",
            "enabled": bool(form_data["enabled"]),
            "save_ok": bool(form_data["save_ok"]),
            "save_ng": bool(form_data["save_ng"]),
            "save_data": bool(form_data["save_data"]),
            "source": source_value,
            "ip": form_data["ip"],
            "username": form_data["username"],
            "password": form_data["password"],
            "fps": form_data["fps"],
            "codec": form_data["codec"],
        }

        if old_name and old_name != name:
            self.cameras.pop(old_name, None)

        return name, payload

    def add_camera(self):
        try:
            form_data = self.get_form_data()
            name, payload = self._normalize_camera_payload(form_data)
            if name in self.cameras:
                messagebox.showwarning("Warning", f"ชื่อกล้อง {name} มีอยู่แล้ว กรุณาเลือกแก้ไขหรือเปลี่ยนชื่อใหม่")
                return
            self.cameras[name] = payload
            self.config["cameras"] = self.cameras
            self._save_config()
            self.refresh_camera_list()
            messagebox.showinfo("สำเร็จ", f"เพิ่มกล้อง {name} เรียบร้อยแล้ว")
        except ValueError as e:
            messagebox.showwarning("Warning", str(e))

    def update_camera(self):
        selected = self.selected_camera_var.get()
        if not selected:
            messagebox.showwarning("Warning", "กรุณาเลือกกล้องก่อน")
            return

        try:
            form_data = self.get_form_data()
            name, payload = self._normalize_camera_payload(form_data, old_name=selected)
            self.cameras[name] = payload
            self.config["cameras"] = self.cameras
            self._save_config()
            self.refresh_camera_list()
            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลกล้อง {name} เรียบร้อยแล้ว")
        except ValueError as e:
            messagebox.showwarning("Warning", str(e))

    def delete_camera(self):
        selected = self.selected_camera_var.get()
        if not selected:
            messagebox.showwarning("Warning", "กรุณาเลือกกล้องที่ต้องการลบ")
            return

        confirm = messagebox.askyesno("ยืนยัน", f"ต้องการลบกล้อง {selected} หรือไม่?")
        if not confirm:
            return

        self.cameras.pop(selected, None)
        self.config["cameras"] = self.cameras
        self._save_config()
        self.refresh_camera_list()
        messagebox.showinfo("สำเร็จ", f"ลบกล้อง {selected} เรียบร้อยแล้ว")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditorGui(root)
    root.mainloop()