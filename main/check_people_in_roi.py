import numpy as np
import time
import cv2
import run_start.default_config_var as df


# ============================================================
# Global Configuration
# ============================================================

KEYPOINT_CONF_THRESHOLD = 0.30


# ============================================================
# Pose Normalization
# ============================================================

def normalize_pose(keypoints, keypoint_conf=None):
    """
    Normalize Pose ให้ไม่ขึ้นกับตำแหน่งของคนในภาพ
    """

    # --------------------------------------------------------
    # ตรวจ Keypoints
    # --------------------------------------------------------
    if keypoints is None:
        return None

    keypoints = np.asarray(keypoints, dtype=np.float32)

    # ป้องกัน Array มิติมั่ว หรือจุดไม่ครบ 17 จุด
    if keypoints.ndim < 2 or keypoints.shape[0] < 17:
        return None

    keypoints = keypoints[:17]

    # --------------------------------------------------------
    # สร้าง Valid Mask
    # --------------------------------------------------------
    valid_mask = np.ones(17, dtype=bool)

    # --------------------------------------------------------
    # ตรวจ Confidence ของ Keypoints (แก้ไขจุดนี้)
    # --------------------------------------------------------
    if keypoint_conf is not None:
        try:
            keypoint_conf = np.asarray(keypoint_conf, dtype=np.float32).flatten()
            
            # ตรวจสอบว่ามีข้อมูลอย่างน้อย 17 ค่าหรือไม่
            if keypoint_conf.ndim > 0 and len(keypoint_conf) >= 17:
                valid_mask = keypoint_conf[:17] >= KEYPOINT_CONF_THRESHOLD
        except Exception:
            # หากแปลงค่าไม่สำเร็จ ให้ใช้ valid_mask เดิม (True ทั้งหมด)
            pass

    # --------------------------------------------------------
    # ตรวจ Hip
    # --------------------------------------------------------
    left_hip_valid = valid_mask[11]
    right_hip_valid = valid_mask[12]

    left_hip = keypoints[11]
    right_hip = keypoints[12]

    if left_hip_valid and right_hip_valid:
        hip_x = (left_hip[0] + right_hip[0]) / 2.0
        hip_y = (left_hip[1] + right_hip[1]) / 2.0
    elif left_hip_valid:
        hip_x = left_hip[0]
        hip_y = left_hip[1]
    elif right_hip_valid:
        hip_x = right_hip[0]
        hip_y = right_hip[1]
    else:
        return None

    # --------------------------------------------------------
    # หาจุดที่ใช้ได้
    # --------------------------------------------------------
    valid_points = keypoints[valid_mask]

    if len(valid_points) < 5:
        return None

    # --------------------------------------------------------
    # หาความสูงของคน
    # --------------------------------------------------------
    min_y = np.min(valid_points[:, 1])
    max_y = np.max(valid_points[:, 1])
    person_height = max_y - min_y

    if person_height <= 1:
        return None

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------
    normalized_points = []

    for i, kp in enumerate(keypoints):
        if not valid_mask[i]:
            normalized_points.extend([0.0, 0.0])
            continue

        x_norm = (kp[0] - hip_x) / person_height
        y_norm = (kp[1] - hip_y) / person_height

        normalized_points.extend([x_norm, y_norm])

    if len(normalized_points) != 34:
        return None

    return np.array(normalized_points, dtype=np.float32)


# ============================================================
# Check People In ROI
# ============================================================

