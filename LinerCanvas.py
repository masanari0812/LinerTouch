from LinerTouch import LinerTouch
import keyboard
import tkinter as tk
import time
import threading
import logging

logger = logging.getLogger(__name__)


class LinerCanvas(tk.Tk):  # tk.Tk を継承
    def __init__(self):
        super().__init__()  # 親クラス (tk.Tk) の初期化を呼び出す
        self.liner = LinerTouch(plot_graph=False)
        while not self.liner.ready:
            time.sleep(0.1)

        self.canvas_width = 900
        self.canvas_height = 900
        self.x_rate = self.canvas_width / (
            self.liner.sensor_num * self.liner.sensor_ratio
        )
        self.y_rate = self.canvas_height / self.liner.sensor_height
        self.title("軌跡描画")  # タイトル設定
        self.canvas = tk.Canvas(
            self, width=self.canvas_width, height=self.canvas_height, bg="white"
        )
        self.canvas.pack()
        self.liner.update_callback = self.rend_loop
        self.liner.tap_callback = self.draw_tap_point

    def rend_loop(self):
        if keyboard.is_pressed("shift"):
            self.canvas.delete("all")
        # self.erace_point()
        self.draw_point()
        # self.draw_line()

    def draw_line(self):
        if keyboard.is_pressed("z"):
            logger.debug(
                f"prev_pos: {self.liner.prev_pos}, estimated_pos: {self.liner.estimated_pos}"
            )

            prev_pos = self.liner.prev_pos
            estimated_pos = self.liner.estimated_pos
            self.canvas.create_line(
                prev_pos[0] * self.x_rate,
                prev_pos[1] * self.y_rate,
                estimated_pos[0] * self.x_rate,
                estimated_pos[1] * self.y_rate,
                fill="blue",
                width=5,
            )

    # 指定された位置 (x, y) に目印の点を描画
    def draw_point(self, color="red", size=3):
        estimated_pos = self.liner.estimated_pos
        x = estimated_pos[0] * self.x_rate
        y = estimated_pos[1] * self.y_rate
        self.canvas.create_oval(
            x - size, y - size, x + size, y + size, fill=color, outline=color
        )

    # 指定された位置 (x, y) にクリック目印の点を描画
    def draw_tap_point(self, color="blue", size=10):
        estimated_pos = self.liner.estimated_pos
        x = estimated_pos[0] * self.x_rate
        y = estimated_pos[1] * self.y_rate
        self.canvas.create_oval(
            x - size, y - size, x + size, y + size, fill=color, outline=color
        )

    def erace_point(self, color="white", size=3):
        prev_pos = self.liner.prev_pos
        x = prev_pos[0] * self.x_rate
        y = prev_pos[1] * self.y_rate
        self.canvas.create_oval(
            x - size, y - size, x + size, y + size, fill=color, outline=color
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    lc = LinerCanvas()
    lc.mainloop()  # Tkinterのメインループを開始
