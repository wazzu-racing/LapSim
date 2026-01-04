import math
import os
import pickle
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import pickle as pkl
import time
import csv

from dataclasses import dataclass
from spline_track import track

from models import drivetrain_model
from models import tire_model
from interface.file_management.file_manager import file_manager


class Car():

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
    h = 9
    # in, CG height to roll axis
    H = 10.521
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
    CMB_STC_F = 1.5
    CMB_STC_R = 1.5
    # in, maximum displacement in jounce for suspension, front and rear
    max_jounce_f = 1
    max_jounce_r = 1
    # Rolling resistence coefficient, unitless
    C_rr = 0.01

    # Converting roll rates to ft*lb/rad
    K_rollF *= 180/np.pi
    K_rollR *= 180/np.pi
    # weight over front track
    W_f = W_1 + W_2
    # weight over rear track
    W_r = W_3 + W_4
    # total weight of car (lbm)
    W_car = W_f + W_r
    # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
    W_bias = W_f/W_car
    # in, distance from CG to rear track
    b = l * W_bias
    # in, distance from CG to front track
    a = l - b
    # in, CG height to roll axis
    H = h - (a*z_rf + b*z_rr)/l
    # x and y positions of each tire relative to the center of the wheelbase
    FI_wheel_position = {"x": -t_f / 2, "y": a}
    FO_wheel_position = {"x": t_f / 2, "y": a}
    RI_wheel_position = {"x": -t_r / 2, "y": -b}
    RO_wheel_position = {"x": t_r / 2, "y": -b}
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
    D_1 = 0 # Front inner wheel vertical displacement in inches
    D_2 = 0 # Front outer wheel vertical displacement in inches
    D_3 = 0 # Rear inner wheel vertical displacement in inches
    D_4 = 0 # Rear outer wheel vertical displacement in inches
    # degrees, theta of accel force of car
    theta_accel = 0

    # aero csv file delimiter
    aero_delimiter = ';'

    tires = None
    train = None

    def __init__(self):
        self.start = time.perf_counter() # keep track of runtime duration
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

        # Initialize arrays
        self.radius_array = []
        self.car_angle_array = []
        self.AX_AY_array = []
        self.AX_AY_array = self.create_accel_2D_array(50, print_info=False)

        self.max_corner = self.max_lateral_accel()
        self.count = 0

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

    @dataclass
    class Car_Data_Snippet():
        AX: float
        AY: float
        torque: float

    def find_accurate_accel(self, radius, car_angle = 0.0, braking=False, print_info = False, print_every_iteration = False):
        """
        Plugs in parameters into the accel function until the inputted AX and AY are approximately equal to the outputted AX and AY.
        The main idea of this is that when an initial AX and AY are plugged into the accel function, those accelerations are
        obviously wrong at first. However, the accel function will calculate a more accurate AX and AY and return those.
        Those outputted AX and AY are then plugged back into the accel function. This is repeated until extremely accurate
        AX and AY are returned.
        :param radius: The radius of the turning curve. (inches)
        :param car_angle: The angle of the car relative to the turning point. (radians)
        :return: A Car_Data_Snippet object that contains the converged AX and AY.
        """

        input_AX, input_AY = 0, 0
        output_AX, output_AY = 0, 0
        torque = 0
        iterations = 0

        while (abs(input_AY - output_AY) > 0.0001 or abs(input_AX - output_AX) > 0.0001) or (input_AX == 0):
            # Change outputs to inputs
            input_AX, input_AY = output_AX, output_AY

            # Run accel function
            accel = self.accel_updated(radius, car_angle, input_AY, input_AX, braking=braking, print_info=print_info, print_every_iteration=print_every_iteration)
            output_AX, output_AY, torque = accel[0], accel[1], accel[2]

            iterations+=1

            # Prevent infinite loop
            if iterations > 100:
                print(f"Max iterations reached in find_accurate_accel. Output AX: {output_AX}, input AX: {input_AX}")
                break

        if print_info or print_every_iteration:
            print(f"iterations: {iterations}")

        return self.Car_Data_Snippet(output_AX, output_AY, torque)

    def create_accel_2D_array(self, n:int=20, print_info = False):
        """
        Fills in the r_carangle_2d_array with Car_Data_Snippet objects with each radius along the rows, and each car angle along
        the columns. Uses the find_accurate_accel function to calculate each AX and AY for each radius and car angle.
        :param n: Determines both the number of radii and car angles used to calculate AX and AY. Cannot go lower than 20.
        :return: None
        """

        # Ensure n is not lower than 20. Prevents inaccurate calculations.
        if n < 20:
            n = 20

        # set up radius and car angle arrays
        self.radius_array = []
        self.radius_array = np.concatenate([self.radius_array, np.linspace(100, 1000, int(n/2))])
        self.radius_array = np.concatenate([self.radius_array, np.linspace(1050, 10000, int(n/4))])
        self.radius_array = np.concatenate([self.radius_array, np.linspace(11000, 100000, int(n/4))])
        print(f"Radii: {self.radius_array}")
        self.car_angle_array = []
        self.car_angle_array = np.concatenate([self.car_angle_array, np.linspace(0, 45, n)])
        print(f"Car angles: {self.car_angle_array}")

        # go through each radius
        for radius in self.radius_array:
            row = []
            # go through each car angle
            for c_angle in self.car_angle_array:
                # convert c_angle to radians
                c_angle *= math.pi/180

                # Compute accurate acceleration and torque for radius and c_angle (car angle) if the car is launching
                accel = self.find_accurate_accel(radius, c_angle, print_info=print_info, print_every_iteration=False)
                output_AX, output_AY, torque = accel.AX, accel.AY, accel.torque

                # Compute accurate acceleration and torque for radius and c_angle (car angle) if the car is braking
                accel = self.find_accurate_accel(radius, c_angle, braking=True, print_info=print_info, print_every_iteration=False)
                output_AX_brake, output_AY_brake, torque_brake = accel.AX, accel.AY, accel.torque

                # add Car_Data_Snippet object to row of a singular radius
                row.append({"launch": self.Car_Data_Snippet(output_AX, output_AY, torque),"brake": self.Car_Data_Snippet(output_AX_brake, output_AY_brake, torque_brake)})

            # add row that contains Car_Data_Snippet objects to r_carangle_2d_array
            self.AX_AY_array.append(row)

        # end timer, print result
        self.end = time.perf_counter()

        # print(car_angle_array)

        # Print out values of r_carangle_2d_array in readable format.
        for index, radius_values in enumerate(self.AX_AY_array):
            print(f"Radius: {self.radius_array[index]} ----- ", end="")
            for data in radius_values:
                print(f"AX: {data["launch"].AX}, AY: {data["launch"].AY}, Torque: {data["launch"].torque} | ", end="")
            print("")

        print(f"Created 2D array!")
        return self.AX_AY_array

    def accel_updated(self, r, car_angle, AY, AX, braking = False, print_info = False, print_every_iteration = False):
        """
        :param r: The radius of the turning curve. (inches)
        :param car_angle: The angle of the car, used to rotate the car (and therefore, the tires) however many radians entered about its z-axis. (radians)
        :param steering_angle: The steering angle of the front wheels relative to the car. (radians)
        :param AY: The lateral acceleration of the car. (g's)
        :param AX: The axial acceleration of the car. (g's)
        :param print_info: If True, prints information about the car in this specific moment when it has the given radius and car angle.
        :param print_every_iteration: If True, prints information about the car for every iteration until accelerations converge (until accurate accelerations are found).
        :return: A tuple of axial acceleration, lateral acceleration, and torque about the z-axis. (net_axial_accel, net_lateral_accel, total_torque_about_z)
        """

        # Calculate steering angle
        steering = np.atan2(self.a, r)

        # Front inner tire direction motion calcs
        FI_length = r - self.a * np.sin(car_angle) - (self.t_f/2) * np.cos(car_angle)
        FI_height = self.a * np.cos(car_angle) - (self.t_f/2) * np.sin(car_angle)
        FI_dir_motion = car_angle + np.atan2(FI_height, FI_length)
        # print(car_angle * 180/math.pi)

        # Rear inner tire direction motion calcs
        RI_length = r + self.b * np.sin(car_angle) - (self.t_r/2) * np.cos(car_angle)
        RI_height = - self.b * np.cos(car_angle) - (self.t_r/2) * np.sin(car_angle)
        RI_dir_motion = car_angle + np.atan2(RI_height, RI_length)

        # Front outer tire direction motion calcs
        FO_length = r - self.a * np.sin(car_angle) + (self.t_f/2) * np.cos(car_angle)
        FO_height = self.a * np.cos(car_angle) + (self.t_f/2) * np.sin(car_angle)
        FO_dir_motion = car_angle + np.atan2(FO_height, FO_length)

        # Rear outer tire direction motion calcs
        RO_length = r + self.b * np.sin(car_angle) + (self.t_r/2) * np.cos(car_angle)
        RO_height = - self.b * np.cos(car_angle) + (self.t_r/2) * np.sin(car_angle)
        RO_dir_motion = car_angle + np.atan2(RO_height, RO_length)

        # Calculate slip angles (added negative sign because a negative slip angle is the standard convention for positive FY)
        FI_slip_angle = -(FI_dir_motion + steering)
        RI_slip_angle = -RI_dir_motion
        FO_slip_angle = -(FO_dir_motion + steering)
        RO_slip_angle = -RO_dir_motion

        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        # Calculate front and rear load transfer
        FO_load = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front outter wheel
        FI_load = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front inner wheel
        RO_load = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear outter wheel
        RI_load = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear inner wheel

        # Calculate vertical displacement of each tire (negative means car is lifted relative to tire, positive means car is lowered relative to tire)
        front_inner_displacement = (FI_load - self.W_1) / self.K_RF # inches
        rear_inner_displacement = (RI_load - self.W_3) / self.K_RR # inches
        front_outer_displacement = (FO_load - self.W_2) / self.K_RF # inches
        rear_outer_displacement = (RO_load - self.W_4) / self.K_RR # inches

        # Calculate camber of each tire
        FI_camber = self.CMB_STC_F + self.CMB_RT_F * front_inner_displacement # degrees
        RI_camber = self.CMB_STC_R + self.CMB_RT_R * rear_inner_displacement # degrees
        FO_camber = self.CMB_STC_F + self.CMB_RT_F * front_outer_displacement # degrees
        RO_camber = self.CMB_STC_R + self.CMB_RT_R * rear_outer_displacement # degrees

        # Calculate the lateral force produced by each tire using the tire model
        FI_FY = self.tires.FY_curves.eval(FI_slip_angle * 180/math.pi, FI_load, FI_camber) # pounds
        RI_FY = self.tires.FY_curves.eval(RI_slip_angle * 180/math.pi, RI_load, RI_camber) # pounds
        FO_FY = self.tires.FY_curves.eval(FO_slip_angle * 180/math.pi, FO_load, FO_camber) # pounds
        RO_FY = self.tires.FY_curves.eval(RO_slip_angle * 180/math.pi, RO_load, RO_camber) # pounds

        # Adding up lateral forces and calculating net lateral acceleration
        FY_car = FI_FY + RI_FY + FO_FY + RO_FY
        net_lat_accel = FY_car / self.W_car

        # Multiple that is used to make FX closer what the real-world number would look like.
        FX_scale_factor = 1.2

        # Determine max FY for each tire.
        max_RI_FY = self.tires.FY_curves.get_max(RI_load, RI_camber)
        max_RO_FY = self.tires.FY_curves.get_max(RO_load, RO_camber)
        max_FI_FY = self.tires.FY_curves.get_max(FI_load, FI_camber)
        max_FO_FY = self.tires.FY_curves.get_max(FO_load, FO_camber)

        # Calculating max axial acceleration by using a friction ellipse to put the remaining force into axial acceleration.
        if not braking:
            RI_FX = self.tires.FX_curves.get_max(RI_load, RI_camber) * ((1 - (RI_FY**2)/(max_RI_FY**2)) if max_RI_FY > RI_FY else 0)**0.5 * FX_scale_factor
            RO_FX = self.tires.FX_curves.get_max(RO_load, RO_camber) * ((1 - (RO_FY**2)/(max_RO_FY**2)) if max_RO_FY > RO_FY else 0)**0.5 * FX_scale_factor
            FI_FX = 0
            FO_FX = 0
            FX_car = RO_FX + RI_FX
        else:
            RI_FX = self.tires.FX_curves.get_max(RI_load, RI_camber) * ((1 - (RI_FY**2)/(max_RI_FY**2))**0.5 if max_RI_FY > RI_FY else 0) * FX_scale_factor
            RO_FX = self.tires.FX_curves.get_max(RO_load, RO_camber) * ((1 - (RO_FY**2)/(max_RO_FY**2))**0.5 if max_RO_FY > RO_FY else 0) * FX_scale_factor
            FI_FX = self.tires.FX_curves.get_max(FI_load, FI_camber) * ((1 - (FI_FY**2)/(max_FI_FY**2))**0.5 if max_FI_FY > FI_FY else 0) * FX_scale_factor
            FO_FX = self.tires.FX_curves.get_max(FO_load, FO_camber) * ((1 - (FO_FY**2)/(max_FO_FY**2))**0.5 if max_FO_FY > FO_FY else 0) * FX_scale_factor
            FX_car = -(RO_FX + RI_FX + FI_FX + FO_FX)

        # Calculate total axial acceleration
        net_axial_accel = FX_car / self.W_car

        # Calculate total torque about z axis for both axles, then calculate total torque about z-axis for the car
        FI_torque = FI_FY * self.a
        RI_torque = -RI_FY * self.b
        FO_torque = FO_FY * self.a
        RO_torque = -RI_FY * self.b

        # calculate total torque about the z-axis
        total_torque_about_z = FI_torque + RI_torque + FO_torque + RO_torque

        # calculate aligning torque using magic curve
        FI_aligning_torque = self.tires.aligning_torque.eval(FI_slip_angle * 180/math.pi, FI_load, FI_camber)
        RI_aligning_torque = self.tires.aligning_torque.eval(RI_slip_angle * 180/math.pi, RI_load, RI_camber)
        FO_aligning_torque = self.tires.aligning_torque.eval(FO_slip_angle * 180/math.pi, FO_load, FO_camber)
        RO_aligning_torque = self.tires.aligning_torque.eval(RO_slip_angle * 180/math.pi, RO_load, RO_camber)

        # calculate total aligning torque
        total_aligning_torque = FI_aligning_torque + RI_aligning_torque + FO_aligning_torque + RO_aligning_torque
        total_aligning_torque *= 12 # Convert to inch pounds

        # Print out info depending on certain vars
        if print_every_iteration or (abs(AY - net_lat_accel) <= 0.0001 and abs(AX - net_axial_accel) <= 0.0001 and print_info):
            print(f"\n------------------- radius: {r} inches, car angle: {car_angle * 180/math.pi} degrees -------------------")
            print(f"steering angle: {steering * 180/math.pi} degrees")
            print(f"FI_slip_angle: {FI_slip_angle * 180/math.pi} degrees\nRI_slip_angle: {RI_slip_angle * 180/math.pi} degrees\nFO_slip_angle: {FO_slip_angle * 180/math.pi} degrees\nRO_slip_angle: {RO_slip_angle * 180/math.pi} degrees",)
            print(f"FI_load: {FI_load} pounds\nRI_load: {RI_load} pounds\nFO_load: {FO_load} pounds\nRO_load: {RO_load} pounds")
            print(f"FI_camber: {FI_camber} degrees\nRI_camber: {RI_camber} degrees\nFO_camber: {FO_camber} degrees\nRO_camber: {RO_camber} degrees")
            print(f"FI_displacement: {front_inner_displacement} in\nRI_displacement: {rear_inner_displacement} in\nFO_displacement: {front_outer_displacement} in\nRO_displacement: {rear_outer_displacement} in")
            print(f"FI_FY: {FI_FY} pounds\nRI_FY: {RI_FY} pounds\nFO_FY: {FO_FY} pounds\nRO_FY: {RO_FY} pounds")
            print(f"FI_FX: {FI_FX} pounds\nRI_FX: {RI_FX} pounds\nFO_FX: {FO_FX} pounds\nRO_FX: {RO_FX} pounds")
            print(f"RI_FX Max: {self.tires.FX_curves.get_max(RI_load, RI_camber) * FX_scale_factor} pounds\nRO_FX Max: {self.tires.FX_curves.get_max(RO_load, RO_camber) * FX_scale_factor} pounds")
            print(f"lat accel: {net_lat_accel} g's\naxial accel: {net_axial_accel} g's")
            print(f"total_torque: {total_torque_about_z} in pounds")
            print(f"total_aligning_torque: {total_aligning_torque} inch pounds")

        return net_axial_accel, net_lat_accel, total_torque_about_z

    def find_closest_radius_index(self, radius):
        """
        Determines the index of the radius array that is closest to the given radius.
        :param radius: The given radius. (inches)
        :return: The index within the radius array that's value is closest to the given radius.
        """
        # If the actual radius (r) is too big for the radius array, then use the last radius in the array.
        if radius > self.radius_array[-1]:
            return len(self.radius_array)-1

        # Find the closest radius to the given radius
        r_index = 0
        prev_rad = self.radius_array[0]
        for index, rad in enumerate(self.radius_array):
            if rad > radius:
                if radius - prev_rad < (rad-prev_rad)/2:
                    # Make sure r_index does not equal -1.
                    if radius < self.radius_array[0]:
                        return index
                    else:
                        return index - 1
                else:
                    return index
            prev_rad = rad


    def curve_brake(self, r, v):
        """
        Calculates the negative axial acceleration of the car at a given radius and velocity.
        :param r: The radius of the car at which to calculate the brake acceleration. (inches)
        :param v: The velocity of the car at which to calculate the brake acceleration. (in/s)
        :return: The negative axial acceleration of the car at the given radius and velocity. (g's)
        """

        if r > 0:
            AY = v**2/r / 12 / 32.17 # g's
        else:
            self.count+=1
            AY = 0

        if AY == 0:
            return self.max_axial_accel()

        r_index = self.find_closest_radius_index(r)

        output_AY = 1.0
        prev_AY = 0.0
        output_AX = 0.0
        prev_AX = 0.0
        car_angle_array_index = 0
        count = 0
        # Find car body angle by increasing car body angle until the car can produce the appropriate AY.
        while output_AY < AY or count == 0:
            if count != 0:
                prev_AY = output_AY
                prev_AX = output_AX

            accel = self.AX_AY_array[r_index][car_angle_array_index]["brake"]

            output_AY = accel.AY
            output_AX = accel.AX

            # If output AY is starting to decrease with increased iterations of car_angle_array_index, maximum AY has been reached.
            if output_AY < prev_AY and count != 0:
                break

            car_angle_array_index += 1
            count += 1

        # If the correct car angle was found in the first iteration above, then use the next car angle instead of the
        # previous one to interpolate AX. Else, use the previous car angle to interpolate AX.
        # if count == 1:
        #     next_output_AX = self.AX_AY_array[r_index][car_angle_array_index+1]["brake"].AX
        #     next_output_AY = self.AX_AY_array[r_index][car_angle_array_index+1]["brake"].AY
        #     output_AX = (next_output_AX - output_AX) * (AY - output_AY)/(next_output_AY - output_AY) + output_AX
        # else:
        #     output_AX = (output_AX - prev_AX) * (AY - prev_AY)/(output_AY - prev_AY) + prev_AX

        print(f"{self.count}: using car angle {self.car_angle_array[car_angle_array_index]}, radius {r} -- AX: {output_AX}, AY: {AY}")

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
        output_AX -= drag # incorporating drag

        self.count+=1

        output_AX *= 32.17 * 12 # Converting from G's to in/s^2
        return output_AX

    # Calculates the positive axial acceleration of the car at a given radius and velocity.
    def curve_accel(self, r, v, transmission_gear ='optimal'):
        """
        Calculates the axial acceleration of the car at a given radius and velocity.
        :param r: The radius of the car at which to calculate the acceleration. (inches)
        :param v: The velocity of the car at which to calculate the acceleration. (in/s)
        :param transmission_gear: The gear the car is in.
        :return: The axial acceleration of the car at the given radius and velocity. (g's)
        """

        if r > 0:
            AY = v**2/r / 12 / 32.17 # g's
        else:
            self.count+=1
            AY = 0

        if AY == 0:
            return self.max_axial_accel()

        r_index = self.find_closest_radius_index(r)

        # Interpolate AX using AX_AY_array
        output_AY = 1.0
        prev_AY = 0.0
        output_AX = 0.0
        prev_AX = 0.0
        car_angle_array_index = 0
        count = 0
        # Find car body angle by increasing car body angle until the car can produce the appropriate AY.
        while output_AY < AY or count == 0:
            if count != 0:
                prev_AY = output_AY
                prev_AX = output_AX

            accel = self.AX_AY_array[r_index][car_angle_array_index]["launch"]

            output_AY = accel.AY
            output_AX = accel.AX

            # If output AY is starting to decrease with increased iterations of car_angle_array_index, maximum AY has been reached.
            if output_AY < prev_AY and count != 0:
                car_angle_array_index += 1
                break

            car_angle_array_index += 1
            count += 1

        # If the correct car angle was found in the first iteration above, then use the next car angle instead of the
        # previous one to interpolate AX. Else, use the previous car angle to interpolate AX.
        # if count == 1:
        #     next_output_AX = self.AX_AY_array[r_index][car_angle_array_index+1]["launch"].AX
        #     next_output_AY = self.AX_AY_array[r_index][car_angle_array_index+1]["launch"].AY
        #     output_AX = (next_output_AX - output_AX) * (AY - output_AY)/(next_output_AY - output_AY) + output_AX
        # else:
        #     output_AX = (AY - prev_AY) * (output_AX - prev_AX)/(output_AY - prev_AY) + prev_AX

        print(f"{self.count}: using car angle {self.car_angle_array[car_angle_array_index-1]}, closest radius {self.radius_array[r_index]}, actual radius {r} -- AX: {output_AX}, AY: {AY}")

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        A_tire = output_AX # Tire traction G's
        A_tire -= drag # incorporating drag
        A_tire *= 32.17*12# converting from G's to in/s^2

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's
        A_engn -= drag # incorporating drag
        A_engn *= 32.17*12 # converting from G's to in/s^2

        self.count+=1

        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_tire < A_engn:
            return A_tire
        else:
            return A_engn

    def max_axial_accel(self):
        """
        Runs the find_accurate_accel function with radius 10000000 and car angle 0.
        :return: The maximum axial acceleration of the car in g's.
        """
        return self.find_accurate_accel(10000000, 0).AX

    def max_lateral_accel(self):
        """
        Starting at a 200-inch radius, decrements by 1 inch and checks the needed lateral acceleration for that radius until getting
        a lateral acceleration that is lower than the previous. The lateral acceleration of the previous check is then returned.
        :return: The maximum lateral acceleration of the car. (g's)
        """
        # Ensure AX_AY_array is created
        if self.AX_AY_array is None:
            self.AX_AY_array = self.create_accel_2D_array(50)

        max = self.AX_AY_array[0][0]["launch"].AY

        # Go through each radius and car angle until maximum lateral acceleration is found.
        for radius in range(0, len(self.AX_AY_array)):
            for c_angle in range(0, len(self.AX_AY_array[0])):
                if self.AX_AY_array[radius][c_angle]["launch"].AY > max:
                    max = self.AX_AY_array[radius][c_angle]["launch"].AY

        return max
    
    # returns drag acceleration (in/s^2) given vehicle speed
    # v = speed (in/s)
    def curve_idle(self, v):
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
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
        # Recalculate AX_AY_array since weight has changed
        self.AX_AY_array = self.create_accel_2D_array(50)

    def adjust_height(self, h):
        ratio = h / self.h
        self.h *= ratio
        self.H *= ratio
        self.z_rf *= ratio
        self.z_rr *= ratio
        # Recalculate AX_AY_array since height has changed
        self.AX_AY_array = self.create_accel_2D_array(50)

