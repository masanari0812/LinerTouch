import numpy as np
import csv
import os
import random
import logging
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # DEBUGレベルを含む全てのログを表示
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",  # フォーマットの設定
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
    cov = np.cov(x, y)  # 共分散行列を計算
    eigenvalues, eigenvectors = np.linalg.eig(cov)  # 固有値と固有ベクトルを計算
    angle = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))  # 楕円の傾きを計算
    width, height = 2 * n_std * np.sqrt(eigenvalues)  # 楕円の幅と高さを計算
    ellipse = Ellipse(
        xy=(np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=angle,
        facecolor="none",
        edgecolor="black",
    )  # 楕円を作成
    return ellipse


def convert_csv_to_numpy_array(arg0, arg1, arg2=0):
    """
    CSVファイルからデータを読み込み、最初の2つの要素をnp.arrayに変換する関数

    Args:
        filename: CSVファイル名 (文字列)

    Returns:
        list: np.arrayのリスト
    """
    result = []
    # 実行中のスクリプトのパスを取得
    current_file = os.path.abspath(__file__)

    # 親ディレクトリのパスを取得
    parent_dir = os.path.dirname(current_file)
    value0 = arg0
    value1 = arg1
    value2 = arg2
    file_path = os.path.join(
        parent_dir, "data", "exp1_", f"{value0}+{value1}x{value2}_estimated.csv"
    )
    # CSVファイルを読み込む
    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        result = []
        for row in reader:
            temp = []
            try:
                # "[14.801996614908228, 99.29362065281744]"のような文字列を処理
                item0 = row[0].strip("[]")  # "[]"を削除
                temp.append([float(n) for n in item0.split(", ")])
                item1 = row[1].strip("[]")  # "[]"を削除
                temp.append([float(n) for n in item1.split(", ")])
            except IndexError:
                # 要素数が2つ未満の行をスキップ
                error += 1
                continue

            # tempが2つの要素を持っていることを確認
            if len(temp) == 2:
                result.append(temp)
    logger.info(f"error {arg0:3.0f}+{arg1:3.0f}:{error:3.0f}")
    # NumPy配列に変換
    return np.array(result)


# 円柱A、Bの座標をすべて結合
def connect_csv_to_numpy_array(arg0):
    all_arrays = []  # 空のリストで初期化
    for idx1 in range(20, 60, 10):
        csv_arr = convert_csv_to_numpy_array(arg0=arg0, arg1=idx1, arg2=0)
        if csv_arr.size > 0:  # 空の配列でない場合のみ追加
            all_arrays.append(csv_arr)

    if not all_arrays:  # すべての配列が空の場合
        return np.array([])  # 空のndarrayを返す

    return np.concatenate(all_arrays)  # リストをconcatenateする


# 変換を実行
ellipseA, ellipseB = [], []
fig, ax = plt.subplots()
for idx0 in range(25, 175, 25):
    for idx1 in range(20, 60, 10):
        for idx2 in range(1):
            arrays = convert_csv_to_numpy_array(idx0, idx1, idx2)

            a = (idx0 / 175 * 0.7) + 0.3
            b = (idx1 / 60 * 0.7) + 0.3
            color0 = (a, 0, 0.5)
            color1 = (0, b, 0.5)

            # それ以外の点群はそのままプロット
            for data in arrays:
                plt.scatter(data[0][0], data[0][1], c=color0, s=3, alpha=0.7)

            # 2番目の点群は線と楕円に変更
            ellipseB.append(std_ellipse(arrays[:, 1, 0], arrays[:, 1, 1], 1))
            # 楕円の中心座標を取得
            center1 = ellipseB[-1].get_center()

            # 線を描画
            plt.plot(
                [idx1 + 20, center1[0]],
                [idx0, center1[1]],
                color="black",
            )

            for data in arrays:
                plt.scatter(data[1][0], data[1][1], c=color1, s=3, alpha=0.7)


for idx0 in range(25, 175, 25):
    arrays = connect_csv_to_numpy_array(idx0)
    # 線の始点と終点を計算
    start_point = (20, idx0)
    end_point = (np.mean(arrays[:, 0, 0]), np.mean(arrays[:, 0, 1]))

    # 線を描画
    plt.plot(
        [start_point[0], end_point[0]],
        [start_point[1], end_point[1]],
        color="black",
    )

    # 楕円を描画
    ellipseA.append(std_ellipse(arrays[:, 0, 0], arrays[:, 0, 1], 1))
    plt.scatter(20, idx0, c="black", s=40)
    for idx1 in range(20, 60, 10):
        plt.scatter(idx1 + 20, idx0, c="black", s=40)


for ellipse in ellipseA:
    ax.add_patch(ellipse)
for ellipse in ellipseB:
    ax.add_patch(ellipse)

plt.show()
