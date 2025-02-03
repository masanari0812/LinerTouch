import serial
import numpy as np
import time
import logging
import threading
import matplotlib.pyplot as plt
from scipy.optimize import minimize, LinearConstraint, Bounds, fsolve
from scipy import signal
from collections import deque, defaultdict
from functools import wraps
from matplotlib import patches
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

logger = logging.getLogger(__name__)


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        if end - start > 0.05:
            logger.info(f"{func.__name__}: {end - start:.4f}秒")
        return result

    return wrapper


class LinerTouch:

    def __init__(self, update_callback=None, tap_callback=None, plot_graph=True):
        # LinerTouchの変数なくてもどこからでもアクセスできるように
        LinerTouch.liner = self
        # LinerTouch が準備できたかを示す
        self.ready = False
        self.ser = serial.Serial(port="COM9", baudrate=115200)
        self.buffer_data = ""

        self.sensor_num = 9
        # 第2指遠位関節幅の半径(mm単位)
        self.finger_radius = 14.9 / 2
        # センサの高さに対しての一個あたりのセンサの横幅のサイズの倍率
        # センサの測定可能距離/センサの横幅=sensor_ratio
        self.sensor_ratio = 10
        # センサの最大測定距離(mm単位)
        self.sensor_height = 200
        # 指のタッチ時間の閾値(sec単位)
        self.release_threshold = 0.5
        # 保存するデータの数
        self.past_data_num = 10

        # グラフを描画するかしないか
        self.plot_graph = plot_graph
        # タップフラグ
        self.tap_flag = False
        self.pinch_dist = None

        self.update_callback = update_callback
        self.tap_callback = tap_callback
        self.pinch_start_callback = None
        self.pinch_end_callback = None
        # pinch_motionとpinch_updateは同じもの
        self.pinch_motion_callback = None
        self.pinch_update_callback = None
        self.plot_data_thread = None
        self.ax = None
        self.past_data = {
            "estimated_data": deque(maxlen=self.past_data_num),
            "actual_data": deque(maxlen=self.past_data_num),
            "len": 0,
        }
        threading.Thread(target=self.update_get_data).start()
        if self.plot_graph:
            threading.Thread(target=self.update_plot_data).start()

    def update_get_data(self):

        self.ser.reset_input_buffer()
        while True:
            try:
                self.get_data()
            except KeyboardInterrupt:
                break
        self.ser.close()

    def get_data(self):
        if self.ser.in_waiting > 0:  # 読み込めるデータがあるかを確認
            self.buffer_data += self.ser.read(self.ser.in_waiting).decode("utf-8")
            split = self.buffer_data.split("\r\n")
            # コンマはセンサ側のオフセットの処理なので次回へ

            # 改行があればデータが完成しているため行を完成させ後ろの行はbuffer_dataに追加
            if len(split) >= 2:
                if len(split) >= 3:
                    logger.error("サンプリングレートに間に合ってない")
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
            logger.info(self.range_data)
            # データがある場合
            if len(self.range_data) > 0:
                # data = self.smoothing_filter()
                self.split_x_data(self.range_data)

                for data in self.estimated_data:
                    logger.info(f"est_pos:{data[0]:.0f},{data[1]:.0f}")

                # LinerTouch が準備できたことを示す
                self.ready = True
            # データがすべてOoRの場合
            else:
                pass
            if self.ready:
                # 更新コールバック
                if self.update_callback:
                    self.update_callback()
                if self.get_pastdata("len") == self.past_data_num:
                    # タッチ検出処理
                    self.get_touch()
                    self.get_pinch()
            self.prev_range_data = self.range_data
            self.add_pastdata(
                estimated_data=self.estimated_data, actual_data=self.range_data
            )

        # シリアル通信のバッファにデータがない場合
        else:
            pass

    # 追加のタイミングが一フレーム遅い
    # estimated_posを求める
    @timeit
    def smoothing_filter(self):
        if self.get_pastdata("len") == self.past_data_num:
            buf = {}
            for data1 in self.range_data:
                buf[str(data1[0])] = [data1[1]]
            for data1 in self.get_pastdata("actual_data").copy():
                for data2 in data1:
                    key = str(data2[0])
                    if key in buf:
                        buf[key].append(data2[1])
                    # バターワースフィルタの設計
            result = []
            for data1 in buf:
                sos = signal.butter(4, 10, "lp", fs=50, output="sos")
                filtered = signal.sosfilt(sos, np.array(buf[data1]))
                result.append([int(data1), float(filtered[0])])
        else:
            result = self.range_data
        return result

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
        if estimated_data is not None:
            self.past_data["estimated_data"].appendleft(estimated_data.copy())
        if actual_data is not None:
            self.past_data["actual_data"].appendleft(actual_data.copy())
        self.past_data["len"] = len(self.past_data["estimated_data"])

    # 指の本数を推測し最も誤差が少ない推定位置を利用
    # @timeit
    # def split_finger_data(self, range_data):
    #     # 指の極大値を格納
    #     range_data_np = np.array(range_data)
    #     if len(range_data) < 2:
    #         return
    #     max_idx = []
    #     range_x = range_data_np[:, 0]  # 1列目
    #     range_r = range_data_np[:, 1]  # 2列目
    #     for i in range(1, len(range_data) - 1):
    #         if range_r[i - 1] < range_r[i] > range_r[i + 1]:
    #             max_idx.append(i)

    #     self.min_err = None
    #     self.min_left = None
    #     self.min_right = None
    #     self.count = 0

    #     def store_min(idx):
    #         # split_finger_dataの変数にアクセスできるように
    #         left = self.filter_inv_solve(range_data[:idx])
    #         right = self.filter_inv_solve(range_data[idx:])
    #         # 計算成功していなければ終了
    #         # if not left.success or not right.success:
    #         # return
    #         # 値が無ければ比較無しで代入
    #         if not self.min_err:
    #             self.min_left = left
    #             self.min_right = right
    #             return
    #         # 現状の最小値と比較し現状以下のものがあれば更新
    #         err = left.fun + right.fun
    #         if err < self.min_err:
    #             self.min_left = left
    #             self.min_right = right
    #         logger.info(self.count)
    #         return

    #     if len(max_idx) > 0:
    #         for idx in max_idx:
    #             # 左に振り分け
    #             store_min(idx + 1)
    #             # 右に振り分け
    #             store_min(idx)
    #         # if not min_err:
    #         #     logger.error("計算失敗してて草")
    #         #     raise AttributeError("計算失敗してて草")
    #         self.estimated_data.append(self.min_left.x.tolist())
    #         self.estimated_data.append(self.min_right.x.tolist())

    #     else:
    #         center = self.lr_min_inv(range_data)
    #         self.estimated_data.append(center.x.tolist())

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
            self.estimated_data.append(self.min_left.x.tolist())
            self.estimated_data.append(self.min_right.x.tolist())

        else:
            center = self.lr_min_inv(range_data)
            self.estimated_data.append(center.x.tolist())

    # 左右のセンサが最短距離でない場合、含めると誤差が大きくなるため少なくなるように
    def lr_min_inv(self, range_data):
        if len(range_data) <= 3:
            result = self.filter_inv_solve(range_data)
            return result
        inv_list = []
        # 左右どちらも除かない
        inv_list.append(self.filter_inv_solve(range_data))
        # 左を除く
        inv_list.append(self.filter_inv_solve(range_data[1:]))
        # 右を除く
        inv_list.append(self.filter_inv_solve(range_data[:-1]))
        if len(range_data) > 4:
            inv_list.append(self.filter_inv_solve(range_data[1:-1]))

        min_fun = min([data.fun for data in inv_list])
        for data in inv_list:
            if data.fun == min_fun:
                return data

        raise ValueError("一致する誤差値がない")

    @timeit
    # 逆問題による推測
    def filter_inv_solve(self, range_data, left=False, right=False):
        # 観測値が1個の場合、観測値から指の半径から推測
        range_data_np = np.array(range_data)
        range_x = range_data_np[:, 0]  # 1列目
        range_r = range_data_np[:, 1]  # 2列目
        min_r = min(range_r)
        range_data = [
            [x, r]
            for x, r in range_data
            if r
            <= min_r + self.sensor_ratio + self.finger_radius * (len(range_data) / 2)
        ]
        range_data_np = np.array(range_data)
        range_x = range_data_np[:, 0]  # 1列目
        range_r = range_data_np[:, 1]  # 2列目

        r = self.finger_radius  # rの値
        e = 0  # riの誤差

        # 誤差関数
        # def error(params):
        #     x, y = params
        #     sum_squared_error = 0
        #     for i in range(len(range_data)):
        #         err_list = []
        #         for r_err in range(-e, e + 1):  # 誤差を考慮
        #             xi = range_x[i]
        #             ri = range_r[i] + r_err
        #             error = (np.sqrt((x - xi) ** 2 + y**2) )- (np.sqrt((ri + r) ** 2))
        #             err_list.append(error**2)
        #         sum_squared_error += min(err_list)
        #         return np.sqrt(sum_squared_error / len(range_data))
        def error(params):
            x, y = params
            sum_squared_error = 0
            for i in range(len(range_data)):
                xi = range_x[i]
                ri = range_r[i]
                error = (np.sqrt((x - xi) ** 2 + y**2)) - (np.sqrt((ri + r) ** 2))
            sum_squared_error += error**2
            return np.sqrt(sum_squared_error / len(range_data))

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
            (0, self.sensor_height),
        ]
        # 初期値 (観測点の中心を使用)
        # rd = int(len(range_data) / 2)
        # initial_guess = self.calculate_intersections(range_data[rd : rd + 2])
        # if initial_guess == None:
        #     initial_guess = [np.mean(range_x), np.mean(range_r)]
        # else:
        #     pass
        initial_guess = [np.mean(range_x), np.mean(range_r)]

        # 最適化
        result = minimize(
            error,
            initial_guess,
            bounds=bounds,
            # constraints=constraints,
            method="SLSQP",
        )
        result.range_x = range_x
        if not result.success:
            logger.error("解けない" + result.message)

        # if result.fun == 0:
        #     logger.error("誤差0" + result.message)
        # else:
        #     logger.info(result.x)
        #     logger.info(result.fun)

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
                pos = self.lr_min_inv(data)
                self.estimated_data.append(pos.x.tolist())

    def update_plot_data(self):
        time.sleep(1)
        while True:
            try:
                self.plot_data()
            except KeyboardInterrupt:
                break

    def plot_data(self):
        if self.ready:
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

    @timeit
    # 指のタッチ検知
    def get_touch(self):
        if self.tap_callback != None:
            # 指のリリース
            now_time = time.time()
            now_range_data = self.range_data
            prev_range_data = self.get_pastdata("actual_data")[0]
            # タップのフラグがある場合
            if self.tap_flag:
                self.estimated_data = self.hold_data  # .copy()
                # if  now_range_data and not prev_range_data:
                if now_range_data != []:
                    self.tap_flag = False
                    logger.info("タッチ")
                    # 冗長な条件式
                    if self.tap_callback:
                        self.tap_callback()
                if now_time - self.hold_start > self.release_threshold:
                    logger.info("タッチタイムアップ")
                    self.tap_flag = False
            # タップのフラグがない場合
            else:
                if now_range_data == [] and prev_range_data != []:
                    self.hold_start = now_time
                    past_estimated_data = self.get_pastdata("estimated_data")[1]
                    if len(past_estimated_data) != 1:
                        logger.error("過去の推測値データの要素数がヘン")
                        return
                    self.hold_data = past_estimated_data
                    logger.info("リリース")
                    self.tap_flag = True

    @timeit
    # 指のピンチ検知
    def get_pinch(self):
        if self.pinch_update_callback != None:
            if len(self.estimated_data) == 2:
                now_estimated_data = self.estimated_data
                past_estimated_data = self.get_pastdata("estimated_data")[0]
                # ピンチ開始時の処理
                if (
                    self.pinch_dist == None
                    or len(now_estimated_data) == 2
                    and len(past_estimated_data) != 2
                ):
                    self.pinch_dist = LinerTouch.get_euclid_dist(now_estimated_data)
                    self.center_pos = LinerTouch.get_mid_pos(now_estimated_data)
                    self.pinch_start_callback()
                    logger.info("ピンチスタート")
                else:
                    if self.pinch_dist == None:
                        return
                    now_dist = LinerTouch.get_euclid_dist(now_estimated_data)
                    self.pinch_update_callback(self.pinch_dist - now_dist)

                    self.center_pos = LinerTouch.get_mid_pos(now_estimated_data)
                    self.pinch_motion_callback()
                    self.pinch_dist = now_dist
            else:
                past_estimated_data = self.get_pastdata("estimated_data")[0]
                if len(past_estimated_data) == 2:
                    self.pinch_end_callback()

    def get_euclid_dist(data):
        pos0 = data[0]
        pos1 = data[1]
        dist = np.sqrt((pos0[0] - pos1[0]) ** 2 + (pos0[1] - pos1[1]) ** 2)
        return dist

    def get_mid_pos(data):
        pos0 = data[0]
        pos1 = data[1]
        pos = [
            (pos0[0] + pos1[0]) / 2,
            (pos0[1] + pos1[1]) / 2,
        ]
        return pos

    # @timeit
    # def calculate_intersections(self, range_data):
    #     """
    #     複数の円の交点を計算し、y座標が最大の点を返す関数。

    #     Args:
    #         circles: 円の情報を含むリスト。各円は [x, r] の形式で、x は中心の x 座標、r は半径。

    #     Returns:
    #         交点のリスト。各交点は [x, y] の形式。
    #     """

    #     # 観測値が1個の場合、観測値から指の半径から推測
    #     r = self.finger_radius  # rの値
    #     # e = 0  # riの誤差

    #     if len(range_data) < 2:
    #         logger.error("2つのrange_dataが必要です。")
    #         return None

    #     angle_range = [(90 - 12.5) / 180 * np.pi, (90 + 12.5) / 180 * np.pi]

    #     x0, r0 = range_data[0]
    #     x1, r1 = range_data[1]
    #     r0, r1 = r0 + r, r1 + r
    #     # シンボルの定義
    #     x, y = symbols("x y")

    #     # 方程式の定義 (yを角度から求めるように変更)
    #     eq0 = Eq((x - x0) ** 2 + (y - 0) ** 2, r0**2)
    #     eq1 = Eq((x - x1) ** 2 + (y - 0) ** 2, r1**2)

    #     # 方程式を解く
    #     solution_eqs = solve([eq0, eq1], (x, y), domain=Reals, real=True)

    #     # 実数解を抽出し、y座標が最大のものを選択
    #     real_sols = []
    #     for sol in solution_eqs:
    #         if not sol[0].is_real or not sol[1].is_real:  # 虚数解は除外
    #             continue
    #         sol_x = float(sol[0])
    #         sol_y = float(sol[1])

    #         # # 角度の範囲をチェック
    #         # angle = math.atan2(sol_y, sol_x - x0)
    #         # if angle_range[0] <= angle <= angle_range[1]:
    #         if sol_y >= 0:
    #             real_sols.append([sol_x, sol_y])
    #     if real_sols:
    #         estimated_pos = max(real_sols, key=lambda sol: sol[1])
    #         return estimated_pos
    #     return None


if __name__ == "__main__":
    # ログの設定 - 全てのログレベルを表示するように設定
    logging.basicConfig(
        level=logging.INFO,  # DEBUGレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",  # フォーマットの設定
    )
    liner_touch = LinerTouch()
    # liner_touch.update_callback = liner_touch.display_data
