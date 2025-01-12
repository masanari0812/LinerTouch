import serial
import numpy as np
import time
import logging
import threading
import matplotlib.pyplot as plt
from scipy.optimize import minimize, LinearConstraint, Bounds, fsolve

from collections import deque, defaultdict
from itertools import combinations
from functools import wraps
from matplotlib import patches

logger = logging.getLogger(__name__)


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if end - start > 0.04:
            logger.info(f"{func.__name__}: {end - start:.4f}秒")
        return result

    return wrapper


class LinerTouch:

    def __init__(self, update_callback=None, tap_callback=None, plot_graph=True):
        # LinerTouchの変数なくてもどこからでもアクセスできるように
        LinerTouch.liner = self
        # LinerTouch が準備できたかを示す
        self.ready = False
        self.ser = serial.Serial(port="COM5", baudrate=115200)
        self.buffer_data = ""

        self.sensor_num = 9
        self.finger_radius = 8
        # センサの高さに対しての一個あたりのセンサの横幅のサイズの倍率
        # センサの測定可能距離/センサの横幅=sensor_ratio
        self.sensor_ratio = 10
        self.sensor_height = 150
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

        self.update_callback = update_callback
        self.tap_callback = tap_callback
        self.plot_data_thread = None
        self.ax = None
        self.past_data = {
            "estimated_data": deque(maxlen=self.past_data_num),
            "actual_data": deque(maxlen=self.past_data_num),
            "len": 0,
        }
        threading.Thread(target=self.update_get_data).start()
        threading.Thread(target=self.update_plot_data).start()
        time.sleep(0.1)

    def update_get_data(self):
        self.ser.reset_input_buffer()
        while True:
            try:
                self.get_data()
            except KeyboardInterrupt:
                break
        self.ser.close()

    @timeit
    def get_data(self):
        if self.ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
            self.buffer_data += self.ser.read(self.ser.in_waiting).decode("utf-8")
            split = self.buffer_data.split("\r\n")
            # コンマはセンサ側のオフセットの処理なので次回へ

            # 改行があればデータが完成しているため行を完成させ後ろの行はbuffer_dataに追加
            if len(split) >= 2:
                if "," in split[-1] or "," in split[-2]:
                    return
                raw_data = split[-2]
                self.buffer_data = split[-1]
            # 改行コードが無ければデータが未完成のためbuffer_dataに追加して次回へ
            else:
                return

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
            # logger.info(self.range_data)
            # データがある場合
            if len(self.range_data) > 0:
                self.smoothing_filter()
                if self.ready:
                    # 更新コールバック
                    if self.update_callback:
                        self.update_callback()
                    # タッチ検出処理
                    self.get_touch()
                # for data in self.estimated_data:
                #     logger.info(f"est_pos:{data[0]:.0f},{data[1]:.0f}")

                # LinerTouch が準備できたことを示す
                self.ready = True
            # データがすべてOoRの場合
            else:
                pass
        # シリアル通信のバッファにデータがない場合
        else:
            pass

    # 追加のタイミングが一フレーム遅い
    # estimated_posを求める
    @timeit
    def smoothing_filter(self):
        if self.ready:
            self.prev_estimated_data = self.estimated_data
        self.add_pastdata(actual_data=self.range_data)

        self.split_x_data(self.range_data)

        self.add_pastdata(estimated_data=self.estimated_data)

    def get_pastdata(self, key: str):
        if self.past_data is None:
            pass
        return self.past_data[key]

    @timeit
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
    @timeit
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

        self.min_err = None
        self.min_left = None
        self.min_right = None
        self.count = 0

        def store_min(idx):
            # split_finger_dataの変数にアクセスできるように
            left = self.filter_inv_solve(range_data[:idx])
            right = self.filter_inv_solve(range_data[idx:])
            # 計算成功していなければ終了
            # if not left.success or not right.success:
            # return
            # 値が無ければ比較無しで代入
            if not self.min_err:
                self.min_left = left
                self.min_right = right
                return
            # 現状の最小値と比較し現状以下のものがあれば更新
            err = left.fun + right.fun
            if err < self.min_err:
                self.min_left = left
                self.min_right = right
            logger.info(self.count)
            return

        if len(max_idx) > 0:
            for idx in max_idx:
                # 左に振り分け
                store_min(idx + 1)
                # 右に振り分け
                store_min(idx)
            # if not min_err:
            #     logger.error("計算失敗してて草")
            #     raise AttributeError("計算失敗してて草")
            self.estimated_data.append(list(self.min_left.x))
            self.estimated_data.append(list(self.min_right.x))

        else:
            center = self.filter_inv_solve(range_data)
            # if not center.success:
            #     logger.error("計算失敗してて草")
            #     raise AttributeError()

            self.estimated_data.append(list(center.x))

    @timeit
    # 逆問題による推測
    def filter_inv_solve(self, range_data, left=False, right=False):
        # 観測値が1個の場合、観測値から指の半径から推測
        range_data_np = np.array(range_data)
        range_x = range_data_np[:, 0]  # 1列目
        range_r = range_data_np[:, 1]  # 2列目
        r = self.finger_radius  # rの値
        e = 3  # riの誤差

        # 誤差関数
        def error(params):
            x, y = params
            sum_squared_error = 0
            for i in range(len(range_data)):
                for r_err in range(-e, e + 1):  # 誤差を考慮
                    xi = range_x[i]
                    ri = range_r[i] + r_err
                    error = np.sqrt((x - xi) ** 2 + y**2) - np.sqrt((ri + r) ** 2)
                    sum_squared_error += error**2
                return np.sqrt(sum_squared_error / len(range_data))

        # def error(params):
        #     x, y = params
        #     sum_squared_error = 0
        #     for i in range(len(range_data)):
        #         xi = range_x[i]
        #         ri = range_r[i]
        #         error = np.sqrt((x - xi) ** 2 + y**2) - np.sqrt((ri + r) ** 2)
        #         sum_squared_error += error**2
        #     return np.sqrt(sum_squared_error / len(range_data))

        # 制約関数
        # 検知できなかったセンサ範囲を除く制約関数
        # 左からの制約
        def left_constraint(params):
            x, y = params
            return (
                (y * (-np.tan(12.5 * np.pi / 180)))
                - (min(range_x) - self.sensor_ratio)
                + x
            )

        # 右からの制約
        def right_constraint(params):
            x, y = params
            return (
                (y * (np.tan(-12.5 * np.pi / 180)))
                + (max(range_x) + self.sensor_ratio)
                - x
            )

        constraints = []
        if left:
            constraints.append({"type": "ineq", "fun": left_constraint})
        if right:
            constraints.append({"type": "ineq", "fun": right_constraint})

        # 入力領域外を除く制約関数

        bounds = [
            (0, self.sensor_num * self.sensor_ratio),
            (min(range_r), self.sensor_height),
        ]
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
            logger.error("解けない" + result.message)

        return result

    # センサのデータを未検知のセンサごとに分割
    @timeit
    def split_x_data(self, range_data):
        result = []
        temp_list = []  # 初期化を空リストに変更
        prev_x = range_data[0][0]
        for i in range(len(range_data)):
            x, y = range_data[i]
            if i > 0 and x - prev_x > self.sensor_ratio:
                result.append(temp_list)
                temp_list = []  # 新しいリストを作成
            temp_list.append([x, y])  # temp_list に要素を追加
            prev_x = x

        if temp_list:  # 最後の temp_list を result に追加
            result.append(temp_list)
        # データ郡が1弧の場合
        if len(result) < 2:
            self.split_finger_data(result[0])
        # データ郡が2弧(以上)の場合
        else:
            for data in result:
                pos = self.filter_inv_solve(data)
                self.estimated_data.append(list(pos.x))

    def update_plot_data(self):
        time.sleep(1)
        self.plot_data(True)
        while True:
            try:
                self.plot_data()
            except KeyboardInterrupt:
                break

    def plot_data(self, init=False):
        if self.plot_graph and self.ready:
            if self.ax is None:
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

                # 円弧のプロット
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
                self.ax.legend()

                # 描画を更新
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()

    # 指のタッチ検知
    def get_touch(self):
        if self.range_data==0:


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUGレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    # liner_touch.update_callback = liner_touch.display_data
