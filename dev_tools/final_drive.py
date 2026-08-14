from enum import Enum

import numpy as np

from dev_tools.run_lapsim import Track_Examine
from models.car_model import car
from matplotlib import pyplot as plt

from models.drivetrain_model import drivetrain

class FinalDrive:
    def __init__(self):
        self.eng_data = "/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/ENG_RPM_DATA_92.csv"
        self.racecar = car()

        # self.analyze_gear_ranges(2.38)
        # self.analyze_gear_changes(3.2,3.8)
        # self.analyze_track(self.TRACK.ACCEL, iterations=50)
        # self.analyze_ratios(3.1, 3.8)

    class TRACK(Enum):
        ACCEL = 1
        AUTO = 2
        ENDURANCE = 3

    def analyze_gear_ranges(self, ratio):
        self.racecar.drivetrain = drivetrain(ratio, self.eng_data)

        prev_gear = 0
        gear_ranges = [[0.0], [], [], [], [], []]
        for index, gear in enumerate(self.racecar.drivetrain.gear_vel):
            if gear == prev_gear:
                pass
            else:
                # Complete current range
                gear_ranges[gear-1].append((index-1)/10)

                # Start new range
                gear_ranges[gear].append(index/10)
                prev_gear = gear

        for index, rang in enumerate(gear_ranges):
            try:
                print(f"Gear {index+1}: {rang[0]}-{rang[1]} mph")
            except IndexError:
                break

    def analyze_gear_changes(self, ratio1, ratio2):
        track_ex = Track_Examine()

        ratio1_vels, ratio2_vels = [], []
        ratio1_gear_changes, ratio2_gear_changes = [], []

        print(f"\n\nRatio = {ratio1}:1")
        self.racecar.drivetrain = drivetrain(ratio1, self.eng_data)
        track_ex.run_accel(self.racecar, 1000)
        ratio1_vels = track_ex.trk.sim.lapsim_data_storage.velocity
        ratio1_gear_changes = track_ex.trk.sim.lapsim_data_storage.changing_gears

        print(f"Ratio = {ratio2}:1")
        self.racecar.drivetrain = drivetrain(ratio2, self.eng_data)
        track_ex.run_accel(self.racecar, 1000)
        ratio2_vels = track_ex.trk.sim.lapsim_data_storage.velocity
        ratio2_gear_changes = track_ex.trk.sim.lapsim_data_storage.changing_gears

        plt.scatter(ratio1_vels, ratio1_gear_changes)
        plt.scatter(ratio2_vels, ratio2_gear_changes)
        plt.xlabel("Velocity (in/s)")
        plt.ylabel("Shifting gears (1/0)")
        plt.legend([f"Ratio = {ratio1}:1", f"Ratio = {ratio2}:1"])
        plt.grid()
        plt.show()

    def analyze_ratios(self, ratio1, ratio2):
        ratio1_vels, ratio2_vels = [], []
        ratio1_tire_forces, ratio2_tire_forces = [], []
        ratio1_eng_forces, ratio2_eng_forces = [], []

        track_ex = Track_Examine()
        print(f"------\nRatio = {ratio1}:1")
        self.racecar.drivetrain = drivetrain(ratio1, self.eng_data)
        track_ex.run_accel(self.racecar, 5000)

        ratio1_vels = self.racecar.vels
        ratio1_tire_forces = self.racecar.tires_force
        ratio1_eng_forces = self.racecar.engine_force

        # Clear racecar data
        self.racecar.vels = []
        self.racecar.tires_force = []
        self.racecar.engine_force = []

        print(f"------\nRatio = {ratio2}:1")
        self.racecar.drivetrain = drivetrain(ratio2, self.eng_data)
        track_ex.run_accel(self.racecar, 5000)

        ratio2_vels = self.racecar.vels
        ratio2_eng_forces = self.racecar.engine_force

        plt.plot(ratio1_vels, ratio1_tire_forces)
        plt.plot(ratio1_vels, ratio1_eng_forces)
        plt.plot(ratio2_vels, ratio2_eng_forces)
        plt.legend([f"tires", f"{ratio1} eng", f"{ratio2} eng"])
        plt.xlabel("Velocity (in/s)")
        plt.ylabel("Force (lbs)")
        plt.title(f"{ratio1}:1 vs {ratio2}:1")
        plt.grid()
        plt.show()

    def analyze_track(self, track:TRACK, iterations):

        track_ex = Track_Examine()

        final_drives = np.linspace(1, 5, iterations)
        times = []
        best_time, best_ratio = 1000, 10

        for ratio in final_drives:
            print(ratio)
            new_dt = drivetrain(ratio, self.eng_data)
            self.racecar.drivetrain = new_dt
            match track:
                case self.TRACK.ACCEL:
                    if len(times) > 0:
                        times.append(track_ex.run_accel(self.racecar, 1000, again=True))
                    else:
                        times.append(track_ex.run_accel(self.racecar, 1000, again=False))
                case self.TRACK.AUTO:
                    if len(times) > 0:
                        times.append(track_ex.run_autocross(self.racecar, 1000, again=True))
                    else:
                        times.append(track_ex.run_autocross(self.racecar, 1000, again=False))
                case self.TRACK.ENDURANCE:
                    if len(times) > 0:
                        times.append(track_ex.run_endurance(self.racecar, 1000, again=True))
                    else:
                        times.append(track_ex.run_endurance(self.racecar, 1000, again=False))
            if times[-1] < best_time:
                best_time = times[-1]
                best_ratio = ratio

        print(f"Best ratio: {best_ratio:.2f}:1")

        return times

        # plt.plot(final_drives, times)
        # plt.xlabel('Final Drive Ratio')
        # plt.ylabel('Time (s)')
        # plt.grid()
        # plt.show()

final = FinalDrive()