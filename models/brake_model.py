import tkinter
from copy import deepcopy

import math

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class Brakes:
    def __init__(self, racecar):
        self.racecar = racecar

        self.times = []

        self.ambient_temp = 24 # degrees, celsius

        self.front_brake_temps = [self.ambient_temp]
        self.rear_brake_temps = [self.ambient_temp]

        # Variables
        self.brake_balance = 0.55 # front
        self.M_brake = 0.4 # kg
        self.C_p = 461 # Specific heat capacity of brakes, J/kg*C
        self.dx = 0 # assigned by lapsim.py
        self.P_air = 1.204 # kg/m^3, air density
        self.dynamic_viscity_air = 1.81e-5 # Pa*secs
        self.D_rotor = 0.1651 # meters
        self.A_rotor = 0.030212843 # meters^2
        self.Pr = 0.71 # unitless, prandtl number of air
        self.K_air = 0.0261 # W/(m*K), thermal conductivity of air at 75 degrees Fahrenheit
        # COOLING COEFFICIENT
        self.C_C = 0.21 # unitless

        self.last_time = 0

        self.max_speed = self.racecar.drivetrain.max_speed * 17.6 # in/s

    def reset(self):
        self.front_brake_temps = [self.ambient_temp]
        self.rear_brake_temps = [self.ambient_temp]
        self.last_time = 0

    def calculate_brake_temps(self, FX_array, vel_array, times):
        self.times = times
        for index, FX in enumerate(FX_array):
            if index == 0:
                continue
            self.add_brake_data(FX, vel_array[index], times[index])

    def add_brake_data(self, F_B, v, t):

        def calculate_cooling_coefficient():
            # Re_U = self.P_air * v*0.0254 * self.D_rotor / self.dynamic_viscity_air # Reynolds number
            # Re_R = self.P_air * v*0.0254/0.2286 * ((self.D_rotor/2)**2) / self.dynamic_viscity_air
            # Nu = math.sqrt((0.036*Re_U**0.8)**2 + (0.556*Re_R**0.5)**2) # Nusselt number
            # h = Nu * self.K_air / self.D_rotor # convection coefficient
            # k = h * self.A_rotor / (self.M_brake * self.C_p) # cooling coefficient

            k = self.C_C * v / self.max_speed

            return k

        if F_B < 0: # If braking
            K_E_F = F_B*4.44822 * self.brake_balance * self.dx*0.0254 # Joules
            K_E_R = F_B*4.44822 * (1 - self.brake_balance) * self.dx*0.0254 # Joules

            # Calculate the heat gained from the kinetic energy absorbed by the rotors.
            F_T_C = -K_E_F * 0.9 / (self.M_brake*2 * self.C_p) # Change in temperature, Celsius
            R_T_C = -K_E_R * 0.9 / (self.M_brake*2 * self.C_p) # Change in temperature, Celsius

            k_c = calculate_cooling_coefficient()
            F_T = self.front_brake_temps[-1] + F_T_C - k_c * (self.front_brake_temps[-1] - self.ambient_temp) * (t - self.last_time)
            R_T = self.rear_brake_temps[-1] + R_T_C - k_c * (self.rear_brake_temps[-1] - self.ambient_temp) * (t - self.last_time)

            # Heat radiation - Only significant at high temps
            F_T -= self.A_rotor * 0.8 * 5.67e-8 * (F_T**4 - self.ambient_temp**4) * (t - self.last_time) / (self.M_brake * self.C_p)
            R_T -= self.A_rotor * 0.8 * 5.67e-8 * (R_T**4 - self.ambient_temp**4) * (t - self.last_time) / (self.M_brake * self.C_p)

        else: # If accelerating

            k_c = calculate_cooling_coefficient()
            # Cooling
            F_T = self.front_brake_temps[-1] - k_c * (self.front_brake_temps[-1] - self.ambient_temp) * (t - self.last_time)
            R_T = self.rear_brake_temps[-1] - k_c * (self.rear_brake_temps[-1] - self.ambient_temp) * (t - self.last_time)

            # Heat radiation - Only significant at high temps
            F_T -= self.A_rotor * 0.8 * 5.67e-8 * (F_T**4 - self.ambient_temp**4) * (t - self.last_time) / (self.M_brake * self.C_p)
            R_T -= self.A_rotor * 0.8 * 5.67e-8 * (R_T**4 - self.ambient_temp**4) * (t - self.last_time) / (self.M_brake * self.C_p)

        self.front_brake_temps.append(F_T)
        self.rear_brake_temps.append(R_T)
        self.last_time = t

    def get_max_temp(self, front=True, convert_to_fahrenheit=True, prin=True):
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

        if prin:
            print(f"Max temp of {"front" if front else "rear"} brakes: {max}° {"F" if convert_to_fahrenheit else "C"}")

        return max

    def get_average_temp(self, front=True, convert_to_fahrenheit=True, prin=True):
        front_brake_temps = deepcopy(self.front_brake_temps)
        rear_brake_temps = deepcopy(self.rear_brake_temps)
        if convert_to_fahrenheit:
            front_brake_temps = [i*9/5 + 32 for i in self.front_brake_temps]
            rear_brake_temps = [i*9/5 + 32 for i in self.rear_brake_temps]
        if front:
            avg = np.average(front_brake_temps)
            if prin:
                print(f"Average temp front brakes: {avg}° {"F" if convert_to_fahrenheit else "C"}")
            return avg
        else:
            avg = np.average(rear_brake_temps)
            if prin:
                print(f"Average temp of rear brakes: {avg}° {"F" if convert_to_fahrenheit else "C"}")
            return avg

    def graph_brake_data(self, convert_to_fahrenheit):
        front_brake_temps = deepcopy(self.front_brake_temps)
        rear_brake_temps = deepcopy(self.rear_brake_temps)
        if convert_to_fahrenheit:
            front_brake_temps = [i*9/5 + 32 for i in self.front_brake_temps]
            rear_brake_temps = [i*9/5 + 32 for i in self.rear_brake_temps]

        # plt.plot(front_brake_temps)
        # plt.plot(rear_brake_temps)
        # plt.legend(["front", "rear"])
        # plt.grid()
        # plt.xlabel("Nodes")
        # plt.ylabel(f"Temp ({"F" if convert_to_fahrenheit else "C"})")
        # plt.show()

        tk = tkinter.Tk()
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        ax.plot(self.times, front_brake_temps)
        ax.plot(self.times, rear_brake_temps)
        ax.legend(["front", "rear"])
        ax.grid()
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel(f"Temp ({"F" if convert_to_fahrenheit else "C"})")
        tk.mainloop()