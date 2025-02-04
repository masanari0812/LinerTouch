import numpy as np
import csv
import os
import logging
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import random

# 日本語フォントの設定
import japanize_matplotlib
plt.rcParams['font.family'] = 'IPAexGothic'
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)


def std_ellipse(x, y, n_std=1):
    """
    xとyの点群データから標準偏差の楕円を生成する関数

    Args:
        x: x座標の配列
        y: y座標の配列
        n_std: 標準偏差の倍率 (デフォルトは1)

    Returns:
        matplotlib.patches.Ellipse: 標準偏差の楕円
    """
    cov = np.cov(x, y)
    eigenvalues, eigenvectors = np.linalg.eig(cov)
    angle = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(eigenvalues)
    ellipse = Ellipse(
        xy=(np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=angle,
        facecolor="none",
        edgecolor="black",
    )
    return ellipse


def convert_csv_to_numpy_array(arg0, arg1, arg2=0):
    """
    CSVファイルからデータを読み込み、最初の2つの要素をnp.arrayに変換する関数

    Args:
        arg0, arg1, arg2: ファイル名生成に使用するパラメータ

    Returns:
        list: np.arrayのリスト
    """
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    file_path = os.path.join(
        parent_dir, "data", "exp1_", f"{arg0}+{arg1}x{arg2}_estimated.csv"
    )

    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            temp = []
            try:
                item0 = row[0].strip("[]")
                temp.append([float(n) for n in item0.split(", ")])
                item1 = row[1].strip("[]")
                temp.append([float(n) for n in item1.split(", ")])
            except IndexError:
                error += 1
                continue

            if len(temp) == 2:
                result.append(temp)

    logger.info(f"error {arg0:3.0f}+{arg1:3.0f}:{error:3.0f}")
    return np.array(result)


def connect_csv_to_numpy_array(arg0):
    all_arrays = []
    for idx1 in range(20, 60, 10):
        csv_arr = convert_csv_to_numpy_array(arg0=arg0, arg1=idx1, arg2=0)
        if csv_arr.size > 0:
            all_arrays.append(csv_arr)

    if not all_arrays:
        return np.array([])

    return np.concatenate(all_arrays)


# ------------------------------
# カラーパレットの定義（暖色・寒色の区別をなくし、全体のリストとして管理）
# ------------------------------
colors = ["tab:red", "tab:blue", "tab:orange", "tab:green",
          "tab:brown", "tab:purple", "tab:pink", "tab:cyan"]
# 順番による偏りを避けるためにシャッフル（必要に応じて）
random.seed(0)  # 再現性のため
random.shuffle(colors)

ellipseA, ellipseB = [], []
fig, ax = plt.subplots()
ax.set_xlim(-10, 100)  # X軸の範囲
ax.set_ylim(0, 200)  # Y軸の範囲
# ループのインデックスの組み合わせから、一意の番号を作成して色を選ぶ
for i, idx0 in enumerate(range(25, 175, 25)):
    for j, idx1 in enumerate(range(20, 60, 10)):
        for idx2 in range(1):
            arrays = convert_csv_to_numpy_array(idx0, idx1, idx2)

            # 組み合わせごとに一意のインデックスを作成
            comb_index = i * 4 + j  # idx1 のループは4回なので
            # 円柱A用の色（comb_index から選択）
            color0 = colors[comb_index % len(colors)]
            # 円柱B用は同じ色にならないようにオフセット
            color1 = colors[(comb_index + 1) % len(colors)]

            # 円柱Aのデータをプロット
            for data in arrays:
                plt.scatter(data[0][0], data[0][1], c=color0, s=3, alpha=0.7)

            ellipseB.append(std_ellipse(arrays[:, 1, 0], arrays[:, 1, 1], 1))
            center1 = ellipseB[-1].get_center()

            plt.plot(
                [idx1 + 20, center1[0]],
                [idx0, center1[1]],
                color="black",
            )

            # 円柱Bのデータをプロット
            for data in arrays:
                plt.scatter(data[1][0], data[1][1], c=color1, s=3, alpha=0.7)

# connect_csv_to_numpy_array() を用いたプロット（黒色で描画）
for idx, idx0 in enumerate(range(25, 175, 25)):
    arrays = connect_csv_to_numpy_array(idx0)
    start_point = (20, idx0)
    end_point = (np.mean(arrays[:, 0, 0]), np.mean(arrays[:, 0, 1]))

    plt.plot(
        [start_point[0], end_point[0]],
        [start_point[1], end_point[1]],
        color="black",
    )

    ellipseA.append(std_ellipse(arrays[:, 0, 0], arrays[:, 0, 1], 1))
    plt.scatter(20, idx0, c="black", s=40)
    for idx1 in range(20, 60, 10):
        plt.scatter(idx1 + 20, idx0, c="black", s=40)

for ellipse in ellipseA:
    ax.add_patch(ellipse)
for ellipse in ellipseB:
    ax.add_patch(ellipse)

# 下部（横軸）と左側（縦軸）に太字、フォントサイズ14で文字を挿入
plt.xlabel("横軸(X軸)の座標(mm)", fontsize=14, fontweight='bold')
plt.ylabel("縦軸(Y軸)の座標(mm)", fontsize=14, fontweight='bold')

plt.show()
