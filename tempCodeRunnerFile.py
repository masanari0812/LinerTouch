
        # if self.get_pastdata("len") == self.past_data_num:
        #     smooth_range_dic = {}
        #     for i in range(self.sensor_num):
        #         smooth_range_dic[f"sum{i*self.sensor_ratio}"] = 0
        #         smooth_range_dic[f"num{i*self.sensor_ratio}"] = 0
        #     for data1 in self.get_pastdata("actual_data"):
        #         for data2 in data1:
        #             smooth_range_dic[f"sum{data2[0]}"] += data2[1]
        #             smooth_range_dic[f"num{data2[0]}"] += 1
        #     smooth_range_ave_dic = {}
        #     for i in range(self.sensor_num):
        #         if smooth_range_dic[f"num{i * self.sensor_ratio}"] > 0:
        #             smooth_range_ave_dic[i * self.sensor_ratio] = (
        #                 smooth_range_dic[f"sum{i * self.sensor_ratio}"]
        #                 / smooth_range_dic[f"num{i * self.sensor_ratio}"]
        #             )
        #     smooth_range_data = []
        #     for idx, value in self.range_data:
        #         smooth_range_data.append([idx, int(smooth_range_ave_dic[idx])])
        #     # 平均値を計算
        #     self.split_x_data(smooth_range_data)

        # else:
        