import pickle

from matplotlib import pyplot as plt

from gen_lapsim.spline_track import track
from models.car_model import car
import numpy as np

class Track_Examine:

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

    points_x = [0, 288, 528, 720, 912, 1104, 1296, 2016, 2256, 2016, 1776, 2016, 2256, 2016, 0, -108, 0, 108, 0, -108]
    points_y = [0, 36, 108, 36, 0, 36, 108, 0, 240, 480, 240, 0, 240, 480, 444, 276, 0, 276, 444, 276]
    points_x2 = [0, 288, 528, 720, 912, 1104, 1296, 2016, 2364, 2016, 1668, 2016, 2364, 2016, 0, -216, 0, 216, 0, -216]
    points_y2 = [108, 144, 216, 144, 108, 144, 216, -108, 240, 588, 240, -108, 240, 588, 552, 276, 108, 276, 552, 276]

    def run_accel(self):
        racecar = car()
        trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, racecar)
        trk.adjust_track([40, 30, 30, 80],[100, 30, 10, 5])
        # trk.plot_without_UI()

        trk.run_sim(racecar, 1000)

    def run(self):
        # self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Auto_Points_25.rtf")
        self.run_accel()

examine = Track_Examine()
examine.run()