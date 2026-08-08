import cv2
import numpy as np
import yaml

# ลิสต์สำหรับเก็บพิกัดพอยต์ [(x1, y1), (x2, y2), ...]
mouse_points = []
# ตัวแปรสถานะเพื่อบอกว่ากดยืนยันแล้วหรือยัง
is_confirmed = False

# 1. Callback ฟังก์ชันดักจับเมาส์
def click_event(event, x, y, flags, param):
    global is_confirmed
    # ถ้ายังไม่ได้กดยืนยัน จะสามารถคลิกเพิ่มจุดได้เรื่อย ๆ
    if not is_confirmed:
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_points.append((x, y))
            print(f"บันทึกจุดที่ {len(mouse_points)}: {x}, {y}")

# 2. อ่านภาพต้นฉบับ (หรือสร้างเฟรมดำขึ้นมาทดสอบ)
cap = cv2.VideoCapture("video\\videoTrain4.mp4") 

# กรณีต้องการใช้หน้าต่างจำลองสำหรับทดสอบ (เปิดใช้งานบรรทัดล่างนี้ได้ครับ)
# import numpy as np; img = np.zeros((600, 800, 3), np.uint8)

window_name = "Point Tracker & Connector"
cv2.namedWindow(window_name)


print("--- วิธีใช้งาน ---")
print("1. คลิกเมาส์ซ้ายบนภาพเพื่อเพิ่มจุด")
print("2. กดปุ่ม '2' บนคีย์บอร์ด เพื่อยืนยัน (Confirm) และลากเส้นปิดรูปทรง")
print("3. กดปุ่ม 'r' เพื่อรีเซ็ตเริ่มใหม่")
print("4. กดปุ่ม 'q' เพื่อออกจากโปรแกรม")

while True:
    ret, temp_img = cap.read()
    
    if not ret:
        break
    # จำนวนจุดที่มีในปัจจุบัน
    temp_img = cv2.resize(temp_img, (640, 480))
    num_pts = len(mouse_points)
    
    # 3. วาดเส้นและจุดบนจอ
    if num_pts > 0:
        # วาดวงกลมเล็ก ๆ ในทุกจุดที่คลิก
        for pt in mouse_points:
            cv2.circle(temp_img, pt, 5, (0, 255, 0), -1)
            
        # ลากเส้นเชื่อมจาก จุด 1 -> 2 -> 3 ไปเรื่อย ๆ
        for i in range(num_pts - 1):
            cv2.line(temp_img, mouse_points[i], mouse_points[i+1], (0, 255, 255), 2)
            
        # ถ้ากดยืนยันแล้ว (is_confirmed == True) ให้ลากเส้นจาก จุดสุดท้าย กลับมา จุดแรก
        if is_confirmed and num_pts > 2:
            cv2.line(temp_img, mouse_points[-1], mouse_points[0], (0, 255, 255), 2)
            # แสดงคำว่า CONFIRMED บนภาพ
            cv2.putText(temp_img, "POLYGON CONFIRMED", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow(window_name, temp_img)
    
    # 4. ดักจับการกดปุ่มบนคีย์บอร์ด
    key = cv2.waitKey(1) & 0xFF
    
    # หากกดปุ่ม '2' -> ยืนยันการตีกรอบ (ตราบใดที่มีมากกว่า 2 จุดขึ้นไป)
    
    if key == ord('1'):
        cv2.setMouseCallback(window_name, click_event)
    elif key == ord('2'):
        if len(mouse_points) > 2:
            is_confirmed = True
            print("\n[ยืนยันพิกัดเรียบร้อย!]")
            print(f"พิกัดรูปปิด (Polygon): {mouse_points}")
        else:
            print("กรุณาคลิกอย่างน้อย 3 จุดก่อนกดยืนยันครับ")
            
    # หากกดปุ่ม 'r' -> รีเซ็ตทุกอย่างเพื่อเริ่มคลิกใหม่
    elif key == ord('r'):
        mouse_points = []
        is_confirmed = False
        print("\nรีเซ็ตพิกัดเรียบร้อย เริ่มคลิกใหม่ได้เลยครับ")
        
    # หากกดปุ่ม 'q' -> ออกจากโปรแกรม
    elif key == ord('q'):
        break

cv2.destroyAllWindows()