#include <Arduino.h>

// ตัวแปรเก็บขา GPIO แบบ Dynamic
int PIN_OK = 2;
int PIN_NG = 4;
int PIN_BUZZER = 5;

// ตัวแปร Flag สำหรับ NG Lock Mode
// เมื่อ NG_LOCKED = true จะไม่ยอมให้เปลี่ยนสถานะเว้นแต่ได้ CMD_RESET
bool NG_LOCKED = false;

void resetOutputs() {
  digitalWrite(PIN_OK, LOW);
  digitalWrite(PIN_NG, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  NG_LOCKED = false;
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
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) {
      return;
    }

    if (input.startsWith("CONFIG:")) {
      parsePinConfig(input);
    }
    else if (input == "CONNECT_DETECT" || input == "CMD_CONNECT") {
      Serial.println("connect detect success");
    }
    else if (input == "CMD_OK") {
      // ถ้า NG_LOCKED = true จะไม่ให้เปลี่ยนสถานะ
      if (NG_LOCKED) {
        Serial.println("ESP32 Status: NG Locked - Ignoring CMD_OK");
      } else {
        digitalWrite(PIN_OK, HIGH);
        digitalWrite(PIN_NG, LOW);
        digitalWrite(PIN_BUZZER, LOW);
        Serial.println("ESP32 Status: OK Active");
      }
    }
    else if (input == "CMD_NG") {
      // ตั้ง NG_LOCKED = true เพื่อให้ไฟ NG คงติดจนกว่าจะได้ CMD_RESET
      NG_LOCKED = true;
      digitalWrite(PIN_OK, LOW);
      digitalWrite(PIN_NG, HIGH);
      digitalWrite(PIN_BUZZER, LOW);
      Serial.println("ESP32 Status: NG Active (Locked until CMD_RESET)");
    }
    else if (input == "CMD_CHECK_START") {
      // ถ้า NG_LOCKED = true จะไม่ให้เปลี่ยนสถานะ
      if (NG_LOCKED) {
        Serial.println("ESP32 Status: NG Locked - Ignoring CMD_CHECK_START");
      } else {
        digitalWrite(PIN_OK, LOW);
        digitalWrite(PIN_NG, LOW);
        digitalWrite(PIN_BUZZER, HIGH);
        Serial.println("ESP32 Status: Person Detected - Buzzer Active!");
      }
    }
    else if (input == "CMD_RESET") {
      resetOutputs();
      Serial.println("ESP32 Status: Reset All Outputs (NG Unlocked)");
    }
  }
}