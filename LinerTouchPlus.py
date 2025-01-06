import serial
import numpy as np
import time
import logging
import math
import threading
import keyboard
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import minimize, LinearConstraint, Bounds, fsolve
from sympy import (
    symbols,
    Eq,
    solve,
    Reals,
    RR,
    im,
    evalf,
    solve_univariate_inequality,
    reduce_inequalities,
)
from pulp import LpMinimize, LpProblem, LpVariable
from collections import deque
from itertools import combinations, cycle

logger = logging.getLogger(__name__)


class LinerTouch:

    def __init__(
        self,
        update_callback=None,
        tap_callback=None,
        load_csv=False,
        save_csv=False,
        plot_graph=True,
    ):
        # LinerTouchの変数なくてもどこからでもアクセスできるように
        LinerTouch.liner = self
        # LinerTouch が準備できたかを示す
        self.ready = False
        if load_csv:
            cd = os.path.dirname(os.path.abspath(__file__))
            csv_file_path = os.path.join(cd, "serial_data", "serial_data.csv")
            with open(csv_file_path, "r", newline="", encoding="utf-8") as csvfile:
                self.dummy_ser = cycle(csv.reader(csvfile))

        else:
            self.ser = serial.Serial("COM3", 115200)

        self.mean_pos = [0, 0]
        # センサーの数
        self.sensor_num = 9
        self.finger_radius = 7
        # センサの高さに対しての一個あたりのセンサの横幅のサイズの倍率
        # センサの測定可能距離/センサの横幅=sensor_ratio
        self.sensor_ratio = 10
        self.sensor_height = 200
        # 指とこぶしの距離の閾値
        self.height_threshold = 30
        # 指のタッチ時間の閾値
        self.release_threshold = 0.5
        # 保存するデータの数
        self.past_data_num = 3
        # csvからデータを読み込むか
        # Falseの場合はシリアル通信でのオンライン接続
        self.load_csv = load_csv
        # CSVからデータを読み込むか
        self.save_csv = save_csv

        # グラフを描画するかしないか
        self.plot_graph = plot_graph
        # タップフラグ
        self.tap_flag = False
        # 指の幅の収束率
        self.width_convergence_rate = 0.7

        self.filtered_past_data = None
        # 初期値を設定
        # for _ in range(self.past_data_num):
        #     self.past_data.append([(self.sensor_num - 1) / 2, 50])

        self.update_callback = update_callback
        self.tap_callback = tap_callback
        time.sleep(0.1)
        threading.Thread(target=self.get_data).start()
        threading.Thread(target=self.update_plot).start()

        self.fig = None  # figを初期化
        self.ax = None  # axも初期化
        self.past_data = {
            "estimated_data": deque(maxlen=self.past_data_num),
            "mean_pos": deque(maxlen=self.past_data_num),
            "min_pos": deque(maxlen=self.past_data_num),
            "actual_data": deque(maxlen=self.past_data_num),
            "oor_flag": deque(maxlen=self.past_data_num),
            "len": 0,
        }

    def get_data(self):
        while True:
            start_time = time.time()

            if self.load_csv:
                pass
            else:
                # 読み込めるデータがあるかを確認
                if self.ser.in_waiting > 0:
                    while self.ser.in_waiting:  # 読み込み可能なデータがある間
                        raw_data = (
                            self.ser.readline().decode("utf-8").strip()
                        )  # 1行ずつ読み取り、最後の行を最新のデータとして保持
                # 読み込めるデータがない場合
                else:
                    pass

            # スペースで区切ってデータをリストに変換
            raw_data_list = raw_data.split()
            self.sensor_num = len(raw_data_list)
            self.estimated_data = []
            # データを二次元配列の形式に整える（[インデックス, 数値] の順）
            self.range_data = np.array(
                [
                    [idx * self.sensor_ratio, int(value)]
                    for idx, value in enumerate(raw_data_list)
                    if value.isdigit()
                ]
            )

            # データがある場合
            if len(self.range_data) > 0:
                # センサーの数値が最も小さいものを選択
                self.min_pos = min([data[1] for data in self.range_data])
                # 閾値以上のデータを除いたセンサーのインデックスの平均を選択
                # self.range_data =np.array( [
                #     data
                #     for data in self.range_data
                #     if data[1] - self.min_pos[1] < self.height_threshold
                # ])

                # デバッグ用出力
                logger.info(f"Processed range_data: {self.range_data}")
                # 生データから位置推定と更新処理

                self.smoothing_filter()
                if self.ready:
                    # 更新コールバック
                    if self.update_callback:
                        self.update_callback()
                    # タッチ検出処理
                    self.get_touch()
                    # self.plot_data()
                # LinerTouch が準備できたことを示す
                self.ready = True
                # データを保存
                self.prev_min_pos = self.min_pos.copy()

            end_time = time.time()
            logger.debug(f"Time taken: {end_time - start_time:.6f} seconds")
