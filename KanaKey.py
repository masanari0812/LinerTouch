import tkinter as tk
from LinerTouch import LinerTouch
import logging

logger = logging.getLogger(__name__)


class KanaKey(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("50音キーボード")

        # 入力用エントリー

        self.cursor_x = 0
        self.cursor_y = 0
        self.liner = LinerTouch(plot_graph=False)
        self.liner.update_callback = self.update_cursor
        self.liner.tap_callback = self.tap_cursor

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
        self.entry = tk.Entry(self, width=40, font=("Arial", 20))
        self.entry.grid(row=+5, column=0, columnspan=10)
        # キーボードボタンを作成
        for i, row in enumerate(self.kana_keys):
            for j, kana in enumerate(row):
                if kana:  # 空でない場合にボタンを配置
                    button = tk.Button(
                        self,
                        text=kana,
                        width=5,
                        height=3,
                        font=("Arial", 20),
                        command=lambda k=kana: self.insert_kana(k),
                    )
                    button.grid(row=i, column=j, padx=0, pady=0)

    def update_cursor(self):
        x_rate = self.winfo_width() / (self.liner.sensor_num * self.liner.sensor_ratio)
        y_rate = self.winfo_height() / self.liner.sensor_height
        self.event_generate(
            "<Motion>",
            warp=True,
            x=self.liner.estimated_pos[0] * x_rate + 25,
            y=self.liner.estimated_pos[1] * y_rate,
        )

    def tap_cursor(self):

        button = self.grid_slaves(row=1, column=0)[0]
        button_width = button.winfo_width()
        button_height = button.winfo_height()
        mouse_x, mouse_y = self.winfo_pointerxy()
        mouse_x -= self.winfo_rootx()
        mouse_y -= self.winfo_rooty()
        x_button = int(mouse_x / button_width)
        y_button = int(mouse_y / button_height)
        try:
            kana = self.kana_keys[y_button][x_button]
            if kana:
                self.insert_kana(kana)
        except IndexError:
            logger.error(f"pos: {x_button:2},{y_button:2}")
            logger.error(f"pos: {mouse_x},{mouse_y}")
            logger.error(f"pos: {button_width},{button_height}")
            logger.error(
                f"pos: {self.liner.estimated_pos[0]:3},{self.liner.estimated_pos[1]:3}"
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
