import subprocess

def speed_up_video(input_file, output_file, speed=2.0):
    # คำนวณค่า setpts สำหรับวิดีโอ (ความเร็ว 2 เท่า ค่า PTS ต้องลดครึ่งหนึ่ง คือ 1/2 = 0.5)
    video_filter = f"setpts={1/speed}*PTS"
    # คำนวณค่า atempo สำหรับเสียง (สามารถซ้อนกันได้ถ้าเร่งเกิน 2 เท่า เช่น atempo=2.0,atempo=2.0)
    audio_filter = f"atempo={speed}"
    
    # สร้าง Command สำหรับ FFmpeg
    command = [
        'ffmpeg', '-i', input_file,
        '-filter:v', video_filter,
        '-filter:a', audio_filter,
        '-y', output_file # -y เพื่อเซฟทับไฟล์เดิมถ้ามีอยู่แล้ว
    ]
    
    # รันคำสั่ง
    subprocess.run(command)

# เรียกใช้งาน: เร่งความเร็ววิดีโอ input.mp4 เป็น 2 เท่า
speed_up_video("Screen Recording 2026-07-14 111101.mp44", "output_ffmpeg.mp4", speed=2.0)
print("เร่งความเร็วด้วย FFmpeg สำเร็จ!")