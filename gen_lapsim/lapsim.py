import math
import tkinter

import numpy as np
import copy
import matplotlib.pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gen_lapsim.spline_track import curve


class LapSimData:
    def __init__(self):
        # Array for time t
        self.time_array = [0]
        # Arrays for lateral and axial acceleration of car
        self.AY = [] # Positive AY is turning right, negative AY is turning left.
        self.AX = []
        self.velocity = []
        # Arrays for vertical force, lateral force, and axial forces on wheels
        self.FI_load_array = []
        self.FO_load_array = []
        self.RI_load_array = []
        self.RO_load_array = []
        self.FI_FY_array = []
        self.FO_FY_array = []
        self.RI_FY_array = []
        self.RO_FY_array = []
        self.FI_FX_array = []
        self.FO_FX_array = []
        self.RI_FX_array = []
        self.RO_FX_array = []
        # Vectors of forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.FI_vector = []
        self.FO_vector = []
        self.RI_vector = []
        self.RO_vector = []
        self.FI_vector_mag = []
        self.FO_vector_mag = []
        self.RI_vector_mag = []
        self.RO_vector_mag = []
        self.FI_vector_dir = []
        self.RI_vector_dir = []
        self.FO_vector_dir = []
        self.RO_vector_dir = []
        # Arrays for vertical displacement of wheels
        self.front_inner_displacement = []
        self.rear_inner_displacement = []
        self.front_outer_displacement = []
        self.rear_outer_displacement = []
        # rpm
        self.rpm = []
        # Angle of accel force of car
        self.theta_accel = []

        self.max_value_names = ["max_time", "max_AY", "max_AX", "max_FI_load", "max_FO_load", "max_RI_load",
                                "max_RO_load", "max_FI_FY", "max_FO_FY", "max_RI_FY", "max_RO_FY", "max_FI_FX",
                                "max_FO_FX", "max_RI_FX", "max_RO_FX", "max_FI_vector_mag", "max_FO_vector_mag",
                                "max_RI_vector_mag", "max_RO_vector_mag", "max_D_1_dis", "max_D_2_dis", "max_D_3_dis",
                                "max_D_4_dis"]

    # Initialize all of the arrays in LapSimData
    def initialize(self, n):
        # array for time elapsed
        self.time_array = [0]
        # Collect lateral and axial acceleration
        self.AX = np.zeros(int(n + 1))
        self.AY = np.zeros(int(n + 1))
        self.velocity = np.zeros(int(n + 1))
        # vertical forces on tires
        self.FO_load_array = np.zeros(int(n + 1))
        self.FI_load_array = np.zeros(int(n + 1))
        self.RO_load_array = np.zeros(int(n + 1))
        self.RI_load_array = np.zeros(int(n + 1))
        self.FO_FY_array = np.zeros(int(n + 1))
        self.FI_FY_array = np.zeros(int(n + 1))
        self.RO_FY_array = np.zeros(int(n + 1))
        self.RI_FY_array = np.zeros(int(n + 1))
        self.FO_FX_array = np.zeros(int(n + 1))
        self.FI_FX_array = np.zeros(int(n + 1))
        self.RO_FX_array = np.zeros(int(n + 1))
        self.RI_FX_array = np.zeros(int(n + 1))
        # vectors for forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.FI_vector = np.zeros(shape=(int(n + 1), 3))
        self.FO_vector = np.zeros(shape=(int(n + 1), 3))
        self.RI_vector = np.zeros(shape=(int(n + 1), 3))
        self.RO_vector = np.zeros(shape=(int(n + 1), 3))
        self.FI_vector_mag = np.zeros(int(n + 1))
        self.FO_vector_mag = np.zeros(int(n + 1))
        self.RI_vector_mag = np.zeros(int(n + 1))
        self.RO_vector_mag = np.zeros(int(n + 1))
        self.FI_vector_dir = np.zeros(shape=(int(n + 1), 3))
        self.RI_vector_dir = np.zeros(shape=(int(n + 1), 3))
        self.FO_vector_dir = np.zeros(shape=(int(n + 1), 3))
        self.RO_vector_dir = np.zeros(shape=(int(n + 1), 3))
        # displacement of wheels
        self.front_inner_displacement = np.zeros(int(n + 1))
        self.front_outer_displacement = np.zeros(int(n + 1))
        self.rear_inner_displacement = np.zeros(int(n + 1))
        self.rear_outer_displacement = np.zeros(int(n + 1))
        # rpm
        self.rpm = np.zeros(int(n + 1))
        # theta of force on car
        self.theta_accel = np.zeros(int(n + 1))

    # Append a data point to all arrays.
    def append_data_arrays(self, snippet, index):
        """
        Append the data inside of the car_data_snippet to the arrays in LapSimData at the specified index.
        :param car_data_snippet: A CarDataSnippet object containing the data to be appended.
        :param index: The index at which to append the data.
        :return: None.
        """
        # Collect lateral and axial acceleration of car
        self.AX[index] = snippet.AX
        self.AY[index] = snippet.AY
        self.velocity[index] = snippet.velocity

        # lateral, axial, and vertical forces on tires
        self.FO_load_array[index] = snippet.FO_load
        self.FI_load_array[index] = snippet.FI_load
        self.RO_load_array[index] = snippet.RO_load
        self.RI_load_array[index] = snippet.RI_load
        self.FO_FY_array[index] = snippet.FO_FY
        self.FI_FY_array[index] = snippet.FI_FY
        self.RO_FY_array[index] = snippet.RO_FY
        self.RI_FY_array[index] = snippet.RI_FY
        self.FO_FX_array[index] = snippet.FO_FX
        self.FI_FX_array[index] = snippet.FI_FX
        self.RO_FX_array[index] = snippet.RO_FX
        self.RI_FX_array[index] = snippet.RI_FX

        # Vectors of forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.FI_vector[index] = np.array([snippet.FO_FX,snippet.FO_FY,snippet.FI_load])
        self.RI_vector[index] = np.array([snippet.FI_FX,snippet.FI_FY,snippet.RI_load])
        self.FO_vector[index] = np.array([snippet.RO_FX,snippet.RO_FY,snippet.FO_load])
        self.RO_vector[index] = np.array([snippet.RI_FX,snippet.RI_FY,snippet.RO_load])
        self.FI_vector_mag[index] = self.get_magnitude(
            self.FI_vector[index])
        self.FO_vector_mag[index] = self.get_magnitude(
            self.FO_vector[index])
        self.RI_vector_mag[index] = self.get_magnitude(
            self.RI_vector[index])
        self.RO_vector_mag[index] = self.get_magnitude(
            self.RO_vector[index])
        self.FI_vector_dir[index] = np.array(
            self.get_unit_vector(self.FI_vector[index]))
        self.RI_vector_dir[index] = np.array(
            self.get_unit_vector(self.RI_vector[index]))
        self.FO_vector_dir[index] = np.array(
            self.get_unit_vector(self.FO_vector[index]))
        self.RO_vector_dir[index] = np.array(
            self.get_unit_vector(self.RO_vector[index]))

        # lapsim_data_storage vertical displacement of wheels
        self.front_inner_displacement[index] = snippet.front_inner_displacement
        self.rear_inner_displacement[index] = snippet.rear_inner_displacement
        self.front_outer_displacement[index] = snippet.front_outer_displacement
        self.rear_outer_displacement[index] = snippet.rear_outer_displacement

    # Returns a dictionary of all the max values within arrays.
    def find_max_values(self):
        max_values_dict = {"max_time": self.time_array[-1], "max_AY": np.max(self.AY),
                           "max_AX": np.max(self.AX), "max_FO_load": np.max(self.FO_load_array),
                           "max_FI_load": np.max(self.FI_load_array), "max_RO_load": np.max(self.RO_load_array),
                           "max_RI_load": np.max(self.RI_load_array), "max_FO_FY": np.max(self.FO_FY_array),
                           "max_RI_FY": np.max(self.RI_FY_array), "max_FO_FX": np.max(self.FO_FX_array),
                           "max_FI_FX": np.max(self.FI_FX_array), "max_RO_FX": np.max(self.RO_FX_array),
                           "max_FI_FY": np.max(self.FI_FY_array), "max_RO_FY": np.max(self.RO_FY_array),
                           "max_RI_FX": np.max(self.RI_FX_array), "max_FI_vector_mag": np.max(self.FI_vector_mag),
                           "max_FO_vector_mag": np.max(self.FO_vector_mag),
                           "max_RI_vector_mag": np.max(self.RI_vector_mag),
                           "max_RO_vector_mag": np.max(self.RO_vector_mag), "max_D_1_dis": np.max(self.D_1_dis),
                           "max_D_2_dis": np.max(self.D_2_dis), "max_D_3_dis": np.max(self.D_3_dis),
                           "max_D_4_dis": np.max(self.D_4_dis)}

        return max_values_dict

    def infect_force_theta(self):
        for index, accel in enumerate(self.AY):
            self.theta_accel[index] = math.atan2(accel, self.AX[index]) * 180 / math.pi

    # Return a unit vector using the vector argument provided.
    def get_unit_vector(self, vector):
        return np.divide(vector, np.sqrt(np.sum(np.power(vector, 2))))

    # Get the magnitude of the argument vector provided.
    def get_magnitude(self, vector):
        return np.sqrt(np.sum(np.power(vector, 2)))

    def brake_temp_post_processing(self, turn_dirs, car, graph:bool = False):
        """
        This function assumes:
            - Uniform temp across brake disc
            - Initial temp of brake disc is equal to the environment temp
        :return: None
        """
        T_ambient = 24 # temp of environment, Celsius (~75 degrees F)
        T_init = 24 # initial temp of brake discs, Celsius (~75 degrees F)
        C_heat = 1 # Heat transfer coefficient, dependent upon air flow and velocity
        C_p = 461 # Specific heat capacity of brakes, J/kg*C
        C_c = 0.5
        A_surface = 0.00064516 # surface area of discs, m^2
        K_E_perc = 0.95
        M_brake = 0.4445205 # mass of brake discs, kg
        W_car = self.FO_load_array[0] + self.RO_load_array[0] + self.FI_load_array[0] + self.RI_load_array[0]

        # Brake temp array across entire track
        FO_brake_temps, FI_brake_temps, RO_brake_temps, RI_brake_temps = [], [], [], []
        FR_brake_temps, FL_brake_temps, RR_brake_temps, RL_brake_temps = [], [], [], []
        F_brake_temps, R_brake_temps = [], []

        FO_T_curr, FI_T_curr, RO_T_curr, RI_T_curr = T_init, T_init, T_init, T_init
        prev_brake_time = 0
        FO_T_last_brake, FI_T_last_brake, RO_T_last_brake, RI_T_last_brake = T_ambient, T_ambient, T_ambient, T_ambient
        for index, AX in enumerate(self.AX):
            # Do not process first node, as there has been no velocity change yet.
            if index == 0:
                continue

            # Braking, heating up
            if self.velocity[index] - self.velocity[index-1] < 0:
                # Front outer brake
                FO_T_change = K_E_perc*(0.5*self.FO_load_array[index-1]*0.453592*((self.velocity[index-1]*0.0254)**2 - (self.velocity[index]*0.0254)**2))/(M_brake*C_p) # Kelvin
                FO_T_curr += FO_T_change
                FO_brake_temps.append(FO_T_curr)

                # Front inner brake
                FI_T_change = K_E_perc*(0.5*self.FI_load_array[index-1]*0.453592*((self.velocity[index-1]*0.0254)**2 - (self.velocity[index]*0.0254)**2))/(M_brake*C_p) # Kelvin
                FI_T_curr += FI_T_change
                FI_brake_temps.append(FI_T_curr)

                # Rear outer brake
                RO_T_change = K_E_perc*(0.5*self.RO_load_array[index-1]*0.453592*((self.velocity[index-1]*0.0254)**2 - (self.velocity[index]*0.0254)**2))/(M_brake*C_p) # Kelvin
                RO_T_curr += RO_T_change
                RO_brake_temps.append(RO_T_curr)

                # Rear inner brake
                RI_T_change = K_E_perc*(0.5*self.RI_load_array[index-1]*0.453592*((self.velocity[index-1]*0.0254)**2 - (self.velocity[index]*0.0254)**2))/(M_brake*C_p) # Kelvin
                RI_T_curr += RI_T_change
                RI_brake_temps.append(RI_T_curr)

                prev_brake_time = self.time_array[index]
                FO_T_last_brake = FO_T_curr
                FI_T_last_brake = FI_T_curr
                RO_T_last_brake = RO_T_curr
                RI_T_last_brake = RI_T_curr
            # Accelerating, cooling down
            else:
                FO_T_curr = T_ambient + (FO_T_last_brake - T_ambient)*np.e**(-(C_c*self.velocity[index]/np.max(self.velocity))*(self.time_array[index] - prev_brake_time))
                FI_T_curr = T_ambient + (FI_T_last_brake - T_ambient)*np.e**(-(C_c*self.velocity[index]/np.max(self.velocity))*(self.time_array[index] - prev_brake_time))
                RO_T_curr = T_ambient + (RO_T_last_brake - T_ambient)*np.e**(-(C_c*self.velocity[index]/np.max(self.velocity))*(self.time_array[index] - prev_brake_time))
                RI_T_curr = T_ambient + (RI_T_last_brake - T_ambient)*np.e**(-(C_c*self.velocity[index]/np.max(self.velocity))*(self.time_array[index] - prev_brake_time))

                FO_brake_temps.append(FO_T_curr)
                FI_brake_temps.append(FI_T_curr)
                RO_brake_temps.append(RO_T_curr)
                RI_brake_temps.append(RI_T_curr)

            # Populate left/right turn direction arrays
            if turn_dirs[index] == curve.Turn.LEFT:
                FR_brake_temps.append(FO_T_curr)
                FL_brake_temps.append(FI_T_curr)
                RR_brake_temps.append(RO_T_curr)
                RL_brake_temps.append(RI_T_curr)
            else:
                FR_brake_temps.append(FI_T_curr)
                FL_brake_temps.append(FO_T_curr)
                RR_brake_temps.append(RI_T_curr)
                RL_brake_temps.append(RO_T_curr)

            F_brake_temps.append(np.max([FO_T_curr, FI_T_curr]))
            R_brake_temps.append(np.max([RO_T_curr, RI_T_curr]))

        if graph:
            tk = tkinter.Tk()
            fig = Figure(figsize=(10, 10), dpi=100)
            ax1 = fig.add_subplot(111)
            canvas = FigureCanvasTkAgg(fig, tk)
            canvas.draw()
            toolbar = NavigationToolbar2Tk(canvas, tk)
            canvas.get_tk_widget().pack()
            toolbar.update()

            ax1.plot(np.arange(len(F_brake_temps)), np.add(np.multiply(F_brake_temps, 9/5), 32), label="F")
            ax1.plot(np.arange(len(R_brake_temps)), np.add(np.multiply(R_brake_temps, 9/5), 32), label="R")
            # ax1.plot(np.arange(len(FR_brake_temps)), np.add(np.multiply(FR_brake_temps, 9/5), 32), label="FR")
            # ax1.plot(np.arange(len(FL_brake_temps)), np.add(np.multiply(FL_brake_temps, 9/5), 32), label="FL")
            # ax1.plot(np.arange(len(RR_brake_temps)), np.add(np.multiply(RR_brake_temps, 9/5), 32), label="RR")
            # ax1.plot(np.arange(len(RL_brake_temps)), np.add(np.multiply(RL_brake_temps, 9/5), 32), label="RL")
            ax1.legend()
            ax1.set_xlabel("Node")
            ax1.set_ylabel("Temperature (F)")

            # ax2 = ax1.twinx()
            # ax2.plot(np.arange(0, len(self.AX), 1), self.AX, color='b')
            # ax2.set_ylabel("Braking Acceleration (G's)")

            tk.mainloop()

