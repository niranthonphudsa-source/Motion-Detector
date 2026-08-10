import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
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
# 2. GUI DATABASE TABLE VIEWER & DASHBOARD
# ==========================================
class SSTableViewerGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("📊 SQL Server Data Viewer & Dashboard")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)

        # ----------------------------------------------------
        # THEME COLORS (White & Blue Modern Light Theme)
        # ----------------------------------------------------
        self.BG_COLOR = "#F8FAFC"        # Slate 50 (พื้นหลังหลัก)
        self.PANEL_COLOR = "#FFFFFF"     # White (พื้นหลังการ์ด/กล่อง)
        self.PRIMARY_BLUE = "#2563EB"    # Blue 600 (สีฟ้าหลัก)
        self.PRIMARY_DARK = "#1E40AF"    # Blue 800 (สีน้ำเงินเข้ม)
        self.ACCENT_BG = "#EFF6FF"       # Blue 50 (สีฟ้าอ่อนมากสำหรับพื้นที่ไฮไลท์)
        self.TEXT_MAIN = "#0F172A"       # Slate 900 (สีข้อความหลัก)
        self.TEXT_MUTED = "#64748B"      # Slate 500 (สีข้อความรอง)
        self.BORDER_COLOR = "#E2E8F0"    # Slate 200 (สีเส้นขอบ)

        # Status Colors
        self.COLOR_OK = "#10B981"        # Emerald 500 (สีเขียว OK)
        self.COLOR_NG = "#EF4444"        # Red 500 (สีแดง NG)

        self.root.configure(bg=self.BG_COLOR)

        # โหลด Config
        self.config_mgr = ConfigManager()
        self.config_data = self.config_mgr.load_config()

        if not self.config_data:
            messagebox.showerror(
                "Error",
                "ไม่พบไฟล์ db_config.json กรุณาตั้งค่าการเชื่อมต่อในหน้า Config ก่อน",
            )
            return

        self._setup_custom_styles()
        self._build_ui()
        self._load_camera_list()
        self._fetch_table_data()

    def _setup_custom_styles(self):
        """ตั้งค่า TTK Styles ให้เป็นดีไซน์โมเดิร์นสีขาว-ฟ้า"""
        style = ttk.Style()
        style.theme_use("clam")

        # Notebook (Tabs)
        style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#E2E8F0",
            foreground=self.TEXT_MUTED,
            font=("Segoe UI", 10, "bold"),
            padding=[16, 8],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.PRIMARY_BLUE)],
            foreground=[("selected", "#FFFFFF")],
        )

        # Custom Buttons
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            background=self.PRIMARY_BLUE,
            foreground="#FFFFFF",
            borderwidth=0,
            focusthickness=0,
            padding=[12, 6],
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.PRIMARY_DARK)],
            foreground=[("active", "#FFFFFF")],
        )

        # Combobox & Entry
        style.configure(
            "TCombobox",
            fieldbackground=self.PANEL_COLOR,
            background=self.PANEL_COLOR,
            bordercolor=self.BORDER_COLOR,
            arrowcolor=self.PRIMARY_BLUE,
            padding=4,
        )
        style.configure("TEntry", fieldbackground=self.PANEL_COLOR, bordercolor=self.BORDER_COLOR, padding=4)

        # Treeview (Table)
        style.configure(
            "Treeview",
            background=self.PANEL_COLOR,
            foreground=self.TEXT_MAIN,
            fieldbackground=self.PANEL_COLOR,
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=self.ACCENT_BG,
            foreground=self.PRIMARY_DARK,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=[6, 6],
        )
        style.map("Treeview", background=[("selected", self.PRIMARY_BLUE)], foreground=[("selected", "#FFFFFF")])

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
        # สร้าง Tab Control สำหรับแยกหน้า Data View กับ Dashboard
        self.tabControl = ttk.Notebook(self.root)

        self.tab_data = tk.Frame(self.tabControl, bg=self.BG_COLOR)
        self.tab_dash = tk.Frame(self.tabControl, bg=self.BG_COLOR)

        self.tabControl.add(self.tab_data, text="📋  ข้อมูลตาราง")
        self.tabControl.add(self.tab_dash, text="📊  สรุปสถิติ (Dashboard)")
        self.tabControl.pack(expand=1, fill="both")

        # ----------------------------------------------------
        # TAB 1: DATA VIEW & FILTERS
        # ----------------------------------------------------
        top_frame = tk.Frame(
            self.tab_data,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        top_frame.pack(fill="x", padx=20, pady=15, ipady=5)

        # Filter: เลือกกล้อง (Camera)
        tk.Label(
            top_frame,
            text="📷 กล้อง:",
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.PRIMARY_DARK,
        ).grid(row=0, column=0, padx=(10, 2), pady=8, sticky="w")

        self.cmb_camera = ttk.Combobox(top_frame, state="readonly", width=12, font=("Segoe UI", 9))
        self.cmb_camera.grid(row=0, column=1, padx=5, pady=8)

        # Filter: วันที่เริ่มต้น
        tk.Label(
            top_frame,
            text="📅 วันที่เริ่ม (YYYY-MM-DD):",
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
        ).grid(row=0, column=2, padx=(10, 2), pady=8, sticky="w")
        self.ent_start_date = ttk.Entry(top_frame, width=12)
        self.ent_start_date.grid(row=0, column=3, padx=5, pady=8)

        # Filter: ถึงวันที่
        tk.Label(
            top_frame,
            text="📅 ถึงวันที่:",
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
        ).grid(row=0, column=4, padx=(10, 2), pady=8, sticky="w")
        self.ent_end_date = ttk.Entry(top_frame, width=12)
        self.ent_end_date.grid(row=0, column=5, padx=5, pady=8)

        # ปุ่มค้นหา/ดึงข้อมูล
        self.btn_load = ttk.Button(
            top_frame,
            text="🔍  กรองข้อมูล",
            style="Primary.TButton",
            command=self._fetch_table_data,
        )
        self.btn_load.grid(row=0, column=6, padx=15, pady=8)

        # Label แสดงจำนวนแถว
        self.lbl_row_count = tk.Label(
            top_frame,
            text="รายการทั้งหมด: 0 แถว",
            font=("Segoe UI", 9),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MUTED,
        )
        self.lbl_row_count.grid(row=1, column=0, columnspan=7, sticky="w", padx=10, pady=(0, 5))

        # Data Table Area (Treeview + Scrollbars)
        table_frame = tk.Frame(
            self.tab_data,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            table_frame,
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            selectmode="extended",
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Tag สีสลับแถวในตาราง
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F1F5F9")

        # ----------------------------------------------------
        # TAB 2: DASHBOARD (สรุปสถิติ - ตกแต่งแบบ MODERN LIGHT)
        # ----------------------------------------------------
        dash_header_frame = tk.Frame(self.tab_dash, bg=self.BG_COLOR)
        dash_header_frame.pack(fill="x", padx=20, pady=(20, 10))

        # Title ของ Dashboard
        title_box = tk.Frame(dash_header_frame, bg=self.BG_COLOR)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="System Performance Dashboard",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_COLOR,
            fg=self.TEXT_MAIN,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="สรุปสถิติจำนวนการตรวจจับและสถานะความถูกต้องของระบบ",
            font=("Segoe UI", 9),
            bg=self.BG_COLOR,
            fg=self.TEXT_MUTED,
        ).pack(anchor="w")

        # ปุ่ม Refresh
        btn_refresh_dash = ttk.Button(
            dash_header_frame,
            text="🔄  อัปเดตสถิติ",
            style="Primary.TButton",
            command=self._load_dashboard,
        )
        btn_refresh_dash.pack(side="right", pady=5)

        # พื้นที่วาง KPI Cards
        self.cards_container = tk.Frame(self.tab_dash, bg=self.BG_COLOR)
        self.cards_container.pack(fill="x", padx=20, pady=10)

        # พื้นที่แสดงรายละเอียดเพิ่มเติมด้านล่าง (Summary Detail Box)
        self.detail_frame = tk.Frame(
            self.tab_dash,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        self.detail_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self._load_dashboard()

    def _load_camera_list(self):
        """ดึงรายชื่อ Camera ID ทั้งหมดที่มีใน DB มาใส่ใน Dropdown อัตโนมัติ"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT camera_id FROM [Tb_Check_Pose] WHERE camera_id IS NOT NULL")
            cams = [str(row[0]) for row in cursor.fetchall()]
            conn.close()

            cams.insert(0, "ทั้งหมด")
            self.cmb_camera["values"] = cams
            self.cmb_camera.current(0)
        except Exception:
            self.cmb_camera["values"] = ["ทั้งหมด"]
            self.cmb_camera.current(0)

    def _fetch_table_data(self):
        """ดึงข้อมูลจากตาราง Tb_Check_Pose โดยรองรับ Filter กล้อง และ วันเวลา"""
        selected_table = "Tb_Check_Pose"
        selected_cam = self.cmb_camera.get()
        start_date = self.ent_start_date.get().strip()
        end_date = self.ent_end_date.get().strip()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"SELECT TOP 500 * FROM [{selected_table}] WHERE 1=1"
            params = []

            if selected_cam and selected_cam != "ทั้งหมด":
                query += " AND camera_id = ?"
                params.append(selected_cam)

            if start_date:
                query += " AND date_time >= ?"
                params.append(f"{start_date} 00:00:00")
            if end_date:
                query += " AND date_time <= ?"
                params.append(f"{end_date} 23:59:59")

            query += " ORDER BY user_id DESC"

            cursor.execute(query, params)

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            # Clear ข้อมูลเก่า
            self.tree.delete(*self.tree.get_children())

            # Setup Columns
            self.tree["columns"] = columns
            self.tree["show"] = "headings"

            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor="w")

            # Insert Rows พร้อม Alternate Row Colors
            for i, row in enumerate(rows):
                row_values = [str(item) if item is not None else "" for item in row]
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row_values, tags=(tag,))

            self.lbl_row_count.config(text=f"รายการทั้งหมด: {len(rows)} แถว (แสดงสูงสุด 500)")

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถดึงข้อมูลตารางได้:\n{str(e)}")

    def _create_modern_kpi_card(self, parent, title, value, subtext, accent_color, icon_symbol):
        """สร้าง UI รูปแบบ Modern KPI Card ที่มี Top Accent Strip และ Clean Layout"""
        card = tk.Frame(
            parent,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        card.pack(side="left", fill="both", expand=True, padx=6)

        # แถบสีด้านบนการ์ด (Top Accent Strip)
        top_strip = tk.Frame(card, bg=accent_color, height=4)
        top_strip.pack(fill="x", side="top")

        content_box = tk.Frame(card, bg=self.PANEL_COLOR, padx=16, pady=16)
        content_box.pack(fill="both", expand=True)

        # Header ของการ์ด (ไอคอน + ชื่อเรื่อง)
        header_frame = tk.Frame(content_box, bg=self.PANEL_COLOR)
        header_frame.pack(fill="x")

        lbl_title = tk.Label(
            header_frame,
            text=title,
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MUTED,
        )
        lbl_title.pack(side="left")

        lbl_icon = tk.Label(
            header_frame,
            text=icon_symbol,
            font=("Segoe UI", 12),
            bg=self.PANEL_COLOR,
            fg=accent_color,
        )
        lbl_icon.pack(side="right")

        # ค่าตัวเลขหลัก (Value)
        lbl_val = tk.Label(
            content_box,
            text=str(value),
            font=("Segoe UI", 22, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
        )
        lbl_val.pack(anchor="w", pady=(8, 2))

        # ข้อความคำอธิบายเพิ่มเติมด้านล่าง
        lbl_sub = tk.Label(
            content_box,
            text=subtext,
            font=("Segoe UI", 8),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MUTED,
        )
        lbl_sub.pack(anchor="w")

    def _load_dashboard(self):
        """ดึงสถิติจาก Database สรุปเป็น KPI Cards และสัดส่วน Progress Bar บน Dashboard"""
        # ล้างการ์ดและรายละเอียดเก่า
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. ยอดตรวจทั้งหมด
            cursor.execute("SELECT COUNT(*) FROM [Tb_Check_Pose]")
            total_checks = cursor.fetchone()[0] or 0

            # 2. ยอด OK
            cursor.execute("SELECT COUNT(*) FROM [Tb_Check_Pose] WHERE status_pose = 'OK'")
            row_ok = cursor.fetchone()
            total_ok = row_ok[0] if row_ok else 0

            # 3. ยอด NG
            cursor.execute("SELECT COUNT(*) FROM [Tb_Check_Pose] WHERE status_pose = 'NG'")
            row_ng = cursor.fetchone()
            total_ng = row_ng[0] if row_ng else 0

            conn.close()

            # คำนวณเปอร์เซ็นต์
            pass_rate = (total_ok / total_checks * 100) if total_checks > 0 else 0
            ok_share = (total_ok / total_checks * 100) if total_checks > 0 else 0
            ng_share = (total_ng / total_checks * 100) if total_checks > 0 else 0

            # --- สร้าง KPI CARDS ---
            # Card 1: Total
            self._create_modern_kpi_card(
                self.cards_container,
                "จำนวนการตรวจทั้งหมด",
                f"{total_checks:,}",
                "รายการทั้งหมดในระบบ",
                self.PRIMARY_BLUE,
                "📊",
            )
            # Card 2: OK
            self._create_modern_kpi_card(
                self.cards_container,
                "ผ่านเกณฑ์ (OK)",
                f"{total_ok:,}",
                f"สัดส่วน {ok_share:.1f}% ของทั้งหมด",
                self.COLOR_OK,
                "✅",
            )
            # Card 3: NG
            self._create_modern_kpi_card(
                self.cards_container,
                "ไม่ผ่าน (NG)",
                f"{total_ng:,}",
                f"สัดส่วน {ng_share:.1f}% ของทั้งหมด",
                self.COLOR_NG,
                "❌",
            )
            # Card 4: Pass Rate
            self._create_modern_kpi_card(
                self.cards_container,
                "อัตราการตรวจผ่าน",
                f"{pass_rate:.1f}%",
                "เป้าหมายระบบ > 95.0%",
                "#8B5CF6" if pass_rate >= 90 else "#F59E0B",  # Purple / Amber
                "🎯",
            )

            # --- ส่วนแสดงรายละเอียดเพิ่มเติม (DETAIL PANEL) ---
            detail_inner = tk.Frame(self.detail_frame, bg=self.PANEL_COLOR, padx=20, pady=20)
            detail_inner.pack(fill="both", expand=True)

            tk.Label(
                detail_inner,
                text="📈 สรุปสัดส่วนผลการตรวจสอบ (Status Distribution)",
                font=("Segoe UI", 11, "bold"),
                bg=self.PANEL_COLOR,
                fg=self.TEXT_MAIN,
            ).pack(anchor="w", pady=(0, 15))

            # Visual Progress Bar สัดส่วน OK vs NG
            progress_bg = tk.Frame(detail_inner, bg=self.BORDER_COLOR, height=20)
            progress_bg.pack(fill="x", pady=5)
            progress_bg.pack_propagate(False)

            if total_checks > 0:
                ok_width_ratio = total_ok / total_checks
                ok_bar = tk.Frame(progress_bg, bg=self.COLOR_OK)
                ok_bar.place(relx=0, rely=0, relwidth=ok_width_ratio, relheight=1.0)

                ng_bar = tk.Frame(progress_bg, bg=self.COLOR_NG)
                ng_bar.place(relx=ok_width_ratio, rely=0, relwidth=(1 - ok_width_ratio), relheight=1.0)

            # Legend คำอธิบายสี Progress Bar
            legend_frame = tk.Frame(detail_inner, bg=self.PANEL_COLOR)
            legend_frame.pack(fill="x", pady=10)

            # Legend OK
            tk.Frame(legend_frame, bg=self.COLOR_OK, width=12, height=12).pack(side="left", padx=(0, 5))
            tk.Label(
                legend_frame,
                text=f"OK ({ok_share:.1f}%)",
                font=("Segoe UI", 9),
                bg=self.PANEL_COLOR,
                fg=self.TEXT_MUTED,
            ).pack(side="left", padx=(0, 20))

            # Legend NG
            tk.Frame(legend_frame, bg=self.COLOR_NG, width=12, height=12).pack(side="left", padx=(0, 5))
            tk.Label(
                legend_frame,
                text=f"NG ({ng_share:.1f}%)",
                font=("Segoe UI", 9),
                bg=self.PANEL_COLOR,
                fg=self.TEXT_MUTED,
            ).pack(side="left")

        except Exception as e:
            lbl_err = tk.Label(
                self.cards_container,
                text=f"ไม่สามารถโหลดข้อมูลสถิติได้: {e}",
                fg=self.COLOR_NG,
                bg=self.BG_COLOR,
                font=("Segoe UI", 10),
            )
            lbl_err.pack(pady=20)


# ==========================================
# 3. CLASS เช็ก LAST ID
# ==========================================
class CheckLastID:

    def __init__(self):
        self.lastID = 0
        self.config_mgr = ConfigManager()
        self.config_data = self.config_mgr.load_config()

        self._getLastID()

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

    def _getLastID(self):
        selected_table = "Tb_Check_Pose"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"SELECT MAX(user_id) FROM [{selected_table}]"
            cursor.execute(query)

            rows = cursor.fetchone()
            conn.close()

            if rows and rows[0] is not None:
                self.lastID = rows[0]

            return self.lastID
        except Exception as e:
            print(f"Error fetching last ID: {e}")
            return 0


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SSTableViewerGUI(root)
    app1 = CheckLastID()
    root.mainloop()