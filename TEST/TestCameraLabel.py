import cv2
import numpy as np
import csv
import os
from ultralytics import YOLO


# ============================================================
# 1. ตั้งค่าไฟล์ CSV
# ============================================================

csv_filename = "pose_dataset_label.csv"

headers = []

# Keypoints 17 จุด
for i in range(17):
    headers.append(f"x_{i}")
    headers.append(f"y_{i}")

headers.append("label")


# สร้าง CSV ถ้ายังไม่มี
if not os.path.exists(csv_filename):
    with open(csv_filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)


# ============================================================
# 2. โหลด YOLO Pose Model
# ============================================================

model = YOLO("yolo26n-pose.pt")


# ============================================================
# 3. Video Source
# ============================================================

video_path = (
    r"../../ProjectDetection/recordings/"
    r"VideoTrain_20260817_153543.mp4"
)

cap = cv2.VideoCapture(video_path)

# ถ้าใช้กล้อง Webcam
# cap = cv2.VideoCapture(0)


if not cap.isOpened():
    print("ไม่สามารถเปิด Video ได้")
    exit()


# ============================================================
# 4. Skeleton Connections
# ============================================================

SKELETON_CONNECTIONS = [
    (0, 1),
    (0, 2),
    (1, 3),
    (2, 4),

    (5, 6),

    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),

    (5, 11),
    (6, 12),

    (11, 12),

    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16)
]


# ============================================================
# 5. ตั้งค่าการตรวจจับ
# ============================================================

CONF_THRESHOLD = 0.5

# Confidence ของ Keypoint
KEYPOINT_CONF_THRESHOLD = 0.3


# ============================================================
# 6. ฟังก์ชัน Normalize Pose
# ============================================================

def normalize_pose(keypoints, keypoint_conf=None):
    """
    แปลง Keypoints ให้เป็นสัดส่วนของร่างกาย

    จุดอ้างอิง:
        - กลางสะโพกซ้าย/ขวา = (0, 0)

    Scale:
        - ความสูงของร่างกาย

    ผลลัพธ์:
        x_0, y_0, ..., x_16, y_16

    ไม่ขึ้นกับ:
        - คนอยู่ตรงไหนของภาพ
        - คนอยู่ใกล้หรือไกลกล้อง
    """

    # --------------------------------------------------------
    # ตรวจว่ามี Keypoints ครบ 17 จุดหรือไม่
    # --------------------------------------------------------

    if keypoints is None:
        return None

    if len(keypoints) < 17:
        return None

    keypoints = np.asarray(keypoints, dtype=np.float32)

    # --------------------------------------------------------
    # ตรวจ Confidence ของ Keypoints
    # --------------------------------------------------------

    valid_mask = np.ones(17, dtype=bool)

    if keypoint_conf is not None:
        keypoint_conf = np.asarray(
            keypoint_conf,
            dtype=np.float32
        )

        if len(keypoint_conf) >= 17:
            valid_mask = keypoint_conf[:17] >= KEYPOINT_CONF_THRESHOLD

    # --------------------------------------------------------
    # ตรวจจุดสะโพก
    #
    # COCO Pose:
    # 11 = Left Hip
    # 12 = Right Hip
    # --------------------------------------------------------

    left_hip_valid = valid_mask[11]
    right_hip_valid = valid_mask[12]

    left_hip = keypoints[11]
    right_hip = keypoints[12]

    # --------------------------------------------------------
    # ถ้ามีสะโพกทั้งสองข้าง
    # ใช้จุดกึ่งกลาง
    # --------------------------------------------------------

    if left_hip_valid and right_hip_valid:

        hip_x = (
            left_hip[0] +
            right_hip[0]
        ) / 2.0

        hip_y = (
            left_hip[1] +
            right_hip[1]
        ) / 2.0

    # --------------------------------------------------------
    # ถ้ามีเฉพาะสะโพกซ้าย
    # --------------------------------------------------------

    elif left_hip_valid:

        hip_x = left_hip[0]
        hip_y = left_hip[1]

    # --------------------------------------------------------
    # ถ้ามีเฉพาะสะโพกขวา
    # --------------------------------------------------------

    elif right_hip_valid:

        hip_x = right_hip[0]
        hip_y = right_hip[1]

    else:

        print("ไม่พบ Hip Keypoint")
        return None

    # --------------------------------------------------------
    # หาจุดบนสุดและล่างสุดของร่างกาย
    # --------------------------------------------------------

    valid_points = keypoints[valid_mask]

    if len(valid_points) < 5:
        print("Keypoints ที่ใช้ได้มีน้อยเกินไป")
        return None

    min_y = np.min(valid_points[:, 1])
    max_y = np.max(valid_points[:, 1])

    person_height = max_y - min_y

    # --------------------------------------------------------
    # ป้องกันหารด้วย 0
    # --------------------------------------------------------

    if person_height <= 1:
        print("ความสูงของคนไม่ถูกต้อง")
        return None

    # --------------------------------------------------------
    # Normalize
    #
    # กลางสะโพก = (0, 0)
    #
    # Scale = ความสูงของคน
    # --------------------------------------------------------

    normalized_points = []

    for i, kp in enumerate(keypoints):

        kpx = kp[0]
        kpy = kp[1]

        # ----------------------------------------------------
        # ถ้า Keypoint confidence ต่ำ
        # ----------------------------------------------------

        if not valid_mask[i]:

            normalized_points.append(
                (0.0, 0.0)
            )

            continue

        # ----------------------------------------------------
        # Relative Position
        # ----------------------------------------------------

        x_norm = (
            kpx - hip_x
        ) / person_height

        y_norm = (
            kpy - hip_y
        ) / person_height

        normalized_points.append(
            (x_norm, y_norm)
        )

    return (
        np.array(normalized_points, dtype=np.float32),
        hip_x,
        hip_y,
        person_height
    )


