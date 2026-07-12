import cv2
from ultralytics import YOLO


model = YOLO('yolo26n-pose.pt')  # โหลดโมเดล YOLO Pose

cap = cv2.VideoCapture(0)  # เปิดกล้อง (0 คือกล้องหลัก)


while True:
    ret, frame = cap.read()
    if not ret:
        break

    