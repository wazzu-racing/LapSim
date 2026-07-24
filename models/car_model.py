import copy
import math
import os
import pickle
from dataclasses import dataclass

import matplotlib.colors
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import csv

from models import drivetrain_model, brake_model
from models import tire_model
from interface.file_management.file_manager import file_manager
from models import aero_model


class car():
    # weight over front left wheel
    W_1 = 165
    # weight over front right wheel
    W_2 = 165
    # weight over rear left wheel
    W_3 = 165
    # weight over rear right wheel
    W_4 = 165
    # length of wheelbase (in)
    l = 60
    # vertical center of gravity (in)
    h = 12.4
    # in, roll axis height, front and rear
    z_rf = 3.1
    z_rr = 3.3
    # Track widths, front and rear (in)
    t_f = 47
    t_r = 46
    # lb/in, ride rates, front and rear
    K_RF = 179.72219842152035 # lbs/in
    K_RR = 163.58335639299756 # lbs/in
    # lb*in/rad, roll rates, front and rear
    K_rollF = 215203 # lb*in/rad
    K_rollR = 195952 # lb*in/rad
    #deg/in, camber rates for front and rear
    CMB_RT_F = 1.3
    CMB_RT_R = 1.15
    # deg, static camber rates for front and rear
    CMB_STC_F = 1
    CMB_STC_R = 1
    # in, maximum displacement in jounce for suspension, front and rear
    max_jounce_f = 1
    max_jounce_r = 1
    # Rolling resistance coefficient
    C_rr = 0.01

    # # weight over front left wheel
    # W_1 = 185 # lbm
    # # weight over front right wheel
    # W_2 = 165 # lbm
    # # weight over rear left wheel
    # W_3 = 145 # lbm
    # # weight over rear right wheel
    # W_4 = 145 # lbm
    # # length of wheelbase (in)
    # l = 60.5
    # # vertical center of gravity (in)
    # h = 11.6
    # # in, roll axis height, front and rear
    # z_rf = 9.5
    # z_rr = 9.7
    # # Track widths, front and rear (in)
    # t_f = 49
    # t_r = 49
    # # lb/in, ride rates, front and rear
    # K_RF = 179.72219842152035 # fernt
    # K_RR = 163.58335639299756 # peir
    # # lb*ft/deg, roll rates, front and rear (later converted to lb*ft/rad)
    # K_rollF = 144439.94389901822
    # K_rollR = 142041.8793828892
    # #deg/in, camber rates for front and rear
    # CMB_RT_F = 1.5
    # CMB_RT_R = 1.75
    # # deg, static camber rates for front and rear
    # CMB_STC_F = 2
    # CMB_STC_R = 1
    # # in, maximum displacement in jounce for suspension, front and rear
    # max_jounce_f = 1
    # max_jounce_r = 1
    # # Rolling resistance coefficient
    # C_rr = 0.01

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

    engine_force = []
    vels = []
    tires_force = []

    # aero csv file delimiter
    aero_delimiter = ';'

    tires = None
    train = None

    def __init__(self):
        self.aero_csv_file_path = file_manager.get_temp_folder_path(
            os.path.join(Path(__file__).resolve().parent.parent, "config_data", "DEFAULT_AERO_ARRAY.csv"))
        self.tire_file_path = ""
        self.drivetrain_file_path = ""

        # Making aero model
        self.aero_model = aero_model.Aero(self)

        # importing tire model
        try:
            with open(self.tire_file_path, 'rb') as f:
                self.tires = pickle.load(f)
        except Exception:
            cornering_data = file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data", "tire_data", "Hoosier_18_6_R20_corner.dat"))
            accel_data = file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data", "tire_data", "Hoosier_18_6_R20_drive.dat"))
            self.tires = tire_model.tire(cornering_data, accel_data)

        # importing drivetrain model
        try:
            with open(self.drivetrain_file_path, 'rb') as f:
                self.drivetrain = pickle.load(f)
        except Exception:
            self.drivetrain = drivetrain_model.drivetrain(engine_data=file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent, "config_data", "ENG_RPM_DATA_92.csv")))

        # Make brake model
        self.brake_model = brake_model.Brakes(self)

        self.file_location = ""

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
        def __init__(self, racecar, index, changing_gears=False, speed = 0):
            # Acceleration & movement
            if not changing_gears:
                self.AX = racecar.instant_AX
                self.AY = racecar.instant_AY
            else:
                self.AX = racecar.instant_AX - racecar.aero_model.get_drag(speed)/racecar.W_car
                self.AY = racecar.instant_AY
            self.velocity = 0
            # Tire measurements
            self.front_outer_displacement = racecar.front_outer_displacement
            self.front_inner_displacement = racecar.front_inner_displacement
            self.rear_outer_displacement = racecar.rear_outer_displacement
            self.rear_inner_displacement = racecar.rear_inner_displacement
            self.FO_camber = racecar.C_out_f
            self.FI_camber = racecar.C_in_f
            self.RO_camber = racecar.C_out_r
            self.RI_camber = racecar.C_in_r
            # Tire forces
            self.FO_load = racecar.W_out_f
            self.FI_load = racecar.W_in_f
            self.RO_load = racecar.W_out_r
            self.RI_load = racecar.W_in_r
            self.FO_FY = racecar.FY_out_f
            self.FI_FY = racecar.FY_in_f
            self.RO_FY = racecar.FY_out_r
            self.RI_FY = racecar.FY_in_r
            self.FO_FX = -racecar.FX_out_f if self.AX < 0 else 0
            self.FI_FX = -racecar.FX_in_f if self.AX < 0 else 0
            self.RO_FX = racecar.FX_out_r if self.AX > 0 else -racecar.FX_out_r
            self.RI_FX = racecar.FX_in_r if self.AX > 0 else -racecar.FX_in_r

            # If changing gears, do not use the maximum possible force
            if changing_gears:
                self.FO_FY = 0
                self.FI_FY = 0
                self.RO_FY = 0
                self.RI_FY = 0
                self.FO_FX = 0
                self.FI_FX = 0
                self.RO_FX = 0
                self.RI_FX = 0

            self.racecar = racecar
            self.index = index

        @classmethod
        def get_interpolated_copy(cls, prev_snippet, next_snippet, prev_ratio, next_ratio):
            snippet = cls(next_snippet.racecar, -1)

            # Interpolate
            if next_snippet.AX > 0: # If car is accelerating
                snippet.AX = next_ratio * next_snippet.AX + prev_ratio * prev_snippet.AX
                snippet.AY = next_ratio * next_snippet.AY + prev_ratio * prev_snippet.AY
                # snippet.velocity = curr_ratio * snippet.velocity + prev_ratio * snippet.racecar.accel_car_data_snippets[curr_snippet.index-1].velocity
                # Tire measurements
                snippet.front_outer_displacement = next_ratio * next_snippet.front_outer_displacement + prev_ratio * prev_snippet.front_outer_displacement
                snippet.front_inner_displacement = next_ratio * next_snippet.front_inner_displacement + prev_ratio * prev_snippet.front_inner_displacement
                snippet.rear_outer_displacement = next_ratio * next_snippet.rear_outer_displacement + prev_ratio * prev_snippet.rear_outer_displacement
                snippet.rear_inner_displacement = next_ratio * next_snippet.rear_inner_displacement + prev_ratio * prev_snippet.rear_inner_displacement
                snippet.FO_camber = next_ratio * next_snippet.FO_camber + prev_ratio * prev_snippet.FO_camber
                snippet.FI_camber = next_ratio * next_snippet.FI_camber + prev_ratio * prev_snippet.FI_camber
                snippet.RO_camber = next_ratio * next_snippet.RO_camber + prev_ratio * prev_snippet.RO_camber
                snippet.RI_camber = next_ratio * next_snippet.RI_camber + prev_ratio * prev_snippet.RI_camber
                # Tire forces
                snippet.FO_load = next_ratio * next_snippet.FO_load + prev_ratio * prev_snippet.FO_load
                snippet.FI_load = next_ratio * next_snippet.FI_load + prev_ratio * prev_snippet.FI_load
                snippet.RO_load = next_ratio * next_snippet.RO_load + prev_ratio * prev_snippet.RO_load
                snippet.RI_load = next_ratio * next_snippet.RI_load + prev_ratio * prev_snippet.RI_load
                snippet.FO_FY = next_ratio * next_snippet.FO_FY + prev_ratio * prev_snippet.FO_FY
                snippet.FI_FY = next_ratio * next_snippet.FI_FY + prev_ratio * prev_snippet.FI_FY
                snippet.RO_FY = next_ratio * next_snippet.RO_FY + prev_ratio * prev_snippet.RO_FY
                snippet.RI_FY = next_ratio * next_snippet.RI_FY + prev_ratio * prev_snippet.RI_FY
                snippet.FO_FX = next_ratio * next_snippet.FO_FX + prev_ratio * prev_snippet.FO_FX
                snippet.FI_FX = next_ratio * next_snippet.FI_FX + prev_ratio * prev_snippet.FI_FX
                snippet.RO_FX = next_ratio * next_snippet.RO_FX + prev_ratio * prev_snippet.RO_FX
                snippet.RI_FX = next_ratio * next_snippet.RI_FX + prev_ratio * prev_snippet.RI_FX
            else: # If car is braking
                snippet.AX = next_ratio * next_snippet.AX + prev_ratio * prev_snippet.AX
                snippet.AY = next_ratio * next_snippet.AY + prev_ratio * prev_snippet.AY
                # snippet.velocity = curr_ratio * snippet.velocity + prev_ratio * snippet.racecar.brake_car_data_snippets[curr_snippet.index-1].velocity
                # Tire measurements
                snippet.front_outer_displacement = next_ratio * next_snippet.front_outer_displacement + prev_ratio * prev_snippet.front_outer_displacement
                snippet.front_inner_displacement = next_ratio * next_snippet.front_inner_displacement + prev_ratio * prev_snippet.front_inner_displacement
                snippet.rear_outer_displacement = next_ratio * next_snippet.rear_outer_displacement + prev_ratio * prev_snippet.rear_outer_displacement
                snippet.rear_inner_displacement = next_ratio * next_snippet.rear_inner_displacement + prev_ratio * prev_snippet.rear_inner_displacement
                snippet.FO_camber = next_ratio * next_snippet.FO_camber + prev_ratio * prev_snippet.FO_camber
                snippet.FI_camber = next_ratio * next_snippet.FI_camber + prev_ratio * prev_snippet.FI_camber
                snippet.RO_camber = next_ratio * next_snippet.RO_camber + prev_ratio * prev_snippet.RO_camber
                snippet.RI_camber = next_ratio * next_snippet.RI_camber + prev_ratio * prev_snippet.RI_camber
                # Tire forces
                snippet.FO_load = next_ratio * next_snippet.FO_load + prev_ratio * prev_snippet.FO_load
                snippet.FI_load = next_ratio * next_snippet.FI_load + prev_ratio * prev_snippet.FI_load
                snippet.RO_load = next_ratio * next_snippet.RO_load + prev_ratio * prev_snippet.RO_load
                snippet.RI_load = next_ratio * next_snippet.RI_load + prev_ratio * prev_snippet.RI_load
                snippet.FO_FY = next_ratio * next_snippet.FO_FY + prev_ratio * prev_snippet.FO_FY
                snippet.FI_FY = next_ratio * next_snippet.FI_FY + prev_ratio * prev_snippet.FI_FY
                snippet.RO_FY = next_ratio * next_snippet.RO_FY + prev_ratio * prev_snippet.RO_FY
                snippet.RI_FY = next_ratio * next_snippet.RI_FY + prev_ratio * prev_snippet.RI_FY
                snippet.FO_FX = next_ratio * next_snippet.FO_FX + prev_ratio * prev_snippet.FO_FX
                snippet.FI_FX = next_ratio * next_snippet.FI_FX + prev_ratio * prev_snippet.FI_FX
                snippet.RO_FX = next_ratio * next_snippet.RO_FX + prev_ratio * prev_snippet.RO_FX
                snippet.RI_FX = next_ratio * next_snippet.RI_FX + prev_ratio * prev_snippet.RI_FX

            return snippet

    class TractionCurve:
        def __init__(self, speed):
            self.speed = speed
            self.AY = []
            self.A_accel = []
            self.A_brake = []
            self.accel_car_snippets = []
            self.brake_car_snippets = []
            self.static_snippet = []

    def compute_traction(self):

        speed_arr = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900] # in/s
        self.curves = []

        for index, speed in enumerate(speed_arr):

            self.curves.append(self.TractionCurve(speed))

            # finding max cornering (lateral) acceleration
            low_guess = 0 # low estimate for max cornering (lateral) acceleration (g)
            high_guess = 3 # high estimate for max cornering (lateral) acceleration (g)

            # when the low and high estimates converge, the converging value is recorded as the max cornering (lateral) acceleration
            while high_guess - low_guess > 0.00001:
                guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering (lateral) acceleration
                out = self.accel(AY=guess, AX=0, speed=speed)
                if out: # sets low estimate to the guess value if the car can handle cornering (lateral) acceleration equal to the guess value
                    low_guess = guess
                else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
                    high_guess = guess

            self.max_corner = guess # max cornering (lateral) acceleration (g)
            self.curves[-1].AY = np.linspace(0, self.max_corner, 100)
            for index, i in enumerate(self.curves[-1].AY):
                self.curves[-1].A_accel.append(self.max_accel(AY=i, speed=speed))
                self.curves[-1].accel_car_snippets.append(self.Car_Data_Snippet(self, index))
                self.curves[-1].A_brake.append(self.max_brake(AY=i, speed=speed))
                self.curves[-1].brake_car_snippets.append(self.Car_Data_Snippet(self, index))
            self.max_corner -= 0.0001
            # Gear changes
            self.accel(0, 0)
            self.curves[-1].static_snippet = self.Car_Data_Snippet(self, -1, changing_gears=True, speed=speed) # Used to describe the state of the car during gear changes

        self.drag_goon()

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
    def accel(self, AY, AX, speed=0):
        self.instant_AY, self.instant_AX = AY, AX

        D_f, D_r = self.aero_model.get_down(speed)

        W_f = self.W_f - self.h*self.W_car*AX/self.l + D_f # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l + D_r # Vertical force on rear track (lb)

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
        self.C_in_f = abs(self.CMB_STC_F + (self.W_in_f-self.W_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        self.C_out_r = abs(self.CMB_STC_R + (self.W_out_r-self.W_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        self.C_in_r = abs(self.CMB_STC_R + (self.W_in_r-self.W_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        self.FY_out_f = self.tires.traction('corner', self.W_out_f, self.C_out_f) # max possible lateral acceleration from front outter wheel in pounds
        self.FY_in_f = self.tires.traction('corner', self.W_in_f, self.C_in_f)    # max possible lateral acceleration from front inner wheel in pounds
        self.FY_out_r = self.tires.traction('corner', self.W_out_r, self.C_out_r) # max possible lateral acceleration from rear outter wheel in pounds
        self.FY_in_r = self.tires.traction('corner', self.W_in_r, self.C_in_r)    # max possible lateral acceleration from rear inner wheel in pounds

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force to make the turn
        if (FY_f > self.FY_out_f+self.FY_in_f) or (FY_r > self.FY_out_r+self.FY_in_r): return False

        # returning true if no axial acceleration
        if AX == 0: return True

        f_factor = ((self.FY_out_f + self.FY_in_f)**2 - FY_f**2)**0.5 / (self.FY_out_f + self.FY_in_f)
        r_factor = ((self.FY_out_r + self.FY_in_r)**2 - FY_r**2)**0.5 / (self.FY_out_r + self.FY_in_r)

        self.FX_out_f = f_factor * self.tires.traction('accel', self.W_out_f, self.C_out_f) # max possible axial acceleration from front outter wheel in pounds
        self.FX_in_f = f_factor * self.tires.traction('accel', self.W_in_f, self.C_in_f)    # max possible axial acceleration from front inner wheel in pounds
        self.FX_out_r = r_factor * self.tires.traction('accel', self.W_out_r, self.C_out_r) # max possible axial acceleration from rear outter wheel in pounds
        self.FX_in_r = r_factor * self.tires.traction('accel', self.W_in_r, self.C_in_r)    # max possible axial acceleration from rear inner wheel in pounds

        self.theta_accel = math.atan2(abs(AY), AX) * 180/math.pi

        # Calculating max axial acceleration from tire traction
        if AX > 0:
            FX = self.FX_out_r + self.FX_in_r
            FX -= self.aero_model.get_drag(speed)
        else:
            FX = self.FX_out_f + self.FX_in_f + self.FX_out_r + self.FX_in_r
            FX += self.aero_model.get_drag(speed)

        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX):return False
        else: return True

    # recursive function to find the max axial acceleration; AY is lateral acceleration in g's
    def max_accel(self, AY, low_guess = 0, high_guess = 2, speed=0):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0000000001:
            return guess

        if self.accel(AY, guess, speed=speed): # sets low estimate to the guess value if the car can handle cornering acceleration equal to the guess value
            return self.max_accel(AY, guess, high_guess, speed=speed)
        else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
            return self.max_accel(AY, low_guess, guess, speed=speed)

    def max_brake(self, AY, low_guess = -3, high_guess = 0, speed=0):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0000000001:
            return guess

        if self.accel(AY, guess, speed=speed): # sets high estimate to the guess value if the car can handle breaking acceleration equal to the guess value
            return self.max_brake(AY, low_guess, guess, speed=speed)
        else: # sets low estimate to the guess value if the car cannot handle breaking acceleration equal to the guess value
            return self.max_brake(AY, guess, high_guess, speed=speed)

    # calculates the max axial acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a straight track with no curvature
    def curve_accel(self, v, r, transmission_gear='optimal'):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track

        low_index, high_index = 0, 0
        low_curve, high_curve = self.find_closest_curve(v, True), self.find_closest_curve(v, False)

        for i, ay_curve in enumerate(low_curve.AY):
            if ay_curve > AY:
                low_index = i
                break

        low_snippet = (
            self.Car_Data_Snippet.get_interpolated_copy(
                prev_snippet=low_curve.accel_car_snippets[low_index-1],
                next_snippet=low_curve.accel_car_snippets[low_index],
                prev_ratio=(low_curve.AY[low_index]-AY)/(low_curve.AY[low_index]-low_curve.AY[low_index-1]),
                next_ratio=(AY-low_curve.AY[low_index-1])/(low_curve.AY[low_index]-low_curve.AY[low_index-1]))
        )

        for i, ay_curve in enumerate(high_curve.AY):
            if ay_curve > low_snippet.AY:
                high_index = i
                break

        high_snippet = (
            self.Car_Data_Snippet.get_interpolated_copy(
                prev_snippet=high_curve.accel_car_snippets[high_index-1],
                next_snippet=high_curve.accel_car_snippets[high_index],
                prev_ratio=(high_curve.AY[high_index]-AY)/(high_curve.AY[high_index]-high_curve.AY[high_index-1]),
                next_ratio=(AY-high_curve.AY[high_index-1])/(high_curve.AY[high_index]-high_curve.AY[high_index-1]))
        )

        distance_from_next = high_curve.speed - v
        next_ratio = 1 - distance_from_next / (high_curve.speed - low_curve.speed)
        prev_ratio = 1 - next_ratio
        interpolated_snippet = self.Car_Data_Snippet.get_interpolated_copy(
            prev_snippet=low_snippet,
            next_snippet=high_snippet,
            next_ratio=next_ratio,
            prev_ratio=prev_ratio
        )

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's

        self.engine_force.append(A_engn*self.W_car)
        self.tires_force.append(interpolated_snippet.FO_FX+interpolated_snippet.FI_FX
                                 +interpolated_snippet.RO_FX+interpolated_snippet.RI_FX)
        self.vels.append(v)

        A_engn -= self.aero_model.get_drag(v)/self.W_car # incorporate drag

        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_engn < interpolated_snippet.AX:
            interpolated_snippet.AX = A_engn
            return interpolated_snippet
        return interpolated_snippet

    # calculates the max braking acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_brake(self, v, r):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track

        low_index, high_index = 0, 0
        low_curve, high_curve = self.find_closest_curve(v, True), self.find_closest_curve(v, False)

        for i, ay_curve in enumerate(low_curve.AY):
            if ay_curve > AY:
                low_index = i
                break

        low_snippet = (
            self.Car_Data_Snippet.get_interpolated_copy(
                prev_snippet=low_curve.brake_car_snippets[low_index-1],
                next_snippet=low_curve.brake_car_snippets[low_index],
                prev_ratio=(low_curve.AY[low_index]-AY)/(low_curve.AY[low_index]-low_curve.AY[low_index-1]),
                next_ratio=(AY-low_curve.AY[low_index-1])/(low_curve.AY[low_index]-low_curve.AY[low_index-1]))
        )

        for i, ay_curve in enumerate(high_curve.AY):
            if ay_curve > low_snippet.AY:
                high_index = i
                break

        high_snippet = (
            self.Car_Data_Snippet.get_interpolated_copy(
                prev_snippet=high_curve.brake_car_snippets[high_index-1],
                next_snippet=high_curve.brake_car_snippets[high_index],
                prev_ratio=(high_curve.AY[high_index]-AY)/(high_curve.AY[high_index]-high_curve.AY[high_index-1]),
                next_ratio=(AY-high_curve.AY[high_index-1])/(high_curve.AY[high_index]-high_curve.AY[high_index-1]))
        )

        distance_from_next = high_curve.speed - v
        next_ratio = 1 - distance_from_next / (high_curve.speed - low_curve.speed)
        prev_ratio = 1 - next_ratio
        interpolated_snippet = self.Car_Data_Snippet.get_interpolated_copy(
            prev_snippet=low_snippet,
            next_snippet=high_snippet,
            next_ratio=next_ratio,
            prev_ratio=prev_ratio
        )

        return interpolated_snippet

    # Reduces AXs that are higher than self.curves[0].A_accel[0] to that same value.
    def drag_goon(self):
        for outer_index, curve in enumerate(self.curves):
            if outer_index == 0:
                continue

            # Increase drag for every higher curve until AX is low enough.

            first_valid_index = 0
            for index, AX in enumerate(curve.A_accel):
                if AX < self.curves[0].A_accel[0]:
                    first_valid_index = index
                    break

            for index, AX in enumerate(curve.A_accel):
                if index >= first_valid_index:
                    break
                if index == 0:
                    curve.A_accel[0] = self.curves[0].A_accel[0]
                    curve.accel_car_snippets[0].AX = self.curves[0].A_accel[0]
                    continue

                next_ratio = curve.AY[index] / curve.AY[first_valid_index]
                prev_ratio = 1 - next_ratio
                new_AX = curve.A_accel[first_valid_index] * next_ratio + curve.A_accel[0] * prev_ratio
                curve.A_accel[index] = new_AX
                curve.accel_car_snippets[index].AX = new_AX

    def find_closest_curve(self, speed, lower):
        for index, curve in enumerate(self.curves):
            if self.curves[index-1].speed <= speed <= self.curves[index].speed:
                if lower:
                    return self.curves[index-1]
                else:
                    return self.curves[index]
        if lower:
            return self.curves[-2]
        else:
            return self.curves[-1]

    # Returns maximum AY at v (velocity) in in/s^2
    def compute_maximum_AY(self, v):
        low_curve, high_curve = self.find_closest_curve(v, True), self.find_closest_curve(v, False)

        next_ratio = 1 - (high_curve.speed - v) / (high_curve.speed - low_curve.speed)
        prev_ratio = 1 - next_ratio

        AY = high_curve.AY[-1] * next_ratio + low_curve.AY[-1] * prev_ratio
        return AY * 386.1

    # returns drag acceleration (in/s^2) given vehicle speed
    # v = speed (in/s)
    def curve_idle(self, v):
        low_curve, high_curve = self.find_closest_curve(v, True), self.find_closest_curve(v, False)

        next_ratio = 1 - (high_curve.speed - v) / (high_curve.speed - low_curve.speed)
        prev_ratio = 1 - next_ratio

        static_snippet = self.Car_Data_Snippet.get_interpolated_copy(
            next_snippet=high_curve.static_snippet,
            prev_snippet=low_curve.static_snippet,
            next_ratio=next_ratio,
            prev_ratio=prev_ratio
        )
        return static_snippet

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

    def traction_curves(self):
        colors = []
        for color in matplotlib.colors.BASE_COLORS.values():
            colors.append(color)
        colors*=100

        for index, curve in enumerate(self.curves):
            plt.plot(self.curves[index].AY, self.curves[index].A_accel, color=colors[index])
            plt.plot(self.curves[index].AY, self.curves[index].A_brake, color=colors[index])
        plt.grid()
        plt.xlabel('Lateral Acceleration (g\'s)')
        plt.ylabel('Axial Acceleration (g\'s)')
        plt.show()

    def plot_forces(self):
        plt.plot(self.vels, self.engine_force)
        plt.plot(self.vels, self.tires_force)
        plt.xlabel('Velocity (in/s)')
        plt.ylabel('Force (lbs)')
        plt.legend(['engine force', 'tire force'])
        plt.grid()
        plt.show()

# racecar = car()
# racecar.traction_curves()
# racecar.compute_maximum_AY(350)
# racecar.curve_brake(1000, 5169.294)