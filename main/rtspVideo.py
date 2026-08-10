import cv2
import threading
import time

class RTSPVideoGrabber:
    def __init__(self, target_fps, src=0):
        self.src = src
        self.target_fps = target_fps
        # คำนวณช่วงเวลาห่างระหว่างเฟรม (เช่น 15 FPS = 0.066 วินาที/เฟรม)
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0
        self.cap = cv2.VideoCapture(src)
        # ตั้งค่า Buffer Size ให้เล็กที่สุดเพื่อลด Latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock() # ป้องกัน Race Condition
        self.last_read_time = 0
        
        # เริ่ม Thread อ่านกล้องเบื้องหลัง
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        """Thread เบื้องหลัง: มีหน้าที่เคลียร์ Buffer และเก็บเฟรมล่าสุดตลอดเวลา"""
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.ret = ret
                        self.frame = frame
            # ให้ CPU ได้พักเล็กน้อย ไม่ให้รัน 100%
            time.sleep(0.005)

    def read(self):
        """Main Thread: ดึงเฟรมไป Detect โดยคุมความเร็ว FPS ตาม target_fps"""
        if self.target_fps > 0:
            now = time.time()
            elapsed = now - self.last_read_time
            
            # ถ้าเรียก read() ถี่เกินไป ให้หน่วงเวลาตาม target_fps
            if elapsed < self.frame_interval:
                time.sleep(self.frame_interval - elapsed)
            
            self.last_read_time = time.time()

        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return self.ret, None

    def release(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()

# ---------------------------------------------------------
# ตัวอย่างการใช้งาน
# ---------------------------------------------------------
if __name__ == "__main__":
    # กำหนด target_fps=15 เพื่อจำกัดการดึงภาพไป Detect ที่ 15 FPS
    rtsp_url = 0  # หรือใส่ "rtsp://admin:password@192.168.1.xxx:554/..."
    app = RTSPVideoGrabber(src=rtsp_url, target_fps=15)

    try:
        while True:
            ret, frame = app.read()
            if not ret or frame is None:
                print("ไม่สามารถรับสัญญาณภาพได้")
                continue

            # นำ frame ไปผ่าน Model Detect ของคุณตรงนี้
            cv2.imshow("RTSP Limited FPS", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        app.release()
        cv2.destroyAllWindows()