import serial
import numpy as np
import time
import logging
import math
import threading
import keyboard
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
                self.estimated_data = []
                # データを二次元配列の形式に整える（[インデックス, 数値] の順）
                self.range_data = [
                    [idx * self.sensor_ratio, int(value)]
                    for idx, value in enumerate(raw_data_list)
                    if value.isdigit()
                ]

                # データがある場合
                if len(self.range_data) > 0:
                    # センサーの数値が最も小さいものを選択
                    self.min_pos = min([data for data in self.range_data])
                    # 閾値以上のデータを除いたセンサーのインデックスの平均を選択
                    self.range_data = [
                        data
                        for data in self.range_data
                        if data[1] - self.min_pos[1] < self.height_threshold
                    ]

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

                # データがない場合
                else:
                    pass

            end_time = time.time()
            logger.debug(f"Time taken: {end_time - start_time:.6f} seconds")

    def culc_mean_pos(self):
        # y_pos から n 以上離れているペアを削除
        self.mean_pos = np.mean(self.range_data, axis=0)

    # 追加のタイミングが一フレーム遅い
    # estimated_posを求める
    def smoothing_filter(self):
        if self.ready:
            self.prev_estimated_data = self.estimated_data

        self.culc_mean_pos()
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
            # self.filter_average()

            # ガウシアンフィルタを適用
            # sigma = 0.5  # 標準偏差（スムージングの強さ）
            # mean_data = [data[0] for data in self.get_pastdata("mean_pos")].copy()
            # self.estimated_pos[0] = gaussian_filter1d(mean_data, sigma)[0]
            self.split_x_data()

        self.add_pastdata(self.mean_pos, self.mean_pos, self.min_pos, self.range_data)
        # self.add_pastdata(
        #     self.estimated_data, self.mean_pos, self.min_pos, self.range_data
        # )

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

    def add_pastdata(
        self,
        estimated_data: list[list[int]] = None,
        mean_pos: list[int] = None,
        min_pos: list[int] = None,
        actual_data: list[list[int]] = None,
    ) -> None:
        self.past_data["estimated_data"].appendleft(estimated_data)
        self.past_data["mean_pos"].appendleft(mean_pos)
        self.past_data["min_pos"].appendleft(min_pos)
        self.past_data["actual_data"].appendleft([actual_data])
        self.past_data["oor_flag"].appendleft([v == 255 for v in actual_data])
        self.past_data["len"] = len(self.past_data["estimated_data"])

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

    # 指の本数を推測し最も誤差が少ない推定位置を利用
    def split_finger_data(self, range_data):
        # 指の極大値を格納
        if len(range_data) < 2:
            return
        max_idx = []
        range_x = range_data[:, 0]  # 1列目
        range_r = range_data[:, 1]  # 2列目
        for i in range(1, range_data - 1):
            if range_r[i - 1] < range_r[i] > range_r[i + 1]:
                max_idx.append(i)
        # max_idxの要素数+1が指の本数になる
        # 極大値のセンサ値の左右に振り分け目的関数の誤差の合計が低い組み合わせを利用
        # 2^(極大値の数)回数試行しそのインデックスを2進数に変換し
        # 極大値と同じインデックスの桁数目の数によって左右どちらに振り分けるか決める
        # 極大値が4本でインデックスが0b0110の場合、左右右左となる。
        if len(max_idx) > 0:
            result = []
            for b in range(2 ** len(max_idx)):
                bits = bin(b)[2:]
                prev_idx = 0
                data = []
                for i in max_idx:
                    # 左に
                    if bits[i] == 0:
                        data.append(range_data[prev_idx:i])
                        prev_idx = i + 1
                    # 右に
                    elif bits[i] == 1:
                        data.append(range_data[prev_idx : i - 1])
                        prev_idx = i
                    else:
                        logger.error("0と1以外の数字が来た")
                data.append(range_data[prev_idx:])
                result.append(data)
        else:
            self.filter_inv_solve(range_data)

    # 逆問題による推測
    def filter_inv_solve(self, range_data, left=False, right=False):
        # 観測値が1個の場合、観測値から指の半径から推測
        if len(self.range_data) < 2:
            logger.error("range_data must have more than one element")
            self.estimated_data.append(self.range_data[0].copy())
            return
        # 観測値が2個以上の場合、推測点とセンサーまでの距離と
        # センサー観測値と指の半径の合計の距離の誤差が最小になるような推測点
        else:
            range_x = range_data[:, 0]  # 1列目
            range_r = range_data[:, 1]  # 2列目
            r = self.finger_radius  # rの値
            e = 3  # riの誤差

            # 誤差関数
            def error(params):
                x, y = params
                residuals = []
                for i in range(len(range_x)):
                    for r_err in [-e, e]:  # 誤差を考慮
                        ri_err = range_r[i] + r_err
                        residual = np.sqrt(
                            (x - range_x[i]) ** 2 + y**2 - (r + ri_err) ** 2
                        )
                        residuals.append(residual)
                return np.sum(np.array(residuals) ** 2)

            # 制約関数
            # 検知できなかったセンサ範囲を除く制約関数
            # 左からの制約
            def left_constraint(params):
                x, y = params
                return (
                    (y * (np.tan(-12.5 * np.pi / 180)))
                    + min(range_x)
                    - self.sensor_ratio
                    - x
                )

            # 右からの制約
            def right_constraint(params):
                x, y = params
                return (
                    (y * (-np.tan(12.5 * np.pi / 180)))
                    - max(range_x)
                    + self.sensor_ratio
                    + x
                )

            constraints = []
            if left:
                constraints.append({"type": "ineq", "fun": left_constraint})
            if right:
                constraints.append({"type": "ineq", "fun": right_constraint})

            # 入力領域外を除く制約関数
            bounds = Bounds([0, 0], [100, 200])

            # 初期値 (観測点の中心を使用)
            initial_guess = [np.mean(range_x), np.mean(range_r)]

            # 最適化
            result = minimize(
                error,
                initial_guess,
                bounds=bounds,
                constraints=constraints,
                method="SLSQP",
            )
            if not result.success:
                logger.error("解求められんかった")
            return result

    # センサのデータを未検知のセンサごとに分割

    def split_x_data(self):
        range_np = np.array(self.range_data)
        result = []
        temp_list = []  # 初期化を空リストに変更
        prev_x = range_np[0][0]
        for i in range(len(range_np)):
            x, y = range_np[i]
            if i > 0 and x - prev_x > self.sensor_ratio:
                result.append(temp_list)
                temp_list = []  # 新しいリストを作成
            temp_list.append([x, y])  # temp_list に要素を追加
            prev_x = x

        if temp_list:  # 最後の temp_list を result に追加

            result.append(temp_list)

        for data in result:

            self.calculate_intersections(data)  # result ではなく data を渡す

    def update_plot(self):
        while not keyboard.is_pressed("g"):
            if self.ready:
                self.plot_data()
            time.sleep(0.05)

    def plot_data(self):
        if self.plot_graph:
            if self.fig is None:
                """
                matplotlibのグラフを初期化する関数。
                """
                self.fig, self.ax = plt.subplots()
                self.ax.set_aspect("equal")
                self.ax.set_xlim(
                    -self.sensor_ratio, self.sensor_num * self.sensor_ratio
                )
                self.ax.set_ylim(0, self.sensor_height)
                self.ax.set_xlabel("X")
                self.ax.set_ylabel("Y")
                self.ax.set_title("Sensor Data, Estimated Position, and Arcs")
                plt.ion()  # 対話モードをオン
                plt.show()
            else:
                """
                センサーデータ、推定位置、および円弧をプロットする関数。
                """
                self.ax.clear()

                # センサーデータのプロット
                x_vals = [data[0] for data in self.range_data]
                y_vals = [data[1] for data in self.range_data]
                self.ax.scatter(x_vals, y_vals, color="blue", label="Sensor Data")

                # 円弧と交点のプロット
                angle_range = [(90 - 12.5) / 180 * np.pi, (90 + 12.5) / 180 * np.pi]
                for i in range(len(self.range_data) - 1):
                    x0, r0 = self.range_data[i]
                    x1, r1 = self.range_data[i + 1]
                    r0, r1 = r0 + self.finger_radius, r1 + self.finger_radius
                    # 円弧の描画
                    arc0 = patches.Arc(
                        (x0, 0),
                        2 * r0,
                        2 * r0,
                        theta1=np.degrees(angle_range[0]),
                        theta2=np.degrees(angle_range[1]),
                        edgecolor="green",
                        linestyle="--",
                    )
                    self.ax.add_patch(arc0)
                    arc1 = patches.Arc(
                        (x1, 0),
                        2 * r1,
                        2 * r1,
                        theta1=np.degrees(angle_range[0]),
                        theta2=np.degrees(angle_range[1]),
                        edgecolor="green",
                        linestyle="--",
                    )
                    self.ax.add_patch(arc1)
                logger.info(self.estimated_data)

                # 推定位置(交点)のプロット
                for estimated_pos in self.estimated_data:
                    self.ax.scatter(
                        estimated_pos[0],
                        estimated_pos[1],
                        color="red",
                        label=(
                            "Estimated Position (Intersection)"
                            if "Estimated Position (Intersection)"
                            not in [l.get_label() for l in self.ax.get_lines()]
                            else ""
                        ),
                    )

                # グラフの設定
                self.ax.set_aspect("equal")
                self.ax.set_xlim(
                    -self.sensor_ratio, self.sensor_num * self.sensor_ratio
                )
                self.ax.set_ylim(0, self.sensor_height)
                self.ax.set_xlabel("X")
                self.ax.set_ylabel("Y")
                self.ax.set_title("Sensor Data, Estimated Position, and Arcs")
                self.ax.legend()

                # 描画を更新
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()

    # def plot_data(self):
    #     if not self.plot_graph:
    #         if self.fig is None:
    #             """
    #             matplotlibのグラフを初期化する関数。
    #             """
    #             self.fig, self.ax = plt.subplots()
    #             self.ax.set_aspect("equal")
    #             self.ax.set_xlim(0, (self.sensor_num - 1) * self.sensor_ratio)
    #             self.ax.set_ylim(0, self.sensor_height)
    #             self.ax.set_xlabel("X")
    #             self.ax.set_ylabel("Y")
    #             self.ax.set_title("Sensor Data and Estimated Position")
    #             plt.ion()  # 対話モードをオン
    #             plt.show()
    #         else:
    #             """
    #             センサーデータと推定位置をプロットする関数。
    #             """

    #             self.ax.clear()

    #             # センサーデータのプロット
    #             x_vals = [data[0] for data in self.range_data]
    #             y_vals = [data[1] for data in self.range_data]
    #             self.ax.scatter(x_vals, y_vals, color="blue", label="Sensor Data")

    #             # 推定位置のプロット
    #             for estimated_pos in self.estimated_data:
    #                 self.ax.scatter(
    #                     estimated_pos[0],
    #                     estimated_pos[1],
    #                     color="red",
    #                     label="Estimated Position",
    #                 )

    #                 # 円弧の描画
    #                 arc = patches.Arc(
    #                     (estimated_pos[0], 0),
    #                     2 * self.sensor_ratio,
    #                     2 * self.sensor_ratio,
    #                     theta1=90 - 12.5,
    #                     theta2=90 + 12.5,
    #                     edgecolor="red",
    #                     linestyle="--",
    #                 )
    #                 self.ax.add_patch(arc)

    #             # グラフの設定
    #             self.ax.set_aspect("equal")
    #             self.ax.set_xlim(0, (self.sensor_num - 1) * self.sensor_ratio)
    #             self.ax.set_ylim(0, self.sensor_height)
    #             self.ax.set_xlabel("X")
    #             self.ax.set_ylabel("Y")
    #             self.ax.set_title("Sensor Data and Estimated Position")
    #             self.ax.legend()

    #             # 描画を更新
    #             self.fig.canvas.draw()
    #             self.fig.canvas.flush_events()

    def calculate_intersections(self, circles):
        """
        複数の円の交点を計算し、y座標が最大の点を返す関数。

        Args:
            circles: 円の情報を含むリスト。各円は [x, r] の形式で、x は中心の x 座標、r は半径。

        Returns:
            交点のリスト。各交点は [x, y] の形式。
        """

        if len(circles) < 2:
            logger.error("少なくとも2つの円が必要です。")
            return

        angle_range = [(90 - 12.5) / 180 * np.pi, (90 + 12.5) / 180 * np.pi]

        for i in range(len(circles) - 1):
            x0, r0 = circles[i]
            x1, r1 = circles[i + 1]
            r0, r1 = r0 + self.sensor_ratio, r1 + self.sensor_ratio
            # シンボルの定義
            x, y = symbols("x y")

            # 方程式の定義 (yを角度から求めるように変更)
            eq0 = Eq((x - x0) ** 2 + (y - 0) ** 2, r0**2)
            eq1 = Eq((x - x1) ** 2 + (y - 0) ** 2, r1**2)

            # 方程式を解く
            solution_eqs = solve([eq0, eq1], (x, y), domain=Reals, real=True)

            # 実数解を抽出し、y座標が最大のものを選択
            real_sols = []
            for sol in solution_eqs:
                if not sol[0].is_real or not sol[1].is_real:  # 虚数解は除外
                    continue
                sol_x = float(sol[0])
                sol_y = float(sol[1])

                # # 角度の範囲をチェック
                # angle = math.atan2(sol_y, sol_x - x0)
                # if angle_range[0] <= angle <= angle_range[1]:
                if sol_y >= 0:
                    real_sols.append([sol_x, sol_y])
            if real_sols:
                estimated_pos = max(real_sols, key=lambda sol: sol[1])
                self.estimated_data.append(estimated_pos)

    # 指のタッチ検知
    def get_touch(self):
        if self.get_pastdata("len") == self.past_data_num and False:

            prev_pos = self.get_pastdata("estimated_pos")[0]
            next_pos = self.get_pastdata("estimated_pos")[2]

            # タッチフラグがある場合
            if self.tap_flag:
                self.estimated_data = self.release_pos.copy()
                # 指が押されていない場合離した際の座標release_posを利用
                self.release_end_time = time.time()
                release_elapsed_time = self.release_end_time - self.release_start_time
                if release_elapsed_time < self.release_threshold:
                    if prev_pos[1] - next_pos[1] > self.height_threshold:
                        self.tap_flag = False
                        logger.info("tap2_act")
                        if self.tap_callback:
                            self.tap_callback()
                else:
                    self.tap_flag = False
                self.estimated_data = self.release_pos.copy()
            # タッチフラグがない場合
            else:
                if next_pos[1] - prev_pos[1] > self.height_threshold:
                    self.release_start_time = time.time()
                    self.tap_flag = True
                    # タッチ予定の座標を記録
                    self.release_pos = self.prev_estimated_data.copy()
            logger.info(f"tap_flag: {self.tap_flag}")

    # 指のタッチ検知
    # def get_touch(self):
    #     # タッチフラグがある場合
    #     if self.tap_flag:
    #         # 指が押されていない場合離した際の座標release_posを利用
    #         self.release_end_time = time.time()
    #         release_elapsed_time = self.release_end_time - self.release_start_time
    #         if release_elapsed_time < self.release_threshold:
    #             if self.estimated_pos[1] - self.min_pos[1] > self.height_threshold:
    #                 self.tap_flag = False
    #                 logger.info("tap2_act")
    #                 if self.tap_callback:
    #                     self.tap_callback()
    #         else:
    #             self.tap_flag = False
    #         self.estimated_pos = self.release_pos.copy()

    #     # タッチフラグがない場合
    #     else:
    #         if self.min_pos[1] - self.prev_min_pos[1] > self.height_threshold:
    #             self.release_start_time = time.time()
    #             self.tap_flag = True
    #             # タッチ予定の座標を記録
    #             self.release_pos = self.prev_estimated_pos.copy()
    #     logger.info(f"tap_flag: {self.tap_flag}")

    # def get_touch(self):
    #     # 指のタッチ検知
    #     if self.ready:
    #         # if self.tap_flag:
    #         #     self.next_pos = self.release_pos
    #         #     # タップ検知の時間閾値を超えた場合
    #         #     if (
    #         #         time.time() - release_start_time
    #         #         > self.release_threshold
    #         #     ):
    #         #         self.tap_flag = False
    #         # 指が離れた場合
    #         latest_pos = self.get_pastdata("estimated_pos")[0]
    #         if (
    #             self.min_pos[1] - self.prev_min_pos[1] > self.height_threshold
    #             and self.tap_flag == False
    #         ):
    #             self.release_start_time = time.time()
    #             self.tap_flag = True
    #             # タッチ予定の座標を記録
    #             self.release_pos = self.estimated_pos.copy()

    #         # タップのフラグがある場合
    #         if self.tap_flag == True:
    #             # 指が押されていない場合離した際の座標release_posを利用
    #             self.estimated_pos = self.release_pos.copy()

    #             # 指が押された場合
    #             if self.prev_min_pos[1] - self.min_pos[1] > self.height_threshold:

    #                 self.release_end_time = time.time()
    #                 release_elapsed_time = (
    #                     self.release_end_time - self.release_start_time
    #                 )
    #                 if release_elapsed_time <= self.release_threshold:
    #                     self.tap_flag = False
    #                     if self.tap_callback:
    #                         self.tap_callback()
    #             else:
    #                 # タッチ時間の閾値を超えた場合フラグをオフにする処理
    #                 if time.time() - self.release_start_time > self.release_threshold:
    #                     self.tap_flag = False
    #                 # 指が押されていない間は最後に離した際の座標release_posを利用
    #         logger.debug(f"tap_flag: {self.tap_flag}")


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    liner_touch.update_callback = liner_touch.display_data
