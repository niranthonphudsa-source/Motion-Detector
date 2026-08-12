import yaml
import tkinter as tk

from tkinter import ttk, messagebox
# from LIB.config_loader_start import AppConfig

class ConfigEditorGui:

    def __init__(self, master, config_path=r"setting\config.yml"):
        self.master = master
        self.master.title("Config Yaml")
        self.config_path = config_path
        self.cameras = None
        self.name_cam = None
        self.source_cam = None
        self.type_cam = None

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)


        self.build_camera()

            
        if self.config and "cameras" in self.config:
            self.cameras = self.config["cameras"] 
        
            #combobox
            tk.Label(master, text="select camera").pack(pady=5)
            self.camera_name = list(self.cameras.keys())
            self.combo = ttk.Combobox(master, values=self.camera_name, state="readonly")
            self.combo.pack(pady=5)
            self.combo.bind("<<ComboboxSelected>>", self.loadCameras)

            self.entries = {}
            self.frome_frame = tk.Frame(master)
            self.frome_frame.pack(pady=10)

            tk.Button(master, text="Save Config", command=self.save_config).pack(pady=10)

        else:
            self.cameras = {}
            self.config = {"cameras": self.cameras}

    def build_camera(self):
        frame = tk.Frame(self.master)
        frame.pack(padx=10, pady=10)
        lb_name = tk.Label(frame, text="Name Camera")
        name_cam = tk.Entry(frame)
        lb_name.grid(row=0, column=0, padx=5, pady=5)
        name_cam.grid(row=0, column=1, padx=5, pady=5)

        lb_type = tk.Label(frame, text="Type Camera")
        type_cam = tk.Entry(frame)
        lb_type.grid(row=0, column=2, padx=5, pady=5)
        type_cam.grid(row=0, column=3, padx=5, pady=5)

        lb_source = tk.Label(frame, text="Source Camera")
        source_cam = tk.Entry(frame)
        lb_source.grid(row=2, column=0, padx=5, pady=5)
        source_cam.grid(row=2, column=1, padx=5, pady=5)

        lb_enable = tk.Label(frame, text="Enable true/false")
        enable_cam = tk.Entry(frame)
        lb_enable.grid(row=2, column=2, padx=5, pady=5)
        enable_cam.grid(row=2, column=3, padx=5, pady=5)

        lb_ng = tk.Label(frame, text="status ng true/false")
        ng_cam = tk.Entry(frame)
        lb_ng.grid(row=3, column=0, padx=5, pady=5)
        ng_cam.grid(row=3, column=1, padx=5, pady=5)

        lb_ok = tk.Label(frame, text="status ok true/false")
        ok_cam = tk.Entry(frame)
        lb_ok.grid(row=3, column=2, padx=5, pady=5)
        ok_cam.grid(row=3, column=3, padx=5, pady=5)

        
        tk.Label(frame, text="Config Display").grid(row=4, column=0,columnspan=4, padx=10, pady=10)
        lb_pos_x = tk.Label(frame, text="Position_X")
        lb_pos_x.grid(row=5, column=0, padx=5, pady=5)
        entry_pos_x = tk.Entry(frame)
        entry_pos_x.grid(row=5, column=1, padx=5, pady=5)

        lb_pos_y = tk.Label(frame, text="Position_Y")
        lb_pos_y.grid(row=5, column=2, padx=5, pady=5)
        entry_pos_y = tk.Entry(frame)
        entry_pos_y.grid(row=5, column=3, padx=5, pady=5)

        lb_size_x = tk.Label(frame, text="Size_X")
        lb_size_x.grid(row=6, column=0, padx=5, pady=5)
        entry_size_x = tk.Entry(frame)
        entry_size_x.grid(row=6, column=1, padx=5, pady=5)

        lb_size_y = tk.Label(frame, text="Size_Y")
        lb_size_y.grid(row=6, column=2, padx=5, pady=5)
        entry_size_y = tk.Entry(frame)
        entry_size_y.grid(row=6, column=3, padx=5, pady=5)

        def addCamera():
            c_name = name_cam.get()
            c_type = type_cam.get()
            c_source_val = source_cam.get()
            c_enable = enable_cam.get().lower() == "true"
            c_ng = ng_cam.get().lower() == "true"
            c_ok = ok_cam.get().lower() == "true"

            pos_x = int(entry_pos_x.get())
            pos_y = int(entry_pos_y.get())
            size_x = int(entry_size_x.get())
            size_y = int(entry_size_y.get())

            if not c_name:
                messagebox.showwarning("Warning", "Please Key Name Camera")
                return

            if c_source_val.isdigit():
                c_source = int(c_source_val)
            else:
                c_source = c_source_val

            self.cameras[c_name] = {
                "Display": {
                    "Position_x": pos_x,
                    "Position_y": pos_y,
                    "Size_x": size_x,
                    "Size_y": size_y
                },
                "Type": c_type,
                "enabled": c_enable,
                "save_ng": c_ng,
                "save_ok": c_ok,
                "source": c_source
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True)

            messagebox.showinfo("Success", f"Add {c_name} Success!")

        tk.Button(frame, text="Save Camera", command=addCamera).grid(columnspan=4, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditorGui(root)
    root.mainloop()