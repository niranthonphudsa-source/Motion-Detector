from ultralytics import YOLO

model = YOLO("main\yolo26n-pose.pt") 
model.export(format='openvino')
# เรียกใช้โมเดล OpenVINO
ov_model = YOLO('yolo26n-pose_openvino_model/')