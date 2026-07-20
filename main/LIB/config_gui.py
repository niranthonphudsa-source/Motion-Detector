import tkinter as tk
from tkinter import ttk, messagebox
import yaml

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

    def open_settings(self, on_close_callback=None):
        """เปิดหน้าต่าง GUI สำหรับการ Setting เบื้องหลัง"""
        # ป้องกันการเปิดซ้ำ
        if self.root is not None and tk.Toplevel.winfo_exists(self.root):
            self.root.lift()
            return

        self.root = tk.Tk()
        self.root.title("System Configuration")
        self.root.geometry("450x400")
        self.root.resizable(False, False)

        # ─── โซนเลือกกล้อง ───
        frame_cam = ttk.LabelFrame(self.root, text=" การจัดการกล้อง ", padding=10)
        frame_cam.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_cam, text="เลือกกล้องที่ต้องการตั้งค่า:").grid(row=0, column=0, sticky="w", pady=5)
        
        camera_list = list(self.config.get("cameras", {}).keys())
        self.cam_var = tk.StringVar()
        self.cb_camera = ttk.Combobox(frame_cam, textvariable=self.cam_var, values=camera_list, state="readonly")
        self.cb_camera.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        if camera_list:
            self.cb_camera.current(0)

        # ─── โซนตั้งค่าตัวเลือกการเซฟไฟล์ ───
        frame_save = ttk.LabelFrame(self.root, text=" การบันทึกวิดีโอ (Video Output) ", padding=10)
        frame_save.pack(fill="x", padx=15, pady=10)

        self.var_ok = tk.BooleanVar()
        self.var_ng = tk.BooleanVar()

        self.chk_ok = ttk.Checkbutton(frame_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น OK (video_ok)", variable=self.var_ok)
        self.chk_ok.pack(anchor="w", pady=5)

        self.chk_ng = ttk.Checkbutton(frame_save, text="บันทึกวิดีโอเมื่อผลลัพธ์เป็น NG (video_ng)", variable=self.var_ng)
        self.chk_ng.pack(anchor="w", pady=5)

        # ฟังก์ชันเมื่อเปลี่ยนชื่อกล้องใน Combobox ให้ดึงค่าตัวเลือกเดิมขึ้นมาโชว์
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

        # ─── ปุ่มบันทึกข้อมูล ───
        def save_and_close():
            cam_id = self.cam_var.get()
            if cam_id:
                if "cameras" not in self.config: self.config["cameras"] = {}
                if cam_id not in self.config["cameras"]: self.config["cameras"][cam_id] = {}
                
                self.config["cameras"][cam_id]["save_ok"] = self.var_ok.get()
                self.config["cameras"][cam_id]["save_ng"] = self.var_ng.get()
                
                if self.save_config():
                    messagebox.showinfo("สำเร็จ", f"บันทึกการตั้งค่าของ {cam_id} เรียบร้อยแล้ว")
                    self.root.destroy()
                    if on_close_callback:
                        on_close_callback() # ส่งสัญญาณกลับไปอัปเดตตัวแปรใน Main script

        btn_save = ttk.Button(self.root, text="บันทึกและปิดหน้าต่าง", command=save_and_close)
        btn_save.pack(pady=20)

        self.root.mainloop()