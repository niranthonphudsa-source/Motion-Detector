import os
import sys
import time
import subprocess
from datetime import datetime

# =========================================================
# ตั้งค่า path
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
POSE_SCRIPT = os.path.join(BASE_DIR, "main.py")

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SUPERVISOR_LOG = os.path.join(LOG_DIR, "supervisor.log")
HEARTBEAT_FILE = os.path.join(LOG_DIR, "heartbeat.txt")

RESTART_DELAY_SEC = 3

# ถ้า heartbeat ไม่อัปเดตเกินกี่วินาที ถือว่าค้าง
HEARTBEAT_TIMEOUT_SEC = 120
STARTUP_GRACE_PERIOD_SEC = 180

# ตรวจ heartbeat ทุกกี่วินาที
CHECK_INTERVAL_SEC = 10


def write_log(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {message}"
    print(line)

    with open(SUPERVISOR_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_heartbeat_age_seconds() -> float | None:
    """
    คืนค่าอายุของ heartbeat file เป็นวินาที
    ถ้าไม่มีไฟล์ คืน None
    """
    if not os.path.exists(HEARTBEAT_FILE):
        return None

    modified_time = os.path.getmtime(HEARTBEAT_FILE)
    return time.time() - modified_time


def start_pose_process() -> subprocess.Popen:
    """
    เปิด main.py เป็น subprocess
    """


    if os.path.exists(HEARTBEAT_FILE):
        try:
            os.remove(HEARTBEAT_FILE)
            write_log("Old heartbeat file removed.")
        except OSError as ex:
            write_log(f"Warning: could not remove old heartbeat: {ex}")

    python_exe = sys.executable
    cmd = [python_exe, POSE_SCRIPT]

    write_log(f"Starting main.py with: {python_exe}")
    
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_DIR,
        env={**os.environ, "PYTHONPATH": PROJECT_DIR}
    )
    return process


def stop_pose_process(process: subprocess.Popen) -> None:
    """
    ปิด process อย่างสุภาพก่อน ถ้าไม่ยอมค่อย kill
    """
    if process.poll() is not None:
        return  # จบไปแล้ว

    write_log("Stopping main.py ...")
    process.terminate()

    try:
        process.wait(timeout=10)
        write_log("main.py terminated gracefully.")
    except subprocess.TimeoutExpired:
        write_log("main.py did not terminate in time. Killing process...")
        process.kill()
        process.wait()
        write_log("main.py killed.")


def main():
    if not os.path.exists(POSE_SCRIPT):
        write_log(f"ERROR: main.py not found at: {POSE_SCRIPT}")
        return

    write_log("Supervisor started.")

    while True:
        process = None

        try:
            process = start_pose_process()
            start_time = time.time()

            while True:
                time.sleep(CHECK_INTERVAL_SEC)

                # 1) เช็กว่าตัวโปรแกรมปิดไปหรือยัง
                exit_code = process.poll()
                if exit_code is not None:
                    write_log(f"main.py stopped. Exit code = {exit_code}")
                    break

                # 2) เช็ก heartbeat ว่ายังอัปเดตอยู่ไหม
                heartbeat_age = get_heartbeat_age_seconds()

                if heartbeat_age is None:
                    if time.time() - start_time < STARTUP_GRACE_PERIOD_SEC:
                        write_log("Waiting for main.py to initialize and create heartbeat...")
                        continue
                    write_log("Heartbeat was not created after startup timeout; main.py may have failed.")
                    stop_pose_process(process)
                    break

                if heartbeat_age > HEARTBEAT_TIMEOUT_SEC:
                    write_log(
                        f"Heartbeat timeout ({heartbeat_age:.1f} sec). "
                        f"Assume main.py is hung. Restarting..."
                    )
                    stop_pose_process(process)
                    break

        except Exception as ex:
            write_log(f"Supervisor ERROR: {ex}")

            # กันกรณี process ยังไม่ปิด
            if process is not None:
                try:
                    stop_pose_process(process)
                except Exception as sub_ex:
                    write_log(f"Error while stopping process: {sub_ex}")

        write_log(f"Restarting in {RESTART_DELAY_SEC} seconds...")
        time.sleep(RESTART_DELAY_SEC)


if __name__ == "__main__":
    main()