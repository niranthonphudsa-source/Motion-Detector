import queue
import threading

# สร้าง Queue สำหรับเก็บ Frame รอเขียนลงดิสก์
video_write_queue = queue.Queue()

def video_writer_worker():
    while True:
        item = video_write_queue.get()
        if item is None:
            break
        writer, frame_data = item
        writer.write(frame_data)
        video_write_queue.task_done()

# สตาร์ท Thread เบื้องหลัง
threading.Thread(target=video_writer_worker, daemon=True).start()