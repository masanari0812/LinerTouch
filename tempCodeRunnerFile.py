
    # 指の本数を推測し最も誤差が少ない推定位置を利用
    def split_finger_data(self, range_data):
        # 指の極大値を格納
        range_data = np.array(range_data)
        if len(range_data) < 2:
            return
        max_idx = []
        range_x = range_data[:, 0]  # 1列目
        range_r = range_data[:, 1]  # 2列目
        for i in range(1, len(range_data) - 1):
            if range_r[i - 1] < range_r[i] > range_r[i + 1]:
                max_idx.append(i)
        # max_idxの要素数+1が指の本数になる
        # 極大値のセンサ値の左右に振り分け目的関数の誤差の合計が低い組み合わせを利用
        # 2^(極大値の数)回数試行しそのインデックスを2進数に変換し
        # 極大値と同じインデックスの桁数目の数によって左右どちらに振り分けるか決める
        # 極大値が4本でインデックスが0b0110の場合、左右右左となる。
        logger.info(max_idx)
        if len(max_idx) > 0:
            result = []
            for b in range(2 ** len(max_idx)):
                # 二進数の接頭辞の削除
                bits = bin(b)[2:]
                prev_idx = 0
                data = []
                for i in range(len(max_idx)):
                    # 左に
                    if bits[i] == "0":
                        data.append(range_data[prev_idx:i])
                        prev_idx = i + 1
                    # 右に
                    elif bits[i] == "1":
                        data.append(range_data[prev_idx : i - 1])
                        prev_idx = i
                    else:
                        logger.error("0と1以外の数字が来た")
                data.append(range_data[prev_idx:])
                result.append(data)
            err_val = []
            for data in result:
                val = 0
                for range_data in data:
                    val += self.filter_inv_solve(range_data).fun
                err_val.append(val)
                logger.info(f"err_val:{val}")
                logger.info(f"data:{data}")
        else:
            self.filter_inv_solve(range_data)