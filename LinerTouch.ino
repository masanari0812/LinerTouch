#include <Wire.h>
#include <VL6180X.h>

#define NUM_SENSOR 10

uint8_t range[NUM_SENSOR];
VL6180X sensor[NUM_SENSOR];
uint8_t pin[NUM_SENSOR] = { 4, 5, 12, 13, 14, 15, 16, 17, 18, 19 };
char logData[NUM_SENSOR];
uint8_t num[NUM_SENSOR];

void range_sensor(void *sensor_id_p) {
  // uint8_t sensor_id = *(uint8_t *)sensor_id_p;
  while (true)
    for (uint8_t sensor_id = 0; sensor_id < NUM_SENSOR; sensor_id++) {
      range[sensor_id] = sensor[sensor_id].readRangeSingle();
      if (sensor[sensor_id].readRangeStatus() > 6)
        range[sensor_id] = 255;
      vTaskDelay(1 / portTICK_PERIOD_MS);
    }
}

void setup() {
  for (uint8_t i = 0; i < NUM_SENSOR; i++) {
    pinMode(pin[i], OUTPUT);
    digitalWrite(pin[i], LOW);
  }
  delay(50);

  Serial.begin(115200);
  Wire.begin();

  //1つ目のセンサーのアドレスの書き換え
  for (uint8_t i = 0; i < NUM_SENSOR; i++) {
    digitalWrite(pin[i], HIGH);
    delay(100);
    sensor[i].init();
    sensor[i].configureDefault();
    sensor[i].setAddress(0x30 + i);  //好きなアドレスに設定
    // digitalWrite(pin[i], LOW);
    num[i] = i;
  }
  xTaskCreate(range_sensor, "range_sensor", 2048, NULL, 1, NULL);
}

void loop() {
  // unsigned long interval, startTime, endTime;
  // interval = 0;
  // startTime = millis();
  for (uint8_t i = 0; i < NUM_SENSOR; i++) {
    // if (sensor[i].readRangeStatus() < 6) {
    //   range[i] = sensor[i].readRangeSingle();
    //   Serial.printf("%03d ", range[i]);
    // } else
    //   Serial.print("OoR ");


    if (range[i] != 255)
      Serial.printf("%03d ", range[i]);
    else
      Serial.print("OoR ");
  }
  Serial.println();
  // endTime = millis();
  // if (interval > endTime - startTime)
  //   delay(interval - (endTime - startTime));
}