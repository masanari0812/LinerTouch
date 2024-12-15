import pandas as pd
import tkinter as tk
import logging
from LinerTouch import LinerTouch


logger = logging.getLogger(__name__)

class GetTrainData(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GetTrainDataApp")
        df.to_csv('data/dst/to_csv_out_columns.csv', columns=['age', 'point'])
        


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    liner_touch.update_callback = display_data