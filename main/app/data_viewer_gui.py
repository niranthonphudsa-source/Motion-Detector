import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc

# ==========================================
# 1. CLASS สำหรับโหลด CONFIG
# ==========================================
class ConfigManager:
    def __init__(self, filename="db_config.json"):
        self.filename = filename

    def load_config(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

# ==========================================
# 2. GUI DATABASE TABLE VIEWER
# ==========================================
class SSTableViewerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 SQL Server Data Viewer")
        self.root.geometry("900x600")

        # กำหนดธีมสี
        self.BG_COLOR = "#F8FAFC"
        self.PANEL_COLOR = "#FFFFFF"
        self.PRIMARY_COLOR = "#1E3A8A"

        self.root.configure(bg=self.BG_COLOR)

        # โหลด Config
        self.config_mgr = ConfigManager()
        self.config_data = self.config_mgr.load_config()

        if not self.config_data:
            messagebox.showerror("Error", "ไม่พบไฟล์ db_config.json กรุณาตั้งค่าการเชื่อมต่อในหน้า Config ก่อน")
            return

        self._build_ui()
        self._load_tables_list() # ดึงรายชื่อตารางทันทีที่เปิดหน้าต่าง

    def _get_connection(self):
        """สร้าง Connection วัตถุ pyodbc จาก Config"""
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
        # 1. Top Control Bar (แถบควบคุมด้านบน)
        top_frame = tk.Frame(self.root, bg=self.PANEL_COLOR, highlightbackground="#E2E8F0", highlightthickness=1)
        top_frame.pack(fill="x", padx=15, pady=15, ipady=5)

        tk.Label(
            top_frame, 
            text="📁 เลือกตาราง (Table):", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.PANEL_COLOR, 
            fg=self.PRIMARY_COLOR
        ).pack(side="left", padx=(15, 5), pady=10)

        # Dropdown เลือก Table
        self.cmb_tables = ttk.Combobox(top_frame, state="readonly", width=30, font=("Segoe UI", 9))
        self.cmb_tables.pack(side="left", padx=5, pady=10)

        # ปุ่มโหลดข้อมูล
        self.btn_load = ttk.Button(top_frame, text="🔄 ดึงข้อมูล", command=self._fetch_table_data)
        self.btn_load.pack(side="left", padx=10, pady=10)

        # Label แสดงจำนวนแถว
        self.lbl_row_count = tk.Label(top_frame, text="รายการทั้งหมด: 0 แถว", font=("Segoe UI", 9), bg=self.PANEL_COLOR, fg="#64748B")
        self.lbl_row_count.pack(side="right", padx=15, pady=10)

        # 2. Data Table Area (พื้นที่แสดงตารางข้อมูล + Scrollbars)
        table_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview (Data Grid)
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
        """ดึงรายชื่อตาราง (Tables) ทั้งหมดที่มีใน Database มาใส่ Dropdown"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Query หาชื่อ Tables ทั้งหมดที่ไม่ใช่ System Tables
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
                self.cmb_tables.current(0) # เลือกตารางแรกเป็นค่าเริ่มต้น
            else:
                messagebox.showwarning("ข้อความ", "ไม่พบตารางข้อมูลใน Database นี้")

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถดึงรายชื่อตารางได้:\n{str(e)}")

    def _fetch_table_data(self):
        """ดึงข้อมูลจากตารางที่เลือกมาแสดงผลใน Treeview"""
        selected_table = self.cmb_tables.get()
        if not selected_table:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกตารางก่อนครับ")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Query ดึงข้อมูล 500 แถวแรก (ป้องกันกรณีตารางใหญ่เกินไปจนโปรแกรมค้าง)
            query = f"SELECT TOP 500 * FROM [{selected_table}]"
            cursor.execute(query)

            # ดึงชื่อคอลัมน์ (Column Headers)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            # --- เคลียร์ข้อมูลเก่าใน Treeview ---
            self.tree.delete(*self.tree.get_children())

            # --- ตั้งค่า คอลัมน์ ใหม่ ---
            self.tree["columns"] = columns
            self.tree["show"] = "headings" # ซ่อนคอลัมน์แรกสุดที่เป็นไอคอน default

            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor="w") # ความกว้างเริ่มต้น

            # --- ใส่ข้อมูล Rows ลงใน Treeview ---
            for row in rows:
                # แปลงค่า None ให้เป็นข้อความว่างเพื่อความสวยงาม
                row_values = [str(item) if item is not None else "" for item in row]
                self.tree.insert("", "end", values=row_values)

            # อัปเดตจำนวนแถว
            self.lbl_row_count.config(text=f"รายการทั้งหมด: {len(rows)} แถว (แสดงสูงสุด 500)")

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถดึงข้อมูลตารางได้:\n{str(e)}")


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SSTableViewerGUI(root)
    root.mainloop()