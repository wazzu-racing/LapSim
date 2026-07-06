import csv
import math
import os
import tkinter
import time
import scipy
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.signal import butter, filtfilt, lfilter, savgol_filter
from scipy.spatial.distance import chebyshev

from models.car_model import car

class Component_Validation:

    def __init__(self, car, csv_path, new_data=False):
        self.start_time = time.perf_counter()

        self.csv_path = csv_path

        self.car = car

        self.MR_F, self.MR_R = 1.0, 1.0 # For the 73

        self.AY_real_raw = [] # g's
        self.AX_real_raw = [] # g's
        self.FR_dis_real = [] # inches
        self.FL_dis_real = [] # inches
        self.RL_dis_real = [] # inches
        self.RR_dis_real = [] # inches

        # Filtered arrays
        self.AY_real_rolling_average = [] # g's
        self.AX_real_rolling_average = [] # g's
        self.AY_real_custom = [] # g's
        self.AX_real_custom = [] # g's

        self.FR_dis_sim = [] # inches
        self.FL_dis_sim = [] # inches
        self.RL_dis_sim = [] # inches
        self.RR_dis_sim = [] # inches

        self.FR_load_real = [] # lbs
        self.FL_load_real = [] # lbs
        self.RR_load_real = [] # lbs
        self.RL_load_real = [] # lbs

        self.parse_acceleration(csv_path, new_data=new_data)
        self.parse_displacement(csv_path, new_data=new_data)

    def parse_acceleration(self, csv_path, new_data=False):
        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            if new_data:
                self.AY_real_raw.append(float(line[35]) / 9.81)
                self.AX_real_raw.append(float(line[36]) / 9.81)
            else:
                self.AY_real_raw.append(float(line[33]) / 9.81)
                self.AX_real_raw.append(float(line[34]) / 9.81)

    def parse_displacement(self, csv_path, new_data=False):
        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        # NEW DATA
        # # Skid pad
        # FL_shift_factor = 1
        # FR_shift_factor = 1
        # RL_shift_factor = 1
        # RR_shift_factor = 1

        # OLD DATA
        # Endurance
        # FR_shift_factor = 1.1
        # FL_shift_factor = 1.92
        # RL_shift_factor = 1
        # RR_shift_factor = 1 # not set

        # Skid pad
        # FR_shift_factor = 0.65
        # FL_shift_factor = 1.21
        # RL_shift_factor = 1.12

        # Accel
        FR_shift_factor = 0.65
        FL_shift_factor = 1.21
        RL_shift_factor = 1.12
        RR_shift_factor = 0 # not usable

        for index, line in enumerate(reader):
            # Skip the first line, as it is just header
            if index == 0:
                continue

            if new_data:
                self.FL_dis_real.append(-(float(line[41]) * self.MR_F) + FL_shift_factor)
                self.FR_dis_real.append(-(float(line[42]) * self.MR_F) + FR_shift_factor)
                self.RL_dis_real.append(-(float(line[44]) * self.MR_R) + RL_shift_factor)
                self.RR_dis_real.append(-(float(line[43]) * self.MR_R) + RR_shift_factor)
            else:
                self.FL_dis_real.append(-(float(line[39]) * self.MR_F) + FL_shift_factor)
                self.FR_dis_real.append(-(float(line[40]) * self.MR_F) + FR_shift_factor)
                self.RL_dis_real.append(-(float(line[42]) * self.MR_R) + RL_shift_factor)

    def filter_acceleration(self):
        np_raw_AX, np_raw_AY = np.array(self.AX_real_raw), np.array(self.AY_real_raw)

        # fs = 50 # sample rate Hz
        # cutoff = 3    # Hz
        # b, a = butter(4, cutoff/(fs/2), btype='low')
        #
        # ax_filt = filtfilt(b, a, np_raw_AX)
        # ay_filt = filtfilt(b, a, np_raw_AY)

        # ax_filt = savgol_filter(ax_filt, window_length=11, polyorder=3)
        # ay_filt = savgol_filter(ay_filt, window_length=11, polyorder=3)

        def ema_scipy(data, alpha):
            # Coefficients for the EMA difference equation
            # b = [alpha], a = [1, -(1 - alpha)]
            b = [alpha]
            a = [1, -(1 - alpha)]

            # Apply the filter along the data array
            return lfilter(b, a, data)

        alpha = 0.05  # Smoothing factor (0 < alpha <= 1)

        AX_lowpass = ema_scipy(np_raw_AX, alpha)
        AY_lowpass = ema_scipy(np_raw_AY, alpha)
        # AX_lowpass = ax_filt
        # AY_lowpass = ay_filt

        # RA_window_size = 21 # Must be odd to have the moving average be centered on the current value
        #
        # self.AX_real_rolling_average = np.convolve(np_raw_AX, np.ones(RA_window_size) / RA_window_size, mode='same')
        # self.AX_real_rolling_average[:int(RA_window_size/2)] = np.nan # Remove the elements which are invalid
        #
        # self.AY_real_rolling_average = np.convolve(np_raw_AY, np.ones(RA_window_size) / RA_window_size, mode='same')
        # self.AY_real_rolling_average[:int(RA_window_size/2)] = np.nan # Remove the elements which are invalid

        self.AY_real_custom = AY_lowpass
        self.AX_real_custom = AX_lowpass

        # moving_average_AY = self.AY_real
        # moving_average_AX = self.AX_real
        #
        # smoothing_constant = 0.15
        #
        # for i in range(len(self.AY_real_rolling_average)):
        #     if i >= int(RA_window_size/2):
        #         prev_AX, prev_AY = 0, 0
        #
        #         if i > int(RA_window_size/2) and len(self.AX_real_custom) > 0:
        #             prev_AX = self.AX_real_custom[-1]
        #             prev_AY = self.AY_real_custom[-1]
        #
        #         self.AX_real_custom.append(smoothing_constant * self.AX_real_rolling_average[i] + (1 - smoothing_constant) * prev_AX)
        #         self.AY_real_custom.append(smoothing_constant * self.AY_real_rolling_average[i] + (1 - smoothing_constant) * prev_AY)

    def calculate_wheel_displacement(self):
        self.car.front_outer_displacement = 0
        self.car.front_inner_displacement = 0
        self.car.rear_inner_displacement = 0
        self.car.rear_outer_displacement = 0

        calc_count = 0
        total_count = 0
        for index, AY in enumerate(self.AY_real_custom):
            if self.car.accel(abs(AY), self.AX_real_custom[index]):
                if AY > 0:
                    self.FR_dis_sim.append(self.car.front_inner_displacement)
                    self.FL_dis_sim.append(self.car.front_outer_displacement)
                    self.RL_dis_sim.append(self.car.rear_outer_displacement)
                    self.RR_dis_sim.append(self.car.rear_inner_displacement)
                else:
                    self.FR_dis_sim.append(self.car.front_outer_displacement)
                    self.FL_dis_sim.append(self.car.front_inner_displacement)
                    self.RL_dis_sim.append(self.car.rear_inner_displacement)
                    self.RR_dis_sim.append(self.car.rear_outer_displacement)
                calc_count += 1
            else:
                self.FR_dis_sim.append(self.FR_dis_sim[-1] if len(self.FR_dis_sim) > 0 else 0)
                self.FL_dis_sim.append(self.FL_dis_sim[-1] if len(self.FL_dis_sim) > 0 else 0)
                self.RL_dis_sim.append(self.RL_dis_sim[-1] if len(self.RL_dis_sim) > 0 else 0)
                self.RR_dis_sim.append(self.RR_dis_sim[-1] if len(self.RR_dis_sim) > 0 else 0)
            total_count += 1

        print(f"Percent calculated: {calc_count/total_count*100:.2f}%")

    def graph_acceleration(self, graph_AY):
        tk = tkinter.Tk()
        fig = Figure(figsize=(15, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        if graph_AY:
            ax.plot(self.AY_real_custom)
        else:
            ax.plot(self.AX_real_custom)

        tk.mainloop()

    def graph_displacement(self, wheel):
        tk = tkinter.Tk()
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        match wheel:
            case "FR":
                ax.set_title("Front Right Displacement")
                ax.plot(self.FR_dis_sim, label="Sim")
                ax.plot(self.FR_dis_real, label="Real")
            case "FL":
                ax.set_title("Front Left Displacement")
                ax.plot(self.FL_dis_sim, label="Sim")
                ax.plot(self.FL_dis_real, label="Real")
            case "RL":
                ax.set_title("Rear Left Displacement")
                ax.plot(self.RL_dis_sim, label="Sim")
                ax.plot(self.RL_dis_real, label="Real")
            case "RR":
                ax.set_title("Rear Right Displacement")
                ax.plot(self.RR_dis_sim, label="Sim")
                ax.plot(self.RR_dis_real, label="Real")

        ax.set_xlabel("Data Point")
        ax.set_xlabel("Displacement")
        tk.mainloop()

    def graph_gg_diagram(self):
        tk = tkinter.Tk()
        fig = Figure(figsize=(15, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        AY_converted = [abs(x) for x in self.AY_real_custom]
        AX_converted = self.AX_real_custom
        #
        # # Step 1: Calculate Q1, Q3, and IQR
        # q1, q3 = np.percentile(AX_converted, [10, 75])
        # iqr = q3 - q1
        #
        # # Step 2: Define bounds
        # lower_bound = q1 - 1.5 * iqr
        # upper_bound = q3 + 1.5 * iqr
        # print(lower_bound, upper_bound)
        #
        # # Step 3: Filter the array
        # filtered_AX, filtered_AY = [], []
        # for index, AX in enumerate(AX_converted):
        #     if lower_bound < AX < upper_bound:
        #         filtered_AX.append(AX)
        #         filtered_AY.append(AY_converted[index])

        ax.scatter(AY_converted, AX_converted)

        ax.set_xlabel("AY")
        ax.set_ylabel("AX")
        tk.mainloop()

    def export_to_csv(self, type):
        csv_file = open(os.getcwd()+"/output/displacement_comparison.csv", "w", newline='\n')
        writer = csv.writer(csv_file)

        match type:
            case "FR":
                writer.writerow(["Sim_FR_displacement", "Real FR displacement"])
                for index, AY in enumerate(self.FR_dis_real):
                    writer.writerow([self.FR_dis_real[index]])
                    # print(self.FR_dis_real[index])
            case "FL":
                writer.writerow(["Sim_FL_displacement", "Real FL displacement"])
                for index, AY in enumerate(self.FL_dis_sim):
                    writer.writerow([AY, self.FL_dis_real[index]])
            case "RL":
                writer.writerow(["Sim_RL_displacement", "Real RL displacement"])
                for index, AY in enumerate(self.RL_dis_sim):
                    writer.writerow([AY, self.RL_dis_real[index]])
            case "RR":
                writer.writerow(["Sim_RR_displacement", "Real RR displacement"])
                for index, AY in enumerate(self.RR_dis_sim):
                    writer.writerow([AY, self.RR_dis_real[index]])
            case "accel":
                writer.writerow(["AY", "AX"])
                for index, AY in enumerate(self.AY_real_custom):
                    writer.writerow([AY, self.AX_real_custom[index]])

        csv_file.close()

        print(f"Time taken: {time.perf_counter() - self.start_time:.3f} seconds")

    def calculate_RL_dis_error(self):
        error_arr = []
        for index, RL_dis in enumerate(self.RL_dis_sim):
            error_arr.append(((RL_dis - self.RL_dis_real[index])/self.RL_dis_real[index])*100)

    def determine_load_from_displacement(self):
        # # Apply a rolling average to the displacement data
        # np_raw_FR, np_raw_FL, np_raw_RL, np_raw_RR = np.array(self.FR_dis_real), np.array(self.FL_dis_real), np.array(self.RL_dis_real), np.array(self.RR_dis_real)
        #
        # window_size = 39 # Must be odd to have the moving average be centered on the current value
        #
        # # FR
        # try:
        #     moving_average_FR = np.convolve(np_raw_FR, np.ones(window_size) / window_size, mode='same')
        #     moving_average_FR[:int(window_size/2)] = np.nan # Remove the elements which are invalid
        # except ValueError:
        #     print("FR does not have valid data.")
        #
        # # FL
        # try:
        #     moving_average_FL = np.convolve(np_raw_FL, np.ones(window_size) / window_size, mode='same')
        #     moving_average_FL[:int(window_size/2)] = np.nan # Remove the elements which are invalid
        # except ValueError:
        #     print("FL does not have valid data.")
        #
        # # RL
        # try:
        #     moving_average_RL = np.convolve(np_raw_RL, np.ones(window_size) / window_size, mode='same')
        #     moving_average_RL[:int(window_size/2)] = np.nan # Remove the elements which are invalid
        # except ValueError:
        #     print("RL does not have valid data.")
        #
        # # RR
        # try:
        #     moving_average_RR = np.convolve(np_raw_RR, np.ones(window_size) / window_size, mode='same')
        #     moving_average_RR[:int(window_size/2)] = np.nan # Remove the elements which are invalid
        # except ValueError:
        #     print("RR does not have valid data.")

        for index, FR_dis in enumerate(self.FR_dis_real):
            self.FR_load_real.append(self.FR_dis_real[index] * car.K_RF)
            self.FL_load_real.append(self.FL_dis_real[index] * car.K_RF)
            self.RL_load_real.append(self.RL_dis_real[index] * car.K_RR)
            self.RR_load_real.append(car.W_car - self.FR_load_real[index] - self.FL_load_real[index] - self.RL_load_real[index])

    def calculate_acceleration_from_slip_ratio(self):
        # Read into string
        csv_file = open(self.csv_path, newline='\n')
        reader = csv.reader(csv_file)
        next(reader)

        rpm = []
        velocity, angular_velocity_at_0 = [], []
        slip_ratio = []
        write_millis = []
        accel_from_velocity = []

        for index, line in enumerate(reader):

            rpm.append(float(line[10]) / (self.car.drivetrain.primary_drive * self.car.drivetrain.gear_ratios[0] * self.car.drivetrain.final_drive))
            velocity.append(float(line[18]) * 1056) # convert to in/min
            write_millis.append(float(line[0]))

            # Calculate how fast the tires should be spinning to give 0 acceleration
            angular_velocity_at_0.append(velocity[index] / (2 * 10.25 * math.pi)) # given in RPM

            if angular_velocity_at_0[index] > 0:
                slip_ratio.append(rpm[index] / angular_velocity_at_0[index])

        indices = (6200, 6800)

        # self.AX_real = [0 if x < 0 else x for x in self.AX_real]

        slip_ratio = slip_ratio[indices[0]:indices[1]]
        self.AX_real_custom = self.AX_real_custom[indices[0]:indices[1]]
        self.RL_load_real = self.RL_load_real[indices[0]:indices[1]]
        self.RL_dis_real = self.RL_dis_real[indices[0]:indices[1]]
        self.RR_load_real = self.RR_load_real[indices[0]:indices[1]]
        write_millis = write_millis[indices[0]:indices[1]]
        velocity = velocity[indices[0]:indices[1]]
        RL_load_C, RR_load_C = self.RL_load_real[0], self.RR_load_real[0]

        # Check if AX can produce the appropriate speed
        predicted_velocity = [0]
        for index, AX in enumerate(self.AX_real_custom):
            if index == 0: continue
            predicted_velocity.append(predicted_velocity[index-1] + AX*386.09 * (write_millis[index] - write_millis[index-1])/1000)
        predicted_velocity = [x*0.0568182 for x in predicted_velocity]

        accel_guess = []
        for index, load in enumerate(self.RL_load_real):
            #left = self.car.tires.FX_curves.eval(slip_ratio[index] - 1, self.RL_load_real[index], self.car.CMB_RT_R*(self.car.W_3 + self.RL_load_real[index]-RL_load_C)/self.car.K_RR + self.car.CMB_STC_R)
            #right = self.car.tires.FX_curves.eval(slip_ratio[index] - 1, self.RR_load_real[index], self.car.CMB_RT_R*(self.car.W_4 + self.RR_load_real[index]-RR_load_C)/self.car.K_RR + self.car.CMB_STC_R)
            left = self.car.tires.FX_curves.eval(slip_ratio[index] - 1, 175, self.car.CMB_RT_R*(self.car.W_3 + self.RL_load_real[index]-RL_load_C)/self.car.K_RR + self.car.CMB_STC_R)
            right = self.car.tires.FX_curves.eval(slip_ratio[index] - 1, 175, self.car.CMB_RT_R*(self.car.W_4 + self.RR_load_real[index]-RR_load_C)/self.car.K_RR + self.car.CMB_STC_R)

            accel_guess.append((left+right)/self.car.W_car)

            print(f"RL load: {self.car.W_3 + self.RL_load_real[index]-RL_load_C}\n"
                  f"RR load: {self.car.W_3 + self.RR_load_real[index]-RR_load_C}\n")

        csv_file = open("output/slip_ratio_accel_comp.csv", "w", newline='\n')
        writer = csv.writer(csv_file)
        writer.writerow(["Guess AX", "Real AX"])
        for index, accel in enumerate(accel_guess):
            writer.writerow([accel, self.AX_real_custom[index]])
        csv_file.close()

        # Convert from in/min to mph
        velocity = [x*0.00094697 for x in velocity]

        tk = tkinter.Tk()
        fig = Figure(figsize=(15, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()
        ax.set_title("Load on tire (lbs)")
        ax.plot(self.RL_load_real)
        # ax.legend()
        tk.mainloop()

        tk = tkinter.Tk()
        fig = Figure(figsize=(15, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()
        ax.set_title("Real vs. Predicted Velocity")
        ax.plot(velocity, label='real')
        ax.plot(predicted_velocity, label='estimate')
        ax.legend()
        tk.mainloop()

        tk = tkinter.Tk()
        fig = Figure(figsize=(15, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()
        ax.set_title("Real vs. Predicted Acceleration")
        ax.set_xlabel("Data point")
        ax.set_ylabel("Acceleration (g's)")
        ax.plot(self.AX_real_custom, label='real, filtered')
        ax.plot(accel_guess, label='estimate')
        ax.legend()
        tk.mainloop()

        # # Make accel from velocity
        # velocity = [x/60 for x in velocity] # convert to in/s^2
        # prev_vel = velocity[1]
        # prev_time = write_millis[1]
        # vel_length = 1
        # for index, vel in enumerate(velocity):
        #     if index == 0: continue
        #
        #     if vel != velocity[index-1] and vel_length > 1:
        #         accel_from_velocity.extend(np.full(vel_length, (vel-prev_vel)/((write_millis[index]-prev_time)/1000)))
        #
        #         prev_vel = velocity[index-1]
        #         prev_time = write_millis[index-1]
        #         vel_length=1
        #     else:
        #         vel_length+=1
        # accel_from_velocity = [x/(32.17 * 12) for x in accel_from_velocity]


racecar = car()
comp_val = Component_Validation(racecar, "validator/data/mock_auto_92.csv", new_data=True)

comp_val.filter_acceleration()
# comp_val.graph_acceleration(True)
comp_val.graph_gg_diagram()
# comp_val.determine_load_from_displacement()
# comp_val.calculate_acceleration_from_slip_ratio()

# comp_val.calculate_wheel_displacement()
# comp_val.calculate_RL_dis_error()
# comp_val.graph_acceleration(False)
# comp_val.graph_gg_diagram()
# comp_val.graph_displacement("FR")
# comp_val.export_to_csv("FR")
# comp_val.determine_load_from_displacement()