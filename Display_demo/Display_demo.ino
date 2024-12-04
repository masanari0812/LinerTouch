#include "driver/i2s.h"

// I2S設定
#define I2S_NUM I2S_NUM_0
#define I2S_BCK_IO 25      // PDM CLK
#define I2S_WS_IO -1       // 未使用
#define I2S_DATA_IN_IO 26  // PDM DAT
#define SAMPLE_RATE 16000  // サンプリング周波数

void setup() {
  Serial.begin(115200);

  // I2Sの設定
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  // ピン設定
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCK_IO,
    .ws_io_num = I2S_WS_IO,
    .data_out_num = -1,  // 出力は未使用
    .data_in_num = I2S_DATA_IN_IO
  };

  // I2S初期化
  i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM, &pin_config);
}

void loop() {
  const int buffer_size = 1024;
  int16_t buffer[buffer_size];
  size_t bytes_read;

  // PCMデータ読み取り
  i2s_read(I2S_NUM, buffer, buffer_size * sizeof(int16_t), &bytes_read, portMAX_DELAY);

  // シリアル通信で送信
  Serial.write((uint8_t*)buffer, bytes_read);
}
