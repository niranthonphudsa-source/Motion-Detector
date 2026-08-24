import threading
import time
import cv2


class RTSPVideoGrabber:

  def __init__(self, target_fps=30, src=0):
    self.src = src
    self.cap = cv2.VideoCapture(src)

    # กำหนด FFmpeg ให้ใช้ TCP และลด Buffer ป้องกัน Latency (ใช้ได้ดีกับ RTSP)
    if isinstance(src, str) and src.startswith("rtsp://"):
      self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not self.cap.isOpened():
      raise RuntimeError(f"ไม่สามารถเปิดวิดีโอ/RTSP source: {src}")

    # ตั้งค่า FPS
    source_fps = self.cap.get(cv2.CAP_PROP_FPS)
    self.target_fps = (
        float(target_fps) if target_fps and target_fps > 0 else 30.0
    )
    if source_fps and source_fps > 0:
      self.target_fps = float(source_fps)

    self.frame_interval = 1.0 / self.target_fps
    self.last_read_time = time.perf_counter()

    # ตัวแปรจัดการ Thread และ Frame Buffer
    self.frame = None
    self.ret = False
    self.running = True
    self.lock = threading.Lock()

    # เริ่ม Background Thread อ่านภาพต่อเนื่อง
    self.thread = threading.Thread(target=self._update, daemon=True)
    self.thread.start()

  def _update(self):
    """Background Thread: อ่านภาพตลอดเวลาเพื่อ Flush Buffer ทิ้ง และเก็บเฉพาะเฟรมล่าสุด"""
    while self.running:
      if not self.cap.isOpened():
        time.sleep(0.01)
        continue

      ret, frame = self.cap.read()
      if ret and frame is not None:
        with self.lock:
          self.ret = ret
          self.frame = frame
      else:
        time.sleep(0.005)

  def read(self):
    """ดึงภาพล่าสุดจาก Memory ทันทีโดยไม่ต้องรอดึงจาก Buffer ของ OpenCV"""
    now = time.perf_counter()
    elapsed = now - self.last_read_time

    # ควบคุม FPS ไม่ให้เกิน Target FPS (ถ้าเรียกถี่เกินไป)
    if elapsed < self.frame_interval:
      time.sleep(self.frame_interval - elapsed)

    self.last_read_time = time.perf_counter()

    with self.lock:
      if not self.ret or self.frame is None:
        return False, None
      # Return สำเนาของภาพล่าสุดเพื่อความปลอดภัย
      return True, self.frame.copy()

  def stop(self):
    """หยุด Thread การทำงาน"""
    self.running = False
    if hasattr(self, 'thread') and self.thread.is_alive():
      self.thread.join(timeout=1.0)

  def release(self):
    """คืนทรัพยากรกล้องและหยุด Thread"""
    self.stop()
    if self.cap is not None:
      self.cap.release()

  def isOpened(self):
    return self.cap.isOpened() if self.cap else False


if __name__ == '__main__':
  rtsp_url = 0
  app = RTSPVideoGrabber(src=rtsp_url, target_fps=15)

  try:
    while True:
      ret, frame = app.read()
      if not ret or frame is None:
        print('ไม่สามารถรับสัญญาณภาพได้')
        time.sleep(0.1)
        continue

      cv2.imshow('RTSP Realtime (No Warp)', frame)
      if cv2.waitKey(1) & 0xFF == ord('q'):
        break
  finally:
    app.release()
    cv2.destroyAllWindows()