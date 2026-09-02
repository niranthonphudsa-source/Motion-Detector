#include <Arduino.h>

// ตัวแปรเก็บขา GPIO แบบ Dynamic
int PIN_OK = 4;
int PIN_NG = 2;
int PIN_BUZZER = 5;

// ตัวแปรควบคุมการกระพริบไฟแบบ Non-blocking (millis)
enum DeviceState { STATE_IDLE, STATE_OK, STATE_NG, STATE_CHECKING };
DeviceState currentState = STATE_IDLE;

unsigned long lastBlinkTime = 0;
const long blinkInterval = 300; // ความเร็วในการกระพริบไฟ (ms)

void resetOutputs() {
  digitalWrite(PIN_OK, LOW);
  digitalWrite(PIN_NG, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  currentState = STATE_IDLE;
}

void applyPinModes() {
  pinMode(PIN_OK, OUTPUT);
  pinMode(PIN_NG, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  resetOutputs();
}

void parsePinConfig(String payload) {
  payload.trim();

  if (payload.startsWith("CONFIG:")) {
    payload = payload.substring(String("CONFIG:").length());
  }

  int startIdx = 0;
  while (startIdx < payload.length()) {
    int commaIdx = payload.indexOf(',', startIdx);
    if (commaIdx == -1) commaIdx = payload.length();

    String pair = payload.substring(startIdx, commaIdx);
    pair.trim();

    int eqIdx = pair.indexOf('=');
    if (eqIdx != -1) {
      String key = pair.substring(0, eqIdx);
      key.trim();

      String valueStr = pair.substring(eqIdx + 1);
      valueStr.trim();

      int pinVal = valueStr.toInt();

      if (key == "PIN_OK") PIN_OK = pinVal;
      else if (key == "PIN_NG") PIN_NG = pinVal;
      else if (key == "PIN_BUZZER") PIN_BUZZER = pinVal;
    }

    startIdx = commaIdx + 1;
  }

  applyPinModes();
  Serial.println("ESP32: Configured Pins Updated!");
}

void setup() {
  Serial.begin(115200);
  applyPinModes();
}

void loop() {
  // --- Part 1: อ่าน Serial Command จาก Python/Mini PC ---
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) return;

    if (input.startsWith("CONFIG:")) {
      parsePinConfig(input);
    }
    else if (input == "CONNECT_DETECT" || input == "CMD_CONNECT") {
      Serial.println("connect detect success");
    }
    else if (input == "CMD_OK") {
      resetOutputs();
      currentState = STATE_OK; // สั่งกระพริบ PIN_OK
      Serial.println("ESP32 Status: OK Blinking Started");
    }
    else if (input == "CMD_NG") {
      resetOutputs();
      currentState = STATE_NG; // สั่งกระพริบ PIN_NG
      Serial.println("ESP32 Status: NG Blinking Started");
    }
    else if (input == "CMD_CHECK_START") {
      resetOutputs();
      currentState = STATE_CHECKING;
      digitalWrite(PIN_BUZZER, HIGH); // สั่ง Buzzer ดังค้างตอนเจอคน
      Serial.println("ESP32 Status: Person Detected - Buzzer Active!");
    }
    else if (input == "CMD_RESET") {
      resetOutputs();
      Serial.println("ESP32 Status: Reset All Outputs");
    }
  }

  // --- Part 2: จัดการการกระพริบไฟตาม State (Non-blocking Timer) ---
  unsigned long currentMillis = millis();

  if (currentMillis - lastBlinkTime >= blinkInterval) {
    lastBlinkTime = currentMillis;

    if (currentState == STATE_OK) {
      digitalWrite(PIN_OK, !digitalRead(PIN_OK)); // สลับไฟ OK
      digitalWrite(PIN_NG, LOW);
      digitalWrite(PIN_BUZZER, LOW);
    } 
    else if (currentState == STATE_NG) {
      digitalWrite(PIN_OK, LOW);
      digitalWrite(PIN_NG, !digitalRead(PIN_NG)); // สลับไฟ NG
      digitalWrite(PIN_BUZZER, LOW);
    }
  }
}