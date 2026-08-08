from LIB.roi_handler import ROIHandler
import cv2
import numpy as np


roi = ROIHandler()
def mark_roi_polygon(num_pts, frame, mark_points, check_people, box_color, is_confirmed):
    if num_pts > 0:
        for idx, pt in enumerate(mark_points):
            x, y = int(pt[0]), int(pt[1])
            cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)
            cv2.putText(frame, str(idx + 1), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
        for i in range(num_pts - 1):
            cv2.line(frame, tuple(mark_points[i]), tuple(mark_points[i+1]), (0, 255, 255), 2)
            
        if is_confirmed and num_pts > 2:
            contour = np.array(mark_points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [contour], isClosed=True, color=box_color, thickness=2)
            cv2.putText(frame, check_people, (int(mark_points[0][0]), int(mark_points[0][1] - 10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)