import numpy as np
import time

from LIB.predict_frame_pose import ShowPredict

predict = ShowPredict()
class SearchKeypoint():
    def __init__(self, 
                 skip_frame,
                 frame,
                 model,
                 frame_count 
                ):
        self.frame = frame
        self.model = model
        self.skip_frame = skip_frame
        self.frame_count = frame_count

    def searchKeypoint(self):
        predict.current_frame_poses = []
        predict.current_frame_ids = []

        
        if self.frame_count % self.skip_frame == 0:
            # count process
            # t=time.perf_counter()
            predict_frame = self.model.track(source=self.frame,
                                        conf=0.7, 
                                        persist=True, 
                                        verbose=False, 
                                        tracker="bytetrack.yaml")
            predict.update_pose_history(predict_frame)   

            # print(time.perf_counter()-t) 
        else:
            predict.predicted_people_kp = []
            predict.predicted_people_ids = []
            predict.predict_keypoints_from_history(predict.pose_history, self.frame_count, self.skip_frame)
            if len(predict.predicted_people_kp) > 0:
                predict.current_frame_poses = np.array(predict.predicted_people_kp)
                predict.current_frame_ids = np.array(predict.predicted_people_ids)

        return predict.current_frame_poses, predict.current_frame_ids