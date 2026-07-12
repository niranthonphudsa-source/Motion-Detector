import cv2
import threading

class VideoCaptureThread:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.ret, self.frame = False, None
        self.is_running = True
        
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while self.is_running:
            self.ret, self.frame = self.cap.read()
            time.sleep(0.01)

    def get_frame(self):
        return self.ret, self.frame

    def release(self):
        self.is_running = False
        self.cap.release()

    def change_src(self, src):
        self.release()
        self.cap = cv2.VideoCapture(src)
        self.is_running = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()