import csv
import os
import logging
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import japanize_matplotlib  # 日本語対応のためのモジュール

# ログ設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)

# 日本語フォント（IPAexGothic）の指定とマイナス記号の対策
plt.rcParams["font.family"] = "IPAexGothic"
plt.rcParams["axes.unicode_minus"] = False


def convert_csv_to_numpy_array(arg0):
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    file_path = os.path.join(parent_dir, "data", "exp2_", f"{arg0}_estimated.csv")

    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            # 1列目の文字列から角括弧を除去してリスト化
            item0 = row[0].strip("[]")
            values = [float(n) for n in item0.split(", ")]
            # (45, arg0) と計測点との距離を算出
            dist0 = np.sqrt(((45 - values[0]) ** 2) + ((arg0 - values[1]) ** 2))
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


# 手入力で最大エラー率を設定（例: 36.67%）
manual_max_error = 36.67
manual_max_distance = 41.21  # 手入力の最大距離

# 表のデータ作成
data = []
success_rates = []  # 成功率のリスト
distance_means = []
idx_values = list(range(25, 175, 25))
# 列ラベル：各 idx 値（単位:mm）
collabels = [f"{idx}mm" for idx in idx_values]

for idx0 in idx_values:
    error_rate, error_count, distance_mean = convert_csv_to_numpy_array(idx0)
    # 成功率を算出：error_rate が 0% なら 100%、10% なら 90% となる
    if error_rate is not None:
        success_rate = 100 - error_rate
    else:
        success_rate = None
    data.append([success_rate, error_count, distance_mean])
    if success_rate is not None:
        success_rates.append(success_rate)
    if distance_mean is not None:
        distance_means.append(distance_mean)

# 成功率のカラーマッピング設定
# 成功率は error_rate が 0% のとき 100%、最大エラー率 36.67% のとき 100-36.67=63.33%
min_success = 100 - manual_max_error  # 63.33
norm_success = mcolors.Normalize(vmin=min_success, vmax=100)
# reversed（反転）した Reds カラーマップを使用することで、
# 成功率 100 のとき（norm=1）は薄い赤、63.33 のとき（norm=0）は濃い赤になります。
cmap_success = cm.Reds_r

# 距離のカラーマッピング設定はそのまま
norm_distance = mcolors.Normalize(vmin=min(distance_means), vmax=manual_max_distance)
cmap_distance = cm.Blues

# 図・軸の作成
fig, ax = plt.subplots()
ax.axis("off")

# 上部タイトルの設定（太字）
fig.suptitle("デバイスと円柱AのY軸方向の距離", fontsize=14, fontweight="bold", y=0.65)

# セルに表示する文字列（1行目：成功率、2行目：平均距離）
cell_text = [
    [f"{row[0]:.2f}%" if row[0] is not None else "N/A" for row in data],
    [f"{row[2]:.2f}mm" if row[2] is not None else "N/A" for row in data],
]

# テーブル作成（colLabelsは上部ラベル、cellLocはセル内中央寄せ）
table = ax.table(
    cellText=cell_text,
    colLabels=collabels,
    loc="center",
    cellLoc="center",
)

# セル背景色の設定
for i, row in enumerate(data):
    # 成功率のセル（cell_text の1行目、テーブル上は行インデックス 1）
    if row[0] is not None:
        # norm_success(row[0]) は 100 のとき 1、63.33 のとき 0
        # cmap_success（Reds_r）を使うと、0で濃い赤、1で薄い赤が得られる
        color = cmap_success(norm_success(row[0]) )  # 0.8は必要に応じて調整
        table[1, i].set_facecolor(color)
    # 平均距離のセル（cell_text の2行目、テーブル上は行インデックス 2）
    if row[2] is not None:
        color = cmap_distance(norm_distance(row[2]))
        table[2, i].set_facecolor(color)

# レイアウト調整（左右上下の余白を削減）
plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)

# テーブル書式の設定：フォントサイズ固定、全セルのテキストを太字に設定
table.auto_set_font_size(False)
table.set_fontsize(10)
for (row, col), cell in table.get_celld().items():
    cell.get_text().set_fontweight("bold")
    cell.set_height(0.08)

plt.show()
