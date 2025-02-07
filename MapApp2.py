import tkinter as tk
import logging

# tkintermapview をインストールしていない場合は
#   pip install tkintermapview
# が必要です
from tkintermapview import TkinterMapView

# 同じフォルダに置いた LinerTouch.py をインポート
from LinerTouch import LinerTouch

logger = logging.getLogger(__name__)


class MapApp:
    def __init__(self, master):
        self.master = master
        master.title("Map App with tkintermapview")

        # ログ出力の設定（必要に応じて）
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(name)s: %(message)s",
        )

        # ウィンドウサイズやキャンバスの大きさは任意に調整
        self.width = 800
        self.height = 600
        master.geometry(f"{self.width}x{self.height}")

        # tkintermapview のウィジェットを設置
        #  - corner_radius=0 にすると角丸なしのウィジェットとなります
        self.map_widget = TkinterMapView(
            master,
            width=self.width,
            height=self.height,
            corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True)

        # マップの初期位置やズームレベルを設定
        # 例: 東京駅付近
        self.map_widget.set_position(35.681236, 139.767125)  # lat, lon
        self.map_widget.set_zoom(12)

        # LinerTouch のインスタンス生成（変更はしない）
        self.liner = LinerTouch(
            update_callback=self.on_sensor_update,
            tap_callback=self.on_tap,
            plot_graph=False
        )

        # ピンチ関連のコールバック（2本指）
        self.liner.pinch_start_callback = self.on_pinch_start
        self.liner.pinch_motion_callback = self.on_pinch_motion
        self.liner.pinch_update_callback = self.on_pinch_update
        self.liner.pinch_end_callback = self.on_pinch_end

        # 1本指ドラッグ用: 前フレームの指位置(センサ座標)を記録
        self.last_single_finger_sensor_pos = None

    def on_sensor_update(self):
        """
        LinerTouchから1フレームごとに呼ばれるコールバック。
        1本指ならパン操作としてマップを移動する。
        """
        estimated_data = self.liner.estimated_data

        # 1本指の場合 → マップをパン（移動）
        if len(estimated_data) == 1:
            current_sensor_pos = estimated_data[0]  # [x, y]
            if self.last_single_finger_sensor_pos is not None:
                # 前フレームとの差分
                dx = current_sensor_pos[0] - self.last_single_finger_sensor_pos[0]
                dy = current_sensor_pos[1] - self.last_single_finger_sensor_pos[1]

                # dx, dy を適宜拡大してピクセル移動量に変換
                px = dx * 2
                py = -dy * 2  # Y方向を反転させたいなら -1

                # ピクセル移動分だけ地図の中心をずらす
                self.move_map_by_pixels(px, py)

            self.last_single_finger_sensor_pos = current_sensor_pos
        else:
            # 1本指以外の時はドラッグ位置をリセット
            self.last_single_finger_sensor_pos = None

    def move_map_by_pixels(self, px, py):
        """
        ピクセルの移動量 (px, py) だけ、地図の中心をシフトする。
        tkintermapview には move(px, py) が無いので、
        中心 (lat, lon) をキャンバス座標に直してから移動し、再度 (lat, lon) に戻す。
        """
        # 1) 現在の中心座標 (lat, lon) を取得
        center_lat, center_lon = self.map_widget.get_position()

        # 2) その中心をキャンバス上のピクセル座標に変換
        center_x, center_y = self.map_widget.get_canvas_position_from_coordinate(
            center_lat, center_lon
        )

        # 3) ピクセル移動量 (px, py) を足す
        new_center_x = center_x + px
        new_center_y = center_y + py

        # 4) 新しいピクセル座標を (lat, lon) に逆変換
        new_lat, new_lon = self.map_widget.get_coordinate_from_canvas_position(
            new_center_x, new_center_y
        )

        # 5) 再設定
        self.map_widget.set_position(new_lat, new_lon)

    def on_tap(self):
        """ タップ動作が検出されたときのコールバック """
        logger.info("Tap detected on the map!")

    # -------------------------------
    #  2本指ピンチ用コールバック群
    # -------------------------------
    def on_pinch_start(self, event=None):
        logger.info("Pinch Start")

    def on_pinch_motion(self, event=None):
        """
        2本指がドラッグ（中心座標が移動）したときに呼ばれる。
        今回の例ではパン操作は1本指に割り当てているので、ここでは何もしない。
        """
        pass

    def on_pinch_update(self, dist):
        """
        ピンチの拡大／縮小量が変化したときのコールバック
        dist が正 → 2本指が離れる(拡大)
        dist が負 → 2本指が近づく(縮小)
        """
        # あまり小さい dist なら無視
        if abs(dist) < 2.0:
            return

        current_zoom = self.map_widget.zoom
        if dist > 0:
            # 拡大方向
            new_zoom = current_zoom + 0.2
        else:
            # 縮小方向
            new_zoom = current_zoom - 0.2

        # tkintermapview のズームは小数点でもOK
        # 0～19 くらいまでが妥当。超えないよう制限
        new_zoom = max(0.0, min(new_zoom, 20.0))

        self.map_widget.set_zoom(new_zoom)
        logger.info(f"Pinch zoom => {new_zoom:.1f}")

    def on_pinch_end(self):
        logger.info("Pinch End")


if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
