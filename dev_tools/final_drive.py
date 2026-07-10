from enum import Enum

import numpy as np

from dev_tools.test_validation import Track_Examine
from models.car_model import car
from matplotlib import pyplot as plt

from models.drivetrain_model import drivetrain

class FinalDrive:
    def __init__(self):
        self.eng_data = "config_data/ENG_RPM_DATA_92.csv"
        self.racecar = car()

        # self.analyze_ratios(3,5)
        self.analyze_track(self.TRACK.ACCEL, iterations=20)

    class TRACK(Enum):
        ACCEL = 1
        AUTO = 2
        ENDURANCE = 3

    def analyze_ratios(self, ratio1, ratio2):
        ratio1_vels, ratio2_vels = [], []
        ratio1_tire_forces, ratio2_tire_forces = [], []
        ratio1_eng_forces, ratio2_eng_forces = [], []

        track_ex = Track_Examine()
        self.racecar.drivetrain = drivetrain(ratio1, self.eng_data)
        track_ex.run_accel(self.racecar, 5000)

        ratio1_vels = self.racecar.vels
        ratio1_tire_forces = self.racecar.tires_force
        ratio1_eng_forces = self.racecar.engine_force

        # Clear racecar data
        self.racecar.vels = []
        self.racecar.tires_force = []
        self.racecar.engine_force = []

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
            new_dt = drivetrain(ratio, self.eng_data)
            self.racecar.drivetrain = new_dt
            match track:
                case self.TRACK.ACCEL:
                    if len(times) > 0:
                        times.append(track_ex.run_accel(self.racecar, 1000, again=True))
                    else:
                        times.append(track_ex.run_accel(self.racecar, 1000, again=False))
                case self.TRACK.AUTO:
                    times = track_ex.run_autocross(self.racecar, 1000)
                case self.TRACK.ENDURANCE:
                    if len(times) > 0:
                        times.append(track_ex.run_endurance(self.racecar, 1000, again=True))
                    else:
                        times.append(track_ex.run_endurance(self.racecar, 1000, again=False))
            if times[-1] < best_time:
                best_time = times[-1]
                best_ratio = ratio

        print(f"Best ratio: {best_ratio:.2f}:1")

        plt.plot(final_drives, times)
        plt.xlabel('Final Drive Ratio')
        plt.ylabel('Time (s)')
        plt.grid()
        plt.show()

final = FinalDrive()