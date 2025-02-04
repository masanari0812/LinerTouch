import numpy as np
import csv
import os
import logging
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse
import japanize_matplotlib  # 日本語表示対応

# ログの設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # DEBUG含む全ログ表示
    format="[%(levelname)s] %(name)s:%(lineno)d:%(message)s",
)

# 日本語フォント設定（IPAexGothic）とマイナス記号対策
plt.rcParams["font.family"] = "IPAexGothic"
plt.rcParams["axes.unicode_minus"] = False


def std_ellipse(x, y, n_std=1):
    """
    点群データ x, y から標準偏差の楕円を生成する関数

    Args:
        x (np.array): x座標の配列
        y (np.array): y座標の配列
        n_std (float): 標準偏差の倍率（デフォルトは1）

    Returns:
        matplotlib.patches.Ellipse: 楕円オブジェクト
    """
    cov = np.cov(x, y)
    eigenvalues, eigenvectors = np.linalg.eig(cov)
    angle = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(eigenvalues)
    ellipse = Ellipse(
        xy=(np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=angle,
        facecolor="none",
        edgecolor="black",
    )
    return ellipse


def convert_csv_to_numpy_array(arg0, arg1=0, arg2=0):
    """
    CSVファイルから文字列データを読み込み、最初の2要素をfloatに変換してnp.arrayにする関数

    CSVの例: "[14.80, 99.29]"

    Args:
        arg0: CSVファイル名の一部（例: 25, 50, ...）
        arg1: （未使用）
        arg2: （未使用）

    Returns:
        np.array: 変換された数値データの配列
    """
    result = []
    current_file = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file)
    file_path = os.path.join(parent_dir, "data", "exp2_", f"{arg0}_estimated.csv")
    error = 0
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            # 1列のみの場合を想定
            if len(row) == 1:
                item0 = row[0].strip("[]")
                try:
                    result.append([float(n) for n in item0.split(", ")])
                except Exception as e:
                    error += 1
                    continue
            else:
                error += 1
                continue
    logger.info(f"error {arg0:3.0f}+{arg1:3.0f}:{error:3.0f}")
    return np.array(result)


# カラーパレット（idx0毎に色分け）
warm_colors = ["red", "orange", "gold", "green", "blue", "purple"]

# プロット用の図と軸を作成
fig, ax = plt.subplots()
# 表の上部にタイトルとして配置（太字）
ax.set_xlim(-10, 100)  # X軸の範囲
ax.set_ylim(0, 200)  # Y軸の範囲

# 各CSVから読み込んだ点群のx, y値を全体で収集するためのリスト
all_x = []
all_y = []

ellipseA = []  # 各グループの楕円を保持

# --- ① 点群データのプロット ---
for idx0 in range(25, 175, 25):
    arrays = convert_csv_to_numpy_array(idx0)
    if arrays.size == 0:
        continue
    # 点群の各座標を全体リストに追加
    all_x.extend(arrays[:, 0].tolist())
    all_y.extend(arrays[:, 1].tolist())

    # 色の選定（idx0に応じた色）
    color0 = warm_colors[(idx0 // 25) % len(warm_colors)]
    for data in arrays:
        ax.scatter(data[0], data[1], c=color0, s=3, alpha=0.7)

# --- ② 平均点への線分と楕円の描画 ---
for idx0 in range(25, 175, 25):
    arrays = convert_csv_to_numpy_array(idx0)
    if arrays.size == 0:
        continue
    # CSVデータが存在する場合、開始点(45, idx0)を追加
    all_x.append(45)
    all_y.append(idx0)

    start_point = (45, idx0)
    end_point = (np.mean(arrays[:, 0]), np.mean(arrays[:, 1]))

    # 始点から各グループの平均点へ線を描画
    ax.plot(
        [start_point[0], end_point[0]], [start_point[1], end_point[1]], color="black"
    )

    # 点群から標準偏差の楕円を生成して保存
    ellipse = std_ellipse(arrays[:, 0], arrays[:, 1], n_std=1)
    ellipseA.append(ellipse)

    # 始点を目立たせるために散布図でプロット
    ax.scatter(45, idx0, c="black", s=40)

# 各楕円をプロット
for ellipse in ellipseA:
    ax.add_patch(ellipse)
plt.xlabel("横軸(X軸)の座標(mm)", fontsize=14, fontweight="bold")
plt.ylabel("縦軸(Y軸)の座標(mm)", fontsize=14, fontweight="bold")

plt.show()
