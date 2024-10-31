#include <Wire.h>
#include <VL6180X.h>

#define NUM_SENSOR 1

uint8_t range;
VL6180X sensor[NUM_SENSOR];
int pin[4] = { 32, 33, 25, 26 };
char logData[4];
void setup() {
  for (int i = 0; i < NUM_SENSOR; i++) {
    pinMode(pin[i], OUTPUT);
    digitalWrite(pin[i], LOW);
  }
  delay(50);

  Serial.begin(9600);
  Wire.begin();

  //1つ目のセンサーのアドレスの書き換え
  for (int i = 0; i < NUM_SENSOR; i++) {
    digitalWrite(pin[i], HIGH);
    delay(100);
    sensor[i].init();
    sensor[i].configureDefault();
    sensor[i].setAddress(0x30 + i);  //好きなアドレスに設定
  }
}

void loop() {
  for (int i = 0; i < NUM_SENSOR; i++) {
    range = sensor[i].readRangeSingle();
    if (sensor[i].readRangeStatus() < 6)
      sprintf(logData, "%03d", range);
    else sprintf(logData, "OoR");
    Serial.print(logData);
    Serial.print(" ");
  }
  Serial.println();
  delay(10);
}
