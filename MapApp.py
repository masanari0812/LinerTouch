import tkinter as tk
import logging
import math
import os
from PIL import Image, ImageTk

# LinerTouch クラスをインポート（同じフォルダ内に LinerTouch.py がある想定）
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)


class MapApp:
    def __init__(self, master):
        self.master = master
        master.title("Map App (Single-finger pan & Two-finger pinch)")

        # ログ出力設定
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(name)s: %(message)s",
        )

        # マップ画像（適当な画像ファイルを指定してください）
        # 例として "map.png" がカレントディレクトリにあるとします
        self.map_image_path = "map.png"
        if not os.path.exists(self.map_image_path):
            # 画像がない場合は、仮の単色イメージを生成します
            from PIL import ImageDraw
            dummy_img = Image.new("RGB", (600, 400), (180, 180, 220))
            draw = ImageDraw.Draw(dummy_img)
            draw.text((50, 50), "No map.png found!", fill=(0, 0, 0))
            dummy_img.save(self.map_image_path)

        self.original_map_image = Image.open(self.map_image_path)
        self.map_scale = 1.0  # マップの拡大率
        self.map_offset_x = 0.0  # マップのオフセット（横方向）
        self.map_offset_y = 0.0  # マップのオフセット（縦方向）

        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas = tk.Canvas(
            master, width=self.canvas_width, height=self.canvas_height, bg="white"
        )
        self.canvas.pack()

        # LinerTouch のインスタンス作成
        #   - plot_graph=False: センサの生データなどの matplotlib 表示をオフ
        #   - update_callback: センサの推定座標が更新されるたびに呼ばれる関数
        #   - tap_callback: タップ検出時のコールバック（用途に応じて実装可）
        self.liner = LinerTouch(
            update_callback=self.on_update,   # フレームごとの更新
            tap_callback=self.on_tap,         # （必要に応じて使用）
            plot_graph=False
        )
        # ピンチのコールバック
        self.liner.pinch_start_callback = self.on_pinch_start
        self.liner.pinch_motion_callback = self.on_pinch_motion
        self.liner.pinch_update_callback = self.on_pinch_update
        self.liner.pinch_end_callback = self.on_pinch_end

        # 1本指ドラッグ用：最後の指位置を記録
        self.last_single_finger_pos = None

        # 初回のマップ描画
        self.draw_map()

    def draw_map(self):
        """
        マップ画像を現在の self.map_scale, self.map_offset_x, self.map_offset_y
        に基づいてキャンバス上に描画する
        """
        # 画像を拡大／縮小
        width = int(self.original_map_image.width * self.map_scale)
        height = int(self.original_map_image.height * self.map_scale)
        resized = self.original_map_image.resize((width, height), Image.LANCZOS)
        self.map_tk = ImageTk.PhotoImage(resized)

        # キャンバスをクリアして描画
        self.canvas.delete("all")
        self.canvas.create_image(
            self.map_offset_x, self.map_offset_y,
            anchor="nw",   # 左上を基準
            image=self.map_tk,
        )

    def sensor_to_canvas_coordinates(self, pos):
        """
        センサ座標 (liner推定の x,y ) → キャンバス座標系 への変換
        例: センサ横幅・高さに応じて正規化してキャンバスへマッピングする等、
            アプリ独自に決めてください。
        ここでは単純に「センサ x=range_data, y=height」を canvas_x, canvas_y として
        スケーリング例を挙げます
        """
        sensor_max_x = self.liner.sensor_num * self.liner.sensor_ratio  # センサの論理最大幅
        sensor_max_y = self.liner.sensor_height

        # キャンバス幅高さへ合わせるスケーリング
        if sensor_max_x == 0 or sensor_max_y == 0:
            return (0, 0)

        canvas_x = (pos[0] / sensor_max_x) * self.canvas_width
        canvas_y = self.canvas_height - (pos[1] / sensor_max_y) * self.canvas_height
        return canvas_x, canvas_y

    def on_update(self):
        """
        LinerTouch から 1フレームごとに呼ばれるコールバック。
        ここでは、1本指の場合にマップをドラッグする処理を行う。
        """
        estimated_data = self.liner.estimated_data
        if len(estimated_data) == 1:
            # 1本指ならパン操作とみなす
            current_pos_sensor = estimated_data[0]
            current_pos_canvas = self.sensor_to_canvas_coordinates(current_pos_sensor)

            if self.last_single_finger_pos is not None:
                # 前フレームとの差分をマップオフセットに加算し、移動
                dx = current_pos_canvas[0] - self.last_single_finger_pos[0]
                dy = current_pos_canvas[1] - self.last_single_finger_pos[1]
                self.map_offset_x += dx
                self.map_offset_y += dy
                self.draw_map()
            self.last_single_finger_pos = current_pos_canvas
        else:
            # 1本指以外のときはドラッグ座標をリセット
            self.last_single_finger_pos = None

    def on_tap(self):
        """
        タップ検出時に呼ばれるコールバック。
        必要に応じて処理を実装（ピンを立てる、情報を表示するなど）
        """
        logger.info("Tap detected on map!")

    # ===== ピンチ用コールバック群 =====
    def on_pinch_start(self, event=None):
        """2本指が新たに検出された時（ピンチ開始）"""
     
