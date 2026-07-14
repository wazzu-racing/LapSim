import csv

import numpy as np

from dev_tools.run_lapsim import Track_Examine
from models.car_model import car
from matplotlib import pyplot as plt

from models.drivetrain_model import drivetrain

racecar = car()
track_ex = Track_Examine()
# track_ex.run_accel(racecar, 5000)

eng_data = "/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimV1_Aero/config_data/ENG_RPM_DATA_92.csv"
final_drives = np.linspace(1, 5, 51)
times = []

for ratio in final_drives:
    new_dt = drivetrain(ratio, eng_data)
    racecar.drivetrain = new_dt
    times.append(track_ex.run_accel(racecar, 5000))

plt.plot(final_drives, times)
plt.xlabel('Final Drive Ratio')
plt.ylabel('Time (s)')
plt.grid()
plt.show()