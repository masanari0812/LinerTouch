import csv
import os
import logging
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)

def convert_csv_to_numpy_array(arg0):
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    file_path = os.path.join(parent_dir, "data", "exp2_", f"{arg0}_estimated.csv")

    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        result = []
        for row in reader:
            item0 = row[0].strip("[]")
            dist0 = np.sqrt(
                ((45 - [float(n) for n in item0.split(", ")][0]) ** 2)
                + ((arg0 - [float(n) for n in item0.split(", ")][1]) ** 2)
            )
            if len(row) != 1:
                error += 1
                continue
            result.append(dist0)

    with open(file_path, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)
        row_count = len(rows)

    error_rate = (error / row_count * 100) if row_count > 0 else None
    error_count = error
    distance_mean = np.mean(np.array(result)) if result else None

    return error_rate, error_count, distance_mean

# 手入力で最大値を設定
manual_max_error = 36.67  # 手入力の最大エラー率
manual_max_distance = 41.21  # 手入力の最大距離

# 表のデータ
data = []
error_rates = []
distance_means = []
idx_values = list(range(25, 175, 25))
collabels = [""] + [f"{idx}mm" for idx in idx_values]  # 先頭に空白を追加

for idx0 in idx_values:
    error_rate, error_count, distance_mean = convert_csv_to_numpy_array(idx0)
    data.append([error_rate, error_count, distance_mean])
    if error_rate is not None:
        error_rates.append(error_rate)
    if distance_mean is not None:
        distance_means.append(distance_mean)

# 色のスケールを定義
norm_error = mcolors.Normalize(vmin=min(error_rates), vmax=manual_max_error)
norm_distance = mcolors.Normalize(vmin=min(distance_means), vmax=manual_max_distance)
cmap_error = cm.Reds
cmap_distance = cm.Blues

# 表を作成
fig, ax = plt.subplots()
ax.axis("off")

# セルデータのフォーマットを変更
cell_text = [
    ["Error Rate"] + [f"{row[0]:.2f}%" if row[0] is not None else "N/A" for row in data],
    ["Distance Mean"] + [f"{row[2]:.2f}mm" if row[2] is not None else "N/A" for row in data]
]

# テーブル作成
table = ax.table(
    cellText=cell_text,
    colLabels=collabels,
    loc="center",
    cellLoc="center",
)

# セルの背景色を設定
for i, row in enumerate(data):
    if row[0] is not None:
        color = cmap_error(norm_error(row[0]) * 0.8)
        table[1, i + 1].set_facecolor(color)
    if row[2] is not None:
        color = cmap_distance(norm_distance(row[2]) * 0.8)
        table[2, i + 1].set_facecolor(color)

# レイアウト調整
plt.subplots_adjust(left=0.2, top=0.8)

# 表の書式設定
table.auto_set_font_size(False)
table.set_fontsize(10)

# セルの高さを調整
table.auto_set_column_width(col=list(range(len(collabels))))
for (row, col), cell in table.get_celld().items():
    cell.set_height(0.1)  # セル高さ調整

plt.show()
