import matplotlib.pyplot as plt
import japanize_matplotlib
import matplotlib.cm as cm  # カラーマップを扱うため

# データの準備
labels = ["25mm", "50mm", "75mm", "100mm", "125mm", "150mm"]
averages = [13.72, 11.67, 12.94, 15.64, 18.39, 34.53]

# 累積平均の計算
cumulative_averages = []
cumulative_sum = 0
for i, val in enumerate(averages):
    cumulative_sum += val
    cum_avg = round(cumulative_sum / (i + 1), 2)
    cumulative_averages.append(cum_avg)

# 表示用テーブルデータの作成（数値に mm を付与）
table_data = [
    ["", *labels],
    ["平均", *[f"{a}mm" for a in averages]],
    ["累積平均", *[f"{ca}mm" for ca in cumulative_averages]],
]

# Figure、Axesの生成
fig, ax = plt.subplots(figsize=(8, 3))  # サイズは適宜調整してください
# 表の上部にタイトルとして配置（太字）
fig.suptitle(
    "デバイスと円柱A、BのY軸方向の距離", fontsize=14, fontweight="bold", y=0.75
)
# Axes上の目盛り等はオフにする
ax.axis("off")

# テーブルを作成して追加
table = ax.table(
    cellText=table_data,  # 表示する文字列の2次元リスト
    loc="center",  # 配置場所('center','upper','lower'など)
)

# フォントサイズやセルの大きさを調整（必要に応じて）
table.auto_set_font_size(False)
table.set_fontsize(12)

# 横方向のスケールを小さくしてセル幅を狭める
table.scale(1, 1.8)  # (横方向の拡大率, 縦方向の拡大率)

# ----------------------------------------------------------------------
# ここからセルの色付けを行う処理
# ----------------------------------------------------------------------
all_values = averages + cumulative_averages
min_val, max_val = min(all_values), 41.21

# セルごとに値を取得し、正規化して色付け（行:1,2 列:1～len(labels)）
for row_idx in [1, 2]:
    for col_idx in range(1, len(labels) + 1):
        # 文字列（"13.72mm" のような形）から数値部分を取り出して float 化
        val_str = table_data[row_idx][col_idx]
        numeric_val = float(val_str.replace("mm", ""))  # "mm" を除去してから変換
        # 0～1に正規化
        norm = (numeric_val - min_val) / (max_val - min_val)
        # カラーマップBluesの 0.2～0.8 の範囲を使用して淡めに
        color = cm.Blues(0.2 + 0.6 * norm)
        table.get_celld()[(row_idx, col_idx)].set_facecolor(color)

plt.show()
