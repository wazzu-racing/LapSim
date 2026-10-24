import os
from copy import deepcopy

import numpy as np
from matplotlib import pyplot as plt

from dev_tools.run_lapsim import Track_Examine
from models.car_model import car
from models.drivetrain_model import drivetrain


class GearRatios:
    def __init__(self):

        # time, final_drive = self.calculate_engine_time("CBR650F", 1.69,
        #                     [3.071, 2.235, 1.777, 1.520, 1.333, 1.214],
        #                     "/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSimV1_Aero/"
        #                     "config_data/ENG_RPM_DATA_92.csv")
        #
        # print(f"\nCBR\nBest Time: {round(time, 3)}\nBest Final Drive:"f" {final_drive}")

        self.ratios = {"KTM690":[2.194, [2.500, 1.750, 1.333, 1.091, 1.045, 1.150]],
                  "R7":[1.925, [2.846,2.125,1.632,1.300,1.091,0.930]]}

        ktm_dir=("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/engine_data/"
                 "690.csv")
        r7_dir=("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/engine_data/"
                "R7.csv")

        ktm_time, ktm_final_drive = self.calculate_engine_time("KTM690", self.ratios["KTM690"][0], self.ratios[
            "KTM690"][1],
                                           eng_dir=ktm_dir)
        # r7_time, r7_final_drive = self.calculate_engine_time("R7", self.ratios["R7"][0], self.ratios["R7"][1],
        #                                                 eng_dir=r7_dir)

        print(f"\nKTM\nBest Time: {round(ktm_time, 3)}\nBest Final Drive:"
              f" {ktm_final_drive}")
        # print(f"\nR7\nBest Time: {round(r7_time, 3)}\nBest Final Drive:"f" {r7_final_drive}")

    def calculate_engine_time(self, name, primary, gears, eng_dir="", final=0):
        track_ex = Track_Examine()
        self.racecar = car()
        times = []
        final_range=np.arange(1,4, 0.1)

        if final == 0:
            for ratio in final_range:
                new_dt = drivetrain(engine_data=eng_dir, final_drive=ratio)
                self.racecar.drivetrain = new_dt
                self.racecar.drivetrain.gear_ratios = gears
                self.racecar.drivetrain.primary_drive = primary

                if any(times):
                    time = track_ex.run_endurance(self.racecar, 1000, again=True)
                else:
                    time = track_ex.run_endurance(self.racecar, 1000, again=False)
                times.append(time)
        else:
            pass

        return np.min(times), final_range[np.where(times == (np.min(times)))]


    def calculate_engine_times(self):
        self.racecar = car()

        track_ex = Track_Examine()

        final_drive_4_times = {key:0 for key in self.ratios.keys()}
        times = {key:[] for key in self.ratios.keys()}

        final_drive_range = [1,5]
        step = 0.1
        for key, value in self.ratios.items():
            dir = '/'.join(os.getcwd().split('/')[:-1])+f"/config_data/engine_data/{key}.csv"

            for i in np.arange(final_drive_range[0], final_drive_range[1], step):
                new_dt = drivetrain(engine_data=dir, final_drive=i)
                self.racecar.drivetrain = new_dt
                self.racecar.drivetrain.primary_drive = self.ratios[key][0]
                self.racecar.drivetrain.gear_ratios = self.ratios[key][1]

                if any(times.values()):
                    time = track_ex.run_endurance(self.racecar, 1000, again=True)
                else:
                    time = track_ex.run_endurance(self.racecar, 1000, again=False)
                times[key].append(time)

                if np.isclose(i, 4, atol=0.0001):
                    final_drive_4_times[key] = time

            if key == "R6":
                plt.plot(times[key])
                plt.grid()
                plt.show()

        print("\n\n")
        print(f"\033[31m4:1 Final Drive Times:\033[0m")
        for key, value in final_drive_4_times.items():
            print(f"{key}: {round(value, 3)} seconds")

        print("\n\n")
        print(f"\033[32mBest Final Drives:\033[0m")
        for key, value in times.items():
            print(f"{key}: {round(np.min(value), 3)} seconds -- Final Drive: {round(final_drive_range[0] + value.index(np.min(value))*step, 2)}:1")

ratios = GearRatios()