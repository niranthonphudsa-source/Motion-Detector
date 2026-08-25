import tkinter as tk
from app.data_viewer_gui import SSTableViewerGUI, CheckLastID
from rtspVideo import RTSPVideoGrabber
from LIB.config_loader_start import AppConfig
# root = tk.Tk()
# data_view = SSTableViewerGUI(root)
# root.mainloop()



# ─── โหลดและจัดการ CONFIG ───
app_config = AppConfig(r"setting\config.yml")

config_manager = app_config.config_manager
config = app_config.config
active_camera_id = app_config.active_camera_id
camera = app_config.camera
source = app_config.source
save_ok_flag = app_config.save_ok_flag
save_ng_flag = app_config.save_ng_flag
save_data_flag = app_config.save_data_flag
model_sklearn = app_config.model_sklearn
type = app_config.type


check = CheckLastID()
lastID = check.get_last_id()
# print(lastID)
check_pose = ["Right", "Left", "Front"]
ok_display_time = 5.0
SKIP_FRAMES = 2
predicted_label = None
confidence = 0.0
any_people_inside = False

strat_y = 0
start_y = 0
reverse_point = None
simulated_key = -1 
fps = 30
save_video_per_frame = float(fps / 2)
keypoint_conf = 0
# lastID = SSTableViewerGUI._getLastID()

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]
