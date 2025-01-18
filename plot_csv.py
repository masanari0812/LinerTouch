import numpy as np
import csv
import os


def convert_csv_to_numpy_array():
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
    value0 = 50
    value1 = 20
    value2 = 0
    file_path = os.path.join(
        parent_dir, "data", "exp1", f"{value0}+{value1}x{value2}.csv"
    )

    with open(file_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            data = row[:2]  # 最初の2つの要素を取得
            temp = []
            for item in data:
                try:
                    # "[", "]" を削除し、"," で分割してfloatに変換
                    temp.append([float(x) for x in item.strip("[]").split(",")])
                except ValueError:
                    # "[]" の場合は空のリストを追加
                    temp.append([])
            result.append(np.array(temp))
    return result


# 変換を実行
arrays = convert_csv_to_numpy_array()

# 結果を表示
print(arrays[2])
# for array in arrays:
#     print(array)
