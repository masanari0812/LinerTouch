#include <Arduino.h>
#line 1 "C:\\Users\\masanari\\Desktop\\Files\\Git\\LinerTouch\\LinerTouch\\testino\\testino.ino"
#define CONNECTION_CHECK_INTERVAL 5000 // 接続確認の間隔 (ミリ秒)

unsigned long lastConnectionCheck = 0;

#line 5 "C:\\Users\\masanari\\Desktop\\Files\\Git\\LinerTouch\\LinerTouch\\testino\\testino.ino"
void setup();
#line 10 "C:\\Users\\masanari\\Desktop\\Files\\Git\\LinerTouch\\LinerTouch\\testino\\testino.ino"
void loop();
#line 5 "C:\\Users\\masanari\\Desktop\\Files\\Git\\LinerTouch\\LinerTouch\\testino\\testino.ino"
void setup()
{
    Serial.begin(115200); // シリアル通信の初期化
}

void loop()
{
    // シリアル通信でデータを受信した場合
    if (Serial.available() > 0)
    {
        String receivedString = Serial.readString(); // 受信した文字列を読み込む
        Serial.println(receivedString);              // 受信した文字列をそのまま返す
    }

      // 定期的に接続確認のための文字列を送信
      if (millis() - lastConnectionCheck > CONNECTION_CHECK_INTERVAL) {
        Serial.println("Connection Check"); // 接続確認用の文字列を送信
        lastConnectionCheck = millis();
      }
}
