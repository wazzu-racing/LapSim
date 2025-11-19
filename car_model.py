from matplotlib import pyplot as plt
import numpy as np
import pickle as pkl

from numpy.ma.core import arctan

import tire_model
import drivetrain_model
import csv
import time
import math
import random
import pandas

from enum import Enum

from tire_model import curve_set


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
    K_RF = 189.5
    K_RR = 207.38
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

    FL_wheel_position = -t_f/2, l/2
    FR_wheel_position = t_f/2, l/2
    RL_wheel_position = -t_r/2, -l/2
    RR_wheel_position = t_r/2, -l/2

    # tire model file path
    tire_file = '18x6-10_R20.pkl'
    # drivetrain_model
    drivetrain_file = '/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSim/Data/pkl/drivetrain.pkl'
    # aero data array file path
    aero_csv = 'aero_array.csv' # contains drag force (lb) acting on vehicle at different speeds (index = mph)
    # aero csv file delimiter
    aero_delimiter = ';'
    
    # importing tire model
    with open(tire_file, 'rb') as f:
        tires = pkl.load(f)


    def __init__(self):
        self.aero_arr = [] # drag force acceleration (G's) emitted on vehicle (index = mph)
        with open(self.aero_csv, newline='') as f:
            reader = csv.reader(f, delimiter=self.aero_delimiter)
            for line in reader:
                for i in line:
                    self.aero_arr.append(float(i)/self.W_car)
        
        # importing drivetrain model
        with open(self.drivetrain_file, 'rb') as f:
            self.drivetrain = pkl.load(f)
        
        self.aero_arr.reverse()
        # self.compute_traction_updated()

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



    def compute_traction(self):

        # finding max cornering acceleration
        low_guess = 0 # low estimate for max cornering acceleration (g)
        high_guess = 3 # high estimate for max cornering acceleration (g)

        # when the low and high estimates converge, the converging value is recorded as the max cornering acceleration
        while high_guess - low_guess > 0.00001:
            guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration
            out = self.accel(guess, 0)
            if out: # sets low estimate to the guess value if the car can handle cornering acceleration equal to the guess value
                low_guess = guess
            else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
                high_guess = guess

        self.max_corner = guess # max cornering acceleration (g)
        self.AY = np.linspace(0, self.max_corner, 100)
        self.A_accel = []
        self.A_brake = []
        for i in self.AY:
            self.A_accel.append(self.max_accel(i))
            self.A_brake.append(self.max_brake(i))
        self.max_corner -= 0.0001

    class Car_Data_Snippet():
        def __init__(self, AX, AY):
            self.AX = AX
            self.AY = AY

    # For each r and car_angle, plug in 0 AY and 0 AX to start.
    # Since those acceleration are unrealistic for the r, car_angle, and steering_angle, keep plugging in the updated AY and AX
    # into the function until the AY and AX that are output equal the AY and AX that are inputted to a certain decimal point.
    # Decimal point will get smaller depending on the amount fo accuracy wanted.
    # This will create a 2D array with 1D arrays for r and car_angle.
    # When r and car_angle are input into the 2D array, realistic AY and AX will be spit out.
    r_carangle_2d_array = [] # radii along rows, car angle along columns
    def find_AY_AX_for_r_carangle(self):
        total_inerations = 0

        # set up radius and car angle arrays
        radius_array = [] # 1000 radii. 1.8 inch step from 100-1000 inch; 35.8 inch step from 1050-10000 inch; 3956 inch step from 11000-1000000 inch.
        radius_array = np.concatenate([radius_array, np.linspace(100, 1000, 500)])
        radius_array = np.concatenate([radius_array, np.linspace(1050, 10000, 250)])
        radius_array = np.concatenate([radius_array, np.linspace(11000, 1000000, 250).astype(float)])
        car_angle_array = []
        for c_angle in range(900):
            angle = c_angle * math.pi/1800 # Take out of required integer, convert to radians
            car_angle_array.append(angle)

        car_angle_array = np.concatenate([car_angle_array, np.linspace(0, 900, 1)])
        for radius in radius_array:
            row = []
            for c_angle in car_angle_array: # 900 car angles, 0.1 radian step
                interations = 0
                input_AX, input_AY = 0, 0
                output_AX, output_AY = 0, 0
                while (abs(input_AY - output_AY) > 0.0001 and abs(input_AX - output_AX) > 0.0001) or input_AX == 0:
                    # Update steering angle
                    steering = math.atan(self.l/radius)

                    # Change outputs to inputs
                    input_AX, input_AY = output_AX, output_AY

                    # Run accel function
                    accel = self.accel_updated(radius, c_angle, steering, input_AY, input_AX)
                    output_AX, output_AY = accel[0], accel[1]

                    interations+=1

                total_inerations += interations
                row.append(self.Car_Data_Snippet(output_AX, output_AY))
                print(f"\n\nResulting AX: {output_AX}\nResulting AY: {output_AY}\n\nIterations: {interations}")

            self.r_carangle_2d_array.append(row)

        print(f"\n\n\nTotal iterations: {total_inerations}")

    # Last step: get torque
    def accel_updated(self, r, car_angle, steering_angle, AY, AX):
        """
        :param r: The radius of the turning curve. (inches)
        :param AY: The lateral acceleration of the car. (in/s^2)
        :param car_angle: The angle of the car relative to the turning point. (radians)
        :param steering_angle: The steering angle of the front wheels relative to the car. (radians)
        :return: A tuple of axial and lateral acceleration. i.e. (net_axial_accel, net_lateral_accel)
        """

        print(f"steering angle: {steering_angle * 180/math.pi} degrees\nradius: {r*180/math.pi} degrees")

        # Find real x and y positions of each tire using the car_angle
        def rotate_wheel(x, y):
            return x * math.cos(car_angle) - y * math.sin(car_angle), x * math.sin(car_angle) + y * math.cos(car_angle)

        # START OF GOT FROM ACCEL 2. MIGHT BE INCORRECT.
        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)
        # END OF GOT FROM ACCEL 2. MIGHT BE INCORRECT.

        # Get each rotated pos for each tire
        FI_rotated_pos = rotate_wheel(self.FR_wheel_position[0], self.FR_wheel_position[1])
        RI_rotated_pos = rotate_wheel(self.RR_wheel_position[0], self.RR_wheel_position[1])
        FO_rotated_pos = rotate_wheel(self.FL_wheel_position[0], self.FL_wheel_position[1])
        RO_rotated_pos = rotate_wheel(self.RL_wheel_position[0], self.RL_wheel_position[1])

        # relate each rotated pos to the turning center (origin of radius)
        FI_relative_to_r = (FI_rotated_pos[0] + r, FI_rotated_pos[1])
        RI_relative_to_r = (RI_rotated_pos[0] + r, RI_rotated_pos[1])
        FO_relative_to_r = (FO_rotated_pos[0] + r, FO_rotated_pos[1])
        RO_relative_to_r = (RO_rotated_pos[0] + r, RO_rotated_pos[1])

        # Get the direction of motion of each wheel relative to origin radius based on the angle perpendicular to the line drawn from radius to wheel
        FI_direction_motion = math.atan2(FI_relative_to_r[1], FI_relative_to_r[0]) + math.pi/2 # in radians
        RI_direction_motion = math.atan2(RI_relative_to_r[1], RI_relative_to_r[0]) + math.pi/2 # in radians
        FO_direction_motion = math.atan2(FO_relative_to_r[1], FO_relative_to_r[0]) + math.pi/2 # in radians
        RO_direction_motion = math.atan2(RO_relative_to_r[1], RO_relative_to_r[0]) + math.pi/2 # in radians

        # Make a heading for each tire based on car angle and steering angle; transform angles to be relative to radius
        front_heading = car_angle + steering_angle + math.pi/2
        rear_heading = car_angle + math.pi/2

        # Get each slip angle by finding the difference between the direction of motion and the heading of each tire. Negative angles mean direction toward inner turn
        FI_slip_angle = FI_direction_motion - front_heading
        RI_slip_angle = RI_direction_motion - rear_heading
        FO_slip_angle = FO_direction_motion - front_heading
        RO_slip_angle = RO_direction_motion - rear_heading

        print(f"FI_slip_angle: {FI_slip_angle * (180/math.pi)}\nRI_slip_angle: {RI_slip_angle * (180/math.pi)}\nFO_slip_angle: {FO_slip_angle * (180/math.pi)}\nRO_slip_angle: {RO_slip_angle * (180/math.pi)}")

        # Calculate front and rear load transfer
        # START OF GOT FROM ACCEL 2. MIGHT BE INCORRECT.
        FO_load = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front outter wheel
        FI_load = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front inner wheel
        RO_load = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear outter wheel
        RI_load = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear inner wheel
        # END OF GOT FROM ACCEL 2. MIGHT BE INCORRECT.

        # print(f"front_track_load_transfer: {front_track_load_transfer} pounds\nrear_track_load_transfer: {rear_track_load_transfer} pounds")

        print(f"FI_load: {FI_load} pounds\nRI_load: {RI_load} pounds\nFO_load: {FO_load} pounds\nRO_load: {RO_load} pounds")

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        # for i in [FI_load, RI_load, FO_load, RO_load]:
        #     if i < 0: return False, 0

        # Calculate vertical displacement of each tire
        front_inner_displacement = (FI_load - self.W_1) / self.K_RF # inches
        rear_inner_displacement = (RI_load - self.W_3) / self.K_RR # inches
        front_outer_displacement = (FO_load - self.W_2) / self.K_RF # inches
        rear_outer_displacement = (RO_load - self.W_4) / self.K_RR # inches

        # print(f"FI_displacement: {front_inner_displacement} in\nRI_displacement: {rear_inner_displacement} in\nFO_displacement: {front_outer_displacement} in\nRO_displacement: {rear_outer_displacement} in")

        # Calculate camber of each tire
        FI_camber = self.CMB_STC_F + self.CMB_RT_F * front_inner_displacement # degrees
        RI_camber = self.CMB_STC_R + self.CMB_RT_R * rear_inner_displacement # degrees
        FO_camber = self.CMB_STC_F + self.CMB_RT_F * front_outer_displacement # degrees
        RO_camber = self.CMB_STC_R + self.CMB_RT_R * rear_outer_displacement # degrees

        # print(f"FI_camber: {FI_camber}\nRI_camber: {RI_camber}\nFO_camber: {FO_camber}\nRO_camber: {RO_camber}")

        # Calculate the lateral force produced by each tire using the tire model
        FI_FY = self.tires.FY_curves.eval(FI_slip_angle * 180/math.pi, FI_load, FI_camber) # pounds
        RI_FY = self.tires.FY_curves.eval(RI_slip_angle * 180/math.pi, RI_load, RI_camber) # pounds
        FO_FY = self.tires.FY_curves.eval(FO_slip_angle * 180/math.pi, FO_load, FO_camber) # pounds
        RO_FY = self.tires.FY_curves.eval(RO_slip_angle * 180/math.pi, RO_load, RO_camber) # pounds

        print(f"FI_FY: {FI_FY} pounds\nRI_FY: {RI_FY} pounds\nFO_FY: {FO_FY} pounds\nRO_FY: {RO_FY} pounds")

        FY_car = FI_FY + RI_FY + FO_FY + RO_FY
        net_lat_accel = FY_car / self.W_car

        FY_front_axle = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_rear_axle = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        # if (FY_front_axle > FO_FY+FI_FY) or (FY_rear_axle > RO_FY+RI_FY):
        #     return False, 0

        # Calculating max axial acceleration by using a friction ellipse to put the remaining force into axial acceleration.
        if AX > 0: # If launching, force is only coming from rear wheels.
            RI_FX = self.tires.FX_curves.get_max(RI_load, RI_camber) * math.sqrt(1 - (RI_FY/self.tires.FY_curves.get_max(RI_load, RI_camber))**2)
            RO_FX = self.tires.FX_curves.get_max(RO_load, RO_camber) * math.sqrt(1 - (RO_FY/self.tires.FY_curves.get_max(RO_load, RO_camber))**2)
            FI_FX = 0
            FO_FX = 0
            FX_car = RO_FX + RI_FX
        else: # If braking, force is coming from all wheels.
            FI_FX = self.tires.FX_curves.get_max(FI_load, FI_camber) * math.sqrt(1 - (FI_FY**2/self.tires.FY_curves.get_max(FI_load, FI_camber)**2))
            RI_FX = self.tires.FX_curves.get_max(RI_load, RI_camber) * math.sqrt(1 - (RI_FY**2/self.tires.FY_curves.get_max(RI_load, RI_camber)**2))
            FO_FX = self.tires.FX_curves.get_max(FO_load, FO_camber) * math.sqrt(1 - (FO_FY**2/self.tires.FY_curves.get_max(FO_load, FO_camber)**2))
            RO_FX = self.tires.FX_curves.get_max(RO_load, RO_camber) * math.sqrt(1 - (RO_FY**2/self.tires.FY_curves.get_max(RO_load, RO_camber)**2))
            FX_car = FO_FX + FI_FX + RO_FX + RI_FX

        print(f"FI_FX: {FI_FX}\nRI_FX: {RI_FX}\nFO_FX: {FO_FX}\nRO_FX: {RO_FX}")

        net_axial_accel = FX_car / self.W_car

        print(f"lat accel: {net_lat_accel}\naxial accel: {net_axial_accel}")

        return net_axial_accel, net_lat_accel

    # calculates the max available traction in
    # AY is magnitude of lateral acceleration, AX is magnitude of axial acceleration, both are measured in g's
    def accel(self, AY, AX, bitch = False):
        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        W_out_f = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # force on front outter wheel
        W_in_f = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # force on front inner wheel
        W_out_r = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # force on rear outter wheel
        W_in_r = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # force on rear inner wheel

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        for i in [W_out_f, W_in_f, W_out_r, W_in_r]:
            if i < 0: return False

        C_out_f = abs(self.CMB_STC_F + (W_out_f-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
        C_in_f = abs(self.CMB_STC_F + (W_in_f-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        C_out_r = abs(self.CMB_STC_F + (W_out_r-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        C_in_r = abs(self.CMB_STC_F + (W_in_r-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        FY_out_f = self.tires.traction('corner', W_out_f, C_out_f) # max possible lateral acceleration from front outter wheel
        FY_in_f = self.tires.traction('corner', W_in_f, C_in_f)    # max possible lateral acceleration from front inner wheel
        FY_out_r = self.tires.traction('corner', W_out_r, C_out_r) # max possible lateral acceleration from rear outter wheel
        FY_in_r = self.tires.traction('corner', W_in_r, C_in_r)    # max possible lateral acceleration from rear inner wheel

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        if (FY_f > FY_out_f+FY_in_f) or (FY_r > FY_out_r+FY_in_r): return False

        if AX == 0: return True # returning true if no axial acceleration

        f_factor = ((FY_out_f + FY_in_f)**2 - FY_f**2)**0.5 / (FY_out_f + FY_in_f)
        r_factor = ((FY_out_r + FY_in_r)**2 - FY_r**2)**0.5 / (FY_out_r + FY_in_r)

        FX_out_f = f_factor * self.tires.traction('accel', W_out_f, C_out_f) # max possible axial acceleration from front outter wheel
        FX_in_f = f_factor * self.tires.traction('accel', W_in_f, C_in_f)    # max possible axial acceleration from front inner wheel
        FX_out_r = r_factor * self.tires.traction('accel', W_out_r, C_out_r) # max possible axial acceleration from rear outter wheel
        FX_in_r = r_factor * self.tires.traction('accel', W_in_r, C_in_r)    # max possible axial acceleration from rear inner wheel

        self.FX_out_f = FX_out_f
        self.FX_in_f = FX_in_f
        self.FX_out_r = FX_out_r
        self.FX_in_r = FX_in_r

        # Calculating max lateral acceleration from tire traction
        if AX > 0:
            FX = FX_out_r + FX_in_r
        else:
            FX = FX_out_f + FX_in_f + FX_out_r + FX_in_r

        if bitch:
            print(FX_out_f / W_out_f)
            print(FX_in_f / W_in_f)
            print(FX_out_r / W_out_r)
            print(FX_in_r / W_in_r)

        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX): return False
        else: return True

    # modified accel function, currently unfinished. Will account for tire orientation
    def accel2(self, AY, AX, S_c, steer, r):
        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        W_f_out = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # force on front outter wheel
        W_f_in = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # force on front inner wheel
        W_r_out = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # force on rear outter wheel
        W_r_in = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # force on rear inner wheel

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        for i in [W_f_out, W_f_in, W_r_out, W_r_in]:
            if i < 0: return False

        C_f_out = abs(self.CMB_STC_F + (W_f_out-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
        C_f_in = abs(self.CMB_STC_F + (W_f_in-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        C_r_out = abs(self.CMB_STC_R + (W_r_out-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        C_r_in = abs(self.CMB_STC_R + (W_r_in-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        if r == 0:
            S_f_in = steer
            S_f_out = steer
            S_r_in = 0
            S_r_out = 0
        else:
            S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
            S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))
            S_r_in  = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a - np.cos(S_c)*self.t_r/2)))
            S_r_out = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a + np.cos(S_c)*self.t_r/2)))
        
        FY_f_in = abs(self.tires.FY_curves.eval(S_f_in, W_f_in, C_f_in))
        FY_f_out = abs(self.tires.FY_curves.eval(S_f_out, W_f_out, C_f_out))
        FY_r_in = abs(self.tires.FY_curves.eval(S_r_in, W_r_in, C_r_in))
        FY_r_out = abs(self.tires.FY_curves.eval(S_r_out, W_r_out, C_r_out))

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        if (FY_f > FY_f_out+FY_f_in) or (FY_r > FY_r_out+FY_r_in): return False

        if AX == 0: return True # returning true if no axial acceleration

        f_factor = ((FY_f_out + FY_f_in)**2 - FY_f**2)**0.5 / (FY_f_out + FY_f_in)
        r_factor = ((FY_r_out + FY_r_in)**2 - FY_r**2)**0.5 / (FY_r_out + FY_r_in)

        # max possible axial acceleration from front outter wheel
        FX_out_f = np.tan(FY_f_out/abs(self.tires.FY_curves.max(W_f_out, C_f_out))) * abs(self.tires.FX_curves.get_max(W_f_out, C_f_out))
        FX_out_r = np.tan(FY_r_out/abs(self.tires.FY_curves.max(W_r_out, C_r_out))) * abs(self.tires.FX_curves.get_max(W_r_out, C_r_out))
        FX_in_f = np.tan(FY_f_in/abs(self.tires.FY_curves.max(W_f_in, C_f_in))) * abs(self.tires.FX_curves.get_max(W_f_in, C_f_in))
        FX_in_r = np.tan(FY_r_in/abs(self.tires.FY_curves.max(W_r_in, C_r_in))) * abs(self.tires.FX_curves.get_max(W_r_in, C_r_in))
        
        # Calculating max axial acceleration from tire traction
        if AX > 0:
            FX = FX_out_r + FX_in_r
        else:
            FX = FX_out_f + FX_in_f + FX_out_r + FX_in_r
        
        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX): return False
        else: return True

    # recursive function; AY is lateral acceleration
    def max_accel(self, AY, low_guess = 0, high_guess = 2):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0001:
            # print(f"maximum axial acceleration at {AY} lateral g's is {guess}")
            return guess

        if self.accel(AY, guess): # sets low estimate to the guess value if the car can handle cornering acceleration equal to the guess value
            return self.max_accel(AY, guess, high_guess)
        else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
            return self.max_accel(AY, low_guess, guess)

    def max_brake(self, AY, low_guess = -3, high_guess = 0):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration
        
        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0001:
            return guess

        if self.accel(AY, guess): # sets high estimate to the guess value if the car can handle breaking acceleration equal to the guess value
            return self.max_brake(AY, low_guess, guess)
        else: # sets low estimate to the guess value if the car cannot handle breaking acceleration equal to the guess value
            return self.max_brake(AY, guess, high_guess)
    
    # calculates the max acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_accel(self, v, r, transmission_gear='optimal'):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track
        
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
        
        A_tire = 0
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY:
                # linearly interpolating self.A_brake to find the max acceleration at lateral acceleration AY
                A_tire = ((AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])*self.A_accel[i] + (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1])*self.A_accel[i-1] - self.get_drag(v * 0.0568182))
                break
        
        A_tire -= drag # incorporating drag
        A_tire *= 32.17 * 12 # Converting from G's to in/s^2

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's
        A_engn -= drag # incorporating drag
        A_engn *= 32.17*12 # converting from G's to in/s^2

        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_tire < A_engn:
            return A_tire
        else:
            return A_engn
        
    
    # calculates the max braking acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_brake(self, v, r):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track
        
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        A_tire = 0
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY:
                # linearly interpolating self.A_brake to find the braking acceleration at lateral acceleration AY
                A_tire = (AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])*self.A_brake[i] + (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1] )*self.A_brake[i-1]
                break
        
        A_tire -= drag # incorporating drag
        A_tire *= 32.17 * 12 # Converting from G's to in/s^2
        
        return A_tire
    
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
        self.compute_traction_updated()
    

    def adjust_height(self, h):
        ratio = h / self.h
        self.h *= ratio
        self.H *= ratio
        self.z_rf *= ratio
        self.z_rr *= ratio
        self.compute_traction_updated()
        
    
    def traction_curve(self):
        print(f"")
        plt.plot(self.AY, self.A_accel)
        plt.plot(self.AY, self.A_brake)
        plt.xlabel('Lateral Acceleration (g\'s)')
        plt.ylabel('Axial Acceleration (g\'s)')
        plt.grid()
        plt.show()

    def get_values(self):

        # For gas
        # print("GAS")
        # for index, lat in enumerate(self.AY):
        #     car.accel(self, AY=lat, AX=self.A_accel[index])
        #     car.append_data_arrays(self,lat=lat, axi=self.A_accel[index], index=0)
        # print(f"Lateral acceleration (g's): {self.AY}")
        # print(f"Axial acceleration (g's): {self.A_accel}")
        # print(f"Vertical: {racecar.W_out_r_array}")
        # print(f"Lateral: {racecar.FY_out_r_array}")
        # print(f"Axial: {racecar.FX_out_r_array}\n")

        def get_rid_of_zeros(array):
            new_array = []
            for i in range(len(array)):
                new_array.append(array[i][0])
            print(new_array)
            return new_array

        # For braking
        # for index, accel_AY in enumerate(self.AY):
        car.accel(self, AY=0, AX=self.A_brake[0])
        car.get_data(self)
        # racecar.append_data_arrays(self, lat=self.AY[index], axi=self.A_brake[index], index=0)
        print(f"Axial acceleration (g's): {self.A_brake[0]}")
        print(f"Axial outer front: {car.axial_force_outer_front}")
        print(f"Axial inner front: {car.axial_force_inner_front}")
        print(f"Axial outer rear: {car.axial_force_outer_rear}")
        print(f"Axial inner rear: {car.axial_force_inner_rear}")
        print(f"----------------------------")

racecar = car()
racecar.find_AY_AX_for_r_carangle()