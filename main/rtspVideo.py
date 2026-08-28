import cv2
import time

<<<<<<< HEAD

class RTSPVideoGrabber:
    def __init__(self, target_fps=30, src=0):
        self.src = src
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise RuntimeError(f"ไม่สามารถเปิดวิดีโอ/RTSP source: {src}")

        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # ใช้ FPS จริงจาก source ถ้า source ไม่ส่งค่าออกมา ให้ใช้ค่าจาก target_fps
        source_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.target_fps = float(target_fps) if target_fps and target_fps > 0 else 30.0
        if source_fps is None or source_fps <= 0:
            source_fps = self.target_fps
        self.target_fps = float(source_fps)
        self.frame_interval = 1.0 / self.target_fps
        self.last_read_time = time.perf_counter()
=======
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
        self.frame = cv2.resize(self.frame, (2560, 1440))
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
                else:
                    break
            # ให้ CPU ได้พักเล็กน้อย ไม่ให้รัน 100%
            time.sleep(0.001)
>>>>>>> test-checkout-comit

    def read(self):
        """อ่านเฟรมตาม FPS จริงของ source เพื่อไม่ให้เล่นเร็วเกินเวลา"""
        while True:
            now = time.perf_counter()
            elapsed = now - self.last_read_time
            if elapsed < self.frame_interval:
                time.sleep(self.frame_interval - elapsed)
                continue

            self.last_read_time = time.perf_counter()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return False, None
            return True, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


if __name__ == "__main__":
<<<<<<< HEAD
    rtsp_url = 0
    app = RTSPVideoGrabber(src=rtsp_url, target_fps=15)
=======
    # กำหนด target_fps=15 เพื่อจำกัดการดึงภาพไป Detect ที่ 15 FPS
    rtsp_url = 0  # หรือใส่ "rtsp://admin:password@192.168.1.xxx:554/..."
    app = RTSPVideoGrabber(src=rtsp_url, target_fps=60)
>>>>>>> test-checkout-comit

    try:
        while True:
            ret, frame = app.read()
            if not ret or frame is None:
                print("ไม่สามารถรับสัญญาณภาพได้")
                time.sleep(0.1)
                continue

            cv2.imshow("RTSP Limited FPS", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        app.release()
        cv2.destroyAllWindows()