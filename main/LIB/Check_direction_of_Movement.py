import get_distance 
import cv2

class Check_direction_of_Movement():
    def __init__(self,
                    person_dir,
                    foot_pos,
                    foot_x,
                    foot_y,
                    start_point,
                    reverse_point,
                    id
                ):
        self.person_dir = person_dir
        self.foot_pos = foot_pos
        self.start_point = start_point
        self.reverse_point = reverse_point
        self.p_id = id
        self.foot_x = foot_x
        self.foot_y = foot_y
        self.reverse_x = 0
        self.reverse_y = 0
        self.start_x = 0
        self.start_y = 0
        

    def checkMovement(self, frame):
       
        if self.person_dir['first_touch'] is None:
            dist_to_start = get_distance.get_distance(self.foot_pos, self.start_point)
            dist_to_reverse = get_distance.get_distance(self.foot_pos, self.reverse_point)
            # ─── ดึงพิกัดแกน Y แบบปลอดภัย (ป้องกัน NoneType Error) ───
            self.start_x = self.start_point[0] if self.start_point is not None else None
            self.start_y = self.start_point[1] if self.start_point is not None else None
            self.reverse_y = self.reverse_point[1] if self.reverse_point is not None else None
            self.reverse_x = self.reverse_point[0] if self.reverse_point is not None else None

            # last_x = w
            # cv2.line(frame, (0, self.reverse_y), (last_x, self.reverse_y), (0, 255, 0), 2, cv2.LINE_AA)
            # ตรวจสอบว่าทั้งคู่มีค่าพิกัดอยู่จริง ก่อนทำเงื่อนไขเปรียบเทียบ
            if self.person_dir['first_touch'] is None and self.start_y is not None and self.reverse_y is not None:

                # (reverse_x0 - reverse_x1) * (reverse_y0 - reverse_y1) - (reverse_y0 - reverse_y1) * (reverse_x2 - reverse_x1)
                
                if dist_to_reverse < 50 or self.foot_y  >= self.reverse_y:
                    self.person_dir['first_touch'] = 'REVERSE'
                    self.person_dir['is_reverse'] = True
                    print(f"🚫 ID {self.p_id}: เดินสวนทาง! (เข้าจุดที่ 2 ก่อน) -> ไม่ตรวจจับท่าทาง")
                elif dist_to_start < 50 or self.foot_y >= self.start_y:
                    self.person_dir['first_touch'] = 'START'
                    self.person_dir['is_reverse'] = False
                    print(f"✅ ID {self.p_id}: เดินถูกทิศทาง! (เข้าจุดที่ 1 ก่อน) -> เริ่มระบบตรวจจับ")


        # 🛑 หากเป็นคนที่เดินสวนทางมา ให้ข้ามตรรกะการตรวจท่าทางและการบันทึกไฟล์ไปเลย
        if self.person_dir['is_reverse']:
            cv2.putText(frame, f"ID: {self.p_id} [REVERSE - IGNORED]", (self.foot_x - 30, self.foot_y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
        return self.person_dir['first_touch'], self.person_dir['is_reverse']
