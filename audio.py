import numpy as np
import matplotlib.pyplot as plt
import serial

# シリアルポート設定
SERIAL_PORT = "COM4"  # 実際のポート名に変更
BAUD_RATE = 115200
CHUNK_SIZE = 64  # ESP32で送信するサンプル数と一致させる

# シリアル接続
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

# プロット準備
plt.ion()
fig, ax = plt.subplots()
x = np.fft.rfftfreq(CHUNK_SIZE, d=1 / 16000)  # サンプリングレート16kHz
(line,) = ax.plot(x, np.zeros_like(x))
ax.set_ylim(-10000, 10000)  # 適宜調整
ax.set_xlim(0, 8000)  # 人間の可聴域（16kHzの半分）

while True:
    # データ受信
    data = ser.read(CHUNK_SIZE * 2)  # 16bitサンプルの2バイトずつ
    samples = np.frombuffer(data, dtype=np.int16)

    # FFTでスペクトラム計算
    spectrum = np.fft.rfft(samples)

    # プロット更新
    line.set_ydata(spectrum)
    plt.pause(0.01)
