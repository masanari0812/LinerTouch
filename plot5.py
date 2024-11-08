import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# シリアル通信の設定
ser = serial.Serial("COM5", 115200)  # COMポートは適切なポート名に置き換える

# 最大値の設定
max_value = 200  # グラフで表示する最大値

# リアルタイムの最新データ
latest_data = [0]  # 最新のデータを保持するリスト

# グラフ描画の設定
fig, ax = plt.subplots()
bar = ax.bar([0], latest_data)  # 1本の棒グラフを初期化


# グラフの初期化
def init():
    ax.set_xlim(-0.5, 0.5)  # x軸の範囲（1本の棒のみ）
    ax.set_ylim(0, max_value)  # y軸の範囲
    return bar


# データの更新
def update(frame):
    global latest_data
    # シリアルからデータを読み込み

    if ser.in_waiting > 0:

        ser.reset_input_buffer()  # バッファのクリア
        while True:
            try:
                new_data = ser.readline().decode("utf-8").strip()
                if len(new_data) != 3:
                    continue
                latest_data[0] = int(new_data)
                break
            except ValueError:
                if new_data == "OoR":
                    latest_data[0] = max_value
                    break
        print(latest_data[0])

    # 棒グラフの高さを更新
    bar[0].set_height(latest_data[0])

    return bar


# アニメーションの設定
ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

plt.show()
