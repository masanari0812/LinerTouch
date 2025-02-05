import csv
import os
import logging
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import japanize_matplotlib

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)

plt.rcParams['font.family'] = 'IPAexGothic'
plt.rcParams['axes.unicode_minus'] = False

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
                # 1列目のデータから距離を算出
                item0 = row[0].strip("[]")
                dist0 = np.sqrt(
                    ((20 - [float(n) for n in item0.split(", ")][0]) ** 2)
                    + ((arg0 - [float(n) for n in item0.split(", ")][1]) ** 2)
                )
                temp.append(dist0)
                # 2列目のデータから距離を算出
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

# 手入力の最大エラー率（例：36.67%）を用いて、成功率の下限を設定
manual_max_error = 36.67  
min_success = 100 - manual_max_error  # 現状は63.33%

# === カスタム正規化クラス ===
class CustomNormalize(mcolors.Normalize):
    """
    デフォルトの正規化結果 (0～1) を [lower, upper] の範囲に再マッピングする。
    lower=0 だと元の最小値に対応し、upper=1 だと元の最大値に対応するが、
    これらを変更することで端点の色合いを調整できる。
    """
    def __init__(self, vmin=None, vmax=None, lower=0.0, upper=1.0, clip=False):
        super().__init__(vmin, vmax, clip)
        self.lower = lower
        self.upper = upper

    def __call__(self, value, clip=None):
        # まず通常のNormalizeで 0～1 にする
        normalized = super().__call__(value, clip)
        # その後 [lower, upper] の範囲に線形マッピング
        return self.lower + normalized * (self.upper - self.lower)

# 表のデータ生成
data = []
success_rates = []  # 成功率を格納するリスト
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
        if error_rate is not None:
            success_rate = 100 - error_rate
        else:
            success_rate = None
        temp.append([success_rate, error_count, distance_mean])
        if success_rate is not None:
            success_rates.append(success_rate)
        if distance_mean is not None:
            distance_means.append(distance_mean)
    data.append(temp)

# カラーマップの定義
# 成功率：100%なら白（極薄）、下限（現状63.33%）よりは少し明るめにするため [0.3, 1.0] の範囲にマッピング
norm_success = CustomNormalize(vmin=min_success, vmax=100, lower=0.3, upper=1.0)
cmap_success = cm.Reds_r  # reversed Reds: 0→濃い赤、1→薄い赤(白寄り)

# 距離：最小値は（通常）0が白、最大値は最大値に対して1だと濃い青になってしまうので、最大値を
# 1未満、例えば0.8にすることで若干薄くする
norm_distance = CustomNormalize(vmin=min(distance_means), vmax=max(distance_means), lower=0.0, upper=0.8)
cmap_distance = cm.Blues

# テーブル作成用の図・軸設定
fig, ax = plt.subplots()

fig.suptitle("デバイスと円柱A、BのY軸方向の距離",
             fontsize=14, fontweight='bold', y=0.80)
fig.text(0.1, 0.5, "円柱A, B間のX軸方向の距離",
         rotation=90, ha="center", va="center",
         fontsize=15, fontweight='bold')
ax.axis("off")

# セルデータのフォーマット（1行目：成功率、2行目：平均距離）
cell_text = []
for row in data:
    cell_row1 = []
    cell_row2 = []
    for success_rate, _, distance_mean in row:
        cell_row1.append(f"{success_rate:.2f}%" if success_rate is not None else "N/A")
        cell_row2.append(f"{distance_mean:.2f}mm" if distance_mean is not None else "N/A")
    cell_text.append(cell_row1)
    cell_text.append(cell_row2)

table = ax.table(
    cellText=cell_text,
    colLabels=collabels,
    rowLabels=rowlabels,
    loc="center",
    cellLoc="center",
)

# セルごとに背景色を設定
# 成功率のセル：norm_success によって 100% が 1（白寄り）、下限側は 0.3（やや赤味）
for i, row in enumerate(data):
    for j, (success_rate, _, distance_mean) in enumerate(row):
        if success_rate is not None:
            color = cmap_success(norm_success(success_rate))
            table[i * 2 + 1, j].set_facecolor(color)
        if distance_mean is not None:
            color = cmap_distance(norm_distance(distance_mean))
            table[i * 2 + 2, j].set_facecolor(color)

plt.subplots_adjust(left=0.2, top=0.85)
table.auto_set_font_size(False)
table.set_fontsize(10)

for (row, col), cell in table.get_celld().items():
    cell.get_text().set_fontweight('bold')
    cell.set_height(0.08)

plt.show()
