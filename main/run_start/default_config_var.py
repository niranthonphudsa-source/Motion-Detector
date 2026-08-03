check_pose = ["Right", "Left", "Front"]
ok_display_time = 5.0
SKIP_FRAMES = 1
predicted_label = "None"
confidence = 0.0
any_people_inside = False
fps = 15
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]