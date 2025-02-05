import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import japanize_matplotlib
# -------------------------
# 設定パラメータ
# -------------------------
# デバイス（入力領域）のサイズ（単位：mm）
width = 90    # X軸最大値
height = 160  # Y軸最大値

# 軸の目盛り設定
xticks = list(range(0, width + 1, 10))  # X軸: 0,10,...,90
# Y軸は25mm間隔、最大値160を含める
yticks = list(range(0, height, 25))
if height not in yticks:
    yticks.append(height)

# 実験2での配置パラメータ
# 円柱A, Bの共通のY座標候補
y_positions = [25, 50, 75, 100, 125, 150]
# 円柱BのX座標は、円柱AのX=20からのオフセットとして
x_offsets = [20, 30, 40, 50]

# 円柱（指に見立てた）の半径（mm）
finger_radius = 5

# 全配置（各フレーム）のリストを作成（6×4=24通り）
configs = []
for y in y_positions:
    for off in x_offsets:
        config = {
            'A': (20, y),           # 円柱Aは常にX=20
            'B': (20 + off, y)      # 円柱Bは円柱Aからoffだけ右に配置
        }
        configs.append(config)

# -------------------------
# 描画の準備
# -------------------------
fig, ax = plt.subplots(figsize=(5, 7.5))
ax.set_xlim(0, width)
ax.set_ylim(0, height)

# タイトルを削除する場合は以下をコメントアウトまたは削除
# ax.set_title("実験2: 円柱A, Bの配置", fontsize=14)

# 軸目盛りの設定（フォントサイズ大きく）
ax.set_xticks(xticks)
ax.set_yticks(yticks)
ax.tick_params(labelsize=14)
ax.grid(True)

# アスペクト比を等しく設定
ax.set_aspect('equal', adjustable='box')

# デバイス領域（方眼紙の領域）を表す矩形を追加
device_rect = patches.Rectangle((0, 0), width, height,
                                fill=False, linestyle='--', edgecolor='gray')
ax.add_patch(device_rect)

# 円柱A, Bを表すCircleパッチを生成
circleA = plt.Circle((0, 0), finger_radius, color='blue', alpha=0.6)
circleB = plt.Circle((0, 0), finger_radius, color='red', alpha=0.6)
ax.add_patch(circleA)
ax.add_patch(circleB)

# 各円のラベルのテキストオブジェクトを生成
# 円柱A：青丸の左上に配置（右寄せ）
textA = ax.text(0, 0, "円柱A", fontsize=14, color="blue",
                ha="right", va="bottom")
# 円柱B：赤丸の右上に配置（左寄せ）
textB = ax.text(0, 0, "円柱B", fontsize=14, color="red",
                ha="left", va="bottom")

# -------------------------
# アニメーション作成用の関数
# -------------------------
def init():
    """アニメーション初期化用関数"""
    first_config = configs[0]
    # 円の位置を初期化
    circleA.center = first_config['A']
    circleB.center = first_config['B']
    # テキストの位置を更新（円の半径分オフセット）
    textA.set_position((first_config['A'][0] - finger_radius,
                         first_config['A'][1] + finger_radius))
    textB.set_position((first_config['B'][0] + finger_radius,
                         first_config['B'][1] + finger_radius))
    return circleA, circleB, textA, textB

def animate(i):
    """フレームiを描画する関数"""
    config = configs[i]
    # 円の位置更新
    circleA.center = config['A']
    circleB.center = config['B']
    # 各円に合わせてテキストの位置を更新
    textA.set_position((config['A'][0] - finger_radius,
                        config['A'][1] + finger_radius))
    textB.set_position((config['B'][0] + finger_radius,
                        config['B'][1] + finger_radius))
    return circleA, circleB, textA, textB

# アニメーション作成（各フレーム800msに設定）
ani = animation.FuncAnimation(fig, animate, frames=len(configs),
                              init_func=init, blit=True, interval=800)

# GIFとして保存 (fpsは1000/800 ≒ 1.25)
ani.save("experiment2_configurations.gif", writer="pillow", fps=1000/800)

plt.show()
