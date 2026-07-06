import os

import matplotlib
import numpy as np

from gen_lapsim.spline_track import track
from models.car_model import car


def parse_text_to_track_pkl(txt_path):
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

    points_x = points_arr[0].astype(float)
    points_y = points_arr[1].astype(float)
    points_x2 = points_arr[2].astype(float)
    points_y2 = points_arr[3].astype(float)

    return points_x, points_y, points_x2, points_y2

points_x, points_y, points_x2, points_y2 = parse_text_to_track_pkl("/".join(os.getcwd().split("/")[:-1]) + "/config_data/track_points/Points for Endurance.rtf")

racecar = car()
trk = track(points_x, points_y, points_x2, points_y2, racecar)
trk.adjust_track([40, 30, 30, 80],[100, 30, 10, 5])
trk.determine_turn_dirs_on_track()

trk.plot_without_UI(show_turns=True)