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

def convert_csv_to_numpy_array(arg0, arg1, arg2=0):
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    file_path = os.path.join(
        parent_dir, "data", "exp1_", f"{arg0}+{arg1}x{arg2}_estimated.csv"
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
    
    error_rate = (error / row_count * 100) if row_count > 0 else None
    error_count = error
    distance_mean = np.mean(np.array(result)) if result else None
    
    return error_rate, error_count, distance_mean

# 表のデータ
data = []
error_rates = []
distance_means = []
collabels = []
rowlabels = []
for idx1 in range(20, 60, 10):  # arg1 を縦方向に
    rowlabels.append(f"{idx1}mm")
    rowlabels.append("")  # 2行分の高さを確保
    temp = []
    for idx0 in range(25, 175, 25):  # arg0 を横方向に
        if idx1 == 20:
            collabels.append(f"{idx0}mm")
        error_rate, error_count, distance_mean = convert_csv_to_numpy_array(idx0, idx1)
        temp.append([error_rate, error_count, distance_mean])
        if error_rate is not None:
            error_rates.append(error_rate)
        if distance_mean is not None:
            distance_means.append(distance_mean)
    data.append(temp)

# 色のスケールを定義
norm_error = mcolors.Normalize(vmin=min(error_rates), vmax=max(error_rates))
norm_distance = mcolors.Normalize(vmin=min(distance_means), vmax=max(distance_means))
cmap_error = cm.Reds
cmap_distance = cm.Blues

# 表を作成
fig, ax = plt.subplots()
ax.axis("off")

# セルデータのフォーマットを変更（2行分のデータを用意）
cell_text = []
for row in data:
    cell_row1 = []
    cell_row2 = []
    for error_rate, error_count, distance_mean in row:
        cell_row1.append(f"{error_rate:.2f}%" if error_rate is not None else "N/A")
        cell_row2.append(f"{distance_mean:.2f}mm" if distance_mean is not None else "N/A")
    cell_text.append(cell_row1)
    cell_text.append(cell_row2)

# テーブル作成
table = ax.table(
    cellText=cell_text,
    colLabels=collabels,
    rowLabels=rowlabels,
    loc="center",
    cellLoc="center",
)

# セルの背景色を設定
for i, row in enumerate(data):
    for j, (error_rate, _, distance_mean) in enumerate(row):
        if error_rate is not None:
            color = cmap_error(norm_error(error_rate) * 0.8)
            table[i * 2, j].set_facecolor(color)
        if distance_mean is not None:
            color = cmap_distance(norm_distance(distance_mean) * 0.8)
            table[i * 2 + 1, j].set_facecolor(color)

# レイアウト調整
plt.subplots_adjust(left=0.2, top=0.8)

# 表の書式設定
table.auto_set_font_size(False)
table.set_fontsize(10)

# セルの高さを調整
table.auto_set_column_width(col=list(range(len(collabels))))
for (row, col), cell in table.get_celld().items():
    if col == -1:  # Row labels
        cell.set_height(0.16)  # 2行分の高さ
    else:
        cell.set_height(0.08)  # 通常のセル高さ

plt.show()
