import serial
import numpy as np
import time
import logging
import threading
import keyboard
import pandas as pd
from collections import deque


logger = logging.getLogger(__name__)


class LinerTouch:
    def __init__(self, update_callback=None, tap_callback=None):
        # LinerTouch が準備できたかを示す
        self.ready = False
        self.ser = serial.Serial("COM9", 115200)

        self.latest_pos = [0, 0]
        self.estimated_pos = [0, 0]
        # センサーの数
        self.sensor_num = 10

        self.sensor_height = 200
        # 指とこぶしの距離の閾値
        self.height_threshold = 20
        # 指のタッチ時間の閾値
        self.release_threshold = 1
        # 保存するデータの数
        self.past_data_num = 20
        self.past_data = deque(maxlen=self.past_data_num)
        # タップフラグ
        self.tap_flag = False
        # 指の幅の収束率
        self.width_convergence_rate = 0.7

        # 初期値を設定
        # for _ in range(self.past_data_num):
        #     self.past_data.append([(self.sensor_num - 1) / 2, 50])

        self.update_callback = update_callback
        self.tap_callback = tap_callback
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
                    self.latest_pos[1] = min([data[1] for data in self.range_data])
                    self.latest_pos[1] = np.mean(
                        [
                            data[1]
                            for data in self.range_data
                            if data[1] - self.latest_pos[1] < self.height_threshold
                        ]
                    )
                    # x軸側
                    # 閾値以上のデータを除いたセンサーのインデックスの平均を選択
                    self.latest_pos[0] = np.mean(
                        [
                            data[0]
                            for data in self.range_data
                            if data[1] - self.latest_pos[1] < self.height_threshold
                        ]
                    )
                    if self.ready:
                        self.prev_pos = self.past_data[0]
                    self.past_data.appendleft(self.latest_pos.copy())
                    self.estimated_pos = self.latest_pos.copy()
                    # 指数移動平均の計算
                    # if self.ready:
                    #     x_data = [data[0] for data in self.past_data]
                    #     data_series = pd.Series(x_data)
                    #     # 指数移動平均の計算
                    #     # 最新データにどのくらい重みをかけるかを決めるパラメータ
                    #     alpha = 0.9
                    #     weighted_average = data_series.ewm(alpha=alpha).mean()
                    #     self.estimated_pos[0] = weighted_average.iloc[-1]

                    # 移動平均の計算
                    if self.ready:
                        self.estimated_pos = np.mean(self.past_data, axis=0)

                    # 指のタッチ検知
                    if self.ready:
                        # if self.tap_flag:
                        #     self.next_pos = self.release_pos
                        #     # タップ検知の時間閾値を超えた場合
                        #     if (
                        #         time.time() - release_start_time
                        #         > self.release_threshold
                        #     ):
                        #         self.tap_flag = False
                        # 指が離れた場合
                        if (
                            self.latest_pos[1] - self.prev_pos[1]
                            > self.height_threshold
                            and self.tap_flag == False
                        ):
                            release_start_time = time.time()
                            self.tap_flag = True
                            # タッチ予定の座標を記録
                            self.release_pos = self.estimated_pos.copy()

                        # タップのフラグがある場合
                        if self.tap_flag == True:
                            # 指が押されていない場合離した際の座標release_posを利用
                            self.estimated_pos = self.release_pos.copy()

                            # 指が押された場合
                            if (
                                self.prev_pos[1] - self.latest_pos[1]
                                > self.height_threshold
                            ):

                                release_end_time = time.time()
                                release_elapsed_time = (
                                    release_end_time - release_start_time
                                )
                                if release_elapsed_time <= self.release_threshold:
                                    self.tap_flag = False
                                    if self.tap_callback:
                                        self.tap_callback()
                            else:
                                # タッチ時間の閾値を超えた場合フラグをオフにする処理
                                if (
                                    time.time() - release_start_time
                                    > self.release_threshold
                                ):
                                    self.tap_flag = False
                                # 指が押されていない間は最後に離した際の座標release_posを利用
                        logger.debug(f"tap_flag: {self.tap_flag}")

                    # 更新コールバック
                    if self.update_callback:
                        self.update_callback()

                    # LinerTouch が準備できたことを示す
                    self.ready = True
                    # データを保存

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
