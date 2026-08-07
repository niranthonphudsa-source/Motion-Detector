import cv2
import threading
import time
class RTSPVideoGrabber:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        # ปรับอ่านผ่าน FFMPEG ให้กระชับขึ้น
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # self.cap = cv2.resize(self.cap, (640, 420))
        self.ret, self.frame = self.cap.read()
        self.running = True
        # เริ่ม Thread อ่านกล้องเบื้องหลัง
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

            
    def _update(self):
        while self.running:
            if self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
                # self.frame = cv2.resize(self.frame, (640, 420))
                if self.ret:
                    self.ret = self.ret
                    self.frame = self.frame # อัปเดตทับเป็นเฟรมล่าสุดเสมอ (ทิ้งเฟรมเก่า)
            time.sleep(0.01)
            
    def read(self):
        return self.ret, self.frame

    def release(self):
        self.running = False
        self.cap.release()

if __name__ == "__main__":
    app = RTSPVideoGrabber()
    app.check_source_type()
