from copy import deepcopy

import math
from matplotlib import pyplot as plt


class Brakes:
    def __init__(self, racecar):
        self.racecar = racecar

        self.ambient_temp = 24 # degrees, celsius

        self.front_brake_temps = [self.ambient_temp]
        self.rear_brake_temps = [self.ambient_temp]

        self.brake_balance = 0.6 # front
        self.M_brake = 0.4445205 # kg
        self.A_surface = 0.00064516 # surface area of discs, m^2
        self.C_p = 461 # Specific heat capacity of brakes, J/kg*C
        self.C_C = 0.5 # cooling constant
        self.dx = 0

        self.last_front_brake_temp = self.ambient_temp
        self.last_rear_brake_temp = self.ambient_temp
        self.last_brake_time = 0

        self.max_speed = self.racecar.drivetrain.max_speed * 17.6 # in/s

    def calculate_brake_temps(self, AX_array, vel_array, times):
        for index, AX in enumerate(AX_array):
            if index == 0:
                continue
            self.add_brake_data(AX*self.racecar.W_car, vel_array[index], times[index])

    def add_brake_data(self, F_B, v, t):
        if F_B < 0: # If braking
            K_E_F = -(F_B*4.44822 * self.brake_balance * self.dx*0.0254) # Joules
            K_E_R = -(F_B*4.44822 * (1 - self.brake_balance) * self.dx*0.0254) # Joules

            F_T_C = K_E_F / (self.M_brake*2 * self.C_p) # Change in temperature, Celsius
            R_T_C = K_E_R / (self.M_brake*2 * self.C_p) # Change in temperature, Celsius

            self.last_front_brake_temp = self.front_brake_temps[-1]
            self.last_rear_brake_temp = self.rear_brake_temps[-1]
            self.last_brake_time = t
        else: # If accelerating


            self.front_brake_temps.append(self.ambient_temp + (self.last_front_brake_temp - self.ambient_temp) *
                                          math.e**(-self.C_C*(v/self.max_speed)*(t-self.last_brake_time)))
            self.rear_brake_temps.append(self.ambient_temp + (self.last_rear_brake_temp - self.ambient_temp) *
                                         math.e**(-self.C_C*(v/self.max_speed)*(t-self.last_brake_time)))
            return

        self.front_brake_temps.append(self.front_brake_temps[-1] + F_T_C)
        self.rear_brake_temps.append(self.rear_brake_temps[-1] + R_T_C)

    def get_max_temp(self, front=True, convert_to_fahrenheit=True):
        max = 0
        front_brake_temps = deepcopy(self.front_brake_temps)
        rear_brake_temps = deepcopy(self.rear_brake_temps)
        if convert_to_fahrenheit:
            front_brake_temps = [i*9/5 + 32 for i in self.front_brake_temps]
            rear_brake_temps = [i*9/5 + 32 for i in self.rear_brake_temps]

        # Find max in either front temp array or rear temp array, depending on the 'front' boolean parameter.
        if front:
            for temp in front_brake_temps:
                if temp > max:
                    max = temp
        else:
            for temp in rear_brake_temps:
                if temp > max:
                    max = temp

        return max

    def graph_brake_data(self, convert_to_fahrenheit):
        front_brake_temps = deepcopy(self.front_brake_temps)
        rear_brake_temps = deepcopy(self.rear_brake_temps)
        if convert_to_fahrenheit:
            front_brake_temps = [i*9/5 + 32 for i in self.front_brake_temps]
            rear_brake_temps = [i*9/5 + 32 for i in self.rear_brake_temps]

        plt.plot(front_brake_temps)
        plt.plot(rear_brake_temps)
        plt.legend(["front", "rear"])
        plt.grid()
        plt.xlabel("Nodes")
        plt.ylabel(f"Temp ({"F" if convert_to_fahrenheit else "C"})")
        plt.show()