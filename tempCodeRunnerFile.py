
    # def get_touch(self):
    #     # 指のタッチ検知
    #     if self.ready:
    #         # if self.tap_flag:
    #         #     self.next_pos = self.release_pos
    #         #     # タップ検知の時間閾値を超えた場合
    #         #     if (
    #         #         time.time() - release_start_time
    #         #         > self.release_threshold
    #         #     ):
    #         #         self.tap_flag = False
    #         # 指が離れた場合
    #         latest_pos = self.get_pastdata("estimated_pos")[0]
    #         if (
    #             self.min_pos[1] - self.prev_min_pos[1] > self.height_threshold
    #             and self.tap_flag == False
    #         ):
    #             self.release_start_time = time.time()
    #             self.tap_flag = True
    #             # タッチ予定の座標を記録
    #             self.release_pos = self.estimated_pos.copy()

    #         # タップのフラグがある場合
    #         if self.tap_flag == True:
    #             # 指が押されていない場合離した際の座標release_posを利用
    #             self.estimated_pos = self.release_pos.copy()

    #             # 指が押された場合
    #             if self.prev_min_pos[1] - self.min_pos[1] > self.height_threshold:

    #                 self.release_end_time = time.time()
    #                 release_elapsed_time = (
    #                     self.release_end_time - self.release_start_time
    #                 )
    #                 if release_elapsed_time <= self.release_threshold:
    #                     self.tap_flag = False
    #                     if self.tap_callback:
    #                         self.tap_callback()
    #             else:
    #                 # タッチ時間の閾値を超えた場合フラグをオフにする処理
    #                 if time.time() - self.release_start_time > self.release_threshold:
    #                     self.tap_flag = False
    #                 # 指が押されていない間は最後に離した際の座標release_posを利用
    #         logger.debug(f"tap_flag: {self.tap_flag}")