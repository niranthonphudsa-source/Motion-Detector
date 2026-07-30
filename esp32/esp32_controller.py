#include <Arduino.h>

// ตัวแปรเก็บขา GPIO แบบ Dynamic
int PIN_OK = 2;      // ค่าเริ่มต้น (ปรับเปลี่ยนได้จาก GUI)
int PIN_NG = 4;
int PIN_BUZZER = 5;

void applyPinModes() {
  pinMode(PIN_OK, OUTPUT);
  pinMode(PIN_NG, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  
  // ตั้งค่าเป็น LOW เริ่มต้น
  digitalWrite(PIN_OK, LOW);
  digitalWrite(PIN_NG, LOW);
  digitalWrite(PIN_BUZZER, LOW);
}

void parsePinConfig(String payload) {
  // รับข้อมูลรูปแบบ: CONFIG:PIN_OK=2,PIN_NG=4,PIN_BUZZER=5
  payload.replace("CONFIG:", "");
  
  int startIdx = 0;
  while (startIdx < payload.length()) {
    int commaIdx = payload.indexOf(',', startIdx);
    if (commaIdx == -1) commaIdx = payload.length();
    
    String pair = payload.substring(startIdx, commaIdx);
    int eqIdx = pair.indexOf('=');
    if (eqIdx != -1) {
      String key = pair.substring(0, eqIdx);
      int pinVal = pair.substring(eqIdx + 1).toInt();
      
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
    
    if (input.startsWith("CONFIG:")) {
      parsePinConfig(input);
    }
    else if (input == "CMD_OK") {
      digitalWrite(PIN_OK, HIGH);
      digitalWrite(PIN_NG, LOW);
      digitalWrite(PIN_BUZZER, LOW);
      Serial.println("ESP32 Status: OK Active");
    }
    else if (input == "CMD_NG") {
      digitalWrite(PIN_OK, LOW);
      digitalWrite(PIN_NG, HIGH);
      digitalWrite(PIN_BUZZER, LOW);
      Serial.println("ESP32 Status: NG Active");
    }
    else if (input == "CMD_CHECK_START") {
      // เมื่อเซนเซอร์พบคนในพื้นที่ Check Start สั่งติดลำโพง/เตือน
      digitalWrite(PIN_OK, LOW);
      digitalWrite(PIN_NG, LOW);
      digitalWrite(PIN_BUZZER, HIGH); 
      Serial.println("ESP32 Status: Person Detected - Buzzer Active!");
    }
    else if (input == "CMD_RESET") {
      digitalWrite(PIN_OK, LOW);
      digitalWrite(PIN_NG, LOW);
      digitalWrite(PIN_BUZZER, LOW);
      Serial.println("ESP32 Status: Reset All Outputs");
    }
  }
}