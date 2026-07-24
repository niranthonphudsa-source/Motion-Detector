import cv2
import threading
import time
class RTSPVideoGrabber:
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        # ปรับอ่านผ่าน FFMPEG ให้กระชับขึ้น
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.running = True
        
        # เริ่ม Thread อ่านกล้องเบื้องหลัง
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.ret = ret
                    self.frame = frame # อัปเดตทับเป็นเฟรมล่าสุดเสมอ (ทิ้งเฟรมเก่า)
            time.sleep(0.005) # หน่วงนิดหน่อยไม่ให้กิน CPU เกินไป

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()
