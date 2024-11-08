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
canvas_width = 900
canvas_height = 900
sensor_num = 10
x_offset = 0
x_rate = canvas_width / sensor_num
y_offset = 0
y_rate = canvas_height / 200
# y_rate = x_rate * 2
root = tk.Tk()


class KanaKeyboard:
    def __init__(self, root):
        self.root = root
        self.root.title("50音キーボード")

        # 入力用エントリー
        self.entry = tk.Entry(root, width=10, font=("Arial", 20))
        self.entry.grid(row=0, column=0, columnspan=10)
        self.cursor_x = 0
        self.cursor_y = 0
        # 50音キーボード配列
        self.kana_keys = [
            ["あ", "い", "う", "え", "お"],
            ["か", "き", "く", "け", "こ"],
            ["さ", "し", "す", "せ", "そ"],
            ["た", "ち", "つ", "て", "と"],
            ["な", "に", "ぬ", "ね", "の"],
            ["は", "ひ", "ふ", "へ", "ほ"],
            ["ま", "み", "む", "め", "も"],
            ["や", "　", "ゆ", "　", "よ"],
            ["ら", "り", "る", "れ", "ろ"],
            ["わ", "　", "を", "　", "ん"],
        ]
        self.kana_keys = [list(row) for row in zip(*self.kana_keys)]
        # キーボードボタンを作成
        for i, row in enumerate(self.kana_keys):
            for j, kana in enumerate(row):
                if kana:  # 空でない場合にボタンを配置
                    button = tk.Button(
                        root,
                        text=kana,
                        width=4,
                        height=1,
                        font=("Arial", 20),
                        command=lambda k=kana: self.insert_kana(k),
                    )
                    button.grid(row=i + 1, column=j, padx=5, pady=5)

    def insert_kana(self, kana):
        # エントリーに選択した文字を挿入
        self.entry.insert(tk.END, kana)


def main():
    global prev_pos, next_pos
    while True:

        start_time = time.time()
        if ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
            while ser.in_waiting:  # 読み込み可能なデータがある間
                raw_data = (
                    ser.readline().decode("utf-8").strip()
                )  # 1行ずつ読み取り、最後の行を最新のデータとして保持
            range_data = raw_data.split()
            # データを整数に変換、失敗した場合はそのまま保持
            sensor_num = len(range_data)
            range_data = [int(r) if r.isdigit() else r for r in range_data]
            # y軸側
            numbers = [int(r) for r in range_data if isinstance(r, int)]
            if numbers:
                # 最小の数字を取得
                y_pos = np.mean(np.array(numbers))
                next_pos[1] = y_pos
            else:
                continue  # 数字が存在しない場合はスキップ

            # x軸側
            if len(range_data) > 0:
                x_pos = min([i for i, r in enumerate(range_data) if isinstance(r, int)])
                next_pos[0] = x_pos
            else:
                continue  # range_data が空の場合はスキップ

            move_pos = np.subtract(prev_pos, next_pos)
            # move_pos が NaN でないか確認
            canvas_width = root.winfo_width()
            canvas_height = root.winfo_height()
            x_rate = canvas_width / sensor_num
            y_rate = canvas_height / 200
            if not np.isnan(move_pos[0]) and not np.isnan(move_pos[1]):
                # root.after(
                #     0,
                #     lambda: root.winfo_toplevel().geometry(
                #         f"+{int(x_pos * x_rate)}+{int(y_pos * y_rate*-1+canvas_height)}"
                #     ),
                # )
                root.event_generate(
                    "<Motion>",
                    warp=True,
                    x=x_pos * x_rate + 25,
                    y=y_pos * y_rate,
                )
            else:
                print("移動量が無効です。")  # デバッグ用メッセージ
        # 現在の位置を次の位置として更新

        prev_pos = next_pos.copy()
        end_time = time.time()
        # if (end_time - start_time) > 0.05:
        #     print("time: ", end_time - start_time)


# main関数を別スレッドで実行する
threading.Thread(target=main, daemon=True).start()
# threading.Thread(target=space_click, daemon=True).start()

# GUIのメインループを開始
app = KanaKeyboard(root)
root.mainloop()
ser.close()
