
import math

from gen_lapsim.spline_track import track, curve
from models.car_model import car
import numpy as np


class Track_Examine:

    def __init__(self, track_txt_path=""):
        self.racecar = car()

        # self.run_accel(self.racecar, 5000, False)
        # self.racecar.plot_forces()
        # self.run_endurance(self.racecar, 5000)
        # self.racecar.calculate_RPM_percentage()
        # self.racecar.drivetrain.engn_rpm_pwr_plot()

    def parse_text_to_track_pkl(self, txt_path):
        """
        Parses data from a .rtf text file to create a track object in pickle format.

        :param txt_path: Path to the input text file containing track data.
        :type txt_path: str
        :param pkl_path: Path where the pickle file will be saved.
        :type pkl_path: str
        :param is_autocross: A flag indicating whether the track is for autocross. If True,
                             a certain number of nodes will be processed. Otherwise, the function
                             will assume that the track is for endurance and generate a certain
                             number of nodes for that track.
        :type is_autocross: bool
        :return: None
        """
        points_arr = [np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType())]

        arr_done_index = 0

        with open(txt_path, "r") as f:
            content = f.read()
        curr_num = ""
        writing = False
        for char in content:
            if char == '[':
                writing = True
            elif char == ']' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
                arr_done_index += 1
                writing = False
            elif char == ',' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
            elif char != " " and writing:
                curr_num += char

        self.points_x = points_arr[0].astype(float)
        self.points_y = points_arr[1].astype(float)
        self.points_x2 = points_arr[2].astype(float)
        self.points_y2 = points_arr[3].astype(float)

    # # 73 weight
    # points_x = [0, 288, 528, 720, 912, 1104, 1296, 2016, 2256, 2016, 1776, 2016, 2256, 2016, 0, -108, 0, 108, 0, -108]
    # points_y = [0, 36, 108, 36, 0, 36, 108, 0, 240, 480, 240, 0, 240, 480, 444, 276, 0, 276, 444, 276]
    # points_x2 = [0, 288, 528, 720, 912, 1104, 1296, 2016, 2364, 2016, 1668, 2016, 2364, 2016, 0, -216, 0, 216, 0, -216]
    # points_y2 = [108, 144, 216, 144, 108, 144, 216, -108, 240, 588, 240, -108, 240, 588, 552, 276, 108, 276, 552, 276]

    # # 92 weight
    # points_x = [0, 0, -108, 324, 756, 972, 1620, 2268, 1728, 1080, 1512, 2268, 1728, 1188, 540]
    # points_y = [0, -384, -768, -1152, -1152, -1584, -1800, -1584, -1368, -960, -528, -312, 0, 432, 432]
    # points_x2 = [216, 216, 108, 324, 756, 1188, 1620, 2052, 1728, 1296, 1512, 2484, 1512, 1188, 540]
    # points_y2 = [0, -384, -768, -1368, -1368, -1584, -2016, -1584, -1152, -960, -744, -312, 0, 648, 648]

    def run_accel(self, car, node_count, again=False):
        if not again:
            self.points_x = [0, 0]
            self.points_y = [0, 2952]
            self.points_x2 = [100, 100]
            self.points_y2 = [0, 2952]

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=False)

        return self.trk.run_sim(car, nodes=node_count, end_vel=2000)

    def run_endurance(self, car, node_count, again=False):
        if not again:
            self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Points for Endurance.rtf")

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=True)
            self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

        return self.trk.run_sim(car, nodes=node_count)

    def run_autocross(self, car, node_count):
        self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Auto_Points_25.rtf")

        self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=True)
        self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

        # self.trk.plot_without_UI()
        return self.trk.run_sim(car, nodes=node_count)

    def run_constant_velocity_skidpad(self):
        # Find max velocity
        max_vel = math.sqrt(self.racecar.max_corner * 386.09 * 359)
        AX = -1
        while AX < 0:
            max_vel -= 0.001 # decrement by in/s
            AX = self.racecar.curve_accel(max_vel, 359).AX

        print(f"max_vel: {max_vel}")
        self.times.append(self.trk.run_sim(self.racecar, 100, start_vel=max_vel, end_vel=max_vel))

    def run_track(self):
        self.times.append(self.trk.run_sim(self.racecar, 100))

    # def run(self):
    #     for i in np.linspace(6, 16, 11):
    #         self.racecar.h = float(i)
    #         self.racecar.recalculate_characteristics()
    #         self.run_constant_velocity_skidpad()
    #
    #     plt.plot(np.linspace(6, 16, 11), self.times)
    #     plt.ylabel("Time (s)")
    #     plt.xlabel("COG (inches)")
    #     plt.show()

examine = Track_Examine()