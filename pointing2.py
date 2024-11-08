import pyautogui
import serial
import numpy as np
import time
import tkinter as tk


# シリアル通信の設定
ser = serial.Serial("COM9", 115200)  # COMポートは適切なポート名に置き換える

prev_pos = [0, 0]
next_pos = [0, 0]
pyautogui.FAILSAFE = False

time.sleep(1)
while True:
    start_time = time.time()
    if ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
        while ser.in_waiting:  # 読み込み可能なデータがある間
            raw_data = (
                ser.readline().decode("utf-8").strip()
            )  # 1行ずつ読み取り、最後の行を最新のデータとして保持
        range_data = raw_data.split()

        # データを整数に変換、失敗した場合はそのまま保持
        range_data = [int(r) if r.isdigit() else r for r in range_data]

        # y軸側
        numbers = [int(r) for r in range_data if isinstance(r, int)]
        if numbers:
            # 最小の数字を取得
            y_pos = min(numbers)
            next_pos[1] = y_pos
        else:
            continue  # 数字が存在しない場合はスキップ

        # x軸側
        if len(range_data) > 0:
            x_pos = np.mean([i for i, r in enumerate(range_data) if isinstance(r, int)])
            next_pos[0] = x_pos
        else:
            continue  # range_data が空の場合はスキップ

        move_pos = np.subtract(prev_pos, next_pos)

        # move_pos が NaN でないか確認
        if not np.isnan(move_pos[0]) and not np.isnan(move_pos[1]):
            pyautogui.move(move_pos[0] * -50, move_pos[1] * 5, duration=0.01)
        else:
            print("移動量が無効です。")  # デバッグ用メッセージ

    # 現在の位置を次の位置として更新
    prev_pos = next_pos.copy()
    end_time = time.time()
    print("time: ", end_time - start_time)
