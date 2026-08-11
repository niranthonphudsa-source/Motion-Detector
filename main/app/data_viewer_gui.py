import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc
from tkcalendar import DateEntry


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
        self.root.geometry("1150x750")
        self.root.minsize(1000, 650)

        # ----------------------------------------------------
        # THEME COLORS (White & Blue Modern Light Theme)
        # ----------------------------------------------------
        self.BG_COLOR = "#F8FAFC"
        self.PANEL_COLOR = "#FFFFFF"
        self.PRIMARY_BLUE = "#2563EB"
        self.PRIMARY_DARK = "#1E40AF"
        self.ACCENT_BG = "#EFF6FF"
        self.TEXT_MAIN = "#0F172A"
        self.TEXT_MUTED = "#64748B"
        self.BORDER_COLOR = "#E2E8F0"

        # Status Colors
        self.COLOR_OK = "#10B981"
        self.COLOR_NG = "#EF4444"

        self.root.configure(bg=self.BG_COLOR)

        # ตัวแปรสำหรับเก็บค่า Filter สถานะ ("ALL", "OK", "NG")
        self.status_var = tk.StringVar(value="ALL")

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
        style = ttk.Style()
        style.theme_use("clam")

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

        style.configure(
            "TCombobox",
            fieldbackground=self.PANEL_COLOR,
            background=self.PANEL_COLOR,
            bordercolor=self.BORDER_COLOR,
            arrowcolor=self.PRIMARY_BLUE,
            padding=4,
        )
        style.configure(
            "TEntry",
            fieldbackground=self.PANEL_COLOR,
            bordercolor=self.BORDER_COLOR,
            padding=4,
        )

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
        style.map(
            "Treeview",
            background=[("selected", self.PRIMARY_BLUE)],
            foreground=[("selected", "#FFFFFF")],
        )

    def _get_connection(self):
        server = self.config_data.get("server")
        database = self.config_data.get("database")
        driver = self.config_data.get(
            "driver", "ODBC Driver 17 for SQL Server"
        )
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

    def get_selected_date(self):
        """ดึงค่าวันที่เริ่มต้นในรูปแบบ String 'YYYY-MM-DD'"""
        return self.ent_start_date.get().strip()

    def get_date_range(self):
        """[แก้ไขจุดพัง] ดึงค่าช่วงวันที่โดยไม่เขียนทับตัวแปร Widget"""
        start_date = self.ent_start_date.get().strip()
        end_date = self.ent_end_date.get().strip()
        return start_date, end_date

    def _toggle_date_widgets(self):
        """เปิด/ปิด การใช้งาน DateEntry ตามการติ๊ก Checkbox"""
        state = "normal" if self.use_date_filter.get() else "disabled"
        self.ent_start_date.config(state=state)
        self.ent_end_date.config(state=state)
        self._fetch_table_data()

    def _build_ui(self):
        self.tabControl = ttk.Notebook(self.root)

        self.tab_data = tk.Frame(self.tabControl, bg=self.BG_COLOR)
        self.tab_dash = tk.Frame(self.tabControl, bg=self.BG_COLOR)

        self.tabControl.add(self.tab_data, text="📋  ข้อมูลตาราง")
        self.tabControl.add(self.tab_dash, text="📊  สรุปสถิติ (Dashboard)")
        self.tabControl.pack(expand=1, fill="both")

        # ----------------------------------------------------
        # TAB 1: DATA VIEW & FILTERS
        # ----------------------------------------------------
        # 1. ประกาศสร้าง top_frame ก่อนเรียกใช้งาน
        top_frame = tk.Frame(
            self.tab_data,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        top_frame.pack(fill="x", padx=20, pady=15, ipady=5)

        # Filter: เลือกกล้อง (Camera) - Column 0, 1
        tk.Label(
            top_frame,
            text="📷 กล้อง:",
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.PRIMARY_DARK,
        ).grid(row=0, column=0, padx=(10, 2), pady=8, sticky="w")

        self.cmb_camera = ttk.Combobox(
            top_frame, state="readonly", width=10, font=("Segoe UI", 9)
        )
        self.cmb_camera.grid(row=0, column=1, padx=5, pady=8)
        self.cmb_camera.bind(
            "<<ComboboxSelected>>", lambda e: self._fetch_table_data()
        )

        # Filter: เลือกสถานะ - Column 2, 3
        tk.Label(
            top_frame,
            text="📌 สถานะ:",
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.PRIMARY_DARK,
        ).grid(row=0, column=2, padx=(10, 2), pady=8, sticky="w")

        status_btn_frame = tk.Frame(top_frame, bg=self.PANEL_COLOR)
        status_btn_frame.grid(row=0, column=3, padx=5, pady=8)

        rb_all = tk.Radiobutton(
            status_btn_frame,
            text="ทั้งหมด",
            variable=self.status_var,
            value="ALL",
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
            activebackground=self.PANEL_COLOR,
            font=("Segoe UI", 9),
            command=self._fetch_table_data,
        )
        rb_ok = tk.Radiobutton(
            status_btn_frame,
            text="🟢 OK",
            variable=self.status_var,
            value="OK",
            bg=self.PANEL_COLOR,
            fg="#059669",
            activebackground=self.PANEL_COLOR,
            font=("Segoe UI", 9, "bold"),
            command=self._fetch_table_data,
        )
        rb_ng = tk.Radiobutton(
            status_btn_frame,
            text="🔴 NG",
            variable=self.status_var,
            value="NG",
            bg=self.PANEL_COLOR,
            fg="#DC2626",
            activebackground=self.PANEL_COLOR,
            font=("Segoe UI", 9, "bold"),
            command=self._fetch_table_data,
        )

        rb_all.pack(side="left", padx=2)
        rb_ok.pack(side="left", padx=2)
        rb_ng.pack(side="left", padx=2)

        # Filter: Checkbox และเลือกช่วงวันที่ - Column 4, 5, 6, 7
        self.use_date_filter = tk.BooleanVar(value=False)

        chk_date = tk.Checkbutton(
            top_frame,
            text="📅 กรองวันที่",
            variable=self.use_date_filter,
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
            font=("Segoe UI", 9, "bold"),
            command=self._toggle_date_widgets,
        )
        chk_date.grid(row=0, column=4, padx=(10, 2), pady=8, sticky="w")

        self.ent_start_date = DateEntry(
            top_frame,
            width=10,
            background="blue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd",
            state="disabled",  # เริ่มต้นปิดใช้งานไว้
        )
        self.ent_start_date.grid(row=0, column=5, padx=2, pady=8)
        self.ent_start_date.bind(
            "<<DateEntrySelected>>", lambda e: self._fetch_table_data()
        )

        tk.Label(
            top_frame, text="-", font=("Segoe UI", 9), bg=self.PANEL_COLOR
        ).grid(row=0, column=6, padx=2)

        self.ent_end_date = DateEntry(
            top_frame,
            width=10,
            background="blue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd",
            state="disabled",  # เริ่มต้นปิดใช้งานไว้
        )
        self.ent_end_date.grid(row=0, column=7, padx=2, pady=8)
        self.ent_end_date.bind(
            "<<DateEntrySelected>>", lambda e: self._fetch_table_data()
        )

        # ปุ่มค้นหา/ดึงข้อมูล - Column 8
        self.btn_load = ttk.Button(
            top_frame,
            text="🔍  กรองข้อมูล",
            style="Primary.TButton",
            command=self._fetch_table_data,
        )
        self.btn_load.grid(row=0, column=8, padx=15, pady=8)

        # Label แสดงจำนวนแถว
        self.lbl_row_count = tk.Label(
            top_frame,
            text="รายการทั้งหมด: 0 แถว",
            font=("Segoe UI", 9),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MUTED,
        )
        self.lbl_row_count.grid(
            row=1, column=0, columnspan=9, sticky="w", padx=10, pady=(0, 5)
        )

        # Data Table Area
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

        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F1F5F9")

        # ----------------------------------------------------
        # TAB 2: DASHBOARD
        # ----------------------------------------------------
        dash_header_frame = tk.Frame(self.tab_dash, bg=self.BG_COLOR)
        dash_header_frame.pack(fill="x", padx=20, pady=(20, 10))

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

        btn_refresh_dash = ttk.Button(
            dash_header_frame,
            text="🔄  อัปเดตสถิติ",
            style="Primary.TButton",
            command=self._load_dashboard,
        )
        btn_refresh_dash.pack(side="right", pady=5)

        self.cards_container = tk.Frame(self.tab_dash, bg=self.BG_COLOR)
        self.cards_container.pack(fill="x", padx=20, pady=10)

        self.detail_frame = tk.Frame(
            self.tab_dash,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        self.detail_frame.pack(
            fill="both", expand=True, padx=20, pady=(10, 20)
        )

        self._load_dashboard()

    def _load_camera_list(self):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT camera_id FROM [Tb_Check_Pose] WHERE camera_id IS NOT NULL"
            )
            cams = [str(row[0]) for row in cursor.fetchall()]
            conn.close()

            cams.insert(0, "ทั้งหมด")
            self.cmb_camera["values"] = cams
            self.cmb_camera.current(0)
        except Exception:
            self.cmb_camera["values"] = ["ทั้งหมด"]
            self.cmb_camera.current(0)

    def _fetch_table_data(self):
        selected_table = "Tb_Check_Pose"
        selected_cam = self.cmb_camera.get()
        selected_status = self.status_var.get()
        start_date, end_date = self.get_date_range()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"SELECT TOP 500 * FROM [{selected_table}] WHERE 1=1"
            params = []

            if selected_cam and selected_cam != "ทั้งหมด":
                query += " AND camera_id = ?"
                params.append(selected_cam)

            if selected_status == "OK":
                query += " AND status_pose = 'OK'"
            elif selected_status == "NG":
                query += " AND status_pose = 'NG'"

            if self.use_date_filter.get():
                start_date, end_date = self.get_date_range()
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

            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columns
            self.tree["show"] = "headings"

            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor="w")

            for i, row in enumerate(rows):
                row_values = [
                    str(item) if item is not None else "" for item in row
                ]
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row_values, tags=(tag,))

            status_text = (
                f" [{selected_status}]" if selected_status != "ALL" else ""
            )
            self.lbl_row_count.config(
                text=f"รายการทั้งหมด{status_text}: {len(rows)} แถว (แสดงสูงสุด 500)"
            )

        except Exception as e:
            messagebox.showerror(
                "Error", f"ไม่สามารถดึงข้อมูลตารางได้:\n{str(e)}"
            )

    def _create_modern_kpi_card(
        self, parent, title, value, subtext, accent_color, icon_symbol
    ):
        card = tk.Frame(
            parent,
            bg=self.PANEL_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        card.pack(side="left", fill="both", expand=True, padx=6)

        top_strip = tk.Frame(card, bg=accent_color, height=4)
        top_strip.pack(fill="x", side="top")

        content_box = tk.Frame(card, bg=self.PANEL_COLOR, padx=16, pady=16)
        content_box.pack(fill="both", expand=True)

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

        lbl_val = tk.Label(
            content_box,
            text=str(value),
            font=("Segoe UI", 22, "bold"),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MAIN,
        )
        lbl_val.pack(anchor="w", pady=(8, 2))

        lbl_sub = tk.Label(
            content_box,
            text=subtext,
            font=("Segoe UI", 8),
            bg=self.PANEL_COLOR,
            fg=self.TEXT_MUTED,
        )
        lbl_sub.pack(anchor="w")

    def _load_dashboard(self):
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM [Tb_Check_Pose]")
            total_checks = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(*) FROM [Tb_Check_Pose] WHERE status_pose = 'OK'"
            )
            row_ok = cursor.fetchone()
            total_ok = row_ok[0] if row_ok else 0

            cursor.execute(
                "SELECT COUNT(*) FROM [Tb_Check_Pose] WHERE status_pose = 'NG'"
            )
            row_ng = cursor.fetchone()
            total_ng = row_ng[0] if row_ng else 0

            conn.close()

            pass_rate = (
                (total_ok / total_checks * 100) if total_checks > 0 else 0
            )
            ok_share = (
                (total_ok / total_checks * 100) if total_checks > 0 else 0
            )
            ng_share = (
                (total_ng / total_checks * 100) if total_checks > 0 else 0
            )

            self._create_modern_kpi_card(
                self.cards_container,
                "จำนวนการตรวจทั้งหมด",
                f"{total_checks:,}",
                "รายการทั้งหมดในระบบ",
                self.PRIMARY_BLUE,
                "📊",
            )
            self._create_modern_kpi_card(
                self.cards_container,
                "ผ่านเกณฑ์ (OK)",
                f"{total_ok:,}",
                f"สัดส่วน {ok_share:.1f}% ของทั้งหมด",
                self.COLOR_OK,
                "✅",
            )
            self._create_modern_kpi_card(
                self.cards_container,
                "ไม่ผ่าน (NG)",
                f"{total_ng:,}",
                f"สัดส่วน {ng_share:.1f}% ของทั้งหมด",
                self.COLOR_NG,
                "❌",
            )
            self._create_modern_kpi_card(
                self.cards_container,
                "อัตราการตรวจผ่าน",
                f"{pass_rate:.1f}%",
                "เป้าหมายระบบ > 95.0%",
                "#8B5CF6" if pass_rate >= 90 else "#F59E0B",
                "🎯",
            )

            detail_inner = tk.Frame(
                self.detail_frame, bg=self.PANEL_COLOR, padx=20, pady=20
            )
            detail_inner.pack(fill="both", expand=True)

            tk.Label(
                detail_inner,
                text="📈 สรุปสัดส่วนผลการตรวจสอบ (Status Distribution)",
                font=("Segoe UI", 11, "bold"),
                bg=self.PANEL_COLOR,
                fg=self.TEXT_MAIN,
            ).pack(anchor="w", pady=(0, 15))

            progress_bg = tk.Frame(
                detail_inner, bg=self.BORDER_COLOR, height=20
            )
            progress_bg.pack(fill="x", pady=5)
            progress_bg.pack_propagate(False)

            if total_checks > 0:
                ok_width_ratio = total_ok / total_checks
                ok_bar = tk.Frame(progress_bg, bg=self.COLOR_OK)
                ok_bar.place(
                    relx=0, rely=0, relwidth=ok_width_ratio, relheight=1.0
                )

                ng_bar = tk.Frame(progress_bg, bg=self.COLOR_NG)
                ng_bar.place(
                    relx=ok_width_ratio,
                    rely=0,
                    relwidth=(1 - ok_width_ratio),
                    relheight=1.0,
                )

            legend_frame = tk.Frame(detail_inner, bg=self.PANEL_COLOR)
            legend_frame.pack(fill="x", pady=10)

            tk.Frame(legend_frame, bg=self.COLOR_OK, width=12, height=12).pack(
                side="left", padx=(0, 5)
            )
            tk.Label(
                legend_frame,
                text=f"OK ({ok_share:.1f}%)",
                font=("Segoe UI", 9),
                bg=self.PANEL_COLOR,
                fg=self.TEXT_MUTED,
            ).pack(side="left", padx=(0, 20))

            tk.Frame(legend_frame, bg=self.COLOR_NG, width=12, height=12).pack(
                side="left", padx=(0, 5)
            )
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

    def _get_connection(self):
        server = self.config_data.get("server")
        database = self.config_data.get("database")
        driver = self.config_data.get(
            "driver", "ODBC Driver 17 for SQL Server"
        )
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

    def get_last_id(self):
        selected_table = "Tb_Check_Pose"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = f"SELECT MAX(user_id) FROM [{selected_table}]"
            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()

            if row and row[0] is not None:
                self.lastID = row[0]
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
    root.mainloop()