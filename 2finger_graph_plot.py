import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import matplotlib as mpl


def plot_graph(
    range_data, estimated_data, sensor_ratio, sensor_num, sensor_height, finger_radius
):
    """
    センサーデータと推定位置をプロットする関数。

    Parameters:
    range_data (list): センサーデータのリスト。各要素は(x, 距離)のタプル。
    estimated_data (list): 推定位置のリスト。各要素は(x, y)のタプル。
    sensor_ratio (float): センサーの間隔。
    sensor_num (int): センサーの数。
    sensor_height (float): センサーの高さ。
    finger_radius (float): 指の半径。
    """

    fig, ax = plt.subplots(figsize=(5, 2))  # figsizeを指定
    ax.set_aspect("equal")
    ax.set_xlim(0, sensor_num * sensor_ratio + sensor_ratio)
    ax.set_ylim(0, sensor_height)
    ax.set_ylabel("Distance(mm)", fontsize=12)  # 日本語フォントが適用される

    # センサーデータのプロット
    x_vals = [data[0] for data in range_data]
    y_vals = [data[1] for data in range_data]
    ax.scatter(x_vals, y_vals, color="blue", s=50, label="Sensor Data")

    # 推定位置のプロット
    estimated_label = "Finger Center"
    for i, estimated_pos in enumerate(estimated_data):
        ax.scatter(
            estimated_pos[0],
            estimated_pos[1],
            color="red",
            s=70,
            label=estimated_label if i == 0 else None,
        )

    # 目盛の設定
    ax.set_xticks(np.arange(sensor_ratio, sensor_num * sensor_ratio + 1, sensor_ratio))
    ax.set_xticklabels(
        [f"S{i+1}" for i in range(sensor_num)], fontsize=12
    )  # fontsizeを指定

    ax.legend()
    plt.show()


# 使用例
# ダミーデータの作成
sensor_ratio = 10
sensor_num = 10
sensor_height = 150
finger_radius = 7.45
range_data = [[20, 77], [30, 67], [40, 78], [50, 85], [60, 73], [70, 81]]
estimated_data = [(29, 80), (59, 88)]

# range_data = [[10,72], [20, 56], [30, 52], [40, 71], [50, 65], [60, 59], [70, 69]]
# estimated_data = [(22, 76), (59, 76)]


# グラフのプロット
plot_graph(
    range_data, estimated_data, sensor_ratio, sensor_num, sensor_height, finger_radius
)
