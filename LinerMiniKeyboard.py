import tkinter as tk
import logging
import math
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)

class KanaKeyboard:
    def __init__(self, master):
        self.master = master
        master.title("50音キーボード")

        # キーボード配置
        self.kana_map = {
            (0, 0): "あ",(0, 1): "い",(0, 2): "う",(0, 3): "え",(0, 4): "お",
            (1, 0): "か",(1, 1): "き",(1, 2): "く",(1, 3): "け",(1, 4): "こ",
            (2, 0): "さ",(2, 1): "し",(2, 2): "す",(2, 3): "せ",(2, 4): "そ",
            (3, 0): "た",(3, 1): "ち",(3, 2): "つ",(3, 3): "て",(3, 4): "と",
            (4, 0): "な",(4, 1): "に",(4, 2): "ぬ",(4, 3): "ね",(4, 4): "の",
            (5, 0): "は",(5, 1): "ひ",(5, 2): "ふ",(5, 3): "へ",(5, 4): "ほ",
            (6, 0): "ま",(6, 1): "み",(6, 2): "む",(6, 3): "め",(6, 4): "も",
            (7, 0): "や",(7, 1): "ゆ",(7, 2): "よ",
            (8, 0): "ら",(8, 1): "り",(8, 2): "る",(8, 3): "れ",(8, 4): "ろ",
            (9, 0): "わ",(9, 1): "を",(9, 2): "ん",
        }
        # (row, col) → (col, row) に変換
        self.kana_map = {(col, row): kana for (row, col), kana in self.kana_map.items()}

        # LinerTouch のインスタンス（1本指＆ダブルタップ検出用）
        # update_callback: センサ座標が更新される度に呼ばれる
        # tap_callback: ダブルタップで呼ばれる
        self.liner = LinerTouch(update_callback=self.update_keyboard,
                                tap_callback=self.tap_action,
                                plot_graph=False)

        # キャンバス設定
        self.canvas_width = 400
        self.canvas_height = 300
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()

        # キー描画用
        self.button_width = 40
        self.button_height = 30
        self.key_margin = 5
        self.current_scale = 1.0

        self.offset_x = 0
        self.offset_y = 0

        self.pointer_x = 0  # キーボード上の列
        self.pointer_y = 0  # キーボード上の行

        self.create_keyboard()      # キーボード描画
        self.draw_pointer()         # ポインタ描画

        # 前フレームの指座標を保持して、移動量を計算する
        self.last_finger_x = None
        self.last_finger_y = None

    def create_keyboard(self):
        """50音キーボードを描画"""
        self.canvas.delete("kana_button")
        self.canvas.delete("kana_text")

        for (col, row), kana in self.kana_map.items():
            x = self.key_margin + col * (self.button_width + self.key_margin)
            y = self.key_margin + row * (self.button_height + self.key_margin)
            scaled_x = x * self.current_scale
            scaled_y = y * self.current_scale
            scaled_width = self.button_width * self.current_scale
            scaled_height = self.button_height * self.current_scale

            self.canvas.create_rectangle(
                scaled_x + self.offset_x,
                scaled_y + self.offset_y,
                scaled_x + scaled_width + self.offset_x,
                scaled_y + scaled_height + self.offset_y,
                fill="lightblue",
                outline="black",
                tags=("kana_button", kana),
            )
            self.canvas.create_text(
                scaled_x + scaled_width / 2 + self.offset_x,
                scaled_y + scaled_height / 2 + self.offset_y,
                text=kana,
                font=("Arial", int(12 * self.current_scale)),
                tags=("kana_text", kana),
            )

    def draw_pointer(self, x=None, y=None):
        """現在の pointer_x, pointer_y を赤丸で表示"""
        self.canvas.delete("pointer")

        if x is None or y is None:
            canvas_x, canvas_y = self.keyboard_to_canvas_coordinates(self.pointer_x, self.pointer_y)
        else:
            canvas_x, canvas_y = x, y

        pointer_size = 10 * self.current_scale
        self.canvas.create_oval(
            canvas_x - pointer_size / 2,
            canvas_y - pointer_size / 2,
            canvas_x + pointer_size / 2,
            canvas_y + pointer_size / 2,
            fill="red",
            tags="pointer",
        )

    def keyboard_to_canvas_coordinates(self, key_x, key_y):
        """
        キーボードの(列, 行) → キャンバス座標
        """
        canvas_x = (
            key_x * (self.button_width + self.key_margin)
            + self.key_margin
            + self.button_width / 2
        ) * self.current_scale + self.offset_x
        canvas_y = (
            key_y * (self.button_height + self.key_margin)
            + self.key_margin
            + self.button_height / 2
        ) * self.current_scale + self.offset_y
        return canvas_x, canvas_y

    def canvas_to_keyboard_coordinates(self, canvas_x, canvas_y):
        """
        キャンバス座標 → キーボード上の(列, 行)
        """
        x = (canvas_x - self.offset_x) / self.current_scale
        y = (canvas_y - self.offset_y) / self.current_scale
        col = int((x - self.key_margin) / (self.button_width + self.key_margin))
        row = int((y - self.key_margin) / (self.button_height + self.key_margin))
        return (col, row)

    def sensor_to_canvas_coordinates(self, pos):
        """
        センサ座標 (x, y) → キャンバス座標 (あくまで一例)
        * デバイスの向きによっては X/Y を入れ替えたりスケーリングを変えたりします。
        """
        # 例: liner.sensor_num * liner.sensor_ratio がセンサの実質的な横幅
        sensor_max_width = self.liner.sensor_num * self.liner.sensor_ratio
        sensor_max_height = self.liner.sensor_height

        # pos = [x, y] として、
        # ここではシンプルに canvas 幅、高さに線形マッピング
        canvas_x = pos[0] / sensor_max_width * self.canvas_width
        canvas_y = pos[1] / sensor_max_height * self.canvas_height
        return canvas_x, canvas_y

    def update_keyboard(self):
        """
        センサから受け取った推定指位置(estimated_data)を用いて、
        1本指の移動量を計算し、キーボードをドラッグ(オフセット変更)。
        ついでにポインタを移動（キー上の行列計算）する。
        """
        estimated_data = self.liner.estimated_data
        if len(estimated_data) == 1:
            finger_x, finger_y = estimated_data[0]
            canvas_x, canvas_y = self.sensor_to_canvas_coordinates([finger_x, finger_y])

            # 前回フレームがあれば移動量を計算してドラッグ
            if self.last_finger_x is not None and self.last_finger_y is not None:
                dx = canvas_x - self.last_finger_x
                dy = canvas_y - self.last_finger_y
                # ここで "スワイプ" としてオフセットを更新
                self.offset_x += dx
                self.offset_y += dy

                # キーボード描画更新
                self.create_keyboard()

            # ポインタ位置をキー座標系に変換
            col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)
            if (col, row) in self.kana_map:
                self.pointer_x = col
                self.pointer_y = row
                self.draw_pointer()
            else:
                # キー範囲外なら、とりあえずポインタだけ再描画
                self.draw_pointer(canvas_x, canvas_y)

            self.last_finger_x = canvas_x
            self.last_finger_y = canvas_y
        else:
            # 指が見つからない場合は移動量計算をリセット
            self.last_finger_x = None
            self.last_finger_y = None

    def tap_action(self):
        """
        LinerTouch でダブルタップ検出されたときに呼び出されるコールバック
        → 現在の pointer_x, pointer_y に対応するキーを入力確定
        """
        # ダブルタップが起きた瞬間の self.pointer_x / self.pointer_y を使う
        kana = self.kana_map.get((self.pointer_x, self.pointer_y), None)
        if kana:
            print(f"【入力確定】{kana}")
        else:
            print("キー範囲外！")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    root = tk.Tk()
    keyboard = KanaKeyboard(root)
    root.mainloop()
