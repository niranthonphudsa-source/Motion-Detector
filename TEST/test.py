import cv2

# ลิสต์สำหรับเก็บพิกัด [(x1, y1), (x2, y2), ...]
mouse_points = []
point_last = []
# 1. สร้าง Function Callback สำหรับจัดการเหตุการณ์เมาส์
def click_event(event, x, y, flags, param):
    # ตรวจสอบว่าเป็นการคลิกเมาส์ซ้ายหรือไม่
    if event == cv2.EVENT_LBUTTONDOWN:
        # บันทึกพิกัดลงในลิสต์
        mouse_points.append((x, y))
        print(f"บันทึกพิกัด: x={x}, y={y} | จุดทั้งหมดในลิสต์: {mouse_points} \n")
        print(f"PointLast {point_last}")

# 2. อ่านภาพหรือสร้างเฟรมเปล่าขึ้นมาทดสอบ
# (ในงานจริงสามารถเปลี่ยนเป็นเฟรมจาก cv2.VideoCapture ได้เลย)
img = cv2.imread("your_image.jpg") 

# กรณีไม่มีไฟล์ภาพ สามารถเปิดบรรทัดล่างนี้เพื่อสร้างภาพสีดำขนาด 512x512 มาทดสอบแทนได้ครับ
# import numpy as np; img = np.zeros((512, 512, 3), np.uint8)

# 3. ตั้งชื่อหน้าต่าง (Window Name ต้องตรงกันทั้งตอนแสดงภาพและดักเมาส์)
window_name = "Mouse Click Tracker"
cv2.namedWindow(window_name)

# 4. ผูกฟังก์ชัน Callback เข้ากับหน้าต่างที่เราสร้างไว้
cv2.setMouseCallback(window_name, click_event)

print("เริ่มโปรแกรม: คลิกเมาส์ซ้ายบนภาพเพื่อบันทึกพิกัด | กด 'q' เพื่อออกจากโปรแกรม")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    # คัดลอกภาพเดิมมาวาดจุดแสดงผล เพื่อไม่ให้ภาพต้นฉบับเสียหาย
    ret, temp_img = cap.read()
    
    if not ret:
        break
    # วาดจุดวงกลมสีแดงตรงพิกัดที่เคยคลิกไว้ทั้งหมด
    for point in mouse_points:
        cv2.circle(temp_img, point, 5, (0, 0, 255), -1)
        # แสดงพิกัดเป็นข้อความบนจอ (Optional)
        cv2.putText(temp_img, f"({point[0]},{point[1]})", (point[0] + 10, point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
 

        
        for idx, pt in enumerate(mouse_points, 1):
            x, y = int(pt[0]), (pt[1])
            # x2, y2 = point_last[idx][0], point_last[idx][1]
            print(f"{idx}, {x}, {y}")
            # print(pt, point_last)
            
            
            # print(f"{mouse_points[idx][0]} {mouse_points[idx][1]}: \n", int(mouse_points[idx][0]) + int(mouse_points[idx][1]))
            cv2.line(temp_img, (mouse_points[idx], mouse_points[idx + 1]), (0,255,0),  1)
            
            # cv2.line(temp_img, (pt[0], pt[1]), (mouse_points[0], mouse_points[1]),(0,255,0), 2 )

    # แสดงผลเฟรมภาพ
    cv2.imshow(window_name, temp_img)
    
    # กด 'q' เพื่อออกจาก Loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

# แสดงผลพิกัดทั้งหมดหลังจากปิดโปรแกรม
print("\n--- สรุปพิกัดทั้งหมดที่คุณคลิก ---")
for i, pt in enumerate(mouse_points, 1):
    print(f"จุดที่ {i}: {pt}")