# ============================================================
# 7. แสดงคำแนะนำ
# ============================================================

print("==========================================")
print("     เริ่มการบันทึกข้อมูล Pose")
print("==========================================")
print()
print("กดเลข 1 : บันทึก Right")
print("กดเลข 2 : บันทึก Left")
print("กดเลข 3 : บันทึก Front")
print("กดเลข 4 : บันทึก Nomal")
print()
print("กด q : ออกจากโปรแกรม")
print()
print("Normalize:")
print("- จุดอ้างอิง = กลางสะโพก")
print("- Scale = ความสูงของร่างกาย")
print("- ไม่สนตำแหน่งของคนในภาพ")
print("- ไม่สนระยะใกล้/ไกลของคน")
print("==========================================")


# ============================================================
# 8. สร้าง Window
# ============================================================

window = "Label Pose"

cv2.namedWindow(
    window,
    cv2.WINDOW_NORMAL
)

cv2.setWindowProperty(
    window,
    cv2.WINDOW_FULLSCREEN,
    cv2.WND_PROP_FULLSCREEN
)


# ============================================================
# 9. Main Loop
# ============================================================

while True:

    # --------------------------------------------------------
    # อ่าน Frame
    # --------------------------------------------------------

    ret, frame = cap.read()
    # frame = cv2.flip(frame, 1)
    # --------------------------------------------------------
    # ถ้า Video จบ ให้เริ่มใหม่
    # --------------------------------------------------------

    if not ret:

        cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            0
        )

        ret, frame = cap.read()

        if not ret:

            print("File video not found")
            break

    # --------------------------------------------------------
    # ขนาดภาพ
    # --------------------------------------------------------

    h, w = frame.shape[:2]

    # --------------------------------------------------------
    # ถ้าต้องการ Resize สามารถเปิดใช้ได้
    #
    # frame = cv2.resize(
    #     frame,
    #     (1280, 720)
    # )
    # --------------------------------------------------------

    # ========================================================
    # YOLO Tracking
    # ========================================================

    results = model.track(
        source=frame,
        conf=CONF_THRESHOLD,
        persist=True,
        verbose=False,
        tracker="bytetrack.yaml"
    )


    # ========================================================
    # เก็บข้อมูลคนใน Frame ปัจจุบัน
    #
    # {
    #     track_id: features
    # }
    # ========================================================

    current_frame_people = {}


    # ========================================================
    # Loop ผลลัพธ์ YOLO
    # ========================================================

    for result in results:

        # ----------------------------------------------------
        # ตรวจว่ามี Keypoints
        # ----------------------------------------------------

        if result.keypoints is None:
            continue

        # ----------------------------------------------------
        # ตรวจว่ามี Boxes
        # ----------------------------------------------------

        if result.boxes is None:
            continue

        # ----------------------------------------------------
        # ตรวจว่ามี Track ID
        # ----------------------------------------------------

        if result.boxes.id is None:
            continue


        # ====================================================
        # Keypoints XY
        # ====================================================

        keypoints_list = (
            result.keypoints.xy
            .cpu()
            .numpy()
        )


        # ====================================================
        # Keypoints Confidence
        # ====================================================

        keypoint_conf_list = None

        if result.keypoints.conf is not None:

            keypoint_conf_list = (
                result.keypoints.conf
                .cpu()
                .numpy()
            )


        # ====================================================
        # Track IDs
        # ====================================================

        track_ids = (
            result.boxes.id
            .int()
            .cpu()
            .numpy()
        )


        # ====================================================
        # Loop แต่ละคน
        # ====================================================

        for person_index, (
            keypoints,
            track_id
        ) in enumerate(
            zip(
                keypoints_list,
                track_ids
            )
        ):

            # ------------------------------------------------
            # ตรวจจำนวน Keypoints
            # ------------------------------------------------

            if len(keypoints) < 17:
                continue


            # ------------------------------------------------
            # Confidence ของคนนี้
            # ------------------------------------------------

            person_keypoint_conf = None

            if keypoint_conf_list is not None:

                if person_index < len(
                    keypoint_conf_list
                ):

                    person_keypoint_conf = (
                        keypoint_conf_list[
                            person_index
                        ]
                    )


            # =================================================
            # Normalize Pose
            # =================================================

            normalized_result = normalize_pose(
                keypoints,
                person_keypoint_conf
            )


            # ------------------------------------------------
            # Normalize ไม่สำเร็จ
            # ------------------------------------------------

            if normalized_result is None:
                continue


            (
                normalized_points,
                hip_x,
                hip_y,
                person_height
            ) = normalized_result


            # =================================================
            # แปลง Keypoints เป็น int สำหรับวาด
            # =================================================

            pts = keypoints.astype(int)


            # =================================================
            # วาด Skeleton
            # =================================================

            for start_idx, end_idx in SKELETON_CONNECTIONS:

                # ---------------------------------------------
                # ตรวจ index
                # ---------------------------------------------

                if (
                    start_idx >= len(pts)
                    or end_idx >= len(pts)
                ):
                    continue


                # ---------------------------------------------
                # ตรวจ Confidence
                # ---------------------------------------------

                if person_keypoint_conf is not None:

                    if (
                        person_keypoint_conf[start_idx]
                        < KEYPOINT_CONF_THRESHOLD
                    ):
                        continue

                    if (
                        person_keypoint_conf[end_idx]
                        < KEYPOINT_CONF_THRESHOLD
                    ):
                        continue


                # ---------------------------------------------
                # วาดเส้น
                # ---------------------------------------------

                cv2.line(
                    frame,
                    tuple(pts[start_idx]),
                    tuple(pts[end_idx]),
                    (0, 255, 0),
                    2
                )


            # =================================================
            # วาด Keypoints
            # =================================================

            for i, kp in enumerate(keypoints):

                kpx = int(kp[0])
                kpy = int(kp[1])


                # ---------------------------------------------
                # ตรวจ Confidence
                # ---------------------------------------------

                if person_keypoint_conf is not None:

                    if (
                        person_keypoint_conf[i]
                        < KEYPOINT_CONF_THRESHOLD
                    ):
                        continue


                # ---------------------------------------------
                # ตรวจตำแหน่ง
                # ---------------------------------------------

                if kpx <= 0 or kpy <= 0:
                    continue


                # ---------------------------------------------
                # วาดจุด
                # ---------------------------------------------

                cv2.circle(
                    frame,
                    (kpx, kpy),
                    4,
                    (0, 0, 255),
                    cv2.FILLED
                )


            # =================================================
            # แสดง ID
            # =================================================

            id_x = int(pts[0][0])
            id_y = int(pts[0][1]) - 10


            cv2.putText(
                frame,
                f"ID: {track_id}",
                (id_x, id_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )


            # =================================================
            # แสดงความสูงของคน
            # =================================================

            cv2.putText(
                frame,
                f"H: {person_height:.1f}",
                (
                    id_x,
                    id_y + 25
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )


            # =================================================
            # แสดงจุดกลางสะโพก
            # =================================================

            cv2.circle(
                frame,
                (
                    int(hip_x),
                    int(hip_y)
                ),
                6,
                (255, 0, 255),
                cv2.FILLED
            )


            # =================================================
            # เก็บ Feature
            #
            # 17 Keypoints × 2
            # = 34 Features
            # =================================================

            features = (
                normalized_points
                .flatten()
            )


            # ------------------------------------------------
            # ตรวจจำนวน Feature
            # ------------------------------------------------

            if len(features) != 34:

                print(
                    f"Feature ผิดปกติ "
                    f"ID={track_id} "
                    f"จำนวน={len(features)}"
                )

                continue


            # =================================================
            # เก็บลง Dictionary
            # =================================================

            current_frame_people[
                int(track_id)
            ] = features


    # ========================================================
    # แสดง Frame
    # ========================================================

    cv2.imshow(
        window,
        frame
    )


    # ========================================================
    # รับ Keyboard
    # ========================================================

    key = cv2.waitKey(25) & 0xFF


    # ========================================================
    # Q = Exit
    # ========================================================

    if key == ord("q"):

        break


    # ========================================================
    # 1 / 2 / 3 / 4 = Save Label
    # ========================================================

    elif (
        key in [
            ord("1"),
            ord("2"),
            ord("3"),
            ord("4")
        ]
        and len(current_frame_people) > 0
    ):

        # ----------------------------------------------------
        # กำหนด Label
        # ----------------------------------------------------

        if key == ord("1"):

            label = "Right"

        elif key == ord("2"):

            label = "Left"

        elif key == ord("3"):

            label = "Front"

        elif key == ord("4"):

            label = "Nomal"

        else:

            label = ""


        # ====================================================
        # เปิด CSV
        # ====================================================

        with open(
            csv_filename,
            mode="a",
            newline=""
        ) as f:

            writer = csv.writer(f)


            # =================================================
            # บันทึกทุกคนใน Frame
            # =================================================

            for p_id, features in (
                current_frame_people.items()
            ):

                # ---------------------------------------------
                # แปลง numpy → list
                # ---------------------------------------------

                row_data = (
                    features.tolist()
                )


                # ---------------------------------------------
                # เพิ่ม Label
                # ---------------------------------------------

                row_data.append(label)


                # ---------------------------------------------
                # เขียน CSV
                # ---------------------------------------------

                writer.writerow(
                    row_data
                )


                # ---------------------------------------------
                # แสดงผล
                # ---------------------------------------------

                print(
                    f"บันทึกข้อมูล "
                    f"ID {p_id} "
                    f"ท่าทาง '{label}' "
                    f"สำเร็จ!"
                )


# ============================================================
# 10. ปิดโปรแกรม
# ============================================================

cap.release()

cv2.destroyAllWindows()

print()
print("==========================================")
print("สิ้นสุดการบันทึก Dataset")
print(f"ไฟล์: {csv_filename}")
print("==========================================")