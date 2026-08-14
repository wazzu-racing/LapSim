import tkinter

import math
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gen_lapsim.spline_track import track, curve
from models.car_model import car
import numpy as np


class Track_Examine:

    def __init__(self, track_txt_path=""):
        self.racecar = car()

        # self.run_endurance(self.racecar, 2500)
        # self.plot_forces("RO")
        # self.run_skidpad(self.racecar, 1000)
        # self.run_autocross(self.racecar, 5000)
        # self.run_accel(self.racecar, 5000)
        # self.racecar.plot_forces()

    def run_accel(self, rcar, node_count, again=False):
        if not again:
            self.points_x = [0, 0]
            self.points_y = [0, 2952]
            self.points_x2 = [100, 100]
            self.points_y2 = [0, 2952]

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, rcar, loop=False)

        return self.trk.run_sim(rcar, nodes=node_count, end_vel=2000)

    def run_endurance(self, car, node_count, again=False):
        if not again:
            self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Points for Endurance.rtf")

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=True)
            self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

        return self.trk.run_sim(car, nodes=node_count)

    def run_autocross(self, car, node_count, again=False):
        if not again:
            self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Auto_Points_25.rtf")

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=True)
            self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

        # self.trk.plot_without_UI()
        return self.trk.run_sim(car, nodes=node_count)

    def run_skidpad(self, car, node_count, again=False):
        if not again:
            self.points_x, self.points_y, self.points_x2, self.points_y2 = [], [], [], []

            self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, car, loop=True)

            self.trk.rad = [300.23622+self.racecar.t_f/2]
            self.trk.lens = [2 * math.pi * self.trk.rad[0]]
            self.trk.turn_dirs = [curve.Turn.RIGHT]

        max_vel = math.sqrt(self.racecar.max_corner*0.99*386.0886*self.trk.rad[0])
        return self.trk.run_sim(car, nodes=node_count, start_vel=max_vel, end_vel=max_vel, clear_arrs=False)

    def plot_forces(self, tire="FO", x=True, y=True, z=True):
        tk = tkinter.Tk()
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()
        leg = []
        if x:
            leg.append('FX')
            ax.plot(self.trk.sim.lapsim_data_storage.FO_FX_array if tire == "FO" else
                    self.trk.sim.lapsim_data_storage.FI_FX_array if tire == "FI" else
                    self.trk.sim.lapsim_data_storage.RO_FX_array if tire == "RO" else
                    self.trk.sim.lapsim_data_storage.RI_FX_array)
        if y:
            leg.append('FY')
            ax.plot(self.trk.sim.lapsim_data_storage.FO_FY_array if tire == "FO" else
                    self.trk.sim.lapsim_data_storage.FI_FY_array if tire == "FI" else
                    self.trk.sim.lapsim_data_storage.RO_FY_array if tire == "RO" else
                    self.trk.sim.lapsim_data_storage.RI_FY_array)
        if z:
            leg.append('FZ')
            ax.plot(self.trk.sim.lapsim_data_storage.FO_load_array if tire == "FO" else
                    self.trk.sim.lapsim_data_storage.FI_load_array if tire == "FI" else
                    self.trk.sim.lapsim_data_storage.RO_load_array if tire == "RO" else
                    self.trk.sim.lapsim_data_storage.RI_load_array)
        ax.legend(leg)
        ax.grid()
        tk.mainloop()

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

examine = Track_Examine()