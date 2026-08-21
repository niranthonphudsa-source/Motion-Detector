import numpy as np
import time
import cv2
import pandas as pd
import run_start.default_config_var as df
import joblib
import sklearn


class CheckPeopleInRoi():
    def __init__(self, frame, mark_points, point_pose):
        self.frame = frame
        self.mark_points = mark_points
        self.point_pose = point_pose

    def checkPeopleInRoi(self):
        people_in_rectangle = False
        any_people_inside = None
         # --- ตรวจสอบว่าอยู่ในพื้นที่ ROI Polygon หรือไม่ ---
        if self.mark_points and len(self.mark_points) >= 2:
            contour = np.array(self.mark_points, dtype=np.int32).reshape((-1, 1, 2))
            foot_inside_count = 0
            for idx in (15, 16):
                hpx, hpy = int(self.point_pose[idx][0]), int(self.point_pose[idx][1])
                inside = cv2.pointPolygonTest(contour, (hpx, hpy), False)
                if inside >= 0:
                    foot_inside_count += 1
            
            if foot_inside_count > 0:
                people_in_rectangle = True
                any_people_inside = True 
                

            for idx in range(17):
                hpx, hpy = int(self.point_pose[idx][0]), int(self.point_pose[idx][1])
                if hpx > 0 and hpy > 0:
                    cv2.circle(self.frame, (hpx, hpy), 3, (0, 255, 255), cv2.FILLED)

        return people_in_rectangle, any_people_inside 

class Check_where_inRectangle():
    def __init__(self, 
                    people_in_rectangle,
                    is_terminating,
                    termination_start_time,
                    is_ok_holding,
                    confirm,
                    valaus_last,
                    ok_start_time,
                    point_pose,
                    p_id,
                    pose_classifier,
                    check_pose
                 ):
        
        self.people_in_rectangle = people_in_rectangle
        self.state_is_terminating = is_terminating
        self.state_termination_start_time = termination_start_time
        self.state_is_ok_holding = is_ok_holding
        self.state_confirm = confirm
        self.state_valaus_last = valaus_last
        self.state_ok_start_time = ok_start_time
        self.point_pose = point_pose
        self.p_id = p_id
        self.pose_classifier = pose_classifier
        self.confidence = None
        self.check_pose = check_pose
    def check_where_inRectangle(self, frame, w, h, manager):
        if self.people_in_rectangle:
            if self.state_is_terminating:
                self.state_is_terminating = False
                self.state_termination_start_time = None
                print(f"🏃‍♂️ ID {self.p_id} กลับเข้ามาในพื้นที่ตรวจ -> ยกเลิกการหน่วงเวลาปิดไฟล์")

            normalized_points = []
            for kp in self.point_pose:
                kpx, kpy = int(kp[0]), int(kp[1])
                if kpx == 0 and kpy == 0:
                    normalized_points.append((0.0, 0.0))
                    continue
                normalized_points.append((kpx / w, kpy / h))
                cv2.circle(frame, (kpx, kpy), 5, (0, 0, 255), cv2.FILLED)

            feature_names = [f"{axis}_{i}" for i in range(17) for axis in ("x", "y")]
            features = np.array(normalized_points).flatten()

            if len(features) == 34:
                features_df = pd.DataFrame([features], columns=feature_names)
                df.predicted_label = self.pose_classifier.predict(features_df)[0]
                probabilities = self.pose_classifier.predict_proba(features_df)[0]
                self.confidence = np.max(probabilities) * 100

                # ล็อกแสดงผล OK ค้าง
                if self.state_is_ok_holding:
                    if time.time() - self.state_ok_start_time < manager.ok_display_time:
                        self.state_confirm = "OK"
                    else:
                        self.state_is_ok_holding = False
                        self.state_confirm = "NG"
                        self.state_valaus_last = [] 

                else:
                    expected_pose_idx = len(self.state_valaus_last)
                    if expected_pose_idx < len(self.check_pose):
                        expected_pose = self.check_pose[expected_pose_idx]
                        if df.predicted_label == expected_pose:
                            if not self.state_valaus_last or df.predicted_label != self.state_valaus_last[-1]:
                                self.state_valaus_last.append(df.predicted_label)
                
                    if self.state_valaus_last == self.check_pose:
                        self.state_confirm = "OK"
                        self.state_is_ok_holding = True
                        self.state_ok_start_time = time.time()

        return self.confidence, self.state_is_terminating, self.state_termination_start_time, self.state_is_ok_holding, self.state_confirm, self.state_valaus_last, self.state_ok_start_time 

class RecordVedioDetect():

    def __init__(self, 
                 state_writer, 
                 state_video_farme, 
                 id, 
                 fourcc,
                 w, 
                 h
        ):
        self.state_writer = state_writer
        self.state_videoFrame = state_video_farme
        self.p_id = id
        self.fourcc = fourcc
        self.w = w
        self.h = h

    def recordingVideo(self):
         # เริมอัดวิดีโอตั้งแต่จุดเช็คทิศทาง
        if self.state_writer is None:
            current_time_str = int(time.time())
            self.state_videoFrame = f"video_center/violation_{self.p_id}_{current_time_str}.mp4"
            self.state_writer = cv2.VideoWriter(self.state_videoFrame, self.fourcc, df.save_video_per_frame, (self.w, self.h))
            print(f"[Record] ID {self.p_id} เข้าจุด -> เริ่มบันทึกวิดีโอ: {self.state_videoFrame}")

        return self.state_writer, self.state_videoFrame