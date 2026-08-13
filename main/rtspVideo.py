import cv2
import threading
import time
import run_start.default_config_var as df
class RTSPVideoGrabber:
    def __init__(self, target_fps, src=0):
        self.src = src
        target_fps = df.fps
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps  # 1/15 = 0.0667s
        self.last_read_time = 0

        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock()
        
        # Thread ???????????????????
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        """??????????????????????? Memory ??????????? Buffer ????"""
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.ret = ret
                        self.frame = frame
                else:
                    # ???????????????? (???? ???????) ???????????????????????
                    time.sleep(0.001)
            else:
                time.sleep(0.005)

    def read(self):
        """???????????????????????????"""
        """Main Thread: คุมจังหวะปล่อยเฟรมออกไปใช้งานที่ 15 FPS"""
        now = time.perf_counter()
        elapsed = now - self.last_read_time
        
        # ถ้าดึงภาพเร็วกว่า 15 FPS ให้สั่งรอเวลาที่เหลือ
        if elapsed < self.frame_interval:
            time.sleep(self.frame_interval - elapsed)
            
        self.last_read_time = time.perf_counter()

        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame
            return False, None

    def release(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
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