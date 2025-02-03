from LinerTouch import LinerTouch
import keyboard
import tkinter as tk
import time
import logging

logger = logging.getLogger(__name__)


class LinerCanvas(tk.Tk):  # tk.Tk を継承
    def __init__(self):
        super().__init__()  # 親クラス (tk.Tk) の初期化を呼び出す
        self.liner = LinerTouch(plot_graph=True)
        while not self.liner.ready:
            time.sleep(0.1)

        self.canvas_width = 1500
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
        self.liner.update_callback = self.render_loop
        # self.liner.tap_callback = self.draw_tap_point

    def render_loop(self):
        self.canvas.delete("all")
        # self.erace_point()
        self.draw_point()
        # self.draw_line()

    def draw_line(self):
        if keyboard.is_pressed("z"):
            logger.debug(
                f"prev_pos: {self.liner.prev_estimated_data}, estimated_pos: {self.liner.estimated_data}"
            )

            prev_pos = self.liner.prev_estimated_data
            estimated_pos = self.liner.estimated_data
            self.canvas.create_line(
                prev_pos[0] * self.x_rate,
                prev_pos[1] * self.y_rate,
                estimated_pos[0] * self.x_rate,
                estimated_pos[1] * self.y_rate,
                fill="blue",
                width=5,
            )

    # 指定された位置 (x, y) に目印の点を描画
    def draw_point(self, size=30):
        for pos in self.liner.estimated_data:
            idx = self.liner.estimated_data.index(pos)
            if idx < 2:
                x = pos[0] * self.x_rate
                y = pos[1] * self.y_rate
                if idx == 0:
                    color = "blue"
                else:
                    color = "red"
                self.canvas.create_oval(
                    x - size, y - size, x + size, y + size, fill=color, outline=color
                )

    # 指定された位置 (x, y) にクリック目印の点を描画
    def draw_tap_point(self, color="green", size=10):
        pos = self.liner.estimated_data[0]
        x = pos[0] * self.x_rate
        y = pos[1] * self.y_rate
        self.canvas.create_oval(
            x - size, y - size, x + size, y + size, fill=color, outline=color
        )


if __name__ == "__main__":

    lc = LinerCanvas()
    lc.mainloop()  # Tkinterのメインループを開始
