import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc

# ==========================================
# 1. CLASS จัดการ CONFIG (JSON)
# ==========================================
class ConfigManager:
    def __init__(self, filename="db_config.json"):
        self.filename = filename
        self.default_config = {
            "server": "localhost",
            "database": "master",
            "auth_type": "Windows Authentication",
            "username": "",
            "password": "",
            "driver": "ODBC Driver 17 for SQL Server"
        }

    def load_config(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self.default_config
        return self.default_config

    def save_config(self, data):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


# ==========================================
# 2. หน้าต่างแสดงตารางข้อมูล (TABLE VIEWER WINDOW)
# ==========================================
class TableViewerWindow(tk.Toplevel):
    def __init__(self, parent, config_data):
        super().__init__(parent)

        print(f"Parent: {parent} Config: {config_data}")
        self.title("📊 SQL Server Data Viewer")
        self.geometry("900x600")
        self.config_data = config_data

        self.BG_COLOR = "#F8FAFC"
        self.PANEL_COLOR = "#FFFFFF"
        self.PRIMARY_COLOR = "#1E3A8A"
        self.configure(bg=self.BG_COLOR)

        self._build_ui()
        self._load_tables_list()
        # if user_id and camera_id and status_pose:
        #     self.insert_data(user_id, camera_id, status_pose)

    def _get_connection(self):
        server = self.config_data.get("server")
        database = self.config_data.get("database")
        driver = self.config_data.get("driver", "ODBC Driver 17 for SQL Server")
        auth_type = self.config_data.get("auth_type")

        if auth_type == "Windows Authentication":
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        else:
            user = self.config_data.get("username")
            pwd = self.config_data.get("password")
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={pwd};"

        if "18" in driver:
            conn_str += "TrustServerCertificate=yes;"

        return pyodbc.connect(conn_str, timeout=5)

    def _build_ui(self):
        # Header / Controls
        top_frame = tk.Frame(self, bg=self.PANEL_COLOR, highlightbackground="#E2E8F0", highlightthickness=1)
        top_frame.pack(fill="x", padx=15, pady=15, ipady=5)

        tk.Label(
            top_frame, 
            text="📁 เลือกตาราง (Table):", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.PANEL_COLOR, 
            fg=self.PRIMARY_COLOR
        ).pack(side="left", padx=(15, 5), pady=10)

        self.cmb_tables = ttk.Combobox(top_frame, state="readonly", width=30, font=("Segoe UI", 9))
        self.cmb_tables.pack(side="left", padx=5, pady=10)

        self.btn_load = ttk.Button(top_frame, text="🔄 ดึงข้อมูล", command=self._fetch_table_data)
        self.btn_load.pack(side="left", padx=10, pady=10)

        self.lbl_row_count = tk.Label(top_frame, text="รายการทั้งหมด: 0 แถว", font=("Segoe UI", 9), bg=self.PANEL_COLOR, fg="#64748B")
        self.lbl_row_count.pack(side="right", padx=15, pady=10)

        # Treeview (Data Grid)
        table_frame = tk.Frame(self, bg=self.BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            table_frame, 
            yscrollcommand=scroll_y.set, 
            xscrollcommand=scroll_x.set,
            selectmode="extended"
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_tables_list(self):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            if tables:
                self.cmb_tables['values'] = tables
                self.cmb_tables.current(0)
                self._fetch_table_data() # ดึงข้อมูลตารางแรกมาแสดงทันที
            else:
                messagebox.showwarning("ข้อความ", "ไม่พบตารางข้อมูลใน Database นี้", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถดึงรายชื่อตารางได้:\n{str(e)}", parent=self)

    @classmethod
    def insert_data(self, config_data, user_id, camera_id, status_pose):
        conn = None

        try:
            # 2. แก้จุดที่เคยเขียนผิด: ดึงค่าจาก Dictionary ให้ใช้ .get('key') ไม่ใช้จุด (.)
            server = config_data.get('server')
            database = config_data.get('database')
            username = config_data.get('username')
            password = config_data.get('password')
            driver = config_data.get('driver', 'ODBC Driver 18 for SQL Server')
            auth_type = config_data.get('auth_type')

            
            # สร้าง Connection String
            if auth_type == 'SQL Server Authentication':
                conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
            else:
                conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"

            # ODBC Driver 18 ต้องใส่ TrustServerCertificate ถ้าไม่ได้ใช้ Certificate จริง
            if "18" in driver:
                conn_str += "TrustServerCertificate=yes;"

            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()

            query = """INSERT INTO dbo.Tb_Check_Pose (user_id, camera_id, status_pose) VALUES (?, ?, ?)"""

            user_id = int(user_id)
            # camera_id = int(camera_id)
            data = (user_id, camera_id, status_pose)
            
            cursor.execute(query, data)
            conn.commit()
            print("✅ Insert Data Successfully!")


        except Exception as e:
            
            print(f"Error: Pimary Key {e}")

        finally:
            if conn:
                conn.close()

    def _fetch_table_data(self):
        selected_table = self.cmb_tables.get()
        if not selected_table:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP 500 * FROM [{selected_table}]")

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columns
            self.tree["show"] = "headings"

            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor="w")

            for row in rows:
                row_values = [str(item) if item is not None else "" for item in row]
                self.tree.insert("", "end", values=row_values)

            self.lbl_row_count.config(text=f"รายการทั้งหมด: {len(rows)} แถว (แสดงสูงสุด 500)")

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถดึงข้อมูลตารางได้:\n{str(e)}", parent=self)


# ==========================================
# 3. หน้าต่างหลักสำหรับการตั้งค่าและเชื่อมต่อ (CONFIG GUI)
# ==========================================
class SSMSConnectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SSMS Database Connection Setup")
        self.root.geometry("460x450")
        self.root.resizable(False, False)

        self.config_mgr = ConfigManager()
        self.config_data = self.config_mgr.load_config()

        self.BG_COLOR = "#F8FAFC"
        self.PANEL_COLOR = "#FFFFFF"
        self.PRIMARY_COLOR = "#2563EB"
        self.root.configure(bg=self.BG_COLOR)

        self._build_ui()
        self._load_values_to_ui()
        self._toggle_auth_fields()

    def _build_ui(self):
        tk.Label(
            self.root, 
            text="🗄️ SQL Server Connection", 
            font=("Segoe UI", 14, "bold"), 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=(15, 10))

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

        # 1. Server
        tk.Label(panel, text="Server Name:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=0, column=0, sticky="w", pady=6)
        self.ent_server = ttk.Entry(panel)
        self.ent_server.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 2. Database
        tk.Label(panel, text="Database:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=1, column=0, sticky="w", pady=6)
        self.ent_database = ttk.Entry(panel)
        self.ent_database.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 3. Auth
        tk.Label(panel, text="Authentication:", font=("Segoe UI", 9, "bold"), bg=self.PANEL_COLOR).grid(row=2, column=0, sticky="w", pady=6)
        self.cmb_auth = ttk.Combobox(panel, values=["Windows Authentication", "SQL Server Authentication"], state="readonly")
        self.cmb_auth.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.cmb_auth.bind("<<ComboboxSelected>>", lambda e: self._toggle_auth_fields())

        # 4. User
        tk.Label(panel, text="Username:", font=("Segoe UI", 9), bg=self.PANEL_COLOR).grid(row=3, column=0, sticky="w", pady=6)
        self.ent_user = ttk.Entry(panel)
        self.ent_user.grid(row=3, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 5. Pass
        tk.Label(panel, text="Password:", font=("Segoe UI", 9), bg=self.PANEL_COLOR).grid(row=4, column=0, sticky="w", pady=6)
        self.ent_pass = ttk.Entry(panel, show="•")
        self.ent_pass.grid(row=4, column=1, sticky="ew", pady=6, padx=(10, 0))

        # 6. Driver
        tk.Label(panel, text="ODBC Driver:", font=("Segoe UI", 9), bg=self.PANEL_COLOR).grid(row=5, column=0, sticky="w", pady=6)
        self.cmb_driver = ttk.Combobox(
            panel, 
            values=["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server", "SQL Server"], 
            state="readonly"
        )
        self.cmb_driver.grid(row=5, column=1, sticky="ew", pady=6, padx=(10, 0))

        # Buttons
        btn_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_connect = ttk.Button(btn_frame, text="⚡ เชื่อมต่อ & แสดงตาราง", command=self._connect_and_open_viewer)
        self.btn_connect.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.btn_save = ttk.Button(btn_frame, text="💾 บันทึก Config", command=self._save_config)
        self.btn_save.pack(side="right", padx=(5, 0), expand=True, fill="x")

    def _load_values_to_ui(self):
        self.ent_server.insert(0, self.config_data.get("server", ""))
        self.ent_database.insert(0, self.config_data.get("database", ""))
        self.cmb_auth.set(self.config_data.get("auth_type", "Windows Authentication"))
        self.ent_user.insert(0, self.config_data.get("username", ""))
        self.ent_pass.insert(0, self.config_data.get("password", ""))
        self.cmb_driver.set(self.config_data.get("driver", "ODBC Driver 17 for SQL Server"))

    def _toggle_auth_fields(self):
        if self.cmb_auth.get() == "Windows Authentication":
            self.ent_user.config(state="disabled")
            self.ent_pass.config(state="disabled")
        else:
            self.ent_user.config(state="normal")
            self.ent_pass.config(state="normal")

    def _get_current_config(self):
        return {
            "server": self.ent_server.get().strip(),
            "database": self.ent_database.get().strip(),
            "auth_type": self.cmb_auth.get(),
            "username": self.ent_user.get().strip(),
            "password": self.ent_pass.get().strip(),
            "driver": self.cmb_driver.get()
        }

    def _connect_and_open_viewer(self):
        """ทดสอบการเชื่อมต่อ หากผ่านจะเปิดหน้าแสดงตารางทันที"""
        current_config = self._get_current_config()
        
        server = current_config["server"]
        database = current_config["database"]
        driver = current_config["driver"]

        if current_config["auth_type"] == "Windows Authentication":
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        else:
            user = current_config["username"]
            pwd = current_config["password"]
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={pwd};"

        if "18" in driver:
            conn_str += "TrustServerCertificate=yes;"

        try:
            # ทดสอบเชื่อมต่อ
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()

            # บันทึก Config ล่าสุดไว้ก่อน
            self.config_mgr.save_config(current_config)

            # 🌟 เปิดหน้าต่างแสดงตารางข้อมูลขึ้นมาอีกหน้า
            TableViewerWindow(self.root, current_config)

        except Exception as e:
            messagebox.showerror("ล้มเหลว", f"❌ ไม่สามารถเชื่อมต่อได้:\n\n{str(e)}")

    def _save_config(self):
        current_config = self._get_current_config()
        if self.config_mgr.save_config(current_config):
            messagebox.showinfo("บันทึกข้อมูล", "💾 บันทึกการตั้งค่าลง db_config.json เรียบร้อยแล้ว")


if __name__ == "__main__":
    root = tk.Tk()
    app = SSMSConnectGUI(root)
    root.mainloop()