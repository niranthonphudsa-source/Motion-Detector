import cv2
import threading
import time
class RTSPVideoGrabber:
    def __init__(self, src, frame_duration):
        self.cap = cv2.VideoCapture(src)
        # ปรับอ่านผ่าน FFMPEG ให้กระชับขึ้น
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # self.cap = cv2.resize(self.cap, (640, 420))
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.delay = frame_duration
        
        # เริ่ม Thread อ่านกล้องเบื้องหลัง
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        self.frame_duration = frame_duration

            
    def _update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.ret = ret
                    self.frame = frame # อัปเดตทับเป็นเฟรมล่าสุดเสมอ (ทิ้งเฟรมเก่า)

            
    def read(self):
        return self.ret, self.frame

    def release(self):
        self.running = False
        self.cap.release()

if __name__ == "__main__":
    app = RTSPVideoGrabber()
    app.check_source_type()
