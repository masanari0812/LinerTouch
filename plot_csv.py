import numpy as np
import csv
import os
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse


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
        arg0: ファイル名の一部
        arg1: ファイル名の一部
        arg2: ファイル名の一部 (デフォルトは0)

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
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            temp = []
            for idx in range(2):
                try:
                    # "[14.801996614908228, 99.29362065281744]"のような文字列を処理
                    item = row[idx].strip("[]")  # "[]"を削除
                    numbers = [float(n) for n in item.split(", ")]
                    if len(numbers) == 2:  # 要素数が2の場合のみ追加
                        temp.append(numbers)
                    else:
                        break  # 要素数が2でない場合はその行の処理をスキップ
                except IndexError:
                    break  # インデックスエラーが発生した場合はその行の処理をスキップ
            if len(temp) == 2:  # 要素数が2の行のみ追加
                result.append(temp)

        # NumPy配列に変換
    return np.array(result)[:100]


# def remove_nan_data(data):
#     """
#     [[x1,y1],[x2,y2]] の形式の NumPy 配列から、
#     [np.nan, np.nan] を含むデータを削除する関数

#     Args:
#         data: 入力データ (np.array)

#     Returns:
#         np.array: [np.nan, np.nan] を含むデータを除去した NumPy 配列
#     """

#     # [np.nan, np.nan] を含むデータのインデックスを取得
#     nan_indices = np.where(np.isnan(data).any(axis=(1, 2)))[0]

#     # インデックスを使用してデータを削除
#     cleaned_data = np.delete(data, nan_indices, axis=0)
#     return cleaned_data
# 変換を実行
fig, ax = plt.subplots()
for idx0 in range(25, 175, 25):
    for idx1 in range(20, 60, 10):
        for idx2 in range(1):
            arrays = convert_csv_to_numpy_array(idx0, idx1, idx2)
            # arrays = remove_nan_data(arrays)
            ax.add_patch(std_ellipse(arrays[:, 0, 0], arrays[:, 0, 1]))
            ax.add_patch(std_ellipse(arrays[:, 1, 0], arrays[:, 1, 1]))
            a = (idx0 / 175 * 0.5) + 0.5
            b = (idx1 / 60 * 0.5) + 0.5
            color0 = (a, 0, 0.5)
            color1 = (0, b, 0.5)

            for data in arrays:
                # pos = data[0]
                # plt.scatter(arrays[:100, 0, 0], arrays[:100, 0, 1])
                plt.scatter(data[0][0], data[0][1], c=color0, s=3)
                plt.scatter(data[1][0], data[1][1], c=color1, s=3)

for idx0 in range(25, 175, 25):
    plt.scatter(20, idx0, c="blue", s=10)
    for idx1 in range(20, 60, 10):
        plt.scatter(idx1, idx0, c="red", s=10)


plt.show()


# 結果を表示
print(arrays[:6])
# for array in arrays:
#     print(array)
