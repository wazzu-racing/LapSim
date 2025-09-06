from matplotlib import pyplot as plt
import numpy as np
import csv
import pickle as pkl

class drivetrain:
    
    def __init__(self, final_drive = 4.8):
        self.engn_rpm = [] # engine crankshaft rpm
        self.hp = [] # horsepower
        self.engn_T = [] # Torque supplied from engine (ft*lb)

        self.axl_T = [] # Torque (ft-lb) supplied to axle (index = mph*10)
        self.axl_pwr = [] # power (hp) supplied to axle (index = mph*10)
        self.full_ratios = [] # full drivetrain ratio (index = gear)
        self.gear_vel = [] # the gear which produces the most torque (index = mph*10)
        self.gear_T = [[], [], [], [], [], []] # 2D array; gives torque supplied to axle; first index = transmission gear :: second index = mph*10

        # Gear ratios
        self.gear_ratios = [3.071, 2.235, 1.777, 1.520, 1.333, 1.214]
        self.final_drive = final_drive
        self.primary_drive = 1.69

        self.wheel_radius = 9 / 12 # ft
        self.circumfrence = 2 * self.wheel_radius * np.pi # wheel circumference (ft)
        self.shift_time = 0 # seconds

        # importing engine data
        engine_data = 'engine_array.csv' # engine file location
        delim = '\t' # csv delimiter

        with open(engine_data, newline='') as dat_file:
            reader = csv.reader(dat_file, delimiter=delim)

            # appending data to engn_rpm, hp, and axl_T lists
            i = 0
            for line in reader:
                if i >= 1: # skipping first line
                    self.engn_rpm.append(int(line[0]))
                    self.hp.append(float(line[1]))
                    self.engn_T.append(float(line[2]))
                i += 1

        # creating a list of full drive train ratios for each gear
        for i in self.gear_ratios:
            self.full_ratios.append(i * self.primary_drive * self.final_drive)
        
        self.speed = []
        previous_gear = 0
        for i in range(0, 700):
            self.speed.append(i/10) # mph
            wheel_rpm = self.speed[-1] * 88 / self.circumfrence # multiplies speed by 88 to convert from mph to ft/min
            best_gear = previous_gear
            max_pwr = 0
            best_rpm = 9999999999999999

            # cycling through the different ratios to find the best 1
            for j in range(0, len(self.full_ratios)):
                rpm = wheel_rpm * self.full_ratios[j] # engine rpm
                pwr = self.get_engn_pwr(rpm) # power output of engine
                engn_T = self.get_engn_T(rpm) # torque output of engine
                axl_T = engn_T * self.full_ratios[j] # torque delivered to axle
                self.gear_T[j].append(axl_T)
                if (pwr > max_pwr) and (j >= previous_gear):
                    max_pwr = pwr
                    best_gear = j
                    previous_gear = j
                    best_rpm = rpm
            
            self.gear_vel.append(best_gear) # most effecient gear at index (index = mph*10)
            self.axl_T.append(self.get_engn_T(best_rpm) * self.full_ratios[best_gear]) # axel torque with most effecient gear (index = mph*10)
            self.axl_pwr.append(self.get_engn_pwr(best_rpm)) # power delivered to axel with most effecient gear (index = mph*10)


    
    def get_engn_pwr(self, rpm):
        if rpm <= self.engn_rpm[0]:
            return self.hp[0]
        if rpm >= self.engn_rpm[-1]:
            return 0
        
        for i in range(1, len(self.engn_rpm)):
            if self.engn_rpm[i] >= rpm:
                indx = i # index of lowest rpm value greater than inputted rpm
                ratio = (rpm - self.engn_rpm[i-1]) / (self.engn_rpm[i] - self.engn_rpm[i-1]) # equals 1 if rpm = self.engn_rpm[indx]
                break                                                                        # equals 0 if rpm = self.engn_rpm[indx-1]
        
        return (1-ratio) * self.hp[indx-1] + ratio * self.hp[indx]
    
    def get_engn_T(self, rpm):
        if rpm <= self.engn_rpm[0]:
            return self.engn_T[0]
        if rpm >= self.engn_rpm[-1]:
            return 0
        
        for i in range(1, len(self.engn_rpm)):
            if self.engn_rpm[i] >= rpm:
                indx = i # index of lowest rpm value greater than inputted rpm
                ratio = (rpm - self.engn_rpm[i-1]) / (self.engn_rpm[i] - self.engn_rpm[i-1]) # equals 1 if rpm = self.engn_rpm[indx]
                break                                                                        # equals 0 if rpm = self.engn_rpm[indx-1]
        
        return (1-ratio) * self.engn_T[indx-1] + ratio * self.engn_T[indx]
    
    def get_F_accel(self, mph, gear='optimal'):
        indx = int(mph*10)
        ratio = (mph*10) % 1
        
        if gear == 'optimal':
            return (self.axl_T[indx]*(1-ratio) + self.axl_T[indx+1]*ratio) / self.wheel_radius
        else:
            return (self.gear_T[gear][indx]*(1-ratio) + self.gear_T[gear][indx+1]*ratio) / self.wheel_radius

train = drivetrain()
x = train.engn_rpm
y = []
for i in x:
    y.append(train.get_engn_pwr(i))

plt.plot(x, y)
plt.grid()
plt.show()