import os
from copy import deepcopy

import numpy as np
from matplotlib import pyplot as plt

from dev_tools.final_drive import FinalDrive
from dev_tools.run_lapsim import Track_Examine
from models.car_model import car
from models.drivetrain_model import drivetrain


class GearRatios:
    def __init__(self):
        self.ratios = {"CBR650F":[1.69, [3.071, 2.235, 1.777, 1.520, 1.333, 1.214]],
                  "R6":[2.073, [2.6,2.063,1.762,1.522,1.364,1.222]],
                  "CBR600RR":[2.111, [2.75,2,1.666,1.444,1.304,1.208]],
                  "SV650":[2.088, [2.461,1.777,1.38,1.125,0.961,0.851]],
                  "GSX-R600":[1.9,[2.786,2.053,1.714,1.5,1.348,1.208]],
                  "ZX-6R":[1.891,[2.923,2.055,1.666,1.45,1.272,1.153]]}

        self.calculate_engine_times()

    def calculate_engine_times(self):
        self.racecar = car()

        track_ex = Track_Examine()

        final_drive_4_times = {key:0 for key in self.ratios.keys()}
        times = {key:[] for key in self.ratios.keys()}

        final_drive_range = [1,6]
        step = 0.1
        for key, value in self.ratios.items():
            dir = '/'.join(os.getcwd().split('/')[:-1])+f"/config_data/engine_data/{key}.csv"

            for i in np.arange(final_drive_range[0], final_drive_range[1], step):
                new_dt = drivetrain(engine_data=dir, final_drive=i)
                self.racecar.drivetrain = new_dt
                self.racecar.drivetrain.primary_drive = self.ratios[key][0]
                self.racecar.drivetrain.gear_ratios = self.ratios[key][1]

                if any(times.values()):
                    time = track_ex.run_accel(self.racecar, 1000, again=True)
                else:
                    time = track_ex.run_accel(self.racecar, 1000, again=False)
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