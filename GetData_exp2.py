import os
import logging
import csv
import tkinter as tk
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)


class GetData_exp1(tk.Tk):
    def __init__(self):
        super().__init__()
        self.rec_flag = False
        self.max_finger = 2
        self.count = 0
        self.max_count = 10
        self.title("get_data_exp2")
        self.liner = LinerTouch(update_callback=self.update_csv)

        # ラベル (文字出力用)
        self.label = tk.Label(self, text="出力データ", font=("Arial", 9))
        self.label.grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )  # ラベルは左右に伸縮

        self.count_max_box = tk.Spinbox(
            self, from_=0, to=300, width=10
        )  # 0から150までの数値入力
        self.count_max_box.grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )  # Spinboxは左右に伸縮

        self.abs_box_y = tk.Spinbox(
            self, from_=0, to=self.liner.sensor_height, width=10
        )  # 0から150までの数値入力
        self.abs_box_y.grid(
            row=1, column=2, columnspan=2, sticky="ew"
        )  # Spinboxは左右に

        self.rel_box_x = tk.Spinbox(
            self, from_=0, to=self.liner.sensor_num * self.liner.sensor_ratio, width=10
        )  # 0から150までの数値入力
        self.rel_box_x.grid(
            row=2, column=0, columnspan=2, sticky="ew"
        )  # Spinboxは左右に伸縮

        # # 掛け算ラベル
        # self.label = tk.Label(self, text="x")
        # self.label.grid(
        #     row=2, column=1, columnspan=2, sticky="ew"
        # )  # ラベルは左右に伸縮

        self.rel_box_y = tk.Spinbox(
            self, from_=0, to=self.liner.sensor_height, width=10
        )  # 0から200までの数値入力
        self.rel_box_y.grid(
            row=2, column=2, columnspan=2, sticky="ew"
        )  # Spinboxは左右に伸縮

        # ボタン1
        self.button1 = tk.Button(self, text="記録", command=self.button1_clicked)
        self.button1.grid(row=3, column=0, sticky="ew")  # ボタンは左右に伸縮

        # ボタン2
        self.button2 = tk.Button(self, text="中止", command=self.button2_clicked)
        self.button2.grid(row=3, column=2, sticky="ew")  # ボタンは左右に伸縮

    def update_csv(self):
        if self.rec_flag:
            # Spinbox1の値を取得
            self.label.config(text=f"recording")
            self.max_count = int(self.count_max_box.get())
            if self.count < self.max_count:
                range_data = self.liner.range_data
                estimated_data = self.liner.estimated_data
                self.range_writer.writerow(range_data)
                self.estimated_writer.writerow(estimated_data)
                self.count += 1
            else:
                self.rec_flag = False
                self.range_f.close()
                self.estimated_f.close()
                return

        else:
            self.label.config(text=f"finished!")

    def button1_clicked(self):
        # ボタン1がクリックされた時の処理
        logger.info("ボタン1がクリックされました")

        # Spinbox1の値を取得
        value1 = self.rel_box_x.get()
        # Spinbox2の値を取得
        value2 = self.rel_box_y.get()

        self.new_csv()
        self.count = 0
        self.rec_flag = True

    def button2_clicked(self):
        # ボタン2がクリックされた時の処理
        logger.info("ボタン2がクリックされました")
        # ラベルに文字列を設定

    def new_csv(self):
        # Spinbox0の値を取得
        value0 = self.abs_box_y.get()
        # Spinbox1の値を取得
        value1 = self.rel_box_x.get()
        # Spinbox2の値を取得
        value2 = self.rel_box_y.get()

        # 実行中のスクリプトのパスを取得
        current_file = os.path.abspath(__file__)

        # 親ディレクトリのパスを取得
        parent_dir = os.path.dirname(current_file)
        range_csv_path = os.path.join(
            parent_dir, "data", "exp2_", f"{value0}_range.csv"
        )
        estimated_csv_path = os.path.join(
            parent_dir, "data", "exp2_", f"{value0}_estimated.csv"
        )
        self.range_f = open(range_csv_path, "w", encoding="utf-8", newline="")
        self.estimated_f = open(estimated_csv_path, "w", encoding="utf-8", newline="")
        self.range_writer = csv.writer(self.range_f)
        self.estimated_writer = csv.writer(self.estimated_f)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    app = GetData_exp1()
    app.mainloop()
