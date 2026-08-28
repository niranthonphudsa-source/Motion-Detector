import datetime
import os
import cv2

# ---------------------------------------------------------
# ตั้งค่ากล้องและการบันทึก
# ---------------------------------------------------------
CAM_INDEX = 0  # 0 คือกล้อง Default (Webcam)
FRAME_WIDTH = 1920  # ความกว้างภาพ (1280x720 = HD)
FRAME_HEIGHT = 1080  # ความสูงภาพ

# สร้างโฟลเดอร์สำหรับเก็บวิดีโอหากยังไม่มี
output_dir = r"../../ProjectDetection/recordings"
if not os.path.exists(output_dir):
  os.makedirs(output_dir)

# เปิดใช้งานกล้อง
cap = cv2.VideoCapture("rtsp://admin:Aoyama456@10.17.7.246:554/cam/realmonitor?channel=1&subtype=0")

# กำหนดความละเอียดกล้อง
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# ดึงค่าความละเอียดและ FPS จริงจากกล้อง
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0 or fps > 60:
  fps = 30.0  # ค่าตั้งต้นกรณีกล้องไม่ส่งค่า FPS ออกมา

is_recording = False
out = None
filename = ""

print("=== โปรแกรมบันทึกวิดีโอจากกล้อง ===")
print("วิธีใช้งาน:")
print(" - กด 'r' หรือ 'R' : เริ่มต้นบันทึก / หยุดบันทึก")
print(" - กด 'q' หรือ 'Q' : ออกจากโปรแกรม")
print("-----------------------------------")

try:
  while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
      print("❌ ไม่สามารถดึงสัญญาณภาพจากกล้องได้")
      break

    # frame = cv2.resize(frame, (640, 420))
    # สร้าง Frame สำหรับแสดงผล (เพื่อไม่ให้ข้อความสัญลักษณ์ไปโผล่ในวิดีโอจริง)
    display_frame = frame.copy()

    # ---------------------------------------------------------
    # ระบบการบันทึกวิดีโอ
    # ---------------------------------------------------------
    if is_recording:
      # บันทึกเฟรมต้นฉบับลงไฟล์วิดีโอ
      out.write(frame)

      # แสดงจุดสัญลักษณ์บันทึก (REC) บนจอแสดงผล
      cv2.circle(display_frame, (30, 30), 12, (0, 0, 255), -1)
      cv2.putText(
          display_frame,
          "REC",
          (50, 38),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.7,
          (0, 0, 255),
          2,
      )
    else:
      # แสดงสถานะ STANDBY
      cv2.circle(display_frame, (30, 30), 10, (0, 255, 0), -1)
      cv2.putText(
          display_frame,
          "STANDBY",
          (50, 37),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.6,
          (0, 255, 0),
          2,
      )

    # แสดงผลวิดีโอบนหน้าต่าง OpenCV
    cv2.imshow("Camera Recorder", display_frame)

    # ---------------------------------------------------------
    # ตรวจจับการกดปุ่มบนคีย์บอร์ด
    # ---------------------------------------------------------
    key = cv2.waitKey(1) & 0xFF

    # กด 'r' เพื่อเริ่ม/หยุด บันทึก
    if key in (ord("r"), ord("R")):
      is_recording = not is_recording

      if is_recording:
        # สร้างชื่อไฟล์อัตโนมัติจาก วัน-เวลา ปัจจุบัน
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"VideoTrain_{timestamp}.mp4")

        # กำหนด Codec mp4v สำหรับไฟล์ .mp4
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        print(f"🔴 เริ่มบันทึกวิดีโอ: {filename}")
      else:
        if out is not None:
          out.release()
          out = None
        print(f"⏹️ หยุดบันทึก บันทึกไฟล์เรียบร้อยแล้ว: {filename}")

    # กด 'q' เพื่อออกจากโปรแกรม
    elif key in (ord("q"), ord("Q")):
      break

finally:
  # ทำความสะอาดและคืน Resource เมื่อเลิกใช้งาน
  if out is not None:
    out.release()
  cap.release()
  cv2.destroyAllWindows()
  print("ปิดโปรแกรมเรียบร้อยแล้ว")