class four_wheel:

    def __init__(self, t_len_tot, t_rad, turn_dirs, car, n):
        # print(min(t_rad))
        x = np.sort(copy.deepcopy(t_rad))
        y = np.linspace(len(x), 0, len(x))
        self.t_len_tot = np.array(t_len_tot)
        self.t_rad = np.array(t_rad)
        self.turn_dirs = np.array(turn_dirs)
        self.car = car
        self.n = n

        # Make LapSimData instance to store LAPSIM data.
        self.lapsim_data_storage = LapSimData()

    def run(self):
        # Finding total length of track
        track = np.sum(self.t_len_tot)

        max_corner = self.car.max_corner * 32.2 * 12

        # discretizing track
        n = self.n
        self.dx = track / n

        # print(f"nodes n: {n}")
        # print(f"dx: {self.dx}")

        # nodespace
        nds = np.linspace(0, track, int(n + 1))

        # Determining maximum tangential velocity for every turn given maximum lateral acceleration; length = # of arcs in track
        self.t_vel = np.sqrt(max_corner * self.t_rad)

        # List showing radius at every node. Used to calculate maximum tangential acceleration
        self.nd_rad = np.zeros(int(n + 1))

        self.nturn_dirs = np.empty(int(n + 1), dtype=curve.Turn)
        for i in range(self.n+1):
            np.append(self.nturn_dirs, curve.Turn.LEFT)

        # Initialize data collection
        self.lapsim_data_storage.initialize(n)

        # Each line sets the maximum velocity for each
        self.arc_beginning_node = []  # Stores the beginning node
        for i in np.arange(len(self.t_len_tot)):
            start_index = int(np.ceil(np.sum(self.t_len_tot[0:i]) / self.dx)) # Get index from 0 to n
            end_index = int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / self.dx)) # Get index from 0 to n + 1

            self.nd_rad[start_index:end_index] = self.t_rad[i]
            self.nturn_dirs[start_index:end_index] = self.turn_dirs[i]

            self.arc_beginning_node.append(int(np.ceil(np.sum(self.t_len_tot[0:i]) / self.dx)))
        self.arc_beginning_node.append(n + 1)

        self.t_rad[-1] = self.t_rad[-2]

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n + 1))
        for i in np.arange(len(self.t_len_tot)):
            v2[int(np.ceil(np.sum(self.t_len_tot[0:i]) / self.dx)):int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / self.dx))] = \
                self.t_vel[i]
        v2[-1] = v2[-2]

        for i in np.arange(n, -1, -1):
            snippet = self.car.curve_brake(v2[int(i)], self.nd_rad[int(i)])
            snippet.AX *= 32.17 * 12
            if (np.sqrt(v2[int(i)] ** 2 - 2 * snippet.AX * self.dx) < v2[int(i - 1)]) or (v2[int(i - 1)] == 0.):
                v2[int(i - 1)] = np.sqrt(v2[int(i)] ** 2 - 2 * snippet.AX * self.dx)
            snippet.AX /= (32.17 * 12)
            self.lapsim_data_storage.AX[int(i)] = snippet.AX

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(int(n + 1))

        for i in np.arange(len(self.t_len_tot)):
            v1[int(np.ceil(np.sum(self.t_len_tot[0:i]) / self.dx)):int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / self.dx))] = \
                self.t_vel[i]
        v1[0] = 0
        v1[-1] = v1[-2]

        gear = 0  # transmission gear
        shift_time = self.car.drivetrain.shift_time  # shifting time (seconds)
        shifting = False  # Set to true while shifting
        snippet = None
        for i in np.arange(n):

            # checks if car is braking by looking of v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i + 1)] <= v1[int(i)]:
                v1[int(i + 1)] = v2[int(i + 1)]
                if np.isclose(v2[int(i+1)], 413.32, rtol=0.1):
                    pass
                gear = self.car.drivetrain.gear_vel[
                    int(v1[int(i)] * 0.0568182 * 10)]  # changes to the optimal gear when braking
                shifting = False  # sets to False so the car doesn't shift when it stops braking

                snippet = self.car.curve_brake(v2[int(i)], self.nd_rad[int(i)])  # in/s^2
                snippet.AX *= 32.17 * 12

                if v2[int(i)] ** 2 + 2 * snippet.AX * self.dx >= 0:
                    v2[int(i + 1)] = np.sqrt(v2[int(i)] ** 2 + 2 * snippet.AX * self.dx)
                else: # Make sure car does not go backwards when setting v2 for each index.
                    v2[int(i + 1)] = v2[int(i)]

            else:
                # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
                if (gear >= self.car.drivetrain.gear_vel[int(v1[int(i)] * 0.0568182 * 10)]) and not shifting:
                    snippet = self.car.curve_accel(v1[int(i)], self.nd_rad[int(i)], gear)  # in in/s^2
                    snippet.AX *= 32.17 * 12
                else:
                    snippet = self.car.static_snippet
                    shifting = True
                    shift_time -= self.dx / v1[int(i)]
                    if shift_time <= 0:
                        gear += 1
                        shift_time = self.car.drivetrain.shift_time
                        shifting = False
                # Figure out if the maximum possible acceleration currently is not enough to satisfy the next velocity.
                # If it does not satisfy the next velocity, then replace that next velocity with the velocity produced
                # from the current axial acceleration.
                if (np.sqrt(v1[int(i)] ** 2 + 2 * snippet.AX * self.dx) < v1[int(i + 1)]) or (v1[int(i + 1)] == 0.):
                    v1[int(i + 1)] = np.sqrt(v1[int(i)] ** 2 + 2 * snippet.AX * self.dx)

            # Calculate and record data
            snippet.AX /= (32.17 * 12)  # in g's
            self.lapsim_data_storage.append_data_arrays(snippet, int(i)) # Positive AY is turning right, negative AY is turning left.

        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n + 1))
        for i in np.arange(int(n + 1)):
            if v1[i] < v2[i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])
        self.lapsim_data_storage.velocity = v3

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(0, len(v2) - 1):
            # calculate time between nodes by averaging the velocities of the nodes at the start and end of the selected time frame
            t += self.dx / np.average([v3[i], v3[i + 1]])
            self.lapsim_data_storage.time_array.append(t)
        print(f"Time: {t}")
        # print(f"Time: {t} seconds")

        # self.lapsim_data_storage.brake_temp_post_processing(turn_dirs=self.nturn_dirs, car=self.car, graph=True)

        self.n = n
        self.nds = nds
        self.v3 = v3
        self.v2 = v2
        self.v1 = v1
        self.t = t

        # tk = tkinter.Tk()
        # fig = Figure(figsize=(10, 10), dpi=100)
        # ax = fig.add_subplot(111)
        # canvas = FigureCanvasTkAgg(fig, tk)
        # canvas.draw()
        # toolbar = NavigationToolbar2Tk(canvas, tk)
        # canvas.get_tk_widget().pack()
        # toolbar.update()
        #
        # ax.plot(np.linspace(0, len(self.v2), len(self.v2)), v2, color="red")
        # ax.plot(np.linspace(0, len(self.v3), len(self.v3)), v3, color="blue")
        # ax.plot(np.linspace(0, len(self.v1), len(self.v1)), v1, color="green")
        # ax.legend()
        # ax.grid()
        # tk.mainloop()

        # plt.plot(self.nds, self.W_out_f_array)
        # plt.show()

        # Print values for lateral and axial acceleration:
        # for index, i in enumerate(self.AY):
        #     print(i)

        # print("Axial accel (g):")
        # for i in self.AX:
        #     print(i)

        return nds / 12, v1 / 17.6, t