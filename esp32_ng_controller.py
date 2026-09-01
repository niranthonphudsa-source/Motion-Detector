import json
import os
import time

try:
    import serial
    import serial.tools.list_ports
except Exception:  # pragma: no cover - optional dependency in some environments
    serial = None
    serial_tools = None


class NGThresholdController:
    """Track cumulative NG count and trigger once the threshold is reached."""

    def __init__(self, threshold=10, on_trigger=None):
        self.threshold = max(1, int(threshold))
        self.on_trigger = on_trigger
        self.ng_count = 0
        self.is_triggered = False

    def set_threshold(self, threshold):
        value = int(threshold)
        if value <= 0:
            value = 1
        self.threshold = value
        if not self.is_triggered:
            self.ng_count = 0

    def register_ng(self):
        if self.is_triggered:
            return False

        self.ng_count += 1
        if self.ng_count >= self.threshold:
            self.is_triggered = True
            if self.on_trigger is not None:
                self.on_trigger()
            return True
        return False

    def reset(self):
        self.ng_count = 0
        self.is_triggered = False


class ESP32SerialController:
    """Send simple commands to an ESP32 serial device for status output."""
    def __init__(self, port=None, baudrate=115200, config_filename=r"main\setting_esp32\esp32_pin_config.json", ng_threshold_controller=None):
        self.port = port
        self.baudrate = int(baudrate)
        self.config_filename = config_filename
        self.ser = None
        self.light_enabled = True
        self.reset_after_sec = 10
        self.reset_timer = None
        self.ng_threshold_controller = ng_threshold_controller  # Reference to reset NG counter

    def _resolve_config_path(self):
        candidates = []
        if self.config_filename:
            if os.path.isabs(self.config_filename):
                candidates.append(self.config_filename)
            else:
                candidates.extend([
                    os.path.join(os.getcwd(), self.config_filename),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main", "setting_esp32", self.config_filename),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main", self.config_filename),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.config_filename),
                ])

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return self.config_filename

    def _load_port_from_file(self):
        config_path = self._resolve_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.port = self.port or data.get("PORT") or data.get("port") or data.get("COM_PORT") or data.get("serial_port")
                baud = data.get("BAUD") or data.get("baud") or data.get("baudrate")
                if baud:
                    self.baudrate = int(baud)
            except Exception:
                self.port = self.port

    def _detect_port(self):
        if serial is None or serial.tools.list_ports is None:
            return None
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            return None
        return ports[0]

    def _ensure_connection(self):
        print(f"[ESP32 DEBUG] _ensure_connection(): port={self.port}, baud={self.baudrate}, ser_open={self.ser is not None and self.ser.is_open}")

        if self.ser is not None and self.ser.is_open:
            print("[ESP32 DEBUG] already connected")
            return True

        if not self.port:
            self._load_port_from_file()
            print(f"[ESP32 DEBUG] after _load_port_from_file(): port={self.port}, baud={self.baudrate}")

        if not self.port:
            self.port = self._detect_port()
            print(f"[ESP32 DEBUG] after _detect_port(): port={self.port}, baud={self.baudrate}")

        if not self.port:
            print("[ESP32 DEBUG] FAIL: no port found")
            return False

        try:
            if serial is None:
                print("[ESP32 DEBUG] FAIL: pyserial is not available")
                return False

            print(f"[ESP32 DEBUG] opening serial: port={self.port}, baud={self.baudrate}")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"[ESP32 DEBUG] connected successfully to {self.port}")
            return True
        except Exception as e:
            print(f"[ESP32 DEBUG] FAIL: serial open error -> {type(e).__name__}: {e}")
            self.ser = None
            return False

    def connect_detect(self):
        if not self._ensure_connection():
            return False

        try:
            self.ser.write(b"CONNECT_DETECT\n")
            self.ser.flush()
            time.sleep(0.3)
            response = self.ser.readline().decode("utf-8", errors="ignore").strip()
            return response
        except Exception:
            self.ser = None
            return False

    def send_command(self, cmd_type):
        print(f"[ESP32 DEBUG] send_command({cmd_type}) start")
        print(f"[ESP32 DEBUG] current state before ensure: port={self.port}, baud={self.baudrate}, ser={self.ser}")

        if self.ser is not None and self.ser.is_open:
            print("[ESP32 DEBUG] reuse existing serial connection")
        elif not self._ensure_connection():
            print(f"[ESP32 DEBUG] cannot send {cmd_type}: connection failed")
            return False

        try:
            print(f"📡 ส่งคำสั่งไปยัง ESP32: {cmd_type}")
            self.ser.write(f"{cmd_type}\n".encode("utf-8"))
            self.ser.flush()
            print(f"[ESP32 DEBUG] write success for {cmd_type}")
            return True
        except Exception as e:
            print(f"[ESP32 DEBUG] FAIL: write error -> {type(e).__name__}: {e}")
            try:
                if self.ser is not None and self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass
            self.ser = None
            return False

    def set_light_enabled(self, enabled):
        """Enable or disable ESP32 light output."""
        self.light_enabled = bool(enabled)

    def set_reset_after_sec(self, seconds):
        """Set the delay (in seconds) before sending CMD_RESET after NG trigger."""
        self.reset_after_sec = max(0, int(seconds))

    def trigger_ng(self, status="NG"):
        """
        Trigger NG status:
        1. Print the trigger event
        2. Send CMD_NG if light_enabled is True
        3. Schedule CMD_RESET after reset_after_sec delay
        """
        port = self.port or self._detect_port() or "auto-detect"
        baud = self.baudrate
        print(f"send esp32 {status}")
        print(f"🚨 [ESP32 NG Trigger] NG detected -> Port={port}, Baud={baud}")

        if not self.light_enabled:
            print("[ESP32] Undon switch is OFF -> skipping CMD_NG")
            return False

        # Send CMD_NG
        result = self.send_command("CMD_NG")

        # Schedule CMD_RESET after delay
        if result and self.reset_after_sec > 0:
            self._schedule_reset()

        return result

    def _schedule_reset(self):
        """Schedule a CMD_RESET to be sent after reset_after_sec seconds."""
        import threading

        def _reset_action():
            try:
                print(f"⏱️ [ESP32 Reset Timer] Waiting {self.reset_after_sec} seconds -> sending CMD_RESET")
                time.sleep(self.reset_after_sec)
                if not self.light_enabled:
                    print("[ESP32 Reset Timer] Undon is OFF -> skipping CMD_RESET")
                    return
                self._load_port_from_file()
                if not self._ensure_connection():
                    print("[ESP32 Reset Timer] Cannot connect to ESP32 -> skipping CMD_RESET")
                    return
                ok = self.send_command("CMD_RESET")
                print(f"[ESP32 Reset Timer] Result: {ok}")
                
                # Reset NG counter after successful CMD_RESET
                if ok and self.ng_threshold_controller is not None:
                    self.ng_threshold_controller.reset()
                    print("[ESP32 Reset Timer] ✅ NG counter reset for next trigger cycle")
            except Exception as e:
                print(f"[ESP32 Reset Timer Error] {e}")

        # Cancel previous timer if any
        if self.reset_timer is not None:
            self.reset_timer.cancel()

        self.reset_timer = threading.Timer(self.reset_after_sec, _reset_action)
        self.reset_timer.daemon = True
        self.reset_timer.start()

    def close(self):
        try:
            if self.reset_timer is not None:
                self.reset_timer.cancel()
        except Exception:
            pass

        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    def reset(self):
        self.send_command("CMD_RESET")
