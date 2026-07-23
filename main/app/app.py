import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import pyodbc
import data_viewer_gui as data_table
print(pyodbc.drivers())

# ==========================================
# 1. CLASS สำหรับจัดการ CONFIG (JSON)
# ==========================================
class ConfigManager:
    def __init__(self, filename="db_config.json"):
        self.filename = filename
        self.default_config = {
            "server": "localhost",
            "database": "master",
            "auth_type": "Windows Authentication", # หรือ "SQL Server Authentication"
            "username": "",
            "password": "",
            "driver": "ODBC Driver 17 for SQL Server"
        }

    def load_config(self):
        """โหลดค่า Config จากไฟล์ JSON ถ้าไม่มีจะใช้ค่า Default"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self.default_config
        return self.default_config

    def save_config(self, data):
        """บันทึกค่า Config ลงไฟล์ JSON"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

# ==========================================
# 2. CLASS สำหรับ GUI ตั้งค่าการเชื่อมต่อ SSMS
# ==========================================
class SSMSConnectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SSMS Database Connection Setup")
        self.root.geometry("460x450")
        self.root.resizable(False, False)
        self.conn = False
        # โหลด Config Manager
        self.config_mgr = ConfigManager()
        self.config_data = self.config_mgr.load_config()

        # กำหนดธีมสี
        self.BG_COLOR = "#F8FAFC"
        self.PANEL_COLOR = "#FFFFFF"
        self.TEXT_COLOR = "#1E293B"
        self.PRIMARY_COLOR = "#2563EB"

        self.root.configure(bg=self.BG_COLOR)

        self._build_ui()
        self._load_values_to_ui()
        self._toggle_auth_fields() # อัปเดตสถานะช่อง Username/Password

    def _build_ui(self):
        # Header Title
        tk.Label(
            self.root, 
            text="🗄️ SQL Server Connection", 
            font=("Segoe UI", 14, "bold"), 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=(15, 10))

        # Main Panel Box
        panel = tk.Frame(
            self.root, 
            bg=self.PANEL_COLOR, 
            highlightbackground="#E2E8F0", 
            highlightthickness=1,
            padx=15, 
            pady=15
        )
        panel.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        panel.columnconfigure(1, weight=1)

        # 1. Server Name
        tk.Label(panel, text="Server Name:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=0, column=0, sticky="w", pady=6)
        self.ent_server = ttk.Entry(panel)
        self.ent_server.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 2. Database Name
        tk.Label(panel, text="Database:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=1, column=0, sticky="w", pady=6)
        self.ent_database = ttk.Entry(panel)
        self.ent_database.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 3. Authentication Type
        tk.Label(panel, text="Authentication:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=2, column=0, sticky="w", pady=6)
        self.cmb_auth = ttk.Combobox(
            panel, 
            values=["Windows Authentication", "SQL Server Authentication"], 
            state="readonly"
        )
        self.cmb_auth.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.cmb_auth.bind("<<ComboboxSelected>>", lambda e: self._toggle_auth_fields())

        # 4. Username
        self.lbl_user = tk.Label(panel, text="Username:", font=("Segoe UI", 9), bg=self.PANEL_COLOR)
        self.lbl_user.grid(row=3, column=0, sticky="w", pady=6)
        self.ent_user = ttk.Entry(panel)
        self.ent_user.grid(row=3, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 5. Password
        self.lbl_pass = tk.Label(panel, text="Password:", font=("Segoe UI", 9), bg=self.PANEL_COLOR)
        self.lbl_pass.grid(row=4, column=0, sticky="w", pady=6)
        self.ent_pass = ttk.Entry(panel, show="•")
        self.ent_pass.grid(row=4, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 6. Driver
        tk.Label(panel, text="ODBC Driver:", font=("Segoe UI", 9), bg=self.PANEL_COLOR).grid(row=5, column=0, sticky="w", pady=6)
        self.cmb_driver = ttk.Combobox(
            panel, 
            values=[
                "ODBC Driver 17 for SQL Server", 
                "ODBC Driver 18 for SQL Server", 
                "SQL Server"
            ], 
            state="readonly"
        )
        self.cmb_driver.grid(row=5, column=1, sticky="ew", pady=6, padx=(10, 0))

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_test = ttk.Button(btn_frame, text="⚡ ทดสอบการเชื่อมต่อ", command=self._test_connection)
        self.btn_test.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.btn_save = ttk.Button(btn_frame, text="💾 บันทึก Config", command=self._save_config)
        self.btn_save.pack(side="right", padx=(5, 0), expand=True, fill="x")

    def _load_values_to_ui(self):
        """นำค่าจาก Config มาใส่ลงในช่องกรอกข้อมูล"""
        self.ent_server.insert(0, self.config_data.get("server", ""))
        self.ent_database.insert(0, self.config_data.get("database", ""))
        self.cmb_auth.set(self.config_data.get("auth_type", "Windows Authentication"))
        self.ent_user.insert(0, self.config_data.get("username", ""))
        self.ent_pass.insert(0, self.config_data.get("password", ""))
        self.cmb_driver.set(self.config_data.get("driver", "ODBC Driver 17 for SQL Server"))

    def _toggle_auth_fields(self):
        """เปิด-ปิดช่องกรอก Username/Password ตามโหมด Authentication"""
        if self.cmb_auth.get() == "Windows Authentication":
            self.ent_user.config(state="disabled")
            self.ent_pass.config(state="disabled")
        else:
            self.ent_user.config(state="normal")
            self.ent_pass.config(state="normal")

    def _get_connection_string(self):
        """สร้าง Connection String สำหรับ pyodbc"""
        server = self.ent_server.get().strip()
        database = self.ent_database.get().strip()
        driver = self.cmb_driver.get()

        if self.cmb_auth.get() == "Windows Authentication":
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        else:
            user = self.ent_user.get().strip()
            pwd = self.ent_pass.get().strip()
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={pwd};"

        # หากใช้ Driver 18 อาจต้องปิดการตรวจ Certificate ชั่วคราวกรณี Dev Local
        if "18" in driver:
            conn_str += "TrustServerCertificate=yes;"

        return conn_str

    def _test_connection(self):
        """ฟังก์ชันทดสอบเชื่อมต่อกับ SSMS/SQL Server"""
        conn_str = self._get_connection_string()
        try:
            # ตั้ง Timeout ไว้ 5 วินาทีป้องกันโปรแกรมค้าง
            
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            messagebox.showinfo("สำเร็จ", "✅ เชื่อมต่อกับ SQL Server เรียบร้อยแล้ว!")
            self.conn = True
        except Exception as e:
            messagebox.showerror("ล้มเหลว", f"❌ ไม่สามารถเชื่อมต่อได้:\n\n{str(e)}")

        # if self.conn:
        #     data_table.SSTableViewerGUI(root)
    def _save_config(self):
        """ฟังก์ชันบันทึกค่าลงไฟล์ db_config.json"""
        data = {
            "server": self.ent_server.get().strip(),
            "database": self.ent_database.get().strip(),
            "auth_type": self.cmb_auth.get(),
            "username": self.ent_user.get().strip(),
            "password": self.ent_pass.get().strip(),
            "driver": self.cmb_driver.get()
        }
        
        if self.config_mgr.save_config(data):
            messagebox.showinfo("บันทึกข้อมูล", "💾 บันทึกการตั้งค่าลง db_config.json เรียบร้อยแล้ว")
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถบันทึกไฟล์ Config ได้")


# ==========================================
# 3. RUN PROGRAM
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SSMSConnectGUI(root)
    root.mainloop()