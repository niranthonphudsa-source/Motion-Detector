import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

class StatsGUI:
    def __init__(self, db_path=r"setting\inspection_stats.db"):
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

import tkinter as tk
from tkinter import ttk

class StatsManager:
    def __init__(self, db_path="stats.db"):
        self.db_path = db_path
        self.root = None  # บันทึกตัวแปรเก็บหน้าต่างไว้

    def open_dashboard(self):
        # 1. เช็กว่าหน้าต่างเปิดค้างผู้อยู่แล้วหรือไม่
        if self.root is not None:
            try:
                if self.root.winfo_exists():
                    self.root.lift()
                    self.root.focus_force()
                    return
            except Exception:
                self.root = None

        # 2. สร้างหน้าต่าง GUI
        self.root = tk.Tk()
        self.root.title("📊 Inspection Statistics Dashboard")
        self.root.geometry("1000x700")

        def on_closing():
            if self.root:
                self.root.destroy()
                self.root = None

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # --- ส่วนควบคุมด้านบน (Filter Dropdown) ---
        filter_frame = ttk.Frame(self.root, padding=10)
        filter_frame.pack(fill="x")

        ttk.Label(filter_frame, text="ช่วงเวลา: ", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        
        range_var = tk.StringVar(value="Today")
        range_dropdown = ttk.Combobox(
            filter_frame, 
            textvariable=range_var, 
            values=["Today", "Last 7 Days", "This Month", "This Year", "All Time"],
            state="readonly",
            width=15
        )
        range_dropdown.pack(side="left", padx=5)

        # --- ส่วนแสดง Summary Cards (4 ช่อง) ---
        cards_frame = ttk.Frame(self.root, padding=10)
        cards_frame.pack(fill="x")

        # ปรับให้ทั้ง 4 คอลัมน์ ขยายขนาดเท่าๆ กัน
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        card_total, lbl_total = self._create_card(cards_frame, "TOTAL CHECK", "0", "#2196F3", 0)
        card_ok, lbl_ok = self._create_card(cards_frame, "OK COUNT", "0", "#4CAF50", 1)
        card_ng, lbl_ng = self._create_card(cards_frame, "NG COUNT", "0", "#F44336", 2)
        card_yield, lbl_yield = self._create_card(cards_frame, "YIELD RATE", "0.0%", "#FF9800", 3)

        # --- ส่วนแสดงกราฟ (Chart Frame) ---
        chart_frame = ttk.Frame(self.root, padding=10)
        chart_frame.pack(fill="both", expand=True)

        # ฟังก์ชันอัปเดตข้อมูลเมื่อเปลี่ยนตัวเลือก Dropdown
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

        # โหลดข้อมูลแสดงผลครั้งแรกทันทีที่เปิดหน้าต่าง
        refresh_data()

        self.root.mainloop()

    def _create_card(self, parent, title, value, color, column):
        frame = tk.Frame(parent, bg=color, padx=15, pady=15)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        
        lbl_title = tk.Label(frame, text=title, fg="white", bg=color, font=("Helvetica", 10, "bold"))
        lbl_title.pack(anchor="w")
        
        lbl_val = tk.Label(frame, text=value, fg="white", bg=color, font=("Helvetica", 20, "bold"))
        lbl_val.pack(anchor="e")
        
        return frame, lbl_val

    def update_dashboard(self, selected_range, lbl_ok, lbl_ng, lbl_total, lbl_yield, chart_frame):
        # คำนวณช่วงเวลา Query
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

        # ดึงข้อมูลจาก DB
        conn = sqlite3.connect(self.db_path)
        query = f"SELECT timestamp, camera_id, status FROM inspection_logs WHERE timestamp >= '{start_date}'"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # สรุปตัวเลข
        total = len(df)
        ok_count = len(df[df['status'] == 'OK'])
        ng_count = len(df[df['status'] == 'NG'])
        yield_rate = (ok_count / total * 100) if total > 0 else 0.0

        lbl_total.config(text=str(total))
        lbl_ok.config(text=str(ok_count))
        lbl_ng.config(text=str(ng_count))
        lbl_yield.config(text=f"{yield_rate:.1f}%")

        # ล้างกราฟเก่าออก
        for widget in chart_frame.winfo_children():
            widget.destroy()

        if df.empty:
            ttk.Label(chart_frame, text="ไม่พบข้อมูลในช่วงเวลาที่เลือก", font=("Arial", 14)).pack(pady=50)
            return

        # สร้าง Matplotlib Figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), dpi=100)

        # กราฟวงกลม (Pie Chart)
        labels = ['OK', 'NG']
        counts = [ok_count, ng_count]
        colors = ['#4CAF50', '#F44336']
        if sum(counts) > 0:
            ax1.pie(counts, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, explode=(0, 0.1))
        ax1.set_title("Status Ratio")

        # กราฟแท่งตามกล้อง (Bar Chart)
        cam_stats = df.groupby(['camera_id', 'status']).size().unstack(fill_value=0)
        cam_stats.plot(kind='bar', ax=ax2, color={'OK': '#4CAF50', 'NG': '#F44336'})
        ax2.set_title("Camera Breakdown")
        ax2.set_xlabel("Camera ID")
        ax2.set_ylabel("Count")
        plt.tight_layout()

        # วาดกราฟลง Tkinter Canvas
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)