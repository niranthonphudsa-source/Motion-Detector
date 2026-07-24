from dataclasses import dataclass, field
import numpy as np
from typing import Any, Dict, List

@dataclass
class FrameContext:
    frame_id: int
    frame: np.ndarray                      # ภาพต้นฉบับ
    annotated_frame: np.ndarray = None     # ภาพที่วาดผลลัพธ์แล้ว
    detections: List[Any] = field(default_factory=list) # ค่าจาก Detection
    tracks: List[Any] = field(default_factory=list)     # ค่าจาก Tracking (IDs, BBoxes)
    inspection_results: Dict[str, Any] = field(default_factory=dict) # ผลการตรวจ ROI
    metadata: Dict[str, Any] = field(default_factory=dict) # Timestamp, Camera ID