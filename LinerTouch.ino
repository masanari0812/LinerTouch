#include <Wire.h>
#include <VL6180X.h>

#define NUM_SENSOR 10
#define HEAD_SENSOR 0
#define TAIL_SENSOR 9
#define CALIBRATE_TIMES 20
#define TARGET_DISTANCE 50
#define SYSRANGE__PART_TO_PART_RANGE_OFFSET 0x024

uint8_t range[NUM_SENSOR];
VL6180X sensor[NUM_SENSOR];
uint8_t pin[NUM_SENSOR] = { 4, 5, 12, 13, 14, 15, 16, 17, 18, 19 };
char logData[NUM_SENSOR];
uint8_t num[NUM_SENSOR];

void range_sensor(void *sensor_id_p) {
  // uint8_t sensor_id = *(uint8_t *)sensor_id_p;
  while (true)
    for (uint8_t sensor_id = HEAD_SENSOR; sensor_id <= TAIL_SENSOR; sensor_id++) {
      range[sensor_id] = sensor[sensor_id].readRangeSingle();
      if (sensor[sensor_id].readRangeStatus() > 6)
        range[sensor_id] = 255;
      vTaskDelay(3 / portTICK_PERIOD_MS);
    }
}
void calibrate_offset() {
  disableWAF();
  disableRangeIgnore();
  for (uint8_t sensor_id = HEAD_SENSOR; sensor_id <= TAIL_SENSOR; sensor_id++) {
    sensor[sensor_id].writeReg(SYSRANGE__PART_TO_PART_RANGE_OFFSET, 0x00);

    uint32_t sum = 0;
    for (uint8_t i = 0; i < CALIBRATE_TIMES; i++)
      sum += sensor[sensor_id].readRangeSingle();
    uint8_t ave = sum / CALIBRATE_TIMES;
    uint8_t offset = TARGET_DISTANCE - ave;
    sensor[sensor_id].writeReg(SYSRANGE__PART_TO_PART_RANGE_OFFSET, offset);
    Serial.printf("%03d ", offset);
    delay(10);
  }
  Serial.println();
  delay(1000);
}

void disableWAF() {
  for (uint8_t sensor_id = HEAD_SENSOR; sensor_id <= TAIL_SENSOR; sensor_id++) {

    writeRegister(sensor_id, 0x001A, 0);  // WAFを無効化
    Serial.println("WAF disabled");
  }
}

void disableRangeIgnore() {
  for (uint8_t sensor_id = HEAD_SENSOR; sensor_id <= TAIL_SENSOR; sensor_id++) {

    writeRegister(sensor_id, 0x002E, 0);  // 範囲無視機能を無効化
    Serial.println("Range Ignore disabled");
  }
}

void writeRegister(uint8_t sensor_id, uint16_t reg, uint8_t value) {
  Wire.beginTransmission(0x30 + sensor_id);
  Wire.write((reg >> 8) & 0xFF);  // 上位バイト
  Wire.write(reg & 0xFF);         // 下位バイト
  Wire.write(value);
  Wire.endTransmission();
  delay(10);
}

void setup() {
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {
    pinMode(pin[i], OUTPUT);
    digitalWrite(pin[i], LOW);
  }
  delay(50);

  Serial.begin(115200);
  Wire.begin();

  //1つ目のセンサーのアドレスの書き換え
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {
    digitalWrite(pin[i], HIGH);
    delay(100);
    sensor[i].init();
    sensor[i].configureDefault();
    sensor[i].setAddress(0x30 + i);  //好きなアドレスに設定
    sensor[i].setTimeout(20);
    // digitalWrite(pin[i], LOW);
    num[i] = i;
  }
  calibrate_offset();
  xTaskCreate(range_sensor, "range_sensor", 2048, NULL, 1, NULL);
}



void loop() {
  // unsigned long interval, startTime, endTime;
  // interval = 0;
  // startTime = millis();
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {
    // if (sensor[i].readRangeStatus() < 6) {
    //   range[i] = sensor[i].readRangeSingle();
    //   Serial.printf("%03d ", range[i]);
    // } else
    //   Serial.print("OoR ");

    if (true) {
      if (range[i] != 255)
        Serial.printf("%03d ", range[i]);
      else
        Serial.print("OoR ");
    }
  }
  Serial.println();
  // endTime = millis();
  // if (interval > endTime - startTime)
  //   delay(interval - (endTime - startTime));
}