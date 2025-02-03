import csv
import os
import logging
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)


def convert_csv_to_numpy_array(arg0, arg1, arg2=0):
    """
    CSVファイルからデータを読み込み、エラー率、エラー回数、距離の平均を計算する関数

    Args:
        arg0: センサーとシリンダー間の距離
        arg1: シリンダー間の距離
        arg2: 使用されていません (デフォルトは0)

    Returns:
        tuple: (エラー率, エラー回数, 距離の平均)
    """
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    value0 = arg0
    value1 = arg1
    value2 = arg2
    file_path = os.path.join(
        parent_dir, "data", "exp1_", f"{value0}+{value1}x{value2}_estimated.csv"
    )

    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        result = []
        for row in reader:
            temp = []
            try:
                item0 = row[0].strip("[]")
                dist0 = np.sqrt(
                    ((20 - [float(n) for n in item0.split(", ")][0]) ** 2)
                    + ((arg0 - [float(n) for n in item0.split(", ")][1]) ** 2)
                )
                temp.append(dist0)
                item1 = row[1].strip("[]")
                dist1 = np.sqrt(
                    ((20 + arg1 - [float(n) for n in item1.split(", ")][0]) ** 2)
                    + ((arg0 - [float(n) for n in item1.split(", ")][1]) ** 2)
                )
                temp.append(dist1)
            except IndexError:
                error += 1
                continue

            if len(temp) == 2:
                result.append(temp)
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)
        row_count = len(rows)
    error_rate = f"{error / row_count * 100:.2f}%" if row_count > 0 else "N/A"
    error_count = f"{error}"
    distance_mean = f"{np.mean(np.array(result)):.2f}mm" if result else "N/A"

    return error_rate, error_count, distance_mean


# 表のデータ
data = []
rowlabels = []
for idx0 in range(25, 175, 25):
    rowlabels.append(idx0)
    temp = []
    collabels = []
    for idx1 in range(20, 60, 10):
        collabels.append(idx1)
        error_rate, error_count, distance_mean = convert_csv_to_numpy_array(idx0, idx1)
        temp.append([error_rate, error_count, distance_mean])
    data.append(temp)

# 表を作成
fig, ax = plt.subplots()
ax.axis("off")

# セルデータのフォーマットを変更
cell_text = []
for row in data:
    cell_row = []
    for error_rate, error_count, distance_mean in row:
        cell_row.append(f"{error_rate}\n({error_count})\n{distance_mean}")
    cell_text.append(cell_row)

table = ax.table(
    cellText=cell_text,
    colLabels=collabels,
    rowLabels=rowlabels,
    loc="center",
    cellLoc="center",
)

# Text above columns
fig.text(
    0.5,
    0.95,
    "Distance between cylinders (n=300)",
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
table.set_fontsize(10)

# セルの高さを自動調整
table.auto_set_column_width(col=list(range(len(collabels))))
for (row, col), cell in table.get_celld().items():
    # if row == 0 or col == -1:
        # continue  # Header and row labels are skipped
    cell.set_height(0.15)  # 高さをさらに調整

plt.show()