import tkinter as tk
import logging
import math
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)

class KanaKeyboard:
    def __init__(self, master):
        self.master = master
        master.title("50音キーボード")

        # キーボード配置
        self.kana_map = {
            (0, 0): "あ",(0, 1): "い",(0, 2): "う",(0, 3): "え",(0, 4): "お",
            (1, 0): "か",(1, 1): "き",(1, 2): "く",(1, 3): "け",(1, 4): "こ",
            (2, 0): "さ",(2, 1): "し",(2, 2): "す",(2, 3): "せ",(2, 4): "そ",
            (3, 0): "た",(3, 1): "ち",(3, 2): "つ",(3, 3): "て",(3, 4): "と",
            (4, 0): "な",(4, 1): "に",(4, 2): "ぬ",(4, 3): "ね",(4, 4): "の",
            (5, 0): "は",(5, 1): "ひ",(5, 2): "ふ",(5, 3): "へ",(5, 4): "ほ",
            (6, 0): "ま",(6, 1): "み",(6, 2): "む",(6, 3): "め",(6, 4): "も",
            (7, 0): "や",(7, 1): "ゆ",(7, 2): "よ",
            (8, 0): "ら",(8, 1): "り",(8, 2): "る",(8, 3): "れ",(8, 4): "ろ",
            (9, 0): "わ",(9, 1): "を",(9, 2): "ん",
        }
        # (row, col) → (col, row) に変換
        self.kana_map = {(col, row): kana for (row, col), kana in self.kana_map.items()}

        # LinerTouch のインスタンス（1本指＆ダブルタップ検出用）
        # update_callback: センサ座標が更新される度に呼ばれる
        # tap_callback: ダブルタップで呼ばれる
        self.liner = LinerTouch(update_callback=self.update_keyboard,
                                tap_callback=self.tap_action,
                                plot_graph=False)

        # キャンバス設定
        self.canvas_width = 400
        self.canvas_height = 300
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()

        # キー描画用
        self.button_width = 40
        self.button_height = 30
        self.key_margin = 5
        self.current_scale = 1.0

        self.offset_x = 0
        self.offset_y = 0

        self.pointer_x = 0  # キーボード上の列
        self.pointer_y = 0  # キーボード上の行

        self.create_keyboard()      # キーボード描画
        self.draw_pointer()         # ポインタ描画

        # 前フレームの指座標を保持して、移動量を計算する
        self.last_finger_x = None
        self.last_finger_y = None

    def create_keyboard(self):
        """50音キーボードを描画"""
        self.canvas.delete("kana_button")
        self.canvas.delete("kana_text")

        for (col, row), kana in self.kana_map.items():
            x = self.key_margin + col * (self.button_width + self.key_margin)
            y = self.key_margin + row * (self.button_height + self.key_margin)
            scaled_x = x * self.current_scale
            scaled_y = y * self.current_scale
            scaled_width = self.button_width * self.current_scale
            scaled_height = self.button_height * self.current_scale

            self.canvas.create_rectangle(
                scaled_x + self.offset_x,
                scaled_y + self.offset_y,
                scaled_x + scaled_width + self.offset_x,
                scaled_y + scaled_height + self.offset_y,
                fill="lightblue",
                outline="black",
                tags=("kana_button", kana),
            )
            self.canvas.create_text(
                scaled_x + scaled_width / 2 + self.offset_x,
                scaled_y + scaled_height / 2 + self.offset_y,
                text=kana,
                font=("Arial", int(12 * self.current_scale)),
                tags=("kana_text", kana),
            )

    def draw_pointer(self, x=None, y=None):
        """現在の pointer_x, pointer_y を赤丸で表示"""
        self.canvas.delete("pointer")

        if x is None or y is None:
            canvas_x, canvas_y = self.keyboard_to_canvas_coordinates(self.pointer_x, self.pointer_y)
        else:
            canvas_x, canvas_y = x, y

        pointer_size = 10 * self.current_scale
        self.canvas.create_oval(
            canvas_x - pointer_size / 2,
            canvas_y - pointer_size / 2,
            canvas_x + pointer_size / 2,
            canvas_y + pointer_size / 2,
            fill="red",
            tags="pointer",
        )

    def keyboard_to_canvas_coordinates(self, key_x, key_y):
        """
        キーボードの(列, 行) → キャンバス座標
        """
        canvas_x = (
            key_x * (self.button_width + self.key_margin)
            + self.key_margin
            + self.button_width / 2
        ) * self.current_scale + self.offset_x
        canvas_y = (
            key_y * (self.button_height + self.key_margin)
            + self.key_margin
            + self.button_height / 2
        ) * self.current_scale + self.offset_y
        return canvas_x, canvas_y

    def canvas_to_keyboard_coordinates(self, canvas_x, canvas_y):
        """
        キャンバス座標 → キーボード上の(列, 行)
        """
        x = (canvas_x - self.offset_x) / self.current_scale
        y = (canvas_y - self.offset_y) / self.current_scale
        col = int((x - self.key_margin) / (self.button_width + self.key_margin))
        row = int((y - self.key_margin) / (self.button_height + self.key_margin))
        return (col, row)

    def sensor_to_canvas_coordinates(self, pos):
        """
        センサ座標 (x, y) → キャンバス座標 (あくまで一例)
        * デバイスの向きによっては X/Y を入れ替えたりスケーリングを変えたりします。
        """
        # 例: liner.sensor_num * liner.sensor_ratio がセンサの実質的な横幅
        sensor_max_width = self.liner.sensor_num * self.liner.sensor_ratio
        sensor_max_height = self.liner.sensor_height

        # pos = [x, y] として、
        # ここではシンプルに canvas 幅、高さに線形マッピング
        canvas_x = pos[0] / sensor_max_width * self.canvas_width
        canvas_y = pos[1] / sensor_max_height * self.canvas_height
        return canvas_x, canvas_y

    def update_keyboard(self):
        """
        センサから受け取った推定指位置(estimated_data)を用いて、
        1本指の移動量を計算し、キーボードをドラッグ(オフセット変更)。
        ついでにポインタを移動（キー上の行列計算）する。
        """
        estimated_data = self.liner.estimated_data
        if len(estimated_data) == 1:
            finger_x, finger_y = estimated_data[0]
            canvas_x, canvas_y = self.sensor_to_canvas_coordinates([finger_x, finger_y])

            # 前回フレームがあれば移動量を計算してドラッグ
            if self.last_finger_x is not None and self.last_finger_y is not None:
                dx = canvas_x - self.last_finger_x
                dy = canvas_y - self.last_finger_y
                # ここで "スワイプ" としてオフセットを更新
                self.offset_x += dx
                self.offset_y += dy

                # キーボード描画更新
                self.create_keyboard()

            # ポインタ位置をキー座標系に変換
            col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)
            if (col, row) in self.kana_map:
                self.pointer_x = col
                self.pointer_y = row
                self.draw_pointer()
            else:
                # キー範囲外なら、とりあえずポインタだけ再描画
                self.draw_pointer(canvas_x, canvas_y)

            self.last_finger_x = canvas_x
            self.last_finger_y = canvas_y
        else:
            # 指が見つからない場合は移動量計算をリセット
            self.last_finger_x = None
            self.last_finger_y = None

    def tap_action(self):
        """
        LinerTouch でダブルタップ検出されたときに呼び出されるコールバック
        → 現在の pointer_x, pointer_y に対応するキーを入力確定
        """
        # ダブルタップが起きた瞬間の self.pointer_x / self.pointer_y を使う
        kana = self.kana_map.get((self.pointer_x, self.pointer_y), None)
        if kana:
            print(f"【入力確定】{kana}")
        else:
            print("キー範囲外！")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    root = tk.Tk()
    keyboard = KanaKeyboard(root)
    root.mainloop()
