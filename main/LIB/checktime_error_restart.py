import os
import sys
import time
import subprocess
import yaml
from datetime import datetime

# =========================================================
# ตั้งค่า path
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
GRAND_DIR = os.path.dirname(PARENT_DIR)
POSE_SCRIPT = os.path.join(PARENT_DIR, "main.py")

GRANDPARENT_DIR = os.path.dirname(PARENT_DIR)
CONFIG_PATH = os.path.join(GRANDPARENT_DIR, "setting", "config.yml")

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SUPERVISOR_LOG = os.path.join(LOG_DIR, "supervisor.log")
MAIN_OUTPUT_LOG = os.path.join(LOG_DIR, "main_output.log")
HEARTBEAT_FILE = os.path.join(LOG_DIR, "heartbeat.txt")

RESTART_DELAY_SEC = 5

# ถ้า heartbeat ไม่อัปเดตเกินกี่วินาที ถือว่าค้าง
HEARTBEAT_TIMEOUT_SEC = 120

# ระยะเวลาสเป็กให้ main.py สร้าง heartbeat ไฟล์แรก (วินาที)
STARTUP_GRACE_PERIOD_SEC = 30

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


def start_pose_process() -> tuple[subprocess.Popen, object]:
    """
    เปิด main.py เป็น subprocess พร้อมเก็บ log output
    """
    # ลบไฟล์ heartbeat.txt เก่าออกทุกครั้งก่อนรันใหม่
    if os.path.exists(HEARTBEAT_FILE):
        try:
            os.remove(HEARTBEAT_FILE)
            write_log("Old heartbeat file removed.")
        except Exception as e:
            write_log(f"Warning: Could not remove old heartbeat file: {e}")

    python_exe = sys.executable
    cmd = [python_exe, POSE_SCRIPT]

    write_log(f"Starting main.py with: {python_exe}")

    # ✅ เปิดไฟล์ log สำหรับเก็บ stdout/stderr จาก main.py
    main_log_file = open(MAIN_OUTPUT_LOG, "a", encoding="utf-8")
    main_log_file.write(f"\n--- Process started at {datetime.now()} ---\n")
    main_log_file.flush()

    process = subprocess.Popen(
        cmd,
        cwd=PARENT_DIR,
        stdout=main_log_file,  # ส่ง stdout ไปลงไฟล์ log
        stderr=subprocess.STDOUT  # ส่ง stderr (Error/Traceback) รวมไปที่ stdout
    )
    return process, main_log_file


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
        log_file_obj = None

        try:
            process, log_file_obj = start_pose_process()
            start_time = time.time()  # บันทึกเวลาที่เริ่มเปิด Process

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
                    # ถ้าเพิ่งเปิดโปรแกรมยังไม่เกินระยะ Grace Period
                    if time.time() - start_time < STARTUP_GRACE_PERIOD_SEC:
                        write_log("Waiting for main.py to initialize and create heartbeat...")
                        continue
                    else:
                        # ✅ แก้ไข: เกิน Grace period แล้วยังไม่มีไฟล์ heartbeat สั่ง Restart ทันที
                        write_log("Heartbeat file was never created after startup timeout. Restarting...")
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

        finally:
            # ปิดไฟล์ Log ของ main.py ในแต่ละรอบ
            if log_file_obj and not log_file_obj.closed:
                log_file_obj.close()

        write_log(f"Restarting in {RESTART_DELAY_SEC} seconds...")
        time.sleep(RESTART_DELAY_SEC)


if __name__ == "__main__":
    main()