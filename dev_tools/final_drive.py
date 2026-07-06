import numpy as np

from dev_tools.test_validation import Track_Examine
from models.car_model import car
from matplotlib import pyplot as plt

from models.drivetrain_model import drivetrain

track_ex = Track_Examine()

eng_data = "/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim_Main/config_data/ENG_RPM_DATA_92.csv"
racecar = car()
final_drives = np.linspace(3, 5, 101)
times = []

for ratio in final_drives:
    new_dt = drivetrain(ratio, eng_data)
    racecar.drivetrain = new_dt
    times.append(track_ex.run_accel(racecar, 1000))

plt.plot(final_drives, times)
plt.xlabel('Final Drive Ratio')
plt.ylabel('Time (s)')
plt.grid()
plt.show()