class CheckPeopleInRoi:

    def __init__(
        self,
        frame,
        mark_points,
        point_pose
    ):

        self.frame = frame
        self.mark_points = mark_points
        self.point_pose = point_pose

    def checkPeopleInRoi(self):

        people_in_rectangle = False

        # ----------------------------------------------------
        # ตรวจ ROI
        # ----------------------------------------------------

        if (
            self.mark_points
            and len(self.mark_points) >= 2
        ):

            contour = np.array(
                self.mark_points,
                dtype=np.int32
            ).reshape(
                (-1, 1, 2)
            )

            # ------------------------------------------------
            # ตรวจข้อเท้าซ้าย/ขวา
            #
            # 15 = Left Ankle
            # 16 = Right Ankle
            # ------------------------------------------------

            foot_inside_count = 0

            for idx in (15, 16):

                # --------------------------------------------
                # ตรวจว่ามี Keypoint
                # --------------------------------------------

                if idx >= len(
                    self.point_pose
                ):
                    continue

                hpx = int(
                    self.point_pose[idx][0]
                )

                hpy = int(
                    self.point_pose[idx][1]
                )

                # --------------------------------------------
                # Keypoint ไม่ถูกต้อง
                # --------------------------------------------

                if hpx <= 0 or hpy <= 0:
                    continue

                # --------------------------------------------
                # ตรวจว่าเท้าอยู่ใน ROI หรือไม่
                # --------------------------------------------

                if cv2.pointPolygonTest(
                    contour,
                    (hpx, hpy),
                    False
                ) >= 0:

                    foot_inside_count += 1

            # ------------------------------------------------
            # ถ้ามีเท้าอย่างน้อย 1 ข้างอยู่ใน ROI
            # ------------------------------------------------

            if foot_inside_count > 0:

                people_in_rectangle = True

            # ------------------------------------------------
            # วาด Keypoints
            # ------------------------------------------------

            for idx in range(
                min(
                    17,
                    len(self.point_pose)
                )
            ):

                hpx = int(
                    self.point_pose[idx][0]
                )

                hpy = int(
                    self.point_pose[idx][1]
                )

                if (
                    hpx > 0
                    and hpy > 0
                ):

                    cv2.circle(
                        self.frame,
                        (hpx, hpy),
                        3,
                        (0, 255, 255),
                        cv2.FILLED
                    )

        return (
            people_in_rectangle,
            people_in_rectangle
        )


# ============================================================
# Check Pose / Classification
# ============================================================

