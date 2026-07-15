import cv2
import numpy as np
from ultralytics import YOLO

# 1. โหลดโมเดล YOLO Pose และตั้งกล้อง
model = YOLO('yolo26n-pose.pt')
cap = cv2.VideoCapture(0)

# กำหนดกรอบพิกัด ROI แบบ Hard-coded ตรงๆ ในโค้ด (x1, y1, x2, y2)
# สมมุติเป็นกล่องขนาด 200x200 บริเวณกลางจอ (ปรับเปลี่ยนตัวเลขได้ตามต้องการ)
roi_rect = (200, 150, 400, 350) 

while True:
    ret, frame = cap.read()
    if not ret: 
        break

    # สั่ง YOLO ประมวลผลหาจุดพิกัดร่างกาย
    results = model.predict(source=frame, conf=0.7, verbose=False)

    head_inside_roi = False  # สถานะเช็คว่าหูอยู่ในกรอบไหม

    for result in results:
        if result.keypoints is not None:
            # ดึงอาเรย์พิกัดออกมา
            keypoints_list = result.keypoints.xy.cpu().numpy()
            
            for keypoints in keypoints_list:
                if len(keypoints) < 17: 
                    continue 
                
                # วนลูปเช็คทุกจุดเพื่อวาดตำแหน่งและเลข Index
                for idx, kp in enumerate(keypoints):
                    kpx, kpy = int(kp[0]), int(kp[1])
                    
                    # ข้ามจุดที่มองไม่เห็น (พิกัดเป็น 0, 0)
                    if kpx == 0 and kpy == 0: 
                        continue
                        
                    # วาดจุดข้อต่อและเลข Index กำกับ (0-16)
                    cv2.circle(frame, (kpx, kpy), 4, (255, 255, 0), cv2.FILLED)
                    cv2.putText(frame, str(idx), (kpx, kpy - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    
                    # 🎯 เช็คตรงๆ: ถ้าเป็นหูซ้าย (3) หรือหูขวา (4)
                    if idx in [3, 4]:
                        x1, y1, x2, y2 = roi_rect
                        xmin, xmax = min(x1, x2), max(x1, x2)
                        ymin, ymax = min(y1, y2), max(y1, y2)
                        
                        # ตรรกะเช็ค Point-in-Box ตรงๆ ไม่ใช้ฟังก์ชันอื่น
                        if (xmin <= kpx <= xmax) and (ymin <= kpy <= ymax):
                            head_inside_roi = True

    # 3. วาดขอบเขตพื้นที่และแสดงผล
    x1, y1, x2, y2 = roi_rect
    box_color = (0, 0, 255) if head_inside_roi else (0, 255, 0)
    status_text = "DANGER: Ears in Zone!" if head_inside_roi else "Safe Zone"
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
    cv2.putText(frame, status_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

    cv2.imshow("Direct Check Frame", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

cap.release()
cv2.destroyAllWindows()