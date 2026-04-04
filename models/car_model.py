import copy
import math
import os
import pickle
from dataclasses import dataclass

from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import csv

from models import drivetrain_model
from models import tire_model
from interface.file_management.file_manager import file_manager

class car():

    # weight over front left wheel
    W_1 = 185.7365
    # weight over front right wheel
    W_2 = 185.7365
    # weight over rear left wheel
    W_3 = 170.7635
    # weight over rear right wheel
    W_4 = 170.7635
    # length of wheelbase (in)
    l = 60.04
    # vertical center of gravity (in)
    h = 14
    # in, roll axis height, front and rear
    z_rf = 2
    z_rr = 3
    # Track widths, front and rear (in)
    t_f = 61.3
    t_r = 59.09
    # lb/in, ride rates, front and rear
    K_RF = 189.5 # front
    K_RR = 207.38 # rear
    # lb*ft/deg, roll rates, front and rear (later converted to lb*ft/rad)
    K_rollF = 144439.94389901822
    K_rollR = 142041.8793828892
    #deg/in, camber rates for front and rear
    CMB_RT_F = 1.5
    CMB_RT_R = 1.25
    # deg, static camber rates for front and rear
    CMB_STC_F = 1
    CMB_STC_R = 1
    # in, maximum displacement in jounce for suspension, front and rear
    max_jounce_f = 1
    max_jounce_r = 1
    # Rolling resistance coefficient
    C_rr = 0.01

    # Converting roll rates to ft*lb/rad
    K_rollF *= 180/np.pi
    K_rollR *= 180/np.pi
    # weight over front track
    W_f = W_1 + W_2
    # weight over rear track
    W_r = W_3 + W_4
    # total weight of car (minus driver) (lbm)
    W_car = W_f + W_r
    # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
    W_bias = W_f/W_car
    # in, distance from CG to rear track
    b = l * W_bias
    # in, distance from CG to front track
    a = l - b
    # in, CG height to roll axis
    H = h - (a*z_rf + b*z_rr)/l
    # Rolling resistance force, in/s^2
    a_rr = -(C_rr * W_1 + C_rr * W_2 + C_rr * W_3 + C_rr * W_4)/W_car * 386.089

    # Weight forces on wheels
    W_out_f =0 # vertical force on front outer wheel
    W_in_f =0  # vertical force on front inner wheel
    W_out_r = 0 # vertical force on rear outer wheel
    W_in_r = 0  # vertical force on rear inner wheel
    #lateral forces on wheels
    FY_out_f = 0 # max possible lateral force from front outer wheel
    FY_in_f = 0  # max possible lateral force from front inner wheel
    FY_out_r = 0 # max possible lateral force from rear outer wheel
    FY_in_r = 0  # max possible lateral force from rear inner wheel
    # axial forces on wheels
    FX_out_f = 0 # max possible axial acceleration from front outer wheel
    FX_in_f = 0  # max possible axial acceleration from front inner wheel
    FX_out_r = 0 # max possible axial acceleration from rear outer wheel
    FX_in_r = 0  # max possible axial acceleration from rear inner wheel
    # in, displacement of tires in vertical based on change in weight on tires. Default to 0.
    front_inner_displacement = 0 # Front inner wheel vertical displacement in inches
    front_outer_displacement = 0 # Front outer wheel vertical displacement in inches
    rear_inner_displacement = 0 # Rear inner wheel vertical displacement in inches
    rear_outer_displacement = 0 # Rear outer wheel vertical displacement in inches
    # degrees, theta of accel force of car
    theta_accel = 0

    velocity = 0

    # aero csv file delimiter
    aero_delimiter = ';'

    tires = None
    train = None

    def __init__(self):
        self.aero_csv_file_path = file_manager.get_temp_folder_path(
            os.path.join(Path(__file__).resolve().parent.parent, "config_data", "DEFAULT_AERO_ARRAY.csv"))
        self.tire_file_path = ""
        self.drivetrain_file_path = ""

        self.aero_arr = [] # drag force acceleration (G's) emitted on vehicle (index = mph)
        with open(self.aero_csv_file_path, newline='') as f:
            reader = csv.reader(f, delimiter=self.aero_delimiter)
            for line in reader:
                for i in line:
                    self.aero_arr.append(float(i)/self.W_car)

        # importing tire model
        try:
            with open(self.tire_file_path, 'rb') as f:
                self.tires = pickle.load(f)
        except Exception:
            cornering_data = file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data","cornering_data.dat"))
            accel_data = file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data","acceleration_data.dat"))
            self.tires = tire_model.tire(cornering_data, accel_data)

        # importing drivetrain model
        try:
            with open(self.drivetrain_file_path, 'rb') as f:
                self.drivetrain = pickle.load(f)
        except Exception:
            self.drivetrain = drivetrain_model.drivetrain(engine_data=file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data", "engine_array.csv")))

        self.file_location = ""

        self.aero_arr.reverse()
        self.compute_traction()

        # future code for accounting for tire orientation
        '''
        min_crv = 70 # minimum curve radius (in) (ideally less than the smallest possible curve given the vehicle's steering geometry)
        max_crv = 1000 # maximum curve radius (in) (the radius at which error from large cruve approximations become negligable)
        d_crv = 5
        self.curves = np.linspace(min_crv, max_crv, int((max_crv-min_crv)/d_crv)+1)
        V_arr = np.linspace(0, 100, 101) * 17.6
        
        start_time = time.time()
        for r in self.curves:
            C_r_in = 0
            C_r_out = 0
            S_c = 0
            
            break_loop = False
            for V in V_arr:
                AY = V**2/r / 12 * 32.17 # total lateral force on car body

                while True:
                    S_c += 0.1
                    # slip angle of rear inner and outter tires respectively
                    if r == 0:
                        S_r_in = S_c
                        S_r_out = S_c
                    else:
                        S_r_in  = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a - np.cos(S_c)*self.t_r/2)))
                        S_r_out = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a + np.cos(S_c)*self.t_r/2)))

                    low = 0
                    high = 3
                    
                    for i in range(20):
                        
                        AX = (low + high) / 2

                        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
                        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)
                        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
                        W_shift_x = roll * self.H # lateral shift in center of mass (in)

                        W_f_out = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # force on front outter wheel
                        W_f_in = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # force on front inner wheel
                        W_r_out = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # force on rear outter wheel
                        W_r_in = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # force on rear inner wheel

                        C_f_out = abs(self.CMB_STC_F + (W_f_out-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
                        C_f_in = abs(self.CMB_STC_F + (W_f_in-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
                        C_r_out = abs(self.CMB_STC_R + (W_r_out-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
                        C_r_in = abs(self.CMB_STC_R + (W_r_in-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

                        FY_r_in = abs(self.tires.FY_curves.eval(S_r_in, W_r_in, C_r_in))
                        FY_r_out = abs(self.tires.FY_curves.eval(S_r_out, W_r_out, C_r_out))
                        FX_r_in = (1 - (FY_r_in / abs(self.tires.FY_curves.get_max(W_r_in, C_r_in)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_r_in, C_r_in))
                        FX_r_out = (1 - (FY_r_out / abs(self.tires.FY_curves.get_max(W_r_out, C_r_out)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_r_out, C_r_out))
                        MZ_r_in = abs(self.tires.aligning_torque.eval(S_r_in, W_r_in, C_r_in))
                        MZ_r_out = abs(self.tires.aligning_torque.eval(S_r_out, W_r_out, C_r_out))

                        if FY_r_in + FY_r_out < 0.7 * AY * self.W_car * (1-self.W_bias):
                            high = AX
                            continue

                        MZ_last =  0   
                        steeeeeeeeeer = 0      
                        for steer in range(20):
                            if r == 0:
                                S_f_in = S_c + steer
                                S_f_out = S_c + steer
                            else:
                                S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
                                S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))

                            FY_f_in = abs(self.tires.FY_curves.eval(S_f_in, W_f_in, C_f_in))
                            FY_f_out = abs(self.tires.FY_curves.eval(S_f_out, W_f_out, C_f_out))
                            MZ_f_in = abs(self.tires.aligning_torque.eval(S_f_in, W_f_in, C_f_in))
                            MZ_f_out = abs(self.tires.aligning_torque.eval(S_f_out, W_f_out, C_f_out))

                            MZ_tot = MZ_f_in + MZ_f_out + MZ_r_in + MZ_r_out + (FY_r_in + FY_r_out)*self.a - (FY_f_in + FY_f_out)*self.b
                            if MZ_tot < 0:
                                MZ_last = MZ_tot

                            else:
                                steeeeeeeeeer = ((steer-1) * MZ_tot - steer * MZ_last) / (MZ_tot + MZ_last)
                                break
                        
                        steer = steeeeeeeeeer
                        if r == 0:
                            S_f_in = S_c + steer
                            S_f_out = S_c + steer
                        else:
                            S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
                            S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))

                        FX_f_in = (1 - (FY_f_in / abs(self.tires.FY_curves.get_max(W_f_in, C_f_in)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_f_in, C_f_in))
                        FX_f_out = (1 - (FY_f_out / abs(self.tires.FY_curves.get_max(W_f_out, C_f_out)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_f_out, C_f_out))
                        
                        if FX_f_in + FX_f_out + FX_r_in + FX_r_out < AX * self.W_car:
                            high = AX
                        else:
                            low = AX


                    if S_c > 20:
                        break_loop = True
                        break

                # lateral forces of rear inner and outter tires respectively
                FY_r_in = self.tires.FY_curves.eval
                if break_loop:
                    break

            break
        print(time.time() - start_time)
        '''

    class Car_Data_Snippet:
        """
        Represents the data that the car model experiences at an instance along the track.
        """
        def __init__(self, racecar, index):
            # Acceleration & movement
            self.AX = racecar.instant_AX
            self.AY = racecar.instant_AY
            self.velocity = racecar.velocity
            # Tire measurements
            self.front_outer_displacement = racecar.front_outer_displacement
            self.front_inner_displacement = racecar.front_inner_displacement
            self.rear_outer_displacement = racecar.rear_outer_displacement
            self.rear_inner_displacement = racecar.rear_inner_displacement
            self.FO_camber = racecar.C_out_f
            self.FI_camber = racecar.C_out_f
            self.RO_camber = racecar.C_out_f
            self.RI_camber = racecar.C_out_f
            # Tire forces
            self.FO_load = racecar.W_out_f
            self.FI_load = racecar.W_in_f
            self.RO_load = racecar.W_out_r
            self.RI_load = racecar.W_in_r
            self.FO_FY = racecar.FY_out_f
            self.FI_FY = racecar.FY_in_f
            self.RO_FY = racecar.FY_out_r
            self.RI_FY = racecar.FY_in_r
            self.FO_FX = racecar.FX_out_f
            self.FI_FX = racecar.FX_in_f
            self.RO_FX = racecar.FX_out_r
            self.RI_FX = racecar.FX_in_r

            self.racecar = racecar
            self.index = index

        @classmethod
        def get_interpolated_copy(cls, curr_snippet, curr_ratio, prev_ratio):
            snippet = cls(curr_snippet.racecar, -1)

            # Interpolate
            if curr_snippet.AX > 0: # If car is accelerating
                snippet.AX = curr_ratio * curr_snippet.AX + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].AX
                snippet.AY = curr_ratio * curr_snippet.AY + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].AY
                snippet.velocity = curr_ratio * snippet.velocity + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].velocity
                # Tire measurements
                snippet.front_outer_displacement = curr_ratio * curr_snippet.front_outer_displacement + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].front_outer_displacement
                snippet.front_inner_displacement = curr_ratio * curr_snippet.front_inner_displacement + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].front_inner_displacement
                snippet.rear_outer_displacement = curr_ratio * curr_snippet.rear_outer_displacement + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].rear_outer_displacement
                snippet.rear_inner_displacement = curr_ratio * curr_snippet.rear_inner_displacement + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].rear_inner_displacement
                snippet.FO_camber = curr_ratio * curr_snippet.FO_camber + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FO_camber
                snippet.FI_camber = curr_ratio * curr_snippet.FI_camber + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FI_camber
                snippet.RO_camber = curr_ratio * curr_snippet.RO_camber + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RO_camber
                snippet.RI_camber = curr_ratio * curr_snippet.RI_camber + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RI_camber
                # Tire forces
                snippet.FO_load = curr_ratio * curr_snippet.FO_load + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FO_load
                snippet.FI_load = curr_ratio * curr_snippet.FI_load + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FI_load
                snippet.RO_load = curr_ratio * curr_snippet.RO_load + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RO_load
                snippet.RI_load = curr_ratio * curr_snippet.RI_load + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RI_load
                snippet.FO_FY = curr_ratio * curr_snippet.FO_FY + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FO_FY
                snippet.FI_FY = curr_ratio * curr_snippet.FI_FY + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FI_FY
                snippet.RO_FY = curr_ratio * curr_snippet.RO_FY + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RO_FY
                snippet.RI_FY = curr_ratio * curr_snippet.RI_FY + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RI_FY
                snippet.FO_FX = curr_ratio * curr_snippet.FO_FX + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FO_FX
                snippet.FI_FX = curr_ratio * curr_snippet.FI_FX + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].FI_FX
                snippet.RO_FX = curr_ratio * curr_snippet.RO_FX + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RO_FX
                snippet.RI_FX = curr_ratio * curr_snippet.RI_FX + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].RI_FX
            else: # If car is braking
                snippet.AX = curr_ratio * curr_snippet.AX + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].AX
                snippet.AY = curr_ratio * curr_snippet.AY + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].AY
                snippet.velocity = curr_ratio * snippet.velocity + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].velocity
                # Tire measurements
                snippet.front_outer_displacement = curr_ratio * curr_snippet.front_outer_displacement + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].front_outer_displacement
                snippet.front_inner_displacement = curr_ratio * curr_snippet.front_inner_displacement + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].front_inner_displacement
                snippet.rear_outer_displacement = curr_ratio * curr_snippet.rear_outer_displacement + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].rear_outer_displacement
                snippet.rear_inner_displacement = curr_ratio * curr_snippet.rear_inner_displacement + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].rear_inner_displacement
                snippet.FO_camber = curr_ratio * curr_snippet.FO_camber + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FO_camber
                snippet.FI_camber = curr_ratio * curr_snippet.FI_camber + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FI_camber
                snippet.RO_camber = curr_ratio * curr_snippet.RO_camber + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RO_camber
                snippet.RI_camber = curr_ratio * curr_snippet.RI_camber + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RI_camber
                # Tire forces
                snippet.FO_load = curr_ratio * curr_snippet.FO_load + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FO_load
                snippet.FI_load = curr_ratio * curr_snippet.FI_load + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FI_load
                snippet.RO_load = curr_ratio * curr_snippet.RO_load + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RO_load
                snippet.RI_load = curr_ratio * curr_snippet.RI_load + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RI_load
                snippet.FO_FY = curr_ratio * curr_snippet.FO_FY + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FO_FY
                snippet.FI_FY = curr_ratio * curr_snippet.FI_FY + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FI_FY
                snippet.RO_FY = curr_ratio * curr_snippet.RO_FY + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RO_FY
                snippet.RI_FY = curr_ratio * curr_snippet.RI_FY + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RI_FY
                snippet.FO_FX = curr_ratio * curr_snippet.FO_FX + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FO_FX
                snippet.FI_FX = curr_ratio * curr_snippet.FI_FX + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].FI_FX
                snippet.RO_FX = curr_ratio * curr_snippet.RO_FX + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RO_FX
                snippet.RI_FX = curr_ratio * curr_snippet.RI_FX + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].RI_FX

            return snippet

    def compute_traction(self):
        # finding max cornering (lateral) acceleration
        low_guess = 0 # low estimate for max cornering (lateral) acceleration (g)
        high_guess = 3 # high estimate for max cornering (lateral) acceleration (g)

        # when the low and high estimates converge, the converging value is recorded as the max cornering (lateral) acceleration
        while high_guess - low_guess > 0.00001:
            guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering (lateral) acceleration
            out = self.accel(guess, 0)
            if out: # sets low estimate to the guess value if the car can handle cornering (lateral) acceleration equal to the guess value
                low_guess = guess
            else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
                high_guess = guess

        self.max_corner = guess # max cornering (lateral) acceleration (g)
        self.AY = np.linspace(0, self.max_corner, 100)
        self.A_accel = []
        self.A_brake = []
        self.accel_car_data_snippets = []
        self.brake_car_data_snippets = []
        for index, i in enumerate(self.AY):
            self.A_accel.append(self.max_accel(i))
            self.accel_car_data_snippets.append(self.Car_Data_Snippet(self, index))
            self.A_brake.append(self.max_brake(i))
            self.brake_car_data_snippets.append(self.Car_Data_Snippet(self, index))
        self.max_corner -= 0.0001
        # Gear changes
        self.accel(0, 0)
        self.static_snippet = self.Car_Data_Snippet(self, -1) # Used to describe the state of the car during gear changes

    def recalculate_characteristics(self):
        # weight over front track
        self.W_f = self.W_1 + self.W_2
        # weight over rear track
        self.W_r = self.W_3 + self.W_4
        # total weight of car (minus driver) (lbm)
        self.W_car = self.W_f + self.W_r
        # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
        self.W_bias = self.W_f/self.W_car
        # in, distance from CG to rear track
        self.b = self.l * self.W_bias
        # in, distance from CG to front track
        self.a = self.l - self.b
        # in, CG height to roll axis
        self.H = self.h - (self.a*self.z_rf + self.b*self.z_rr)/self.l
        # Rolling resistance force, in/s^2
        self.a_rr = -(self.C_rr * self.W_1 + self.C_rr * self.W_2 + self.C_rr * self.W_3 + self.C_rr * self.W_4)/self.W_car * 386.089

        self.compute_traction()

    # Returns true if the car can generate the axial traction based on AY and AX. Returns false otherwise.
    # AY is magnitude of lateral acceleration, AX is magnitude of axial acceleration, both are measured in g's
    def accel(self, AY, AX, bitch = False):
        self.instant_AY, self.instant_AX = AY, AX

        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        self.W_out_f = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front outter wheel in pounds
        self.W_in_f = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # vertical force on front inner wheel in pounds
        self.W_out_r = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear outter wheel in pounds
        self.W_in_r = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # vertical force on rear inner wheel in pounds

        # Set displacement vars to their values
        self.front_inner_displacement = (self.W_in_f - self.W_1) / self.K_RF # doesn't matter whether W_1 is the outer or inner tire at the moment since both front tires have the same weight.
        self.front_outer_displacement = (self.W_out_f - self.W_2) / self.K_RF # doesn't matter whether W_2 is the outer or inner tire at the moment since both front tires have the same weight.
        self.rear_inner_displacement = (self.W_in_r - self.W_3) / self.K_RR # doesn't matter whether W_3 is the outer or inner tire at the moment since both rear tires have the same weight.
        self.rear_outer_displacement = (self.W_out_r - self.W_4) / self.K_RR # doesn't matter whether W_4 is the outer or inner tire at the moment since both rear tires have the same weight.

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        for i in [self.W_out_f, self.W_in_f, self.W_out_r, self.W_in_r]:
            if i < 0: return False

        self.C_out_f = abs(self.CMB_STC_F + (self.W_out_f-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
        self.C_in_f = abs(self.CMB_STC_F + (self.W_in_f-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        self.C_out_r = abs(self.CMB_STC_R + (self.W_out_r-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        self.C_in_r = abs(self.CMB_STC_R + (self.W_in_r-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        self.FY_out_f = self.tires.traction('corner', self.W_out_f, self.C_out_f) # max possible lateral acceleration from front outter wheel in pounds
        self.FY_in_f = self.tires.traction('corner', self.W_in_f, self.C_in_f)    # max possible lateral acceleration from front inner wheel in pounds
        self.FY_out_r = self.tires.traction('corner', self.W_out_r, self.C_out_r) # max possible lateral acceleration from rear outter wheel in pounds
        self.FY_in_r = self.tires.traction('corner', self.W_in_r, self.C_in_r)    # max possible lateral acceleration from rear inner wheel in pounds

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        if (FY_f > self.FY_out_f+self.FY_in_f) or (FY_r > self.FY_out_r+self.FY_in_r): return False

        if bitch:
            print((self.W_in_f + self.W_out_f) / (self.W_out_f + self.W_out_r + self.W_in_f +self. W_in_r))

        if AX == 0: return True # returning true if no axial acceleration

        f_factor = ((self.FY_out_f + self.FY_in_f)**2 - FY_f**2)**0.5 / (self.FY_out_f + self.FY_in_f)
        r_factor = ((self.FY_out_r + self.FY_in_r)**2 - FY_r**2)**0.5 / (self.FY_out_r + self.FY_in_r)

        self.FX_out_f = f_factor * self.tires.traction('accel', self.W_out_f, self.C_out_f) # max possible axial acceleration from front outter wheel in pounds
        self.FX_in_f = f_factor * self.tires.traction('accel', self.W_in_f, self.C_in_f)    # max possible axial acceleration from front inner wheel in pounds
        self.FX_out_r = r_factor * self.tires.traction('accel', self.W_out_r, self.C_out_r) # max possible axial acceleration from rear outter wheel in pounds
        self.FX_in_r = r_factor * self.tires.traction('accel', self.W_in_r, self.C_in_r)    # max possible axial acceleration from rear inner wheel in pounds

        self.theta_accel = math.atan2(abs(AY), AX) * 180/math.pi

        # Calculating max lateral acceleration from tire traction
        if AX > 0:
            FX = self.FX_out_r + self.FX_in_r
        else:
            FX = self.FX_out_f + self.FX_in_f + self.FX_out_r + self.FX_in_r

        if bitch:
            print(self.FX_out_f / self.W_out_f)
            print(self.FX_in_f / self.W_in_f)
            print(self.FX_out_r / self.W_out_r)
            print(self.FX_in_r / self.W_in_r)

        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX):return False
        else: return True

    # recursive function to find the max axial acceleration; AY is lateral acceleration in g's
    def max_accel(self, AY, low_guess = 0, high_guess = 2):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0000000001:
            return guess

        if self.accel(AY, guess): # sets low estimate to the guess value if the car can handle cornering acceleration equal to the guess value
            return self.max_accel(AY, guess, high_guess)
        else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
            return self.max_accel(AY, low_guess, guess)

    def max_brake(self, AY, low_guess = -3, high_guess = 0):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0000000001:
            return guess

        if self.accel(AY, guess): # sets high estimate to the guess value if the car can handle breaking acceleration equal to the guess value
            return self.max_brake(AY, low_guess, guess)
        else: # sets low estimate to the guess value if the car cannot handle breaking acceleration equal to the guess value
            return self.max_brake(AY, guess, high_guess)

    # calculates the max axial acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_accel(self, v, r, transmission_gear='optimal'):
        snippet = None

        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        returned = False
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY: # If max AY along a turn is more than or equal to the current AY
                # linearly interpolating self.A_accel to find the max acceleration at lateral acceleration AY
                curr_ratio = (AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])
                prev_ratio = (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1])
                snippet = self.Car_Data_Snippet.get_interpolated_copy(self.accel_car_data_snippets[i], curr_ratio, prev_ratio)
                returned = True
                break
        if not returned:
            snippet = copy.deepcopy(self.accel_car_data_snippets[-1])

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's

        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_engn < snippet.AX:
            snippet.AX = A_engn
            snippet.AX -= drag
            return snippet
        snippet.AX -= drag
        return snippet

    # calculates the max braking acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_brake(self, v, r):
        snippet = None

        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        returned = False
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY:
                # linearly interpolating self.A_accel to find the max acceleration at lateral acceleration AY
                curr_ratio = (AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])
                prev_ratio = (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1])
                snippet = self.Car_Data_Snippet.get_interpolated_copy(self.brake_car_data_snippets[i], curr_ratio, prev_ratio)
                returned = True
                break
        if not returned:
            snippet = copy.deepcopy(self.brake_car_data_snippets[-1])

        snippet.AX -= drag # incorporating drag
        # print(snippet.AX)

        return snippet

    # returns drag acceleration (in/s^2) given vehicle speed
    # v = speed (in/s)
    def curve_idle(self, v):
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
        drag *= 32.17 * 12 # converting from G's to in/s^2
        return -drag # returns negative because drag slows the car

    # returns drag force in G's (index = speed of car (mph))
    def get_drag(self, mph):
        if mph >= len(self.aero_arr)-1: # check if car speed exceeds aero_arr size
            return self.aero_arr[-1] # return drag accel value for highest speed if max speed is exceeded
        else:
            # finding drag by linearly interpolating the aero array
            ratio = mph % 1
            return self.aero_arr[int(mph)]*(1-ratio) + self.aero_arr[int(mph)+1]*ratio


    def adjust_weight(self, w):
        ratio = w / self.W_car

        self.W_1 *= ratio
        self.W_2 *= ratio
        self.W_3 *= ratio
        self.W_4 *= ratio
        self.W_car *= ratio
        self.W_f *= ratio
        self.W_r *= ratio
        self.K_RF *= ratio
        self.K_RR *= ratio
        self.K_rollF *= ratio
        self.K_rollR *= ratio

        self.compute_traction()


    def adjust_height(self, h):
        ratio = h / self.h
        self.h *= ratio
        self.H *= ratio
        self.z_rf *= ratio
        self.z_rr *= ratio
        self.compute_traction()

    def traction_curve(self):
        plt.plot(self.AY, self.A_accel)
        plt.plot(self.AY, self.A_brake)
        plt.xlabel('Lateral Acceleration (g\'s)')
        plt.ylabel('Axial Acceleration (g\'s)')
        plt.grid()
        plt.show()

# print(racecar.accel_car_data_snippets[-1].FO_load)
# snippet100 = racecar.brake_car_data_snippets[-1]
# print(snippet100.AY)
# print(f"FO_load: {snippet100.FO_load}\nFI_load: {snippet100.FI_load}\nRO_load: {snippet100.RO_load}\nRI_load: {snippet100.RI_load}\n")
# snippet66 = racecar.brake_car_data_snippets[66]
# print(snippet66.AY)
# print(f"FO_load: {snippet66.FO_load}\nFI_load: {snippet66.FI_load}\nRO_load: {snippet66.RO_load}\nRI_load: {snippet66.RI_load}\n")
# snippet33 = racecar.brake_car_data_snippets[33]
# print(snippet33.AY)
# print(f"FO_load: {snippet33.FO_load}\nFI_load: {snippet33.FI_load}\nRO_load: {snippet33.RO_load}\nRI_load: {snippet33.RI_load}\n")
# for index, snippet in enumerate(racecar.accel_car_data_snippets):
#     print(snippet.AX)

# racecar.accel(racecar.AY[-1], racecar.A_brake[-1])
# print(f"FO: {racecar.FY_out_f}, RO: {racecar.FY_out_r}")