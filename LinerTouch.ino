#include <Wire.h>
#include <VL6180X.h>

#define NUM_SENSOR 10
#define HEAD_SENSOR 0
#define TAIL_SENSOR 9
#define CALIBRATE_TIMES 30
#define TARGET_DISTANCE 50
#define SYSRANGE__PART_TO_PART_RANGE_OFFSET 0x024

uint8_t range[NUM_SENSOR];
VL6180X sensor[NUM_SENSOR];
uint8_t pin[NUM_SENSOR] = { 4, 5, 12, 13, 14, 15, 16, 17, 18, 19 };
char logData[NUM_SENSOR];
uint8_t num[NUM_SENSOR];

// 指定されたセンサの測距
void range_sensor(void *sensor_id_p) {
  uint8_t sensor_id = *(uint8_t *)sensor_id_p;
  while (true) {
    range[sensor_id] = sensor[sensor_id].readRangeSingle();
    if (sensor[sensor_id].readRangeStatus() > 6)
      range[sensor_id] = 255;
  }
}
// すべてのセンサの測距
void p_range_sensor(void *sensor_id_p) {
  while (true)
    for (uint8_t sensor_id = HEAD_SENSOR; sensor_id <= TAIL_SENSOR; sensor_id++) {
      range[sensor_id] = sensor[sensor_id].readRangeSingle();
      if (sensor[sensor_id].readRangeStatus() > 6)
        range[sensor_id] = 255;
    }
}


// 測距のキャリブレーション
void calibrate_offset(uint8_t sensor_id) {
  disableWAF(sensor_id);
  disableRangeIgnore(sensor_id);
  sensor[sensor_id].writeReg(SYSRANGE__PART_TO_PART_RANGE_OFFSET, 0x00);
  delay(10);
  // センサによる複数回の測定処理とその値の平均値の差分が補正値になる
  uint32_t sum = 0;
  for (uint8_t i = 0; i < CALIBRATE_TIMES; i++)
    sum += sensor[sensor_id].readRangeSingle();
  uint8_t ave = sum / CALIBRATE_TIMES;
  uint8_t offset = TARGET_DISTANCE - ave;
  sensor[sensor_id].writeReg(SYSRANGE__PART_TO_PART_RANGE_OFFSET, offset);
  Serial.printf("Sensor %2u: offset->%03u \n", sensor_id, offset);
  delay(10);
}

void disableWAF(uint8_t sensor_id) {
  Serial.printf("Sensor %2u: WAF disabled\n", sensor_id);
  writeRegister(sensor_id, 0x001A, 0);  // WAFを無効化
}

void disableRangeIgnore(uint8_t sensor_id) {
  Serial.printf("Sensor %2u: Range Ignore disabled\n", sensor_id);
  writeRegister(sensor_id, 0x002E, 0);  // 範囲無視機能を無効化
}

// VL6180Xのセンサの内部メモリデータ書き換え処理
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
    delay(10);
    sensor[i].init();
    sensor[i].configureDefault();
    sensor[i].setAddress(0x30 + i);  //好きなアドレスに設定
    sensor[i].setTimeout(20);
    // digitalWrite(pin[i], LOW);
    num[i] = i;
    calibrate_offset(i);
    // xTaskCreate(range_sensor, "range_sensor", 2048, (void *)&num[i], 1, NULL);
    // sensor[sensor_id].startContinuous(interval)
  }
  // for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++)
  //   xTaskCreate(range_sensor, "range_sensor", 2048, (void *)&num[i], 1, NULL);

  xTaskCreate(p_range_sensor, "p_range_sensor", 2048, NULL, 1, NULL);
}



void loop() {
  // unsigned long interval, startTime, endTime;
  // interval = 0;
  // startTime = millis();
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {
    // if (sensor[i].readRangeStatus() < 6) {
    //   range[i] = sensor[i].readRangeSingle();
    //   Serial.printf("%03u ", range[i]);
    // } else
    //   Serial.print("OoR ");

    if (true) {
      if (range[i] != 255)
        Serial.printf("%03u ", range[i]);
      else
        Serial.print("OoR ");
    }
  }
  Serial.println();
  // endTime = millis();
  // if (interval > endTime - startTime)
  //   delay(interval - (endTime - startTime));
}