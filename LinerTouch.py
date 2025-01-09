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
from collections import deque, defaultdict
from itertools import combinations

logger = logging.getLogger(__name__)


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
        self.finger_radius = 8
        # センサの高さに対しての一個あたりのセンサの横幅のサイズの倍率
        # センサの測定可能距離/センサの横幅=sensor_ratio
        self.sensor_ratio = 10
        self.sensor_height = 200
        # 指とこぶしの距離の閾値
        self.height_threshold = 30
        # 指のタッチ時間の閾値
        self.release_threshold = 0.5
        # 保存するデータの数
        self.past_data_num = 10

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
            "actual_data": deque(maxlen=self.past_data_num),
            "len": 0,
        }

    def get_data(self):
        # gキーが押されるまでループ
        while not keyboard.is_pressed("g"):
            if self.ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
                start_time = time.time()
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

                    end_time = time.time()
                    logger.debug(f"Time taken: {end_time - start_time:.6f} seconds")
                # データがない場合
                else:
                    pass

    # 追加のタイミングが一フレーム遅い
    # estimated_posを求める
    def smoothing_filter(self):
        if self.ready:
            self.prev_estimated_data = self.estimated_data
        self.add_pastdata(actual_data=self.range_data)

        # if self.get_pastdata("len") == self.past_data_num:
        #     smooth_range_dic = {}
        #     for i in range(self.sensor_num):
        #         smooth_range_dic[f"sum{i*self.sensor_ratio}"] = 0
        #         smooth_range_dic[f"num{i*self.sensor_ratio}"] = 0
        #     for data1 in self.get_pastdata("actual_data"):
        #         for data2 in data1:
        #             smooth_range_dic[f"sum{data2[0]}"] += data2[1]
        #             smooth_range_dic[f"num{data2[0]}"] += 1
        #     smooth_range_ave_dic = {}
        #     for i in range(self.sensor_num):
        #         if smooth_range_dic[f"num{i * self.sensor_ratio}"] > 0:
        #             smooth_range_ave_dic[i * self.sensor_ratio] = (
        #                 smooth_range_dic[f"sum{i * self.sensor_ratio}"]
        #                 / smooth_range_dic[f"num{i * self.sensor_ratio}"]
        #             )
        #     smooth_range_data = []
        #     for idx, value in self.range_data:
        #         smooth_range_data.append([idx, int(smooth_range_ave_dic[idx])])
        #     # 平均値を計算
        #     self.split_x_data(smooth_range_data)

        # else:
        #     self.split_x_data(self.range_data)
        self.split_x_data(self.range_data)

        self.add_pastdata(estimated_data=self.estimated_data)

    def get_pastdata(self, key: str):
        if self.past_data is None:
            pass
        return self.past_data[key]

    def add_pastdata(
        self,
        estimated_data: list[list[int]] = None,
        actual_data: list[list[int]] = None,
    ) -> None:
        if estimated_data:
            self.past_data["estimated_data"].appendleft(estimated_data)
        if actual_data:
            self.past_data["actual_data"].appendleft(actual_data)
        self.past_data["len"] = len(self.past_data["estimated_data"])

    # 指の本数を推測し最も誤差が少ない推定位置を利用
    def split_finger_data(self, range_data):
        # 指の極大値を格納
        range_data_np = np.array(range_data)
        if len(range_data) < 2:
            return
        max_idx = []
        range_x = range_data_np[:, 0]  # 1列目
        range_r = range_data_np[:, 1]  # 2列目
        for i in range(1, len(range_data) - 1):
            if range_r[i - 1] < range_r[i] > range_r[i + 1]:
                max_idx.append(i)
        # max_idxの要素数+1が指の本数になる
        # 極大値のセンサ値の左右に振り分け目的関数の誤差の合計が低い組み合わせを利用
        # 2^(極大値の数)回数試行しそのインデックスを2進数に変換し
        # 極大値と同じインデックスの桁数目の数によって左右どちらに振り分けるか決める
        # 極大値が4本でインデックスが0b0110の場合、左右右左となる。
        # logger.info(max_idx)
        if len(max_idx) > 0:
            min_err_data = None
            for b in range(2 ** len(max_idx)):
                # 二進数の接頭辞の削除
                bits = format(b, f"0{len(max_idx)}b")
                prev_idx = 0
                data1 = []
                for i in range(len(max_idx)):
                    # 左に
                    if bits[i] == "0":
                        data1.append(range_data[prev_idx : max_idx[i] + 1].copy())
                        prev_idx = max_idx[i] + 1
                    # 右に
                    elif bits[i] == "1":
                        data1.append(range_data[prev_idx : max_idx[i]].copy())
                        prev_idx = max_idx[i]
                    else:
                        logger.error("0と1以外の数字が来た")
                data1.append(range_data[prev_idx:].copy())
                err = 0
                buf_data = []
                pass_flag = False
                for data2 in data1:
                    fis = self.filter_inv_solve(data2)
                    if fis.success:
                        buf_data.append(list(fis.x))
                        err += fis.fun
                    else:
                        pass_flag = True
                        break
                if pass_flag:
                    # logger.info(bits)
                    # logger.info(max_idx)
                    # logger.info(data1)
                    continue
                if not min_err_data or min_err > err:
                    min_err = err
                    min_err_data = buf_data.copy()
            if min_err_data:
                self.estimated_data.extend(min_err_data)
            else:
                logger.error("解が存在しない")

        else:
            a = list(self.filter_inv_solve(range_data).x).copy()
            self.estimated_data.append(a)

    # 逆問題による推測
    def filter_inv_solve(self, range_data, left=False, right=False):
        # 観測値が1個の場合、観測値から指の半径から推測
        range_data_np = np.array(range_data)
        range_x = range_data_np[:, 0]  # 1列目
        range_r = range_data_np[:, 1]  # 2列目
        r = self.finger_radius  # rの値
        e = 3  # riの誤差

        # 誤差関数
        # def error(params):
        #     x, y = params
        #     residuals = []
        #     for i in range(len(range_data)):
        #         for r_err in [-e, e]:  # 誤差を考慮
        #             ri_err = range_r[i] + r_err
        #             residual = np.sqrt((x - range_x[i]) ** 2 + y**2 - (r + ri_err) ** 2)
        #             residuals.append(residual)
        #     return np.sum(np.array(residuals) ** 2) / len(range_data)

        def error(params):
            x, y = params
            sum_squared_error = 0
            for i in range(len(range_data)):
                xi = range_x[i]
                ri = range_r[i]
                error = (x - xi) ** 2 + y**2 - (ri + r) ** 2
                sum_squared_error += error**2
            return sum_squared_error / len(range_data)

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

        bounds = [(0, self.sensor_num * self.sensor_ratio), (0, self.sensor_height)]
        # 初期値 (観測点の中心を使用)
        initial_guess = [np.mean(range_x), np.mean(range_r)]
        # 最適化
        result = minimize(
            error,
            initial_guess,
            bounds=bounds,
            # constraints=constraints,
            # method="SLSQP",
        )
        if not result.success:
            logger.error("解けない" + result.message)
        return result

    # センサのデータを未検知のセンサごとに分割

    def split_x_data(self, range_data):
        range_np = range_data
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
            self.split_finger_data(data)

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
                for i in range(len(self.range_data)):
                    x0, r0 = self.range_data[i]
                    r0 += self.finger_radius
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

                # 推定位置のプロット
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


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    # liner_touch.update_callback = liner_touch.display_data
