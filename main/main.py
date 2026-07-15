# main.py
import cv2
from roi_handler import ROIHandler
from file_manager import save_roi_to_txt, load_roi_from_txt
from ultralytics import YOLO
import sklearn
from ultralytics import YOLO

# 1. ตั้งค่าเริ่มต้นและโหลดโมดูล
roi = ROIHandler()
window_name = "Mode Control ROI"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, roi.draw_rectangle_callback)

# โหลดพิกัดเก่าที่เคยบันทึกไว้ (ถ้ามี)
roi.current_rect = load_roi_from_txt()


model = YOLO('yolo26n-pose.pt')
head_inside_roi = False

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

check_face = "None Face"


print("=== คู่มือการใช้งาน ===")
print("กด '1' : เปิดโหมดลากกล่อง (ลากเมาส์ซ้ายค้าง)")
print("กด '2' : บันทึกค่าพิกัดล่าสุดที่ลากไว้")
print("กด 'c' : ล้างพิกัดที่เลือกไว้")
print("กด 'q' : ออกจากโปรแกรม")
print("====================")


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
    
    predict_fram = model.predict(source=frame, conf=0.8, verbose=False)
    for results in predict_fram:
        if results.keypoints is not None:
            point_list = results.keypoints.xy.cpu().numpy()
            for point_pose in point_list:
                if len(point_pose) < 5: continue

                head_point = point_list[0]
    
                for idx, hp in enumerate(head_point):
                    hpx, hpy = int(hp[0]), int(hp[1])
                    # print(f"{head_point} :  {hp}")

                    if hpx == 0 and hpx == 0:
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

                    cv2.putText(frame, f"point:{idx} X: {hpx} Y: {hpy}",(hpx, hpy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 1)
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