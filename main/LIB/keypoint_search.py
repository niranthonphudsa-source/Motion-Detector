class SearchKeypoint:
    def __init__(self):
        self.pose_history = {}
        self.frame_count = 0
        self.current_frame_poses = 0
        self.current_frame_ids = 0

    def searchKeypoint(self, result, predict_frame):
        for results in predict_frame:
            if results.keypoints is not None and results.boxes.id is not None:
                point_list = results.keypoints.xy.cpu().numpy()  # (N, 17, 2)
                track_ids = results.boxes.id.cpu().numpy().astype(int)  # [1, 2]
                
                for idx, p_id in enumerate(track_ids):
                    person_kp = point_list[idx]
                    if p_id not in self.pose_history:
                        self.pose_history[p_id] = []
                    self.pose_history[p_id].append([self.frame_count, person_kp])
                    
                    if len(self.pose_history[p_id]) > 4:
                        self.pose_history[p_id].pop(0)
                
                self.current_frame_poses = point_list
                self.current_frame_ids = track_ids