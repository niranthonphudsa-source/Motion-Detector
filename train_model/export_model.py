from ultralytics import YOLO

model = YOLO() 
model.export(format='openvino')
# เรียกใช้โมเดล OpenVINO
ov_model = YOLO('yolo26n-pose_openvino_model/')