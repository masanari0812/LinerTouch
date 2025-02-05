import tkinter as tk
import serial

# シリアルポートの設定
port = "COM9"  # 実際のシリアルポートに合わせてください
baudrate = 115200  # ボーレートも合わせてください

# Tkinterウィンドウの作成
root = tk.Tk()
root.title("Serial Data Display")
root.geometry("1800x600")

# Labelの作成と配置
label = tk.Label(root, font=("Helvetica", 280))  # フォントサイズを大きく設定
label.pack(padx=20, pady=20)

# シリアル通信の開始
ser = serial.Serial(port, baudrate)


def update_label():
    if ser.in_waiting > 0:
        line = ser.readline().decode("utf-8").rstrip()  # 改行文字を取り除く
        label.config(text=line)  # 最新の文字列をLabelに表示

    root.after(10, update_label)  # 100ミリ秒後に再度更新


# 定期更新の開始
update_label()

root.mainloop()
