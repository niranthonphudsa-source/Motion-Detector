import cv2
import tkinter as tk
import run_start.default_config_var as df


class ShowStatusPose():
    def __init__(self, p_id, 
                    predicted_label,
                    confidence,
                    people_in_rectangle,
                    line_height, 
                    status_color,
                    text_x, 
                    text_y_start, 
                    stateConfirm, 
                    stateValuelast
                ):
    
        self.id = p_id
        self.predic_label = predicted_label
        self.confidence = confidence
        self.people_in_rectangle = people_in_rectangle
        self.line_height = line_height
        self.status_color = status_color
        self.state_confirm = stateConfirm
        self.state_valaus_last = stateValuelast
        self.text_x = text_x 
        self.text_y_start = text_y_start

    def showStatus(self, frame):
        state = self.state_valaus_last
        color_state1 = (0, 255, 0) if len(state) >= 1 else (255, 255, 255)
        color_state2 = (0, 255, 0) if len(state) >= 2 else (255, 255, 255)
        color_state3 = (0, 255, 0) if len(state) >= 3 else (255, 255, 255)
        
        display_lines = [
            f"ID: {self.id}",
            f"Pose: {self.predic_label} ({self.confidence:.1f}%)" if self.people_in_rectangle else "Pose: Outside ROI",
            # f"Progress Test: {len(state['valaus_last'])}/{len(check_pose)} {state['valaus_last']}",
            f"State Right",
            f"State Left",
            f"State Front",
            f"STATUS: {self.state_confirm}"
        ]

        for i, line_text in enumerate(display_lines):
            current_y = self.text_y_start + (i * self.line_height)
            if "Pose" in line_text:
                cv2.putText(frame, line_text, (self.text_x + 40, current_y + 40), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255), 1, 3)
            elif "State Right" in line_text:
                cv2.putText(frame, line_text, (self.text_x + 40, current_y + 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, color_state1, 1, 3)

            elif "State Left" in line_text:
                cv2.putText(frame, line_text, (self.text_x + 40, current_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_state2, 1, 3)

            elif "State Front" in line_text:
                cv2.putText(frame, line_text, (self.text_x + 40, current_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_state3, 1, 3)

            elif "STATUS" in line_text:
                # แสดงสถานะไว้เหนือหัวของคนคนนั้น โดยใช้ตำแหน่งศีรษะที่เคยคำนวณไว้
                cv2.putText(frame, line_text, (self.text_x + 10, self.text_y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, self.status_color, 2)
            elif "ID" in line_text:
                cv2.putText(frame, line_text, (self.text_x - 50, current_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, 3)
            else:
                cv2.putText(frame, line_text, (self.text_x - 50, current_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1, 3)
