import json
import os

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

    def __init__(self, port=None, baudrate=115200, config_filename="esp32_pin_config.json"):
        self.port = port
        self.baudrate = int(baudrate)
        self.config_filename = config_filename
        self.ser = None

    def _load_port_from_file(self):
        if not self.port and os.path.exists(self.config_filename):
            try:
                with open(self.config_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.port = data.get("PORT") or data.get("port")
            except Exception:
                self.port = None

    def _detect_port(self):
        if serial is None or serial.tools.list_ports is None:
            return None
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            return None
        return ports[0]

    def _ensure_connection(self):
        if self.ser is not None and self.ser.is_open:
            return True

        self._load_port_from_file()
        if not self.port:
            self.port = self._detect_port()

        if not self.port:
            return False

        try:
            if serial is None:
                return False
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except Exception:
            self.ser = None
            return False

    def send_command(self, cmd_type):
        if not self._ensure_connection():
            return False

        try:
            self.ser.write(f"{cmd_type}\n".encode("utf-8"))
            self.ser.flush()
            return True
        except Exception:
            self.ser = None
            return False

    def reset(self):
        self.send_command("CMD_RESET")
