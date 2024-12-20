#include <BTAddress.h>
#include <BTAdvertisedDevice.h>
#include <BTScan.h>
#include <BluetoothSerial.h>

/* この例では、インターリーブ・モードを使用して、連続レンジ測定と環境光測定を行う方法を示します。
データシートでは "レンジと ALS の連続モードを同時に（つまり非同期に）"実行する代わりに
インターリーブモードを使うことを推奨しています。

より高速な更新レート（10Hz）を達成するために、測距の最大収束時間と環境光測定の積分時間は、
通常推奨されるデフォルト値よりも短縮されています。 詳細については、
VL6180X データシートの「連続モードの制限」のセクションと
「インターリーブ・モードの制限（10 Hz 動作）」の表を参照してください。

生の環境光測定値は、データシートの「ALSカウントからルクスへの変換」セクションの式を使用して
ルクス単位に変換することができます。

例 VL6180Xは、このスケッチで設定されたように、
デフォルトのゲイン1、積分周期50ms（configureDefault()で設定された100msから減少）で
613の周囲光の読み取り値を示します。 
工場出荷時に較正された0.32ルクス/カウントの分解能では、
光量は(0.32 * 613 * 100) / (1 * 50)または392ルクスです。

レンジの読みはmm単位。 */

#include <Wire.h>
#include <VL6180X.h>
#include "BluetoothSerial.h"

#define MAX_NUM_SENSOR 10
#define NUM_SENSOR 9
#define HEAD_SENSOR 0
#define TAIL_SENSOR 8
#define CALIBRATE_TIMES 30
#define TARGET_DISTANCE 50
#define HEAD_I2C_ADDRESS 0x30

// キャリブレーションを行うかの設定
#define CALIBRATE_MODE true

// 範囲外だった場合の出力する値の設定
#define OUT_OF_RANGE_OUTPUT true

BluetoothSerial SerialBT;

uint8_t range[NUM_SENSOR];
uint8_t ambient[NUM_SENSOR];
VL6180X sensor[NUM_SENSOR];
uint8_t pin[MAX_NUM_SENSOR] = { 4, 5, 12, 13, 14, 15, 16, 17, 18, 19 };
uint8_t num[NUM_SENSOR];
uint8_t offset_range[MAX_NUM_SENSOR] = { 13, 16, 19, 15, 251, 4, 26, 11, 14, 6 };

void setup() {
  Serial.begin(115200);
  SerialBT.begin("Esp32-tmk");
  Wire.begin();
  // すでにアクティブな場合は、連続モードを停止する
  for (uint8_t i = 0; i < NUM_SENSOR; i++) {
    pinMode(pin[i], OUTPUT);
    digitalWrite(pin[i], LOW);
    digitalWrite(pin[i], HIGH);
    delay(10);

    sensor[i].init();
    sensor[i].configureDefault();
    sensor[i].setAddress(HEAD_I2C_ADDRESS + i);  //好きなアドレスに設定
    delay(10);
    sensor[i].stopContinuous();
  }


  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {
    // WAFを無効化
    // sensor[i].writeReg(0x2D, 0x00);
    // Range Ignoreを無効化
    // sensor[i].writeReg(0x60, 0x00);
    if (CALIBRATE_MODE) {
      sensor[i].writeReg(VL6180X::SYSRANGE__PART_TO_PART_RANGE_OFFSET, 0x00);
      delay(10);
      uint32_t sum = 0;
      for (uint8_t j = 0; j < CALIBRATE_TIMES; j++)
        sum += sensor[i].readRangeSingle();
      uint8_t ave = sum / CALIBRATE_TIMES;
      uint8_t offset = TARGET_DISTANCE - ave;
      sensor[i].writeReg(VL6180X::SYSRANGE__PART_TO_PART_RANGE_OFFSET, offset);
      // SerialBT.printf("Sensor %2u: offset->%03u ,\n", i, offset);
      // Serial.printf("Sensor %2u: offset->%03u ,\n", i, offset);
      SerialBT.printf("%3u ,", offset);
      Serial.printf("%3u ,", offset);
      delay(10);
    } else {
      sensor[i].writeReg(VL6180X::SYSRANGE__PART_TO_PART_RANGE_OFFSET, offset_range[i]);
      delay(10);
    }

    // レンジの最大収束時間と ALS の積分時間をそれぞれ 30 ms と 50 ms に短縮し、10 Hz
    // 動作を可能にする（データシートの表「インターリーブモードの制限（10 Hz 動作）」で示唆されている通り）。
    sensor[i].writeReg(VL6180X::SYSRANGE__MAX_CONVERGENCE_TIME, 15);
    sensor[i].writeReg16Bit(VL6180X::SYSALS__INTEGRATION_PERIOD, 25);

    sensor[i].setTimeout(500);


    // stopContinuous() がシングルショット測定をトリガした場合は、
    // 測定が完了するまで待つ。
    delay(10);
  }
  SerialBT.println();
  Serial.println();
  delay(1000);

  // 100ミリ秒周期のインターリーブ連続モード開始
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++)
    sensor[i].startInterleavedContinuous(50);
}

void loop() {
  for (uint8_t i = HEAD_SENSOR; i <= TAIL_SENSOR; i++) {

    ambient[i] = sensor[i].readAmbientContinuous();
    range[i] = sensor[i].readRangeContinuousMillimeters();
    if (range[i] == 255 && OUT_OF_RANGE_OUTPUT) {
      SerialBT.print("OoR ");
      Serial.print("OoR ");
    } else {
      SerialBT.printf("%3u ", range[i]);
      Serial.printf("%3u ", range[i]);
    }
    if (sensor[i].timeoutOccurred()) {
      SerialBT.printf("Sensor %2u: TIMEOUT\n", i);
      Serial.printf("Sensor %2u: TIMEOUT\n", i);
      while (true)
        ;
    }
  }
  SerialBT.println();
  Serial.println();
}