class Check_where_inRectangle:

    def __init__(
        self,
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
        check_pose,
        keypoint_conf=None
    ):

        self.people_in_rectangle = (
            people_in_rectangle
        )

        self.state_is_terminating = (
            is_terminating
        )

        self.state_termination_start_time = (
            termination_start_time
        )

        self.state_is_ok_holding = (
            is_ok_holding
        )

        self.state_confirm = (
            confirm
        )

        self.state_valaus_last = (
            valaus_last
        )

        self.state_ok_start_time = (
            ok_start_time
        )

        self.point_pose = point_pose

        self.p_id = p_id

        self.pose_classifier = (
            pose_classifier
        )

        self.confidence = None

        self.check_pose = check_pose

        self.keypoint_conf = (
            keypoint_conf
        )

    # ========================================================
    # Classification
    # ========================================================

    def check_where_inRectangle(
        self,
        frame,
        w,
        h,
        manager
    ):

        # ----------------------------------------------------
        # ถ้าไม่มีคนใน ROI
        # ----------------------------------------------------

        if not self.people_in_rectangle:

            return (
                self.confidence,
                self.state_is_terminating,
                self.state_termination_start_time,
                self.state_is_ok_holding,
                self.state_confirm,
                self.state_valaus_last,
                self.state_ok_start_time
            )

        # ====================================================
        # ยกเลิกสถานะ Terminating
        # ====================================================

        if self.state_is_terminating:

            self.state_is_terminating = False

            self.state_termination_start_time = (
                None
            )

        # ====================================================
        # Normalize Pose
        # ====================================================

        normalized_points = normalize_pose(
            self.point_pose,
            self.keypoint_conf
        )

        # ----------------------------------------------------
        # Normalize ไม่สำเร็จ
        # ----------------------------------------------------

        if normalized_points is None:

            self.confidence = None

            return (
                self.confidence,
                self.state_is_terminating,
                self.state_termination_start_time,
                self.state_is_ok_holding,
                self.state_confirm,
                self.state_valaus_last,
                self.state_ok_start_time
            )

        # ====================================================
        # เตรียม Feature
        # ====================================================

        features = normalized_points.reshape(
            1,
            -1
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # ตรวจ Feature ต้องมี 34 ค่า
        # ----------------------------------------------------

        if features.shape[1] != 34:

            print(
                f"[Pose] Feature ผิดปกติ "
                f"ID={self.p_id} "
                f"shape={features.shape}"
            )

            return (
                self.confidence,
                self.state_is_terminating,
                self.state_termination_start_time,
                self.state_is_ok_holding,
                self.state_confirm,
                self.state_valaus_last,
                self.state_ok_start_time
            )

        # ====================================================
        # วาด Keypoints บนภาพ
        # ====================================================

        for idx in range(
            min(
                17,
                len(self.point_pose)
            )
        ):

            kpx = int(
                self.point_pose[idx][0]
            )

            kpy = int(
                self.point_pose[idx][1]
            )

            if (
                kpx > 0
                and kpy > 0
            ):

                cv2.circle(
                    frame,
                    (kpx, kpy),
                    5,
                    (0, 0, 255),
                    cv2.FILLED
                )

        # ====================================================
        # Classification
        # ====================================================

        try:

            predicted_label = (
                self.pose_classifier
                .predict(features)[0]
            )

            probabilities = (
                self.pose_classifier
                .predict_proba(features)[0]
            )

            self.confidence = float(
                np.max(probabilities)
                * 100
            )

        except Exception as e:

            print(
                f"[Pose Classifier Error] "
                f"ID={self.p_id}: {e}"
            )

            self.confidence = None

            return (
                self.confidence,
                self.state_is_terminating,
                self.state_termination_start_time,
                self.state_is_ok_holding,
                self.state_confirm,
                self.state_valaus_last,
                self.state_ok_start_time
            )

        # # ====================================================
        # # แสดงผล Classification
        # # ====================================================

        # try:

        #     cv2.putText(
        #         frame,
        #         f"ID: {self.p_id}",
        #         (20, 40),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (255, 255, 0),
        #         2
        #     )

        #     cv2.putText(
        #         frame,
        #         f"Pose: {predicted_label}",
        #         (20, 70),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (0, 255, 0),
        #         2
        #     )

        #     cv2.putText(
        #         frame,
        #         f"Confidence: {self.confidence:.1f}%",
        #         (20, 100),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.7,
        #         (0, 255, 255),
        #         2
        #     )

        # except Exception:
        #     pass

        # ====================================================
        # State OK Holding
        # ====================================================

        if self.state_is_ok_holding:

            if (
                time.time()
                - self.state_ok_start_time
                < manager.ok_display_time
            ):

                self.state_confirm = "OK"

            else:

                self.state_is_ok_holding = False

                self.state_confirm = "NG"

                self.state_valaus_last = []

        # ====================================================
        # ตรวจลำดับ Pose
        # ====================================================

        else:

            expected_pose_idx = len(
                self.state_valaus_last
            )

            if (
                expected_pose_idx
                < len(self.check_pose)
            ):

                expected_pose = (
                    self.check_pose[
                        expected_pose_idx
                    ]
                )

                # ------------------------------------------------
                # ตรวจ Label
                # ------------------------------------------------

                if predicted_label == expected_pose:

                    # --------------------------------------------
                    # ป้องกัน Label ซ้ำ
                    # --------------------------------------------

                    if (
                        not self.state_valaus_last
                        or predicted_label
                        != self.state_valaus_last[-1]
                    ):

                        self.state_valaus_last.append(
                            predicted_label
                        )

                        print(
                            f"[Pose] "
                            f"ID={self.p_id} "
                            f"พบ {predicted_label} "
                            f"Confidence="
                            f"{self.confidence:.1f}%"
                        )

            # ====================================================
            # ตรวจครบทุก Pose
            # ====================================================

            if (
                self.state_valaus_last
                == self.check_pose
            ):

                self.state_confirm = "OK"

                self.state_is_ok_holding = True

                self.state_ok_start_time = (
                    time.time()
                )

        # ====================================================
        # Return State
        # ====================================================

        return (
            self.confidence,
            self.state_is_terminating,
            self.state_termination_start_time,
            self.state_is_ok_holding,
            self.state_confirm,
            self.state_valaus_last,
            self.state_ok_start_time
        )


# ============================================================
# Record Video
# ============================================================

class RecordVedioDetect:

    def __init__(
        self,
        state_writer,
        state_video_farme,
        id,
        fourcc,
        w,
        h
    ):

        self.state_writer = state_writer

        self.state_videoFrame = (
            state_video_farme
        )

        self.p_id = id

        self.fourcc = fourcc

        self.w = w

        self.h = h

    # ========================================================
    # Start Recording
    # ========================================================

    def recordingVideo(self):

        # ----------------------------------------------------
        # ถ้ายังไม่มี VideoWriter
        # ----------------------------------------------------

        if self.state_writer is None:

            current_time_str = int(
                time.time()
            )

            self.state_videoFrame = (
                f"video_center/"
                f"violation_"
                f"{self.p_id}_"
                f"{current_time_str}.mp4"
            )

            self.state_writer = (
                cv2.VideoWriter(
                    self.state_videoFrame,
                    self.fourcc,
                    df.save_video_per_frame,
                    (self.w, self.h)
                )
            )

            print(
                f"[Record] "
                f"ID {self.p_id} "
                f"เข้าจุด -> "
                f"เริ่มบันทึกวิดีโอ: "
                f"{self.state_videoFrame}"
            )

        return (
            self.state_writer,
            self.state_videoFrame
        )