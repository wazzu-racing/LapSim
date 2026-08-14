import csv
import math
import tkinter

import matplotlib.pyplot as plt
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
        # self.trk.sim.plot_velocities()
        # self.export_csv()
        # self.run_accel(self.racecar, 1000)
        # self.racecar.plot_forces()

        # print(self.estimate_cooling_coefficient(max_temp=750))

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

    def run_autocross(self, car, node_count, again=False):
        if not again:
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

    def export_csv(self, time_increment:float=0):
        # Makes arrays of FX, FY, FZ that correspond to the FRONT RIGHT tire
        turn_dirs = self.trk.sim.nturn_dirs
        RO_FX, RI_FX = self.trk.sim.lapsim_data_storage.RO_FX_array, self.trk.sim.lapsim_data_storage.RI_FX_array
        RO_FY, RI_FY = self.trk.sim.lapsim_data_storage.RO_FY_array, self.trk.sim.lapsim_data_storage.RI_FY_array
        RO_FZ, RI_FZ = self.trk.sim.lapsim_data_storage.RO_load_array, self.trk.sim.lapsim_data_storage.RI_load_array
        FX, FY, FZ = [], [], []
        for i in range(len(RO_FX)):
            if turn_dirs[i] == curve.Turn.LEFT:
                FX.append(RO_FX[i])
                FY.append(RO_FY[i])
                FZ.append(RO_FZ[i])
            else:
                FX.append(RI_FX[i])
                FY.append(RI_FY[i])
                FZ.append(RI_FZ[i])

        time = self.trk.sim.lapsim_data_storage.time_array
        RPM = [i/9/2/math.pi*60 for i in self.trk.sim.lapsim_data_storage.velocity]

        MX = [i*8.8 for i in FY]
        MY = [i*8.8 for i in FX]

        f = open("data.csv", "w")
        writer = csv.writer(f)

        if time_increment != 0:
            iterate_by = time_increment # seconds
            inter_FX, inter_FY, inter_FZ, inter_MX, inter_MY, inter_RPM, inter_time = [], [], [], [], [], [], []
            next_time = 0
            for index, t in enumerate(time):
                if FX[index] < 0:
                    pass
                if t > next_time:
                    amount = math.ceil((t - next_time)/iterate_by)
                    for i in range(amount):
                        inter_time.append(next_time)
                        inter_FX.append(FX[index-1] + (FX[index]-FX[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        inter_FY.append(FY[index-1] + (FY[index]-FY[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        inter_FZ.append(FZ[index-1] + (FZ[index]-FZ[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        inter_MX.append(MX[index-1] + (MX[index]-MX[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        inter_MY.append(MY[index-1] + (MY[index]-MY[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        inter_RPM.append(RPM[index-1] + (RPM[index]-RPM[index-1])/(t-time[index-1])*(next_time-time[index-1]))
                        next_time += iterate_by
                    else:
                        next_time += iterate_by

            writer.writerow(["Time (sec)", "FX (lbs)", "FY (lbs)", "FZ (lbs)", "MX (in*lbs)", "MY (in*lbs)", "RPM"])
            for index in range(len(inter_time)):
                writer.writerow([round(inter_time[index], 3), round(inter_FX[index], 3), round(inter_FY[index], 3), round(inter_FZ[index], 3), round(inter_MX[index], 3), round(inter_MY[index], 3), round(inter_RPM[index], 3)])
        else:
            writer.writerow(["Time (sec)", "FX (lbs)", "FY (lbs)", "FZ (lbs)", "MX (in*lbs)", "MY (in*lbs)", "RPM"])
            for index in range(len(time)):
                writer.writerow([time[index], FX[index], FY[index], FZ[index], MX[index], MY[index], RPM[index]])
        f.close()

    def run_track(self):
        self.times.append(self.trk.run_sim(self.racecar, 100))

    def estimate_cooling_coefficient(self, max_temp):
        self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/track_points/Points for Endurance.rtf")

        self.trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, self.racecar, loop=True)
        self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

        self.trk.car.brake_model.C_C = 0.7
        while self.trk.car.brake_model.get_max_temp() < max_temp:
            self.trk.car.brake_model.reset()
            self.trk.car.brake_model.C_C -= 0.01
            print(f"testing C_C = {self.trk.car.brake_model.C_C}")

            self.trk.run_sim(self.racecar, 5000)

            AX_FX = []
            for index in range(len(self.trk.sim.lapsim_data_storage.FO_FX_array)):
                AX_FX.append(self.trk.sim.lapsim_data_storage.FO_FX_array[index] + self.trk.sim.lapsim_data_storage.FI_FX_array[index]
                             + self.trk.sim.lapsim_data_storage.RO_FX_array[index] + self.trk.sim.lapsim_data_storage.RI_FX_array[index])
            self.trk.sim.car.brake_model.calculate_brake_temps(AX_FX, self.trk.sim.lapsim_data_storage.velocity,
                                                               self.trk.sim.lapsim_data_storage.time_array)

        return self.trk.car.brake_model.C_C

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