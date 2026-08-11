from abc import ABC, abstractmethod
import queue
import threading
from core.context import FrameContext

class BaseEngine(ABC, threading.Thread):
    def __init__(self, in_queue: queue.Queue = None, out_queue: queue.Queue = None):
        super().__init__()
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.running = True
        self.daemon = True

    def run(self):
        while self.running:
            try:
                # ดึง Data Context จาก Queue ก่อนหน้า (Timeout 1 Sec ป้องกันการค้าง)
                ctx: FrameContext = self.in_queue.get(timeout=1.0) if self.in_queue else None
                
                # ประมวลผลใน Engine นั้นๆ
                ctx = self.process(ctx)
                
                # ส่งต่อให้ Queue ถัดไป
                if self.out_queue and ctx is not None:
                    self.out_queue.put(ctx)
                    
            except queue.Empty:
                continue

    @abstractmethod
    def process(self, ctx: FrameContext) -> FrameContext:
        """เขียน Logic การทำงานของแต่ละ Engine ที่นี่"""
        pass

    def stop(self):
        self.running = False