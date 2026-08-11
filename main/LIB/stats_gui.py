import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from LIB.export_data.export_data_to_exel import InspectionExporter
# from main.app.run_app_combined import ConfigManager, SSMSConnectGUI

class StatsGUI:
    def __init__(self, db_path=r"db_config.json"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """สร้างตาราง SQLite สำหรับเก็บสถิติถ้ายังไม่มี"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                camera_id TEXT,
                status TEXT,
                user_id INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def log_event(self, camera_id, status, user_id):
        """ฟังก์ชันสำหรับ call จาก Main Loop เพื่อบันทึกผล"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO inspection_logs (timestamp, camera_id, status, user_id)
            VALUES (?, ?, ?, ?)
        ''', (now_str, camera_id, status, user_id))
        conn.commit()
        conn.close()


class StatsManager:
    def __init__(self, db_path=r"setting\inspection_stats.db"):
        self.db_path = db_path
        self.root = None
        self.fig = None 

    def handle_export_excel(self):
        """ฟังก์ชันจัดการเมื่อผู้ใช้กดปุ่ม Export"""
        exporter = InspectionExporter(db_path=self.db_path)
        success, message = exporter.export_to_excel(auto_open=True)
        
        if success:
            messagebox.showinfo("สำเร็จ", f"Export ข้อมูลเรียบร้อยแล้ว!\n\nไฟล์: {message}")
        else:
            messagebox.showwarning("ข้อผิดพลาด", message)

    def open_dashboard(self):
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.lift()
                    self.root.focus_force()
                    return
            except Exception:
                self.root = None

        # ─── โทนสีหลักของ Dashboard (White & Blue Theme) ───
        BG_COLOR = "#F8FAFC"        # สีพื้นหลังหลัก (ขาวนวล/ฟ้าอ่อนสว่าง)
        PANEL_COLOR = "#FFFFFF"     # สีพื้นหลังการ์ด/กล่อง (ขาวบริสุทธิ์)
        BORDER_COLOR = "#E2E8F0"    # สีขอบกล่อง (เทาอ่อน)
        TEXT_MAIN = "#0F172A"       # สีตัวหนังสือหลัก (น้ำเงินเข้มเกือบดำ)
        TEXT_MUTED = "#64748B"      # สีตัวหนังสือรอง (เทาอมน้ำเงิน)
        PRIMARY_BLUE = "#2563EB"    # สีน้ำเงินสว่างสำหรับปุ่ม/จุดเน้น

        self.root = tk.Tk()
        self.root.title("Inspection Analytics & Statistics Dashboard")
        self.root.geometry("1400x850")
        self.root.configure(bg=BG_COLOR)

        # 🎨 ตั้งค่า Style ให้กับ TTK Widget
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(".", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Panel.TFrame", background=PANEL_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_MAIN)
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#1E3A8A", background=BG_COLOR)
        
        # Style ปุ่ม Export (น้ำเงินสด)
        style.configure(
            "Accent.TButton", 
            font=("Segoe UI", 10, "bold"), 
            background=PRIMARY_BLUE, 
            foreground="#FFFFFF", 
            borderwidth=0, 
            padding=(12, 8)
        )
        style.map("Accent.TButton", background=[("active", "#1D4ED8")])

        # Style Combobox Dropdown
        style.configure("TCombobox", fieldbackground=PANEL_COLOR, background=PANEL_COLOR, foreground=TEXT_MAIN, padding=5)

        try:
            self.root.iconphoto(r"main\Logo\atc_logo.png")
        except Exception:
            pass

        # ─── 1. HEADER SECTION ───
        header_frame = ttk.Frame(self.root, padding=(25, 20, 25, 10))
        header_frame.pack(fill="x")

        # Logo
        try:
            self.logo_icon = tk.PhotoImage(file=r"main\Logo\atc_logo.png").subsample(2, 2)
            lbl_logo = ttk.Label(header_frame, image=self.logo_icon)
            lbl_logo.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด Icon ได้: {e}")

        # Title + Subtitle
        title_box = ttk.Frame(header_frame)
        title_box.pack(side="left")
        
        lbl_title = ttk.Label(title_box, text="Inspection Analytics", style="Header.TLabel")
        lbl_title.pack(anchor="w")
        
        lbl_sub = tk.Label(title_box, text="Real-time Quality & Performance Monitoring System", fg=TEXT_MUTED, bg=BG_COLOR, font=("Segoe UI", 9))
        lbl_sub.pack(anchor="w")

        # ─── 2. FILTER & TOOLBAR SECTION ───
        toolbar_frame = tk.Frame(self.root, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        toolbar_frame.pack(fill="x", padx=25, pady=(10, 15), ipady=5)

        # Toolbar Content Container
        tb_inner = tk.Frame(toolbar_frame, bg=PANEL_COLOR)
        tb_inner.pack(fill="x", padx=15, pady=5)

        tk.Label(tb_inner, text="PERIOD RANGE:", fg="#1E3A8A", bg=PANEL_COLOR, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))

        range_var = tk.StringVar(value="Today")
        range_dropdown = ttk.Combobox(
            tb_inner, 
            textvariable=range_var, 
            values=["Today", "Last 7 Days", "This Month", "This Year", "All Time"],
            state="readonly",
            width=16
        )
        range_dropdown.pack(side="left")

        # Export Button
        btn_export = ttk.Button(
            tb_inner, 
            text="📥 Export Excel Report", 
            style="Accent.TButton",
            command=self.handle_export_excel
        )
        btn_export.pack(side="right")

        def on_closing():
            if self.fig:
                plt.close(self.fig)
            if self.root:
                self.root.destroy()
                self.root = None

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # ─── 3. KPI SUMMARY CARDS (4 CARDS) ───
        cards_frame = ttk.Frame(self.root, padding=(25, 0, 25, 15))
        cards_frame.pack(fill="x")

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        # การ์ดขาว ขอบเน้นสีน้ำเงินและสถานะ
        _, lbl_total = self._create_kpi_card(cards_frame, "TOTAL INSPECTION", "0", "Total items scanned", "#2563EB", 0)
        _, lbl_ok = self._create_kpi_card(cards_frame, "PASSED (OK)", "0", "Passed items", "#059669", 1)
        _, lbl_ng = self._create_kpi_card(cards_frame, "REJECTED (NG)", "0", "Defects detected", "#DC2626", 2)
        _, lbl_yield = self._create_kpi_card(cards_frame, "YIELD RATE", "0.0%", "Pass percentage", "#D97706", 3)

        # ─── 4. CHARTS SECTION ───
        chart_frame = tk.Frame(self.root, bg=PANEL_COLOR, highlightbackground=BORDER_COLOR, highlightthickness=1)
        chart_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        def refresh_data(event=None):
            self.update_dashboard(
                range_var.get(), 
                lbl_ok, 
                lbl_ng, 
                lbl_total, 
                lbl_yield, 
                chart_frame
            )

        range_dropdown.bind("<<ComboboxSelected>>", refresh_data)
        refresh_data()

    def update_window(self):
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.update_idletasks()
                    self.root.update()
            except Exception:
                self.root = None

    def _create_kpi_card(self, parent, title, value, subtitle, accent_color, column):
        """สร้างการ์ด KPI สไตล์ White & Blue Modern Light"""
        CARD_BG = "#FFFFFF"
        BORDER_COLOR = "#E2E8F0"
        
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=column, padx=8, pady=0, sticky="nsew")
        
        # แถบสีด้านบนการ์ด
        top_bar = tk.Frame(card, bg=accent_color, height=4)
        top_bar.pack(fill="x", side="top")

        content = tk.Frame(card, bg=CARD_BG, padx=18, pady=12)
        content.pack(fill="both", expand=True)

        lbl_title = tk.Label(content, text=title, fg="#64748B", bg=CARD_BG, font=("Segoe UI", 9, "bold"))
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(content, text=value, fg="#1E3A8A", bg=CARD_BG, font=("Segoe UI", 22, "bold"))
        lbl_val.pack(anchor="w", pady=(4, 0))

        lbl_sub = tk.Label(content, text=subtitle, fg="#94A3B8", bg=CARD_BG, font=("Segoe UI", 8))
        lbl_sub.pack(anchor="w")

        return card, lbl_val

    def update_dashboard(self, selected_range, lbl_ok, lbl_ng, lbl_total, lbl_yield, chart_frame):
        now = datetime.now()
        if selected_range == "Today":
            start_date = now.strftime("%Y-%m-%d 00:00:00")
        elif selected_range == "Last 7 Days":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        elif selected_range == "This Month":
            start_date = now.strftime("%Y-%m-01 00:00:00")
        elif selected_range == "This Year":
            start_date = now.strftime("%Y-01-01 00:00:00")
        else:
            start_date = "1970-01-01 00:00:00"

        try:
            conn = sqlite3.connect(self.db_path)
            query = f"SELECT timestamp, camera_id, status FROM inspection_logs WHERE timestamp >= '{start_date}'"
            df = pd.read_sql_query(query, conn)
            conn.close()
        except Exception as e:
            print(f"❌ Error Reading DB: {e}")
            df = pd.DataFrame(columns=['timestamp', 'camera_id', 'status'])

        total = len(df)
        ok_count = len(df[df['status'] == 'OK'])
        ng_count = len(df[df['status'] == 'NG'])
        yield_rate = (ok_count / total * 100) if total > 0 else 0.0

        lbl_total.config(text=f"{total:,}")
        lbl_ok.config(text=f"{ok_count:,}")
        lbl_ng.config(text=f"{ng_count:,}")
        lbl_yield.config(text=f"{yield_rate:.1f}%")

        # ล้าง Canvas เก่า
        for widget in chart_frame.winfo_children():
            widget.destroy()

        if self.fig:
            plt.close(self.fig)

        if df.empty:
            no_data_lbl = tk.Label(
                chart_frame, 
                text="📊 No inspection data available for the selected period", 
                fg="#64748B", 
                bg="#FFFFFF", 
                font=("Segoe UI", 12)
            )
            no_data_lbl.pack(expand=True)
            return

        # ─── ตกแต่ง MATPLOTLIB CHARTS (LIGHT MODE / BLUE THEME) ───
        plt.style.use('default')
        self.fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=100)
        self.fig.patch.set_facecolor('#FFFFFF')

        TEXT_COLOR = "#1E3A8A"
        COLOR_OK = '#059669'   # เขียวสว่าง
        COLOR_NG = '#DC2626'   # แดงสว่าง

        # 🍩 1. Donut Chart (Status Ratio)
        labels = ['OK', 'NG']
        counts = [ok_count, ng_count]
        colors = [COLOR_OK, COLOR_NG]

        if sum(counts) > 0:
            wedges, texts, autotexts = ax1.pie(
                counts, 
                labels=labels, 
                autopct='%1.1f%%', 
                colors=colors, 
                startangle=90,
                pctdistance=0.75,
                textprops=dict(color=TEXT_COLOR, fontsize=10, weight="bold"),
                wedgeprops=dict(width=0.4, edgecolor='#FFFFFF', linewidth=3)
            )
            for autotext in autotexts:
                autotext.set_color('#FFFFFF')

        ax1.set_title("Overall Pass/Fail Ratio", color=TEXT_COLOR, fontsize=12, pad=15, weight="bold")
        ax1.set_facecolor('#FFFFFF')

        # 📊 2. Bar Chart (Camera Breakdown)
        cam_stats = df.groupby(['camera_id', 'status']).size().unstack(fill_value=0)
        
        for st in ['OK', 'NG']:
            if st not in cam_stats.columns:
                cam_stats[st] = 0

        cam_stats[['OK', 'NG']].plot(
            kind='bar', 
            ax=ax2, 
            color={'OK': COLOR_OK, 'NG': COLOR_NG}, 
            width=0.5,
            edgecolor="none"
        )

        ax2.set_title("Breakdown by Camera", color=TEXT_COLOR, fontsize=12, pad=15, weight="bold")
        ax2.set_xlabel("Camera ID", color="#64748B", fontsize=9, labelpad=8)
        ax2.set_ylabel("Inspection Count", color="#64748B", fontsize=9)
        ax2.set_facecolor('#FFFFFF')
        ax2.tick_params(colors="#334155", labelsize=9)
        ax2.grid(axis='y', color='#F1F5F9', linestyle='--', alpha=1.0)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#CBD5E1')
        ax2.spines['bottom'].set_color('#CBD5E1')
        
        # Custom Legend
        leg = ax2.legend(frameon=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')
        for text in leg.get_texts():
            text.set_color("#334155")

        plt.tight_layout()

        # วาดกราฟลงบน Canvas
        canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)