import numpy as np
import cv2

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