#include <driver/i2s.h>

#define I2S_SAMPLE_RATE   (16000)
#define I2S_SAMPLE_BITS   (I2S_BITS_PER_SAMPLE_16BIT)
#define I2S_CHANNEL_NUM   (1)
#define I2S_CLK_PIN       (25)
#define I2S_DATA_PIN      (26)

void setup() {
  Serial.begin(115200);
  
  // I2Sの設定
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_PDM),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  // I2Sピンの設定
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_CLK_PIN,
    .ws_io_num = -1,  // ワードセレクトピンは使用しない
    .data_out_num = -1,
    .data_in_num = I2S_DATA_PIN
  };

  // I2Sドライバのインストール
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

void loop() {
  int16_t sample[64];
  size_t bytes_read;
  
  // I2Sからデータ読み取り
  i2s_read(I2S_NUM_0, (void*)sample, sizeof(sample), &bytes_read, portMAX_DELAY);
  
  // シリアルポートを通じてサンプルデータを送信
  for (int i = 0; i < bytes_read / sizeof(int16_t); i++) {
    Serial.write((uint8_t*)&sample[i], sizeof(int16_t));
  }
}