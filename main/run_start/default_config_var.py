import tkinter as tk
from app.data_viewer_gui import SSTableViewerGUI, checklastID

# root = tk.Tk()
# data_view = SSTableViewerGUI(root)
# root.mainloop()



lastID = checklastID
print(lastID)
check_pose = ["Right", "Left", "Front"]
ok_display_time = 3.0
SKIP_FRAMES = 1
predicted_label = "None"
confidence = 0.0
any_people_inside = False
fps = 15
strat_y = 0
start_y = 0
reverse_point = None
# lastID = SSTableViewerGUI._getLastID()

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]
