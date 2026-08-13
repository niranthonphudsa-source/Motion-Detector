import cv2
import time


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
    rtsp_url = 0
    app = RTSPVideoGrabber(src=rtsp_url, target_fps=15)

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