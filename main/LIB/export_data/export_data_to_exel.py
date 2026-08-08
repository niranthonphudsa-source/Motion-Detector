import sqlite3
import pandas as pd
from datetime import datetime
import os
import subprocess
import platform

class InspectionExporter:
    """
    คลาสสำหรับดึงข้อมูลสถิติจาก SQLite และ Export เป็นไฟล์ Excel (.xlsx)
    """
    def __init__(self, db_path="inspection_stats.db", output_folder="exports"):
        self.db_path = db_path
        self.output_folder = output_folder

    def export_to_excel(self, start_date=None, end_date=None, auto_open=True):
        """
        ฟังก์ชันดึงข้อมูลจาก DB แล้ว Export ลง Excel
        
        :param start_date: (Optional) วันที่เริ่มต้น รูปแบบ 'YYYY-MM-DD'
        :param end_date: (Optional) วันที่สิ้นสุด รูปแบบ 'YYYY-MM-DD'
        :param auto_open: เปิดไฟล์ Excel ทันทีหลัง Export เสร็จหรือไม่ (True/False)
        :return: (bool, str) ส่งคืน (สถานะความสำเร็จ, ข้อความอธิบาย/Path ไฟล์)
        """
        if not os.path.exists(self.db_path):
            return False, f"ไม่พบไฟล์ฐานข้อมูล: {self.db_path}"

        try:
            # 1. เชื่อมต่อฐานข้อมูล
            conn = sqlite3.connect(self.db_path)
            
            # 2. สร้าง SQL Query (รองรับการ Filter วันที่)
            query = "SELECT * FROM inspection_logs"
            params = []
            
            # ปรับแต่งชื่อตารางให้ตรงกับตารางจริงของคุณ (เช่น inspection_logs / stats)
            # ตัวอย่างการกรองตามวันที่ถ้ามีส่งค่ามา
            conditions = []
            if start_date:
                conditions.append("DATE(timestamp) >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(timestamp) <= ?")
                params.append(end_date)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY id DESC"  # เรียงจากล่าสุดไปเก่าสุด

            # 3. อ่านข้อมูลด้วย Pandas
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return False, "ไม่พบข้อมูลสถิติในช่วงเวลาที่เลือก"

            # 4. สร้างโฟลเดอร์ปลายทาง
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

            # 5. ตั้งชื่อไฟล์ตาม วัน-เวลา
            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = os.path.join(self.output_folder, f"Inspection_Report_{file_timestamp}.xlsx")

            # 6. เขียนลงไฟล์ Excel แบบแบ่ง Sheet
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                # Sheet 1: รายการ Log ทั้งหมด
                df.to_excel(writer, sheet_name='All_Logs', index=False)
                
                # Sheet 2: สรุปผล OK / NG
                if 'status' in df.columns:
                    summary_df = df['status'].value_counts().reset_index()
                    summary_df.columns = ['Status', 'Total Count']
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # 7. สั่งเปิดไฟล์อัตโนมัติ (ถ้าเปิด auto_open=True)
            if auto_open:
                self._open_file(excel_filename)

            return True, excel_filename

        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการ Export: {str(e)}"

    def _open_file(self, filepath):
        """ผู้ช่วยสั่งเปิดไฟล์รองรับทั้ง Windows และ OS อื่นๆ"""
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux
                subprocess.call(('xdg-open', filepath))
        except Exception as e:
            print(f"⚠️ ไม่สามารถเปิดไฟล์อัตโนมัติได้: {e}")