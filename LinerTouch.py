import serial
import numpy as np
import time
import logging
import threading
import keyboard
from collections import deque

logger = logging.getLogger(__name__)


class LinerTouch:
    def __init__(self, update_callback=None, click_callback=None):
        # LinerTouch が準備できたかを示す
        self.ready = False
        self.ser = serial.Serial("COM9", 115200)
        self.next_pos = [0, 0]

        # センサーの数
        self.sensor_num = 10
        # キャンバスのサイズ
        self.sensor_width = 10 * self.sensor_num
        self.sensor_height = 200
        # 指とこぶしの距離の閾値
        self.threshold = 30
        # 指のタッチ時間の閾値
        self.release_threshold = 0.3
        # 保存するデータの数
        self.past_data_num = 10
        self.past_data = deque(maxlen=self.past_data_num)
        for _ in range(self.past_data_num):
            self.past_data.append([(self.sensor_num - 1) / 2, 50])

        self.update_callback = update_callback
        self.click_callback = click_callback
        time.sleep(0.1)
        threading.Thread(target=self.get_data).start()

    def get_data(self):
        # gキーが押されるまでループ
        while not keyboard.is_pressed("g"):
            start_time = time.time()
            if self.ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
                while self.ser.in_waiting:  # 読み込み可能なデータがある間
                    raw_data = (
                        self.ser.readline().decode("utf-8").strip()
                    )  # 1行ずつ読み取り、最後の行を最新のデータとして保持

                # スペースで区切ってデータをリストに変換
                raw_data_list = raw_data.split()
                self.sensor_num = len(raw_data_list)
                # データを二次元配列の形式に整える（[インデックス, 数値] の順）
                self.range_data = [
                    [idx, int(value)]
                    for idx, value in enumerate(raw_data_list)
                    if value.isdigit()
                ]

                # データがある場合
                if len(self.range_data) > 0:

                    # デバッグ用出力
                    logger.debug(f"Processed range_data: {self.range_data}")
                    # y_pos から n 以上離れているペアを削除

                    # y軸側
                    # センサーの数値が最も小さいものを選択
                    y_pos = min([data[1] for data in self.range_data])
                    self.next_pos[1] = y_pos

                    # 閾値以上のデータを除く
                    self.range_data = [
                        data
                        for data in self.range_data
                        if data[1] - y_pos < self.threshold
                    ]

                    # x軸側
                    # センサーのインデックスの平均を選択
                    x_pos = np.mean([data[0] for data in self.range_data])

                    self.next_pos[0] = x_pos
                    logger.info(f"x: {self.next_pos[0]:.1f}, y: {self.next_pos[1]:.1f}")

                    # 指のタッチ検知
                    if self.ready:
                        if self.prev_pos[1] - self.next_pos[1] > self.threshold:
                            release_start_time = time.time()
                        if self.next_pos[1] - self.prev_pos[1] > self.threshold:
                            release_end_time = time.time()
                            release_elapsed_time = release_end_time - release_start_time
                            if release_elapsed_time < self.release_threshold:
                                if self.click_callback:
                                    self.click_callback()

                    # LinerTouch が準備できたことを示す
                    self.ready = True
                    self.past_data.append(self.next_pos)

                    if self.update_callback:
                        self.update_callback()
                    self.prev_pos = self.next_pos
                # データがない場合
                else:
                    pass

            end_time = time.time()
            logger.debug(f"Time taken: {end_time - start_time:.6f} seconds")


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
