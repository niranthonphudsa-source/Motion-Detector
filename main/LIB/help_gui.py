import tkinter as tk
from tkinter import ttk

class HelpGUI:
    def __init__(self, key_callback=None):
        """
        :param key_callback: ฟังก์ชันสำหรับส่งรหัสปุ่มกดกลับไปยัง main.py
        """
        self.key_callback = key_callback
        self.root = None

    def open_window(self):
        # ถ้าหน้าต่างเปิดอยู่แล้ว ให้อยู่ข้างหน้า ไม่สร้างซ้ำ
        if self.root is not None and self.root.winfo_exists():
            self.root.lift()
            return

        self.root = tk.Tk()
        self.root.title("⌨️ Keyboard Shortcuts & Controls")
        self.root.geometry("420x520")
        self.root.attributes("-topmost", True)  # แสดงอยู่บนสุดเสมอ

        # ตกแต่งสไตล์
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padding=4)

        title_label = ttk.Label(
            self.root, 
            text="🎮 เมนูควบคุมระบบ (Key Controls)", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=10)

        # รายการปุ่มกด (Text ปุ่ม, คำอธิบาย, Char Code)
        buttons_info = [
            ("1", "✏️ วาด Polygon ROI", '1'),
            ("3", "🟢 กำหนดจุด Start Point", '3'),
            ("4", "🔴 กำหนดจุด Reverse Point", '4'),
            ("2", "💾 บันทึก Config (Save)", '2'),
            ("C", "🧹 ล้างพิกัดบนหน้าจอ", 'c'),
            ("S", "⚙️ เปิดหน้าต่างตั้งค่า (Settings)", 's'),
            ("D", "📊 เปิดหน้า Dashboard", 'd'),
            ("O", "📈 เปิดหน้า SSMS GUI", 'o'),
            ("Q", "❌ ปิดโปรแกรม (Quit)", 'q'),
        ]

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        for key_text, desc, char_val in buttons_info:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill="x", pady=3)

            # ปุ่มกดฝั่งซ้าย
            btn = ttk.Button(
                row_frame, 
                text=f" กด [{key_text}] ", 
                width=10,
                command=lambda c=char_val: self._trigger_key(c)
            )
            btn.pack(side="left", padx=5)

            # คำอธิบายฝั่งขวา
            lbl = ttk.Label(row_frame, text=desc, font=("Helvetica", 10))
            lbl.pack(side="left", padx=5)

        # เมื่อกดปิดหน้าต่าง X
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _trigger_key(self, char_val):
        """ส่งรหัสอักขระไปยัง main.py (ถ้ามี)"""
        if self.key_callback:
            self.key_callback(ord(char_val))
            print(f"👉 [Help GUI] Triggered Key: '{char_val}'")
        else:
            print(f"ℹ️ [Help GUI Standalone] Clicked: '{char_val}' (ไม่ได้เชื่อมต่อกับ main.py)")

    def _on_close(self):
        if self.root:
            self.root.destroy()
            self.root = None

# =========================================================
# 🚀 บล็อกนี้ช่วยให้สามารถสั่งรัน python help_gui.py เดี่ยวๆ ได้
# =========================================================
if __name__ == "__main__":
    print("💡 เปิดหน้าต่าง Help GUI ในโหมด Standalone...")
    app = HelpGUI()
    app.open_window()