import serial
import keyboard
import numpy as np
import time
import threading
import tkinter as tk

# シリアル通信の設定
ser = serial.Serial("COM9", 115200)  # COMポートは適切なポート名に置き換える

prev_pos = [0, 0]
next_pos = [0, 0]

variance = 0


def main():
    global prev_pos, next_pos
    while True:
        if ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
            while ser.in_waiting:  # 読み込み可能なデータがある間
                raw_data = (
                    ser.readline().decode("utf-8").strip()
                )  # 1行ずつ読み取り、最後の行を最新のデータとして保持
            range_data = raw_data.split()
            # データを整数に変換、失敗した場合はそのまま保持
            range_data = [int(r) if r.isdigit() else r for r in range_data]
            data = np.var([int(r) for r in range_data if isinstance(r, int)])
            specified_mean=93
            variance_with_specified_mean = np.mean((data - specified_mean) ** 2)
            print(variance)


main()
