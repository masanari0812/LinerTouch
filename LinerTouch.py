import serial
import numpy as np
import time
import logging
import threading
import keyboard
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.ndimage import gaussian_filter1d
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

from collections import deque
from itertools import combinations

logger = logging.getLogger(__name__)

# 過去データの中身
# past_data = [{
#     "estimated_pos": [5, 50],
#     "actual_data": [[i, i * 10] for i in range(10)]
#     },...]


class LinerTouch:

    def __init__(self, update_callback=None, tap_callback=None, plot_graph=True):
        # LinerTouchの変数なくてもどこからでもアクセスできるように
        LinerTouch.liner = self
        # LinerTouch が準備できたかを示す
        self.ready = False
        self.ser = serial.Serial("COM9", 115200)

        self.mean_pos = [0, 0]
        # センサーの数
        self.sensor_num = 9

        # センサの高さに対しての一個あたりのセンサの横幅のサイズの倍率
        # センサの測定可能距離/センサの横幅=sensor_ratio
        self.sensor_ratio = 10
        self.sensor_height = 200
        # 指とこぶしの距離の閾値
        self.height_threshold = 20
        # 指のタッチ時間の閾値
        self.release_threshold = 1
        # 保存するデータの数
        self.past_data_num = 3

        # グラフを描画するかしないか
        self.plot_graph = plot_graph
        # タップフラグ
        self.tap_flag = False
        # 指の幅の収束率
        self.width_convergence_rate = 0.7

        #
        self.filtered_past_data = None
        # 初期値を設定
        # for _ in range(self.past_data_num):
        #     self.past_data.append([(self.sensor_num - 1) / 2, 50])

        self.update_callback = update_callback
        self.tap_callback = tap_callback
        time.sleep(0.1)
        threading.Thread(target=self.get_data).start()

        self.fig = None  # figを初期化
        self.ax = None  # axも初期化
        self.past_data = {
            "estimated_pos": deque(maxlen=self.past_data_num),
            "mean_pos": deque(maxlen=self.past_data_num),
            "actual_data": deque(maxlen=self.past_data_num),
            "oor_flag": deque(maxlen=self.past_data_num),
            "len": 0,
        }

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
                    [idx * self.sensor_ratio, int(value)]
                    for idx, value in enumerate(raw_data_list)
                    if value.isdigit()
                ]

                # データがある場合
                if len(self.range_data) > 0:

                    # デバッグ用出力
                    logger.info(f"Processed range_data: {self.range_data}")
                    if self.ready:
                        self.prev_pos = self.estimated_pos.copy()
                        self.smoothing_filter()
                    self.get_touch()

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

    def culc_mean_pos(self):
        # y_pos から n 以上離れているペアを削除

        # y軸側
        # センサーの数値が最も小さいものを選択
        min_range = min([data[1] for data in self.range_data])
        self.mean_pos[1] = np.mean(
            [
                data[1]
                for data in self.range_data
                if data[1] - min_range < self.height_threshold
            ]
        )
        # x軸側
        # 閾値以上のデータを除いたセンサーのインデックスの平均を選択
        self.mean_pos[0] = np.mean(
            [
                data[0]
                for data in self.range_data
                if data[1] - min_range < self.height_threshold
            ]
        )

        self.mean_pos = self.mean_pos.copy()

    # 追加のタイミングが一フレーム遅い
    # estimated_posを求める
    def smoothing_filter(self):
        self.culc_mean_pos()
        self.estimated_pos = self.mean_pos.copy()
        if self.get_pastdata("len") == self.past_data_num:
            # 指数移動平均の計算
            # alpha = 0.4
            # data = [data[0] for data in self.past_data]
            # ema = np.zeros_like(data, dtype=float)
            # ema[0] = data[0]

            # for i in range(1, len(data)):
            #     ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
            # self.estimated_pos[0] = ema[-1]

            # 移動平均の計算
            # self.estimated_pos = np.mean(self.get_pastdata("mean_pos"), axis=0)

            # ガウシアンフィルタを適用
            # sigma = 0.5  # 標準偏差（スムージングの強さ）
            # mean_data = [data[0] for data in self.get_pastdata("mean_pos")].copy()
            # self.estimated_pos[0] = gaussian_filter1d(mean_data, sigma)[0]

            self.filter_inv_solve()
        self.add_pastdata(self.estimated_pos, self.mean_pos, self.range_data)
        data = self.get_pastdata("estimated_pos")
        # xとyの平均をそれぞれ計算
        self.estimated_pos = np.mean(np.array(data), axis=0)
        self.plot_data()
        logger.info(f"est: {self.estimated_pos}")

    def plot_data(self):
        if self.plot_graph:
            mean_data = [data[0] for data in self.get_pastdata("mean_pos")]
            estimated_data = [data[0] for data in self.get_pastdata("estimated_pos")]
            # 描画の設定

            if self.get_pastdata("len") == self.past_data_num:
                if self.fig is None:
                    plt.ion()  # インタラクティブモードを有効化
                    self.fig, self.ax = plt.subplots()

                    (self.mean_line,) = self.ax.plot(
                        mean_data,
                        range(self.past_data_num),
                        label="mean_data",
                        color="blue",
                    )  # 折れ線グラフを作成
                    (self.estimated_line,) = self.ax.plot(
                        estimated_data,
                        range(self.past_data_num),
                        label="estimated_data",
                        color="orange",
                    )  # 折れ線グラフを作成
                    self.ax.set_xlim(
                        -1 * self.sensor_ratio, self.sensor_num * self.sensor_ratio
                    )  # Y軸の範囲
                else:
                    self.mean_line.set_ydata(range(self.past_data_num))
                    self.mean_line.set_xdata(mean_data)
                    self.estimated_line.set_ydata(range(self.past_data_num))
                    self.estimated_line.set_xdata(estimated_data)
                    self.ax.set_ylim(0, self.past_data_num)
                    # 円の描画の機能未完成　なんかスレッド間でデータがうまくいかない
                    # # 円の削除
                    # for patch in reversed(self.ax.patches):
                    #     patch.remove()
                    # # 円の描画
                    # for range in self.get_pastdata("actual_data"):
                    #     circle = patches.Circle((range[0], range[1]), 10, color="red", fill=False)
                    #     self.ax.add_patch(circle)
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()

    def get_pastdata(self, key: str):
        if self.past_data is None:
            pass
        return self.past_data[key]

    # def get_pastdata(estimated_pos=None, mean_pos=None, actual_data=None):
    #     past_data = {
    #         "estimated_pos": [].append(),
    #         "mean_pos": [],
    #         "actual_data": [],
    #         "oor_flag": [[v == 255 for v in actual_data]],
    #         "len": 0,
    #     }
    #     return

    def add_pastdata(self, estimated_pos=None, mean_pos=None, actual_data=None):
        self.past_data["estimated_pos"].appendleft(estimated_pos)
        self.past_data["mean_pos"].appendleft(mean_pos)
        self.past_data["actual_data"].appendleft([actual_data])
        self.past_data["oor_flag"].appendleft([v == 255 for v in actual_data])
        self.past_data["len"] = len(self.past_data["estimated_pos"])

    # def add_pastdata(self, estimated_pos=None):
    #     pass
    # 測定データ保管用クラス
    # class DataFrame(dict):
    #     def __init__(self):
    #         super().__init__()
    #         self["estimated_pos"]

    #     def __len__():
    #         return

    def display_data(self):
        if self.get_pastdata("len") > 0 and keyboard.is_pressed("p"):
            first_mean_pos = self.get_pastdata("mean_pos")[0]
            first_estimated_pos = self.get_pastdata("estimated_pos")[0]
            logger.info(f"m_pos: {first_mean_pos[0]:3.2f}, {first_mean_pos[1]:3.2f}")
            logger.info(
                f"e_pos: {first_estimated_pos[0]:3.2f}, {first_estimated_pos[1]:3.2f}"
            )

    # 方程式の解求めるヤツ
    def filter_inv_solve(self):
        if len(self.range_data) <= 1:
            logger.error("range_data must have more than one element")
            self.estimated_pos[1] += self.sensor_ratio / 2
            return
        max_sols = []
        # 範囲データから解を求める
        for f_range, p_range in zip(self.range_data, self.range_data[1:]):

            # 変数の定義
            f_a, f_b, p_a, p_b, c, d, r = symbols("f_a f_b p_a p_b c d r")

            # 方程式の定義
            eq_f = Eq((c - f_a) ** 2 + (d - f_b) ** 2, r**2)
            eq_p = Eq((c - p_a) ** 2 + (d - p_b) ** 2, r**2)

            # 代入する値
            subs_values = {
                f_a: f_range[0],
                f_b: f_range[1],
                p_a: p_range[0],
                p_b: p_range[1],
                r: self.sensor_ratio,  # 半径
            }

            # 方程式に値を代入して解を求める
            eq_f = eq_f.subs(subs_values)
            eq_p = eq_p.subs(subs_values)
            solution_eqs = solve([eq_f, eq_p], (c, d), domain=Reals)
            # logger.info(solution_eqs)
            # 解をフィルタリングする
            filtered_solutions = []
            for sol in solution_eqs:
                # 解がタプルまたは辞書として返されるケースに対応
                sol_c = sol[0] if isinstance(sol, tuple) else sol[c]
                sol_d = sol[1] if isinstance(sol, tuple) else sol[d]
                # 実数かどうかを判定
                if sol_c.is_real and sol_d.is_real:
                    filtered_solutions.append((sol_c, sol_d))
            # sol_d が最大の解を選択して表示
            if filtered_solutions:
                max_sols.append(
                    max(filtered_solutions, key=lambda x: x[1])
                )  # sol_d を基準に最大値を選択
        # x（c）と y（d）の値をリストに格納
        c_values = [sol[0].evalf() for sol in max_sols]
        d_values = [sol[1].evalf() for sol in max_sols]

        # x（c）と y（d）の平均を計算
        self.estimated_pos[0] = sum(c_values) / len(c_values) if c_values else 0
        self.estimated_pos[1] = sum(d_values) / len(d_values) if d_values else 0

    def get_touch(self):

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
            latest_pos = self.get_pastdata("estimated_pos")[0]
            if (
                latest_pos[1] - self.prev_pos[1] > self.height_threshold
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
                if self.prev_pos[1] - latest_pos[1] > self.height_threshold:

                    release_end_time = time.time()
                    release_elapsed_time = release_end_time - release_start_time
                    if release_elapsed_time <= self.release_threshold:
                        self.tap_flag = False
                        if self.tap_callback:
                            self.tap_callback()
                else:
                    # タッチ時間の閾値を超えた場合フラグをオフにする処理
                    if time.time() - release_start_time > self.release_threshold:
                        self.tap_flag = False
                    # 指が押されていない間は最後に離した際の座標release_posを利用
            logger.debug(f"tap_flag: {self.tap_flag}")


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    liner_touch.update_callback = liner_touch.display_data
