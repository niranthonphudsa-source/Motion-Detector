import cv2
import time
import threading
import os

class IntervalSnapshot:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.is_capturing = False
        self.output_dir = "captured_frames"
        self.timer_thread = None
        
        # สร้างโฟลเดอร์สำหรับเก็บภาพถ้ายังไม่มี
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start_capture_loop(self):
        """ ฟังก์ชันลูปภายใน Thread สำหรับบันทึกภาพทุกๆ 1 วินาที """
        print("▶️ เริ่มระบบบันทึกภาพอัตโนมัติ...")
        while self.is_capturing:
            # ดึงเฟรมปัจจุบันจากกล้อง ณ วินาทีนั้น
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # พลิกภาพให้เป็นกระจก (ถ้าต้องการ)
                frame = cv2.flip(frame, 1)
                
                # ตั้งชื่อไฟล์ด้วย Timestamp ป้องกันการซ้ำ
                timestamp = int(time.time())
                filename = f"{self.output_dir}/cap_{timestamp}.jpg"
                
                # เซฟภาพลงเครื่อง
                cv2.imwrite(filename, frame)
                print(f"📸 บันทึกภาพสำเร็จ: {filename}")
            
            # หน่วงเวลา 1 วินาทีก่อนแคปภาพถัดไป
            time.sleep(1.0)

    def run(self):
        print("========================================")
        print("กด [ s ] เพื่อ เริ่มต้น / หยุด การแคปภาพทุก 1 วินาที")
        print("กด [ q ] เพื่อ ปิดโปรแกรม")
        print("========================================")

        while True:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("❌ ไม่สามารถเปิดกล้องได้")
                break

            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()

            # แสดงไฟสถานะบนหน้าจอวิดีโอเพื่อความสะดวกของผู้ใช้
            if self.is_capturing:
                cv2.circle(display_frame, (30, 30), 10, (0, 0, 255), -1) # จุดสีแดง
                cv2.putText(display_frame, "REC (EVERY 1S)", (50, 38), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.circle(display_frame, (30, 30), 10, (128, 128, 128), -1) # จุดสีเทา
                cv2.putText(display_frame, "STANDBY", (50, 38), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2)

            # แสดงผลหน้าจอวิดีโอ
            cv2.imshow("Video Capture Frame", display_frame)

            # รอรับการกดปุ่มบนคีย์บอร์ด
            key = cv2.waitKey(1) & 0xFF

            # 🎯 เงื่อนไขกดปุ่ม 's' เพื่อเริ่มหรือหยุด
            if key == ord('s'):
                if not self.is_capturing:
                    # ถ้ายังไม่ได้แคป -> ให้เริ่มแคป
                    self.is_capturing = True
                    # เปิด Thread ใหม่เพื่อไม่ให้ตัวเวลา sleep(1) ไปขัดขวางการแสดงผลของวิดีโอหลัก
                    self.timer_thread = threading.Thread(target=self.start_capture_loop)
                    self.timer_thread.daemon = True
                    self.timer_thread.start()
                else:
                    # ถ้ากำลังแคปอยู่ -> ให้หยุด
                    self.is_capturing = False
                    print("⏸️ หยุดการบันทึกภาพชั่วคราว")

            # เงื่อนไขกดปุ่ม 'q' เพื่อปิดโปรแกรม
            elif key == ord('q'):
                self.is_capturing = False
                break

        # คืนทรัพยากรกล้อง
        self.cap.release()
        cv2.destroyAllWindows()
        print("🚪 ปิดโปรแกรมเรียบร้อย")

if __name__ == "__main__":
    # สามารถเปลี่ยนเลข 0 เป็น 1 ได้หากต่อกล้องเว็บแคมแยก
    app = IntervalSnapshot(src=1)
    app.run()