import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from numba import jit

@jit
def mandelbrot(c, max_iter):
    """
    マンデルブロ集合を計算する関数

    Args:
      c: 複素数
      max_iter: 最大反復回数

    Returns:
      発散するまでの反復回数
    """
    z = 0
    n = 0
    while abs(z) <= 2 and n < max_iter:
        z = z * z + c
        n += 1
    return n

def create_fractal(min_x, max_x, min_y, max_y, image_size, max_iter):
    """
    マンデルブロ集合を画像として生成する関数

    Args:
      min_x: x軸の最小値
      max_x: x軸の最大値
      min_y: y軸の最小値
      max_y: y軸の最大値
      image_size: 画像サイズ (タプル)
      max_iter: 最大反復回数

    Returns:
      マンデルブロ集合の画像 (NumPy配列)
    """
    height, width = image_size
    pixel_size_x = (max_x - min_x) / width
    pixel_size_y = (max_y - min_y) / height
    x, y = np.mgrid[min_x:max_x:pixel_size_x, min_y:max_y:pixel_size_y]
    c = x + y * 1j
    fractal = np.frompyfunc(mandelbrot, 2, 1)(c, max_iter).astype(np.float64)
    return fractal


def zoom_fractal(fractal, center_x, center_y, zoom_level, image_size):
    """
    マンデルブロ集合をズームする関数

    Args:
      fractal: ズーム前のマンデルブロ集合の画像 (NumPy配列)
      center_x: ズーム中心のx座標
      center_y: ズーム中心のy座標
      zoom_level: ズームレベル
      image_size: 画像サイズ (タプル)

    Returns:
      ズーム後のマンデルブロ集合の画像 (NumPy配列)
    """
    height, width = image_size
    x_range = 3 / zoom_level
    y_range = 3 / zoom_level
    min_x = center_x - x_range / 2
    max_x = center_x + x_range / 2
    min_y = center_y - y_range / 2
    max_y = center_y + y_range / 2
    zoomed_fractal = create_fractal(min_x, max_x, min_y, max_y, image_size, 1000)
    return zoomed_fractal


def update(frame):
    """
    アニメーションのフレームを更新する関数

    Args:
      frame: フレーム番号

    Returns:
      更新された画像
    """
    global zoom_level, center_x, center_y
    zoom_level *= 1.05  # ズームレベルを徐々に増加
    zoomed_fractal = zoom_fractal(fractal, center_x, center_y, zoom_level, image_size)
    img.set_array(zoomed_fractal)
    return (img,)


# 初期設定
image_size = (500, 500)
fractal = create_fractal(-2.0, 1.0, -1.5, 1.5, image_size, 1000)
center_x = -0.75  # ズーム中心のx座標
center_y = 0.0  # ズーム中心のy座標
zoom_level = 1  # 初期ズームレベル

# アニメーションの設定
fig = plt.figure()
img = plt.imshow(fractal, cmap="hot", interpolation="nearest")
ani = FuncAnimation(fig, update, frames=range(1000), interval=50, blit=True)

# アニメーションの表示
plt.show()
