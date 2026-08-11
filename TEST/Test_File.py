import os
import time

def create_mock_old_file(folder_path, filename="test_old_video.mp4", days_ago=35):
    """
    สร้างไฟล์วิดีโอจำลอง แล้วย้อนเวลาแก้ไขล่าสุด (mtime) กลับไปตามจำนวนวันที่กำหนด
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = os.path.join(folder_path, filename)

    # 1. สร้างไฟล์เปล่าขนาดเล็กขึ้นมา
    with open(filepath, "wb") as f:
        f.write(b"MOCK VIDEO DATA" * 1000)

    # 2. คำนวณเวลาในอดีต (1 วัน = 86,400 วินาที)
    now = time.time()
    past_time = now - (days_ago * 86400)

    # 3. สั่งเปลี่ยนเวลา atime (Access Time) และ mtime (Modified Time) ของไฟล์
    os.utime(filepath, (past_time, past_time))

    print(f"✅ สร้างไฟล์ทดสอบสำเร็จ: {filename}")
    print(f"📅 กำหนดวันที่แก้ไขเป็น: {days_ago} วันที่แล้ว")

# 🧪 ทดลองสร้างไฟล์เก่า 35 วันในโฟลเดอร์ video_center
create_mock_old_file("video_center", "old_video_35days.mp4", days_ago=35)
create_mock_old_file("video_center", "new_video_5days.mp4", days_ago=5)