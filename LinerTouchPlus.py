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
                self.dummy_ser = csv.reader(csvfile)

        else:
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
        if plot_graph:
            threading.Thread(target=self.plot_data).start()

        self.fig = None  # figを初期化
        self.ax = None  # axも初期化
        self.past_data = {
            "estimated_data": deque(maxlen=self.past_data_num),
            "min_pos": deque(maxlen=self.past_data_num),
            "actual_data": deque(maxlen=self.past_data_num),
            "len": 0,
        }

    def get_data(self):
        while True:
            start_time = time.time()

            if self.load_csv:
                raw_data = self.read_csv_row()
            else:
                # 読み込めるデータがあるかを確認
                while self.ser.in_waiting:  # 読み込み可能なデータがある間
                    raw_data = (
                        self.ser.readline().decode("utf-8").strip()
                    )  # 1行ずつ読み取り、最後の行を最新のデータとして保持
                # 読み込めるデータがない場合

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
                logger.info(f"Processed range_data: {self.range_data}")
                # 生データから位置推定と更新処理

                self.estimation_finger()
                if self.ready:
                    # 更新コールバック
                    if self.update_callback:
                        self.update_callback()

                self.ready = True
                # データを保存

            end_time = time.time()
            logger.debug(f"Time taken: {end_time - start_time:.6f} seconds")

    # CSVの読み込み関数
    def read_csv_row(self):
        try:
            row = next(self.dummy_ser)
        except StopIteration:
            self.csvfile.seek(0)  # ファイルポインタを先頭に戻す
            self.dummy_ser = csv.reader(self.csvfile)  # readerを再作成
            row = next(self.dummy_ser)  # 最初の行を読み込む
        return row

    def estimation_finger(self):
        if self.ready:
            self.prev_estimated_data = self.estimated_data
        for data in self.split_x_data():
            self.split_finger_data(data)

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

        return np.array(result)

    # 指の本数を推測し最も誤差が少ない推定位置を利用
    def split_finger_data(self, range_data):
        # 指の極大値を格納
        range_data = np.array(range_data)
        if len(range_data) < 2:
            return
        max_idx = []
        range_x = range_data[:, 0]  # 1列目
        range_r = range_data[:, 1]  # 2列目
        for i in range(1, len(range_data) - 1):
            if range_r[i - 1] < range_r[i] > range_r[i + 1]:
                max_idx.append(i)
        # max_idxの要素数+1が指の本数になる
        # 極大値のセンサ値の左右に振り分け目的関数の誤差の合計が低い組み合わせを利用
        # 2^(極大値の数)回数試行しそのインデックスを2進数に変換し
        # 極大値と同じインデックスの桁数目の数によって左右どちらに振り分けるか決める
        # 極大値が4本でインデックスが0b0110の場合、左右右左となる。
        logger.info(max_idx)
        if len(max_idx) > 0:
            result = []
            for b in range(2 ** len(max_idx)):
                # 二進数の接頭辞の削除
                bits = format(b, f"0{len(max_idx)}b")
                prev_idx = 0
                data = []
                for i in range(len(max_idx)):
                    # 左に
                    if bits[i] == "0":
                        data.append(range_data[prev_idx:i])
                        prev_idx = i + 1
                    # 右に
                    elif bits[i] == "1":
                        data.append(range_data[prev_idx : i - 1])
                        prev_idx = i
                    else:
                        logger.error("0と1以外の数字が来た")
                data.append(range_data[prev_idx:])
                result.append(data)
            err_val = []
            for data in result:
                fis = []
                success_flags = []  # successフラグを格納するリスト
                for d in data:
                    res = self.filter_inv_solve(d)
                    fis.append(res)
                    success_flags.append(res.success)  # successフラグを格納

                # 全てのsuccessフラグがTrueの場合のみerr_valを計算
                if all(success_flags):
                    val = sum([f.fun for f in fis])  # 誤差値の計算
                    err_val.append(val)
                    logger.info(f"err_val:{val}")
                    logger.info(f"data:{data}")

            # err_valが空の場合は、全ての分割パターンでfilter_inv_solve()が失敗している
            if err_val:
                min_idx = err_val.index(min(err_val))
                for d in result[min_idx]:
                    a = list(self.filter_inv_solve(d).x).copy()
                    self.estimated_data.append(a)
            else:
                logger.warning("All filter_inv_solve() failed.")  # 失敗ログを出力
        else:
            a = list(self.filter_inv_solve(range_data).x).copy()
            self.estimated_data.append(a)

    # 逆問題による推測
    def filter_inv_solve(self, range_data, left=False, right=False):
        # 観測値が1個の場合、観測値から指の半径から推測

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
                    residual = np.sqrt((x - range_x[i]) ** 2 + y**2 - (r + ri_err) ** 2)
                    residuals.append(residual)
            return np.sum(np.array(residuals) ** 2) / len(range_data)

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

    def plot_data(self):
        if self.ready:
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


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
