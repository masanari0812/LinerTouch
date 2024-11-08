import matplotlib.pyplot as plt
import numpy as np
import time
import serial
import threading

# データをリアルタイムで更新する関数

# 初期データ
data = {}
buffer = []


def update_bar_chart():
    plt.clf()  # 現在のプロットをクリア
    keys = list(data.keys())
    values = list(data.values())
    plt.bar(keys, values)  # 棒グラフをプロット
    plt.ylim(0, 220)  # y軸の範囲を設定
    plt.xticks(range(len(keys)))  # x軸の目盛りを1ずつに設定

    # x軸の目盛りを1ずつに設定
    plt.xticks(range(len(keys)))

    # y軸の目盛りを50ずつに設定
    plt.yticks(range(0, 220, 50))
    plt.pause(0.001)  # プロットを更新するまでの待機時間


# グラフを表示するための設定
def render_bar_chart():
    plt.ion()  # インタラクティブモードをオン
    fig, ax = plt.subplots()

    # データを更新し続けるループ
    try:
        while True:
            update_bar_chart()  # 棒グラフを更新
    except KeyboardInterrupt:
        pass  # キーボード割り込みでループを終了

    plt.ioff()  # インタラクティブモードをオフ
    plt.show()  # 最終的なグラフを表示


def update_data():
    ser = serial.Serial("COM9", 9600)  # 'COM3'を適切なポートに置き換える

    time.sleep(2)  # Arduinoがリセットされる時間を確保

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").rstrip()
            col = line.split()
            for i in range(len(col)):
                if col[i].isdecimal():
                    data[i] = int(col[i])
                else:
                    data[i] = 256

    ser.close()


thread1 = threading.Thread(target=render_bar_chart)
thread2 = threading.Thread(target=update_data)

thread1.start()
thread2.start()

thread1.join()
thread2.join()
