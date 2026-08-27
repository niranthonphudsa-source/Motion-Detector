import cv2
import queue
import threading


class AsyncVideoWriter:
    """Write video frames outside the detection thread."""

    def __init__(self, filename, fourcc, fps, frame_size, max_queue_size=30):
        self.filename = filename
        self.fourcc = fourcc
        self.fps = fps
        self.frame_size = frame_size
        self.frames = queue.Queue(maxsize=max_queue_size)
        self.closed = False
        self.ready = threading.Event()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()
        self.ready.wait()

    def _run(self):
        writer = cv2.VideoWriter(
            self.filename, self.fourcc, self.fps, self.frame_size
        )
        self.ready.set()
        while True:
            frame = self.frames.get()
            try:
                if frame is None:
                    writer.release()
                    return
                writer.write(frame)
            finally:
                self.frames.task_done()

    def write(self, frame):
        if self.closed:
            return
        frame_copy = frame.copy()
        try:
            self.frames.put_nowait(frame_copy)
        except queue.Full:
            try:
                self.frames.get_nowait()
                self.frames.task_done()
            except queue.Empty:
                return
            try:
                self.frames.put_nowait(frame_copy)
            except queue.Full:
                pass

    def release(self):
        if self.closed:
            return
        self.closed = True
        self.frames.put(None)
        self.frames.join()
        self.worker.join(timeout=2)