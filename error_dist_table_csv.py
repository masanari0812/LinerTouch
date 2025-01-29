import csv
import os
import logging
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # DEBUGレベルを含む全てのログを表示
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",  # フォーマットの設定
)


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
                dist0 = np.sqrt(
                    ((20 - [float(n) for n in item0.split(", ")][0]) ** 2)
                    + ((arg0 - [float(n) for n in item0.split(", ")][1]) ** 2)
                )
                temp.append(dist0)
                item1 = row[1].strip("[]")  # "[]"を削除
                dist1 = np.sqrt(
                    ((20 + arg1 - [float(n) for n in item1.split(", ")][0]) ** 2)
                    + ((arg0 - [float(n) for n in item1.split(", ")][1]) ** 2)
                )
                temp.append(dist1)
            except IndexError:
                # 要素数が2つ未満の行をスキップ
                error += 1
                continue

            # tempが2つの要素を持っていることを確認
            if len(temp) == 2:
                result.append(temp)

    # logger.info(f"error {arg0:3.0f}+{arg1:3.0f}:{error:3.0f}")
    # NumPy配列に変換
    return f"{np.mean(np.array(result)):.2f}mm"


# 表のデータ
data = []
rowlabels = []
for idx0 in range(25, 175, 25):
    rowlabels.append(idx0)
    temp = []
    collabels = []
    for idx1 in range(20, 60, 10):
        collabels.append(idx1)
        for idx2 in range(1):
            arrays = convert_csv_to_numpy_array(idx0, idx1, idx2)
            temp.append(arrays)
    data.append(temp)

logger.info(data)

# 表を作成

fig, ax = plt.subplots()

ax.axis("off")

table = ax.table(
    cellText=data,
    colLabels=collabels,
    rowLabels=rowlabels,
    loc="center",
)  # x, y, width, height

# Text above columns

fig.text(
    0.5,
    0.95,
    "Distance between cylinders",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold",
)


# Text left of rows

fig.text(
    0.05,
    0.5,
    "Distance between \nsensor and cylinder",
    ha="center",
    va="center",
    fontsize=16,
    fontweight="bold",
    rotation="vertical",
)


# Adjust layout for better spacing

plt.subplots_adjust(left=0.2, top=0.8)

# 表の書式設定

table.auto_set_font_size(False)

table.set_fontsize(12)


plt.show()