# Purpose of this class is to create pickles for autocross and endurance
# class points:
#     def __init__ (self):
#         self.nds = []
#
# def create_track_pickle(txt_path, pkl_path, is_autocross):
#     points_arr = [np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType())]
#
#     arr_done_index = 0
#
#     with open(txt_path, "r") as f:
#         content = f.read()
#     curr_num = ""
#     writing = False
#     for char in content:
#         if char == '[':
#             writing = True
#         elif char == ']' and writing:
#             points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
#             curr_num = ""
#             arr_done_index += 1
#             writing = False
#         elif char == ',' and writing:
#             points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
#             curr_num = ""
#         elif char != " " and writing:
#             curr_num += char
#
#     points_x = points_arr[0].astype(float)
#     points_y = points_arr[1].astype(float)
#     points_x2 = points_arr[2].astype(float)
#     points_y2 = points_arr[3].astype(float)
#
#     track = points()
#
#     rang = 97 if is_autocross else 129
#     for i in range(rang):
#         n = node(points_x[i], points_y[i], points_x2[i], points_y2[i])
#         track.nds.append(n)
#
#     with open(pkl_path, "wb") as f:
#         pickle.dump(track, f)

racecar = Car()

# print(racecar.max_axial_accel())

print(f"Total runtime: {racecar.end - racecar.start} seconds")

with open("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim/autocross_trk_points.pkl", "rb") as f:
    points_trk = pkl.load(f)

points_x = []
points_y = []
points_x2 = []
points_y2 = []
for node in points_trk.nds:
    points_x.append(node.x1)
    points_y.append(node.y1)
    points_x2.append(node.x2)
    points_y2.append(node.y2)

track = track(points_x, points_y, points_x2, points_y2, racecar)
track.adjust_track([40, 30, 30, 80],[100, 30, 10, 5])
track.run_sim(racecar)
# print(racecar.AY_arr)