import tkinter as tk
from LinerTouch import LinerTouch
import logging

logger = logging.getLogger(__name__)


class KanaKey(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("50音キーボード")

        # 入力用エントリー
        self.entry = tk.Entry(self, width=40, font=("Arial", 20))
        self.entry.grid(row=0, column=0, columnspan=10)
        self.cursor_x = 0
        self.cursor_y = 0
        self.liner = LinerTouch(self.update_cursor, self.tap_cursor)

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
                        self,
                        text=kana,
                        width=4,
                        height=1,
                        font=("Arial", 20),
                        command=lambda k=kana: self.insert_kana(k),
                    )
                    button.grid(row=i + 1, column=j, padx=5, pady=5)

    def update_cursor(self):
        x_rate = self.winfo_width() / self.liner.sensor_num
        y_rate = self.winfo_height() / self.liner.sensor_height
        self.event_generate(
            "<Motion>",
            warp=True,
            x=self.liner.next_pos[0] * x_rate + 25,
            y=self.liner.next_pos[1] * y_rate,
        )

    def tap_cursor(self):
        x_rate = self.winfo_width() / self.liner.sensor_num
        y_rate = self.winfo_height() / self.liner.sensor_height
        self.event_generate(
            "<ButtonPress>",
            warp=True,
            x=self.liner.next_pos[0] * x_rate + 25,
            y=self.liner.next_pos[1] * y_rate,
        )

    def insert_kana(self, kana):
        # エントリーに選択した文字を挿入
        self.entry.insert(tk.END, kana)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
# メインプログラム
app = KanaKey()
app.mainloop()
