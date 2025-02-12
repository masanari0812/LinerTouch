import tkinter as tk
import logging
import math
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)


class KanaKeyboard:
    def __init__(self, master):
        self.master = master
        master.title("50音キーボード")

        self.kana_map = {
            (0, 0): "あ",
            (1, 0): "い",
            (2, 0): "う",
            (3, 0): "え",
            (4, 0): "お",
            (0, 1): "か",
            (1, 1): "き",
            (2, 1): "く",
            (3, 1): "け",
            (4, 1): "こ",
            (0, 2): "さ",
            (1, 2): "し",
            (2, 2): "す",
            (3, 2): "せ",
            (4, 2): "そ",
            (0, 3): "た",
            (1, 3): "ち",
            (2, 3): "つ",
            (3, 3): "て",
            (4, 3): "と",
            (0, 4): "な",
            (1, 4): "に",
            (2, 4): "ぬ",
            (3, 4): "ね",
            (4, 4): "の",
            (0, 5): "は",
            (1, 5): "ひ",
            (2, 5): "ふ",
            (3, 5): "へ",
            (4, 5): "ほ",
            (0, 6): "ま",
            (1, 6): "み",
            (2, 6): "む",
            (3, 6): "め",
            (4, 6): "も",
            (0, 7): "や",
            (1, 7): "ゆ",
            (2, 7): "よ",
            (0, 8): "ら",
            (1, 8): "り",
            (2, 8): "る",
            (3, 8): "れ",
            (4, 8): "ろ",
            (0, 9): "わ",
            (1, 9): "を",
            (2, 9): "ん",
        }
        # self.liner = LinerTouch(self.update_keyboard, self.tap_key)
        self.current_scale = 1.0
        self.pointer_x = 0  # 外部ポインタのX座標（キーボード座標系）
        self.pointer_y = 0  # 外部ポインタのY座標（キーボード座標系）
        self.canvas_width = 400
        self.canvas_height = 300
        self.button_width = 40
        self.button_height = 30
        self.key_margin = 5
        self.offset_x = 0  # キャンバスのスクロールオフセット X
        self.offset_y = 0  # キャンバスのスクロールオフセット Y
        self.is_dragging = False  # ドラッグ中かどうかを判定するフラグ

        self.canvas = tk.Canvas(
            master, width=self.canvas_width, height=self.canvas_height, bg="white"
        )
        self.canvas.pack()

        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-1>", self.on_canvas_left_click)  # 左クリックイベント
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # 右クリックイベント
        self.canvas.bind(
            "<B3-Motion>", self.on_canvas_drag
        )  # 右クリックドラッグイベント
        self.canvas.bind(
            "<ButtonRelease-3>", self.on_canvas_right_release
        )  # 右クリックリリースイベント
        self.master.bind("<Motion>", self.on_mouse_move)  # マウス移動イベント

        self.create_keyboard()
        self.draw_pointer()

    def create_keyboard(self):
        """50音キーボードを描画する"""
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
                tags=("kana_button", kana),  # タグを追加
            )
            self.canvas.create_text(
                scaled_x + scaled_width / 2 + self.offset_x,
                scaled_y + scaled_height / 2 + self.offset_y,
                text=kana,
                font=("Arial", int(12 * self.current_scale)),
                tags=("kana_text", kana),
            )

    def draw_pointer(self):
        """赤い点のポインタを描画する"""
        pointer_size = 10 * self.current_scale
        # キャンバス座標に変換
        canvas_x, canvas_y = self.keyboard_to_canvas_coordinates(
            self.pointer_x, self.pointer_y
        )

        self.canvas.delete("pointer")  # 既存のポインタを削除
        self.canvas.create_oval(
            canvas_x - pointer_size / 2,
            canvas_y - pointer_size / 2,
            canvas_x + pointer_size / 2,
            canvas_y + pointer_size / 2,
            fill="red",
            tags="pointer",
        )

    def input_kana(self):
        """ポインタ位置の文字を入力する"""
        kana = self.kana_map.get((self.pointer_x, self.pointer_y))
        if kana:
            print(
                f"入力: {kana}"
            )  # 入力された文字をコンソールに出力（必要に応じてテキストボックス等に変更）

    def on_canvas_left_click(self, event):
        """左クリック時の処理"""
        if not self.is_dragging:
            # canvas座標からキーボード座標に変換
            canvas_x = event.x
            canvas_y = event.y
            col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)
            kana = self.kana_map.get((col, row))

            if kana:
                print(f"入力: {kana}")

    def on_canvas_right_click(self, event):
        """右クリック時の処理"""
        self.is_dragging = True
        self.last_x = event.x
        self.last_y = event.y

    def on_canvas_drag(self, event):
        """キャンバスドラッグ時の処理"""
        if self.is_dragging:
            dx = event.x - self.last_x
            dy = event.y - self.last_y

            self.offset_x += dx
            self.offset_y += dy

            self.canvas.delete("kana_button")
            self.canvas.delete("kana_text")
            self.create_keyboard()

            self.draw_pointer()

            self.last_x = event.x
            self.last_y = event.y

    def on_canvas_right_release(self, event):
        """右クリックリリース時の処理"""
        self.is_dragging = False

    def scale_keyboard(self, scale_factor, center_x, center_y):
        """キーボードを拡大縮小する
        scale_factor: 拡大率
        center_x: 拡大の中心 X 座標 (キャンバス座標系)
        center_y: 拡大の中心 Y 座標 (キャンバス座標系)
        """
        # 拡大の中心がキーボードの外側にならないように調整
        min_x = (self.button_width + self.key_margin) * self.current_scale / 2
        max_x = self.canvas_width - min_x
        min_y = (self.button_height + self.key_margin) * self.current_scale / 2
        max_y = self.canvas_height - min_y

        center_x = max(min_x, min(center_x, max_x))
        center_y = max(min_y, min(center_y, max_y))

        self.current_scale *= scale_factor

        # 拡大/縮小の中心を基準にオフセットを調整
        self.offset_x = center_x - (center_x - self.offset_x) * scale_factor
        self.offset_y = center_y - (center_y - self.offset_y) * scale_factor

        self.canvas.delete("kana_button")
        self.canvas.delete("kana_text")
        self.create_keyboard()
        self.draw_pointer()

    def on_mousewheel(self, event):
        """マウスホイールイベント"""
        # ホイールの方向を判定
        if event.delta > 0:
            scale_factor = 1.1  # 拡大
        else:
            scale_factor = 0.9  # 縮小

        # ホイールの中心位置
        center_x = event.x
        center_y = event.y

        self.scale_keyboard(scale_factor, center_x, center_y)

    def keyboard_to_canvas_coordinates(self, key_x, key_y):
        """キーボード座標をキャンバス座標に変換する"""
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
        """キャンバス座標をキーボード座標に変換する"""
        x = (canvas_x - self.offset_x) / self.current_scale
        y = (canvas_y - self.offset_y) / self.current_scale

        col = int((x - self.key_margin) / (self.button_width + self.key_margin))
        row = int((y - self.key_margin) / (self.button_height + self.key_margin))

        return col, row

    def on_mouse_move(self, event):
        """マウスポインタの移動イベント"""
        canvas_x = event.x
        canvas_y = event.y

        # キャンバス座標からキーボード座標に変換
        col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)

        # 範囲外の場合は更新しない
        if (col, row) in self.kana_map:
            self.pointer_x = col
            self.pointer_y = row
            self.draw_pointer()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    root = tk.Tk()
    keyboard = KanaKeyboard(root)
    root.mainloop()
