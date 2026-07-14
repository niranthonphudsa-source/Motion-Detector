import cv2
import numpy as np

# กำหนดตัวแปร Global สำหรับเก็บสถานะและพิกัด
drawing = False      # True ถ้ากำลังคลิกค้างเพื่อลากสี่เหลี่ยม
ix, iy = -1, -1      # พิกัดเริ่มต้น (x, y)
ex, ey = -1, -1      # พิกัดระหว่างลาก/สิ้นสุด (x, y)

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, ex, ey, drawing, img, img_temp

           
    # 1. เมื่อคลิกเมาส์ซ้ายปุ่มลง (จุดเริ่มต้น)
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    # 2. เมื่อมีการขยับเมาส์
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            # คัดลอกภาพจริงมาไว้ที่ภาพชั่วคราว เพื่อไม่ให้เกิดเส้นซ้อนกันขณะลาก
            img_temp = img.copy()
            # วาดสี่เหลี่ยมจำลองสีเขียว (ความหนา 2) บนภาพชั่วคราวขณะลาก
            cv2.rectangle(img_temp, (ix, iy), (x, y), (0, 255, 0), 2)

    # 3. เมื่อปล่อยปุ่มเมาส์ซ้าย (จุดสิ้นสุด)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        ex, ey = x, y
        # วาดสี่เหลี่ยมสีเขียวถาวรลงบนภาพจริง
        cv2.rectangle(img, (ix, iy), (ex, ey), (0, 255, 0), 2)


# สร้างภาพสีดำขนาด 512x512 พิกเซลขึ้นมาเป็นพื้นหลัง (หรือจะโหลดภาพจริงด้วย cv2.imread ก็ได้)
img = np.zeros((512, 512, 3), np.uint8)
img_temp = img.copy()

# ตั้งชื่อ Window
cv2.namedWindow('Draw Rectangle')
# ผูก Event เมาส์เข้ากับ Window และฟังก์ชัน draw_rectangle
cv2.setMouseCallback('Draw Rectangle', draw_rectangle)

print("วิธีใช้งาน: คลิกซ้ายค้างแล้วลากเพื่อวาดสี่เหลี่ยม | กดปุ่ม 'c' เพื่อล้างหน้าจอ | กด 'q' เพื่อออก")


while True:
    key = cv2.waitKey(1) & 0xFF

    # ถ้ากำลังลากเมาส์อยู่ ให้แสดงภาพชั่วคราว (img_temp) เพื่อให้เห็นเส้นที่กำลังลากตามเมาส์
    if drawing:
        cv2.imshow('Draw Rectangle', img_temp)
    else:
        # ถ้าไม่ได้ลาก (หรือปล่อยเมาส์แล้ว) ให้แสดงภาพจริง (img)
        cv2.imshow('Draw Rectangle', img)

    
    
    # กด 'c' เพื่อ Clear หน้าจอ (ลบรูปสี่เหลี่ยมทั้งหมด)
    if key == ord('c'):
        img = np.zeros((512, 512, 3), np.uint8)
        img_temp = img.copy()
        print("ล้างหน้าจอแล้ว")
        
    # กด 'q' เพื่อออกจากโปรแกรม
    elif key == ord('q'):
        break

cv2.destroyAllWindows()