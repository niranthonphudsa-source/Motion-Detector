# camera_handler.py
import os
import joblib
from LIB.config_loader_start import AppConfig

# ---------------------------------------------------------
# State Variables (เก็บสถานะระบบเพื่อใช้อ้างอิงข้ามโมดูล)
# ---------------------------------------------------------
app_config = AppConfig(r"setting\config.yml")

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
model_sklearn = app_config.model_sklearn


def reload_config_callback(
    new_camera_id,
    updated_config=None,
    config_manager=None,
    RTSPVideoGrabber=None,
):
  """ฟังก์ชันสำหรับ Reload Config, เปลี่ยนโมเดล และสลับกล้อง (Camera Switch)

  รองรับการแยกโมดูลออกจาก main.py โดยส่ง config_manager และ RTSPVideoGrabber เข้ามา
  """
  global save_ok_flag, save_ng_flag, config, active_camera_id, camera, cap
  global window_name, roi, model_sklearn, pose_classifier

  # 1. โหลด / อัปเดต Config
  if updated_config:
    config = updated_config
    if config_manager:
      config_manager.config = updated_config
  elif config_manager:
    config_manager.config = config_manager.load_config()
    config = config_manager.config

  # 2. โหลด AI Model ใหม่
  try:
    model_info = config.get("model", {}).get("Model_path_1", {})
    new_model_path = (
        model_info.get("source", "")
        if isinstance(model_info, dict)
        else str(model_info)
    )

    if new_model_path and os.path.exists(new_model_path):
      model_sklearn = new_model_path
      pose_classifier = joblib.load(model_sklearn)
      print(f"🤖 [Model Reloaded] อัปเดตโมเดลเป็น: {model_sklearn}")
    else:
      print(f"⚠️ [Model Warning] ไม่พบไฟล์โมเดลที่ Path: {new_model_path}")
  except Exception as e:
    print(f"❌ [Model Error] เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")

  # 3. สลับกล้อง (Switch Camera)
  if active_camera_id != new_camera_id:
    print(
        "🔄 [Switch Camera] ตรวจพบการเปลี่ยนกล้องจาก"
        f" {active_camera_id} ➡️ {new_camera_id}"
    )

    old_cap = cap
    active_camera_id = new_camera_id

    if "cameras" in config and active_camera_id in config["cameras"]:
      camera = config["cameras"][active_camera_id]
      new_source = camera.get("source", "")

      # สร้างการเชื่อมต่อกล้องใหม่ผ่าน RTSPVideoGrabber
      if RTSPVideoGrabber and new_source:
        cap = RTSPVideoGrabber(new_source)

    # ปิดการเชื่อมต่อกล้องตัวเก่าแบบปลอดภัย
    if old_cap:
      if hasattr(old_cap, "stop"):
        old_cap.stop()
      elif hasattr(old_cap, "release"):
        old_cap.release()

    # อัปเดตพิกัด ROI & จุดมาร์ก
    if roi and camera:
      roi.clear()
      roi.mark_points = camera.get("mark_points", [])
      roi.start_point = camera.get("start_point", None)
      roi.reverse_point = camera.get("reverse_point", None)
      roi.point_zoom = camera.get("point_zoom", None)
      if len(roi.mark_points) > 0:
        roi.is_confirmed = True

  # 4. อัปเดต Flag การบันทึกภาพ OK / NG
  cam_data = config.get("cameras", {}).get(active_camera_id, {})
  save_ok_flag = cam_data.get("save_ok", True)
  save_ng_flag = cam_data.get("save_ng", True)

  print(
      f"⚙️ สเตตัสปัจจุบัน: Save OK={save_ok_flag}, Save"
      f" NG={save_ng_flag}, Model={model_sklearn}"
  )