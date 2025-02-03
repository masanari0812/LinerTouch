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
            (0, 1): "い",
            (0, 2): "う",
            (0, 3): "え",
            (0, 4): "お",
            (1, 0): "か",
            (1, 1): "き",
            (1, 2): "く",
            (1, 3): "け",
            (1, 4): "こ",
            (2, 0): "さ",
            (2, 1): "し",
            (2, 2): "す",
            (2, 3): "せ",
            (2, 4): "そ",
            (3, 0): "た",
            (3, 1): "ち",
            (3, 2): "つ",
            (3, 3): "て",
            (3, 4): "と",
            (4, 0): "な",
            (4, 1): "に",
            (4, 2): "ぬ",
            (4, 3): "ね",
            (4, 4): "の",
            (5, 0): "は",
            (5, 1): "ひ",
            (5, 2): "ふ",
            (5, 3): "へ",
            (5, 4): "ほ",
            (6, 0): "ま",
            (6, 1): "み",
            (6, 2): "む",
            (6, 3): "め",
            (6, 4): "も",
            (7, 0): "や",
            (7, 1): "ゆ",
            (7, 2): "よ",
            (8, 0): "ら",
            (8, 1): "り",
            (8, 2): "る",
            (8, 3): "れ",
            (8, 4): "ろ",
            (9, 0): "わ",
            (9, 1): "を",
            (9, 2): "ん",
        }
        self.liner = LinerTouch(self.update_keyboard, self.tap_action, False)
        self.liner.pinch_update_callback = self.pinch_action
        self.liner.pinch_start_callback = self.on_canvas_right_click
        self.liner.pinch_motion_callback = self.on_canvas_drag
        self.liner.pinch_end_callback = self.on_canvas_right_release
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
        # self.master.bind("<Motion>", self.on_mouse_move)  # マウス移動イベント

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

    def draw_pointer(self, x=None, y=None):
        """赤い点のポインタを描画する"""
        pointer_size = 10 * self.current_scale
        # キャンバス座標に変換
        if x is None or y is None:
            canvas_x, canvas_y = self.keyboard_to_canvas_coordinates(
                self.pointer_x, self.pointer_y
            )
        else:
            canvas_x, canvas_y = x, y

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

    def on_canvas_right_click(self, event=None):
        """右クリック時の処理"""
        self.is_dragging = True
        if event is None:
            sensor_width = self.liner.sensor_num * self.liner.sensor_num
            sensor_height = self.liner.sensor_height
            pos = self.liner.center_pos
            width = root.winfo_width()
            height = root.winfo_height()
            x = pos[0] / sensor_width * width
            y = pos[1] / sensor_height * height
        else:
            x, y = event.x, event.y
        self.last_x = x
        self.last_y = y

    def on_canvas_drag(self, event=None):
        """キャンバスドラッグ時の処理"""
        if self.is_dragging:
            if event is None:
                sensor_width = self.liner.sensor_num * self.liner.sensor_num
                sensor_height = self.liner.sensor_height
                pos = self.liner.center_pos
                width = root.winfo_width()
                height = root.winfo_height()
                x = pos[0] / sensor_width * width
                y = pos[1] / sensor_height * height
            else:
                x, y = event.x, event.y

            dx = x - self.last_x
            dy = y - self.last_y

            self.offset_x += dx
            self.offset_y += dy

            self.canvas.delete("kana_button")
            self.canvas.delete("kana_text")
            self.create_keyboard()

            self.draw_pointer()

            self.last_x = x
            self.last_y = y

    def on_canvas_right_release(self, event=None):
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

    def update_keyboard(self):
        """ポインタの移動イベント"""
        estimated_data = self.liner.estimated_data
        sensor_width = self.liner.sensor_num * self.liner.sensor_num
        sensor_height = self.liner.sensor_height

        if len(estimated_data) == 1:
            pos = estimated_data[0]
            width = root.winfo_width()
            height = root.winfo_height()
            canvas_x = pos[0] / sensor_width * width
            canvas_y = pos[1] / sensor_height * height

            # キャンバス座標からキーボード座標に変換
            col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)

            # 範囲外の場合は更新しない
            if (col, row) in self.kana_map:
                self.pointer_x = col
                self.pointer_y = row
                self.draw_pointer(canvas_x, canvas_y)
        else:
            return

    def tap_action(self):
        estimated_data = self.liner.estimated_data
        sensor_width = self.liner.sensor_num * self.liner.sensor_num
        sensor_height = self.liner.sensor_height

        if len(estimated_data) == 1:
            pos = estimated_data[0]
            width = root.winfo_width()
            height = root.winfo_height()
            canvas_x = pos[0] / sensor_width * width
            canvas_y = pos[1] / sensor_height * height
        if not self.is_dragging:
            # canvas座標からキーボード座標に変換
            col, row = self.canvas_to_keyboard_coordinates(canvas_x, canvas_y)
            kana = self.kana_map.get((col, row))

            if kana:
                print(f"入力: {kana}")
        pass

    def move_action(self, x_y):
        """ムーブジェスチャイベント"""
        pass

    def pinch_action(self, dist):
        """ピンチジェスチャイベント"""
        # ホイールの方向を判定
        # 何ミリごとに一回分とするか、反復式
        # gap = 10
        if -5 < dist < 5:
            return
        scale_factor = 1.1 ** (dist / -3)
        # if factor > 0:
        #     for i in range(0, factor, gap):
        #         scale_factor * 0.9
        # elif factor < 0:
        #     for i in range(0, factor, -gap):
        #         scale_factor * 1.1
        estimated_data = self.liner.estimated_data
        sensor_width = self.liner.sensor_num * self.liner.sensor_num
        sensor_height = self.liner.sensor_height
        if len(estimated_data) != 2:
            raise IndexError
            return
        # スクロールの中心位置

        width = root.winfo_width()
        height = root.winfo_height()
        center_x = self.liner.center_pos[0] / sensor_width * width
        center_y = self.liner.center_pos[1] / sensor_height * height
        self.draw_pointer(center_x, center_y)
        self.scale_keyboard(scale_factor, center_x, center_y)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    root = tk.Tk()
    keyboard = KanaKeyboard(root)
    root.mainloop()
