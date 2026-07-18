import numpy as np
from sklearn.linear_model import LinearRegression

class ShowPredict():
    def __init__(self):
        self.pose_history = {}
        self.frame_count = 0
        self.p_id = 0
        self.current_frame_poses = []
        self.current_frame_ids = []
        self.idx = 0
        self.predicted_people_kp = []
        self.predicted_people_ids = []

    def update_pose_history(self, predict_frame):
        # print(predict_frame)
        for results in predict_frame:
            if results.keypoints is not None and results.boxes.id is not None:
                point_list = results.keypoints.xy.cpu().numpy()  # (N, 17, 2)
                track_ids = results.boxes.id.cpu().numpy().astype(int)  # [1, 2]
                
                for self.idx, self.p_id in enumerate(track_ids):
                    person_kp = point_list[self.idx]
                    if self.p_id not in self.pose_history:
                        self.pose_history[self.p_id] = []
                    self.pose_history[self.p_id].append([self.frame_count, person_kp])
                    
                    if len(self.pose_history[self.p_id]) > 4:
                        self.pose_history[self.p_id].pop(0)
                
                self.current_frame_poses = point_list
                self.current_frame_ids = track_ids
            
    def predict_keypoints_from_history(self, pose_history, frame_count, skip_frames):
        self.predicted_people_kp = []
        self.predicted_people_ids = []

        active_ids = list(pose_history.keys())
        for self.p_id in active_ids:
            history = pose_history[self.p_id]
            if len(history) >= 2 and (frame_count - history[-1][0]) < (skip_frames * 2):
                X_train = np.array([item[0] for item in history]).reshape(-1, 1)
                predicted_kp = np.zeros((17, 2))

                for kp_idx in range(17):
                    y_train_x = np.array([item[1][kp_idx][0] for item in history])
                    y_train_y = np.array([item[1][kp_idx][1] for item in history])

                    if np.any(y_train_x > 0):
                        reg_x = LinearRegression().fit(X_train, y_train_x)
                        pred_x = reg_x.predict(np.array([[frame_count]]))[0]

                        reg_y = LinearRegression().fit(X_train, y_train_y)
                        pred_y = reg_y.predict(np.array([[frame_count]]))[0]

                        predicted_kp[kp_idx] = [pred_x, pred_y]

                self.predicted_people_kp.append(predicted_kp)
                self.predicted_people_ids.append(self.p_id)
            else:
                if len(history) > 0 and (self.frame_count - history[-1][0]) < (skip_frames * 2):
                    self.predicted_people_kp.append(history[-1][1])
                    self.predicted_people_ids.append(self.p_id)

