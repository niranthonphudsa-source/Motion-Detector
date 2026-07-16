# main.py
import cv2
from roi_handler import ROIHandler
from file_manager import save_roi_to_txt, load_roi_from_txt
from ultralytics import YOLO
import sklearn
import numpy as np
import joblib
import time

# 1. ตั้งค่าเริ่มต้นและโหลดโมดูล
roi = ROIHandler()
window_name = "Mode Control ROI"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, roi.draw_rectangle_callback)

# โหลดพิกัดเก่าที่เคยบันทึกไว้ (ถ้ามี)
roi.current_rect = load_roi_from_txt()


model = YOLO('yolo26n-pose.pt')
pose_classifier = joblib.load('pose_classifier.pkl')  # โมเดล Sklearn สำหรับจำแนกท่าทาง
head_inside_roi = False

# cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap = cv2.VideoCapture("Screen Recording 2026-07-14 111101.mp4")
# cap = cv2.VideoCapture("videoTrain1.mp4")

check_face = "None Face"


print("=== คู่มือการใช้งาน ===")
print("กด '1' : เปิดโหมดลากกล่อง (ลากเมาส์ซ้ายค้าง)")
print("กด '2' : บันทึกค่าพิกัดล่าสุดที่ลากไว้")
print("กด 'c' : ล้างพิกัดที่เลือกไว้")
print("กด 'q' : ออกจากโปรแกรม")
print("====================")

check_pose  = ["Right", "Left", "Front"]
pose_last = []
confirm = "NG"
predicted_label = None

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),      # หัว
    (5, 6),                              # ไหล่
    (5, 7), (7, 9), (6, 8), (8, 10),    # แขน
    (5, 11), (6, 12),                    # ลำตัว
    (11, 12),                            # สะโพก
    (11, 13), (13, 15), (12, 14), (14, 16) # ขา
]

while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    predict_fram = model.predict(source=frame, conf=0.8, verbose=False)
    for results in predict_fram:
        if results.keypoints is not None:
            point_list = results.keypoints.xy.cpu().numpy()
            for point_pose in point_list:
                if len(point_pose) < 17: 
                    continue
                

                point_skel = point_pose.astype(int)

                # 1. วาดเส้นโครงกระดูก
                for start_idx, end_idx in SKELETON_CONNECTIONS:
                    if (point_skel[start_idx, 0] == 0 and point_skel[start_idx, 1] == 0) or \
                    (point_skel[end_idx, 0] == 0 and point_skel[end_idx, 1] == 0):
                        continue
                    cv2.line(frame, tuple(point_skel[start_idx]), tuple(point_skel[end_idx]), (0, 255, 0), 2)

                if head_inside_roi:
                    # 2. ทำ Normalize พิกัดเพื่อเตรียมส่งให้โมเดลทายผล
                    normalized_points = []
                    for kp in point_pose:
                        kpx, kpy = int(kp[0]), int(kp[1])
                        
                        if kpx == 0 and kpy == 0:
                            normalized_points.append((0.0, 0.0))
                            continue
                        
                        x_norm = kpx / w
                        y_norm = kpy / h
                        normalized_points.append((x_norm, y_norm))
                        
                        cv2.circle(frame, (kpx, kpy), 5, (0, 0, 255), cv2.FILLED)

                    # แปลงข้อมูลเป็น 1D Array ขนาด 34 ค่า
                    features = np.array(normalized_points).flatten()


                    predicted_label = pose_classifier.predict([features])[0]
                    # ดึงค่าความมั่นใจ (Probability) ออกมาแสดง (Optional)
                    probabilities = pose_classifier.predict_proba([features])[0]
                    confidence = np.max(probabilities) * 100

                    # หาพิกัดตำแหน่งที่จะเขียนข้อความ (ใช้พิกัดของจุดจมูก Index 0 หรือไหล่ Index 5 ก็ได้)
                    text_x = point_skel[5][0] if point_skel[5][0] > 0 else 50
                    text_y = point_skel[5][1] - 30 if point_skel[5][1] > 30 else 50

                    for check in range(len(check_pose)):
                        if predicted_label == check_pose[check]:
                            if not pose_last or predicted_label != pose_last[-1]:
                                pose_last.append(predicted_label)
                                # print(pose_last)

                        if pose_last == check_pose:
                            confirm = "OK"
                            pose_last = []
                            print(len(pose_last))
                            break
                        else:
                            confirm = "NG"

                        cv2.putText(frame, f"{len(pose_last)}Pose: {pose_last} ({confidence:.1f}%) Status: {confirm}", 
                            (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, (255, 0, 255), 1)
         
                                        
                # check face in rectangle
                head_point = point_list[0]
                for idx, hp in enumerate(head_point):
                    hpx, hpy = int(hp[0]), int(hp[1])
                    # print(f"{head_point} :  {hp}")

                    if hpx == 0 and hpy == 0:
                        check_face = "None Face"
                        head_inside_roi = False
                        continue
                    
                    if idx in (3,4):
                        x1, y1, x2, y2 = roi.current_rect
                        xmin, xmax = min(x1, x2), max(x1, x2)
                        ymin, ymax = min(y1, y2), max(y1, y2)

                        if (xmin <= hpx <= xmax) and (ymin <= hpy <= ymax):
                            check_face = "Face in Rectangle"
                            head_inside_roi = True
                        else:
                            check_face = "None Face"
                            head_inside_roi = False 
                        

                    # cv2.putText(frame, f"point:{idx} X: {hpx} Y: {hpy}",(hpx, hpy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 1)
                    cv2.circle(frame, (hpx, hpy), 2, (0,255,255), 5)



    # 1. วาดกล่องที่เลือกค้างไว้บนหน้าจอ
    box_color = (0, 0, 255) if head_inside_roi else (0, 255, 0)
    if roi.current_rect is not None:
        cv2.rectangle(frame, (roi.current_rect[0], roi.current_rect[1]), 
                      (roi.current_rect[2], roi.current_rect[3]), box_color, 2)
        cv2.putText(frame, check_face, (roi.current_rect[0], roi.current_rect[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # 2. แสดงกล่องสีแดงแบบ Real-time ขณะลากเมาส์
    if roi.current_mode == 1 and roi.drawing:
        cv2.rectangle(frame, (roi.ix, roi.iy), (roi.cx, roi.cy), (0, 0, 255), 2)

    # 3. แสดงสถานะโหมดปัจจุบัน
    mode_text = "Mode: DRAWING (Press Mouse & Drag)" if roi.current_mode == 1 else "Mode: NORMAL (Press '1' to Edit)"
    mode_color = (0, 0, 255) if roi.current_mode == 1 else (255, 0, 0)
    cv2.putText(frame, mode_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)

    cv2.imshow(window_name, frame)
    
    key = cv2.waitKey(1) & 0xFF

    if key == ord('1'):
        roi.current_mode = 1
        print(">> เข้าสู่โหมด: ลากวาง (กดเมาส์ซ้ายค้างเพื่อวาดขอบเขต)")

    elif key == ord('2'):
        if save_roi_to_txt(roi.current_rect):
            print(f"Successfully Saved! บันทึกพิกัด {roi.current_rect} เรียบร้อย")
            # print(roi.current_rect[0])
            roi.current_mode = 0
        else:
            print("❌ ยังไม่ได้ลากกล่องพิกัด กรุณากด 1 แล้วลากกล่องก่อน")

    elif key == ord('c'):
        roi.clear()
        print("ล้างค่าพิกัดและกลับสู่โหมดปกติ")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()