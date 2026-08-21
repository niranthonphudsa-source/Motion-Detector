import cv2
import time
import threading

class RTSPVideoGrabber:
    def __init__(self, target_fps=30, src=0):
        self.src = src
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise RuntimeError(f"ไม่สามารถเปิดวิดีโอ/RTSP source: {src}")

        # ล็อก Buffer Size ให้เหลือ 1 เฟรม
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.ret = False
        self.frame = None
        self.running = True

        # ควบคุม FPS ในการดึงเฟรมไปใช้งาน
        source_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.target_fps = float(target_fps) if target_fps and target_fps > 0 else 30.0
        if source_fps and source_fps > 0:
            self.target_fps = float(source_fps)
        self.frame_interval = 1.0 / self.target_fps
        self.last_grab_time = 0

        # สร้าง Thread แยกสำหรับอ่านภาพจากกล้องตลอดเวลา (ป้องกันภาพค้างสะสมใน Buffer)
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._update_frame, daemon=True)
        self.thread.start()

    def _update_frame(self):
        """Thread ย่อย: ดึงเฟรมจาก OpenCV ออกจาก Buffer ให้เร็วที่สุดเพื่อไม่ให้เกิด Delay"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        """อ่านเฟรมล่าสุด โดยคุม FPS ฝั่ง Consumer ไม่ให้เรียกถี่เกินไป"""
        now = time.perf_counter()
        elapsed = now - self.last_grab_time

        # ถ้ารายงานภาพเร็วกว่า target_fps ให้หน่วงเฉพาะเวลาดึงไปใช้ (ไม่กระทบการอ่านจากกล้อง)
        if elapsed < self.frame_interval:
            time.sleep(self.frame_interval - elapsed)

        with self.lock:
            self.last_grab_time = time.perf_counter()
            return self.ret, self.frame

    def release(self):
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


if __name__ == "__main__":
    rtsp_url = 0  # เปลี่ยนเป็น RTSP URL เช่น "rtsp://admin:12345@192.168.1.100:554/stream1"
    app = RTSPVideoGrabber(src=rtsp_url, target_fps=30)

    try:
        while True:
            ret, frame = app.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            cv2.imshow("RTSP Realtime (No Lag)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        app.release()
        cv2.destroyAllWindows()