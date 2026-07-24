import cv2

# รูปแบบ RTSP URL มาตรฐาน (ขึ้นอยู่กับยี่ห้อกล้อง)
# rtsp://username:password@IP_ADDRESS:PORT/stream_path
rtsp_url = "rtsp://admin:123456@192.168.1.100:554/stream1"

cap = cv2.VideoCapture(rtsp_url)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("ไม่สามารถดึงภาพจาก IP Camera ได้")
        break

    cv2.imshow("IP Camera Stream", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()