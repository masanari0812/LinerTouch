import numpy as np
import csv
import os
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


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
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        result = []
        for row in reader:
            temp = []
            for idx in range(2):
                try:
                    # "[14.801996614908228, 99.29362065281744]"のような文字列を処理
                    item = row[idx].strip("[]")  # "[]"を削除
                    temp.append([float(n) for n in item.split(", ")])
                except IndexError:
                    temp.append([np.nan, np.nan])
            result.append(temp)

        # NumPy配列に変換
    return np.array(result)


# 変換を実行
for idx0 in range(25, 75, 25):
    for idx1 in range(20, 60, 10):
        for idx2 in range(1):
            arrays = convert_csv_to_numpy_array(idx0, idx1, idx2)
            r = random.random()  # 0.0 から 1.0 の間のランダムな浮動小数点数
            g = random.random()
            b = random.random()
            color = (r, g, b)
            # arrays[:100,0,0]
            for data in arrays[:100]:
                # pos = data[0]
                # plt.scatter(arrays[:100, 0, 0], arrays[:100, 0, 1])
                if np.isnan(data[1][0]) and np.isnan(data[1][1]):
                    # print(data)
                    pass
                else:
                    plt.scatter(data[0][0] - 20, data[0][1] - idx0, c=color, s=3)
plt.show()


# 結果を表示
print(arrays[:6])
# for array in arrays:
#     print(array)
