import json
import pandas as pd
from datetime import datetime
import os
import subprocess
import platform
import re
import pyodbc

class InspectionExporter:
    """ดึงข้อมูลจาก SQL Server และ Export เป็นไฟล์ Excel (.xlsx)."""
    def __init__(self, db_path="db_config.json", output_folder="exports"):
        self.config_path = db_path
        self.output_folder = output_folder

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        table_name = str(config.get("table_name", "Tb_Check_Pose")).strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError("ชื่อ table ไม่ถูกต้อง")
        config["table_name"] = table_name
        return config

    def _get_connection(self, config):
        driver = config.get("driver", "ODBC Driver 17 for SQL Server")
        if config.get("auth_type") == "Windows Authentication":
            connection_string = f"DRIVER={{{driver}}};SERVER={config.get('server')};DATABASE={config.get('database')};Trusted_Connection=yes;"
        else:
            connection_string = f"DRIVER={{{driver}}};SERVER={config.get('server')};DATABASE={config.get('database')};UID={config.get('username')};PWD={config.get('password')};"
        if "18" in driver:
            connection_string += "TrustServerCertificate=yes;"
        return pyodbc.connect(connection_string, timeout=10)

    def export_to_excel(self, start_date=None, end_date=None, auto_open=True):
        """
        ฟังก์ชันดึงข้อมูลจาก DB แล้ว Export ลง Excel
        
        :param start_date: (Optional) วันที่เริ่มต้น รูปแบบ 'YYYY-MM-DD'
        :param end_date: (Optional) วันที่สิ้นสุด รูปแบบ 'YYYY-MM-DD'
        :param auto_open: เปิดไฟล์ Excel ทันทีหลัง Export เสร็จหรือไม่ (True/False)
        :return: (bool, str) ส่งคืน (สถานะความสำเร็จ, ข้อความอธิบาย/Path ไฟล์)
        """
        if not os.path.exists(self.config_path):
            return False, f"ไม่พบไฟล์ตั้งค่าฐานข้อมูล: {self.config_path}"

        conn = None
        try:
            config = self._load_config()
            conn = self._get_connection(config)
            table_name = f"[dbo].[{config['table_name']}]"
            query = f"SELECT user_id, camera_id, status_pose, date_time FROM {table_name}"
            params = []
            conditions = []
            if start_date:
                conditions.append("date_time >= ?")
                params.append(f"{start_date} 00:00:00")
            if end_date:
                conditions.append("date_time <= ?")
                params.append(f"{end_date} 23:59:59")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY date_time DESC"

            df = pd.read_sql_query(query, conn, params=params)

            if df.empty:
                return False, "ไม่พบข้อมูลสถิติในช่วงเวลาที่เลือก"

            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

            file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = os.path.join(self.output_folder, f"Inspection_Report_{file_timestamp}.xlsx")

            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='All_Logs', index=False)
                if 'status_pose' in df.columns:
                    summary_df = df['status_pose'].value_counts().reset_index()
                    summary_df.columns = ['Status', 'Total Count']
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

            if auto_open:
                self._open_file(excel_filename)

            return True, excel_filename

        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการ Export: {str(e)}"
        finally:
            if conn:
                conn.close()

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