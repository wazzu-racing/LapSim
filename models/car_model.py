import math
import os
import pickle
import threading
import numpy as np
from pathlib import Path
import time
import csv
from dataclasses import dataclass

from matplotlib import pyplot as plt

from models import drivetrain_model
from models import tire_model
from interface.file_management.file_manager import file_manager
from interface.loading_window import run_car_model_loading_window

class Car:

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

    # aero csv file delimiter
    aero_delimiter = ';'

    tires = None
    train = None

    def __init__(self, compute_acceleration = True, resolution: int = 100, tire_path ="", drivetrain_path =""):
        """
        Class to initialize and set up configurations for a vehicle's aerodynamic, tire, and drivetrain models.
        :param compute_acceleration: A boolean flag to specify whether initial computations for acceleration should be
                                     performed during initialization.
        :param resolution: An integer specifying the accuracy of acceleration computation.
        """
        self.start = time.perf_counter() # keep track of runtime duration

        self.aero_csv_file_path = file_manager.get_temp_folder_path(
            os.path.join(Path(__file__).resolve().parent.parent, "config_data", "DEFAULT_AERO_ARRAY.csv"))
        self.tire_file_path = tire_path
        self.drivetrain_file_path = drivetrain_path

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

        self.resolution = resolution

        self.reached_max_iterations = False

        self.count = 0

        # Arrays for traction curve. (fill arrays using compute_traction_curve() function)
        self.traction_curve_snippets = []
        self.launch_AX = []
        self.brake_AX = []
        self.launch_AY = []
        self.brake_AY = []

        # Initialize main arrays
        self.radius_array = []
        self.car_angle_array = []
        self.AX_AY_array = []
        if compute_acceleration:
            self.compute_acceleration(resolution)

    @dataclass
    class Car_Data_Snippet:
        """
        Represents the data that the car model experiences at an instance along the track.
        """
        AX: float = 0.0
        AY: float = 0.0
        torque: float = 0.0
        car_body_angle: float = 0.0
        theta_accel: float = 0.0
        FO_load: float = 0.0
        FI_load: float = 0.0
        RO_load: float = 0.0
        RI_load: float = 0.0
        front_outer_displacement: float = 0.0
        front_inner_displacement: float = 0.0
        rear_outer_displacement: float = 0.0
        rear_inner_displacement: float = 0.0
        FO_camber: float = 0.0
        FI_camber: float = 0.0
        RO_camber: float = 0.0
        RI_camber: float = 0.0
        FO_slip: float = 0.0
        FI_slip: float = 0.0
        RO_slip: float = 0.0
        RI_slip: float = 0.0
        FO_FY: float = 0.0
        FI_FY: float = 0.0
        RO_FY: float = 0.0
        RI_FY: float = 0.0
        FO_FX: float = 0.0
        FI_FX: float = 0.0
        RO_FX: float = 0.0
        RI_FX: float = 0.0

    def compute_acceleration(self, n, func=None, open_main_window = False, prev_lap_data=None, controller=None, run_from=""):
        """
        Computes the acceleration array required for running the simulation.
        :param n: Number of intervals for acceleration data creation. The higher this number, the more accurate the simulation will be, but the longer it will take to run this function.
        :type n: int
        :return: None.
        """
        def compute():
            self.AX_AY_array = self.create_accel_2D_array(n, print_info=False)
            self.max_corner = self.max_lateral_accel()

        n_threshold = 100

        # If the controller is not None, then compute the acceleration array in a separate thread and make a loading Window.
        if controller is not None and n > n_threshold:
            x = threading.Thread(target=compute)
            x.daemon = True
            x.start()
            self.resolution = n
            run_car_model_loading_window(self, n, func, prev_lap_data, x, controller, run_from)
            self.end = time.perf_counter()
            print("[Generated Car Object]. Time taken: ", self.end - self.start, " seconds")
        else:
            compute()
            self.end = time.perf_counter()
            print("[Generated Car Object]. Time taken: ", self.end - self.start, " seconds")
            if open_main_window:
                func()

        self.compute_traction_curve()

    def accel(self, r, car_angle, AY, AX, braking = False, print_info = False, print_every_iteration = False):
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
        RO_height = -self.b * np.cos(car_angle) + (self.t_r/2) * np.sin(car_angle)
        RO_dir_motion = car_angle + np.atan2(RO_height, RO_length)

        # Calculate slip angles (signed negative because a negative slip angle is the standard convention for positive FY)
        FI_slip_angle = -(FI_dir_motion + steering) # (car_angle + steering) - FI_dir_motion # -(FI_dir_motion + steering)
        FO_slip_angle = -(FO_dir_motion + steering) # (car_angle + steering) - FO_dir_motion # -(FO_dir_motion + steering)
        RI_slip_angle = -RI_dir_motion # car_angle - RI_dir_motion # -RI_dir_motion
        RO_slip_angle = -RO_dir_motion # car_angle - RO_dir_motion # -RO_dir_motion

        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        # Calculate front and rear load transfer
        self.FO_load = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front outter wheel
        self.FI_load = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front inner wheel
        self.RO_load = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear outter wheel
        self.RI_load = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear inner wheel

        # Calculate vertical displacement of each tire (negative means car is lifted relative to tire, positive means car is lowered relative to tire)
        self.front_inner_displacement = (self.FI_load - self.W_1) / self.K_RF # inches
        self.rear_inner_displacement = (self.RI_load - self.W_3) / self.K_RR # inches
        self.front_outer_displacement = (self.FO_load - self.W_2) / self.K_RF # inches
        self.rear_outer_displacement = (self.RO_load - self.W_4) / self.K_RR # inches

        # Calculate camber of each tire
        self.FI_camber = self.CMB_STC_F + self.CMB_RT_F * self.front_inner_displacement # degrees
        self.RI_camber = self.CMB_STC_R + self.CMB_RT_R * self.rear_inner_displacement # degrees
        self.FO_camber = self.CMB_STC_F + self.CMB_RT_F * self.front_outer_displacement # degrees
        self.RO_camber = self.CMB_STC_R + self.CMB_RT_R * self.rear_outer_displacement # degrees

        # Calculate the lateral force produced by each tire using the tire model
        self.FI_FY = self.tires.FY_curves.eval(FI_slip_angle * 180/math.pi, self.FI_load, self.FI_camber) # pounds
        self.RI_FY = self.tires.FY_curves.eval(RI_slip_angle * 180/math.pi, self.RI_load, self.RI_camber) # pounds
        self.FO_FY = self.tires.FY_curves.eval(FO_slip_angle * 180/math.pi, self.FO_load, self.FO_camber) # pounds
        self.RO_FY = self.tires.FY_curves.eval(RO_slip_angle * 180/math.pi, self.RO_load, self.RO_camber) # pounds

        # Adding up lateral forces and calculating net lateral acceleration
        FY_car = self.FI_FY + self.RI_FY + self.FO_FY + self.RO_FY
        self.net_lat_accel = FY_car / self.W_car

        # Multiple that is used to make FX closer to what the real-world number would look like.
        FX_scale_factor = 1.2

        # Determine max FY for each tire.
        max_RI_FY = self.tires.FY_curves.get_max(self.RI_load, self.RI_camber)
        max_RO_FY = self.tires.FY_curves.get_max(self.RO_load, self.RO_camber)
        max_FI_FY = self.tires.FY_curves.get_max(self.FI_load, self.FI_camber)
        max_FO_FY = self.tires.FY_curves.get_max(self.FO_load, self.FO_camber)

        # Calculating max axial acceleration by using a friction ellipse to put the remaining force into axial acceleration.
        if not braking:
            self.RI_FX = self.tires.FX_curves.get_max(self.RI_load, self.RI_camber) * ((1 - (self.RI_FY**2)/(max_RI_FY**2)) if max_RI_FY > self.RI_FY else 0)**0.5 * FX_scale_factor
            self.RO_FX = self.tires.FX_curves.get_max(self.RO_load, self.RO_camber) * ((1 - (self.RO_FY**2)/(max_RO_FY**2)) if max_RO_FY > self.RO_FY else 0)**0.5 * FX_scale_factor
            self.FI_FX = 0
            self.FO_FX = 0
            FX_car = self.RO_FX + self.RI_FX
        else:
            self.RI_FX = self.tires.FX_curves.get_max(self.RI_load, self.RI_camber) * ((1 - (self.RI_FY**2)/(max_RI_FY**2))**0.5 if max_RI_FY > self.RI_FY else 0) * FX_scale_factor
            self.RO_FX = self.tires.FX_curves.get_max(self.RO_load, self.RO_camber) * ((1 - (self.RO_FY**2)/(max_RO_FY**2))**0.5 if max_RO_FY > self.RO_FY else 0) * FX_scale_factor
            self.FI_FX = self.tires.FX_curves.get_max(self.FI_load, self.FI_camber) * ((1 - (self.FI_FY**2)/(max_FI_FY**2))**0.5 if max_FI_FY > self.FI_FY else 0) * FX_scale_factor
            self.FO_FX = self.tires.FX_curves.get_max(self.FO_load, self.FO_camber) * ((1 - (self.FO_FY**2)/(max_FO_FY**2))**0.5 if max_FO_FY > self.FO_FY else 0) * FX_scale_factor
            FX_car = -(self.RO_FX + self.RI_FX + self.FI_FX + self.FO_FX)

        # Calculate total axial acceleration
        self.net_axial_accel = FX_car / self.W_car

        # Calculate total torque about z axis for both axles, then calculate total torque about z-axis for the car
        FI_torque = self.FI_FY * self.a
        RI_torque = -self.RI_FY * self.b
        FO_torque = self.FO_FY * self.a
        RO_torque = -self.RI_FY * self.b

        # calculate total torque about the z-axis
        total_torque_about_z = FI_torque + RI_torque + FO_torque + RO_torque

        # calculate aligning torque using magic curve
        FI_aligning_torque = self.tires.aligning_torque.eval(FI_slip_angle * 180/math.pi, self.FI_load, self.FI_camber)
        RI_aligning_torque = self.tires.aligning_torque.eval(RI_slip_angle * 180/math.pi, self.RI_load, self.RI_camber)
        FO_aligning_torque = self.tires.aligning_torque.eval(FO_slip_angle * 180/math.pi, self.FO_load, self.FO_camber)
        RO_aligning_torque = self.tires.aligning_torque.eval(RO_slip_angle * 180/math.pi, self.RO_load, self.RO_camber)

        # calculate total aligning torque
        total_aligning_torque = FI_aligning_torque + RI_aligning_torque + FO_aligning_torque + RO_aligning_torque
        total_aligning_torque *= 12 # Convert to inch pounds

        # Print out info depending on certain vars
        if print_every_iteration or (abs(AY - self.net_lat_accel) <= 0.0001 and abs(AX - self.net_axial_accel) <= 0.0001 and print_info and r < 10000):
            print(f"\n------------------- radius: {r} inches, car angle: {car_angle * 180/math.pi} degrees -------------------")
            print(f"steering angle: {steering * 180/math.pi} degrees")
            print(f"FI_slip_angle: {FI_slip_angle * 180/math.pi} degrees\nRI_slip_angle: {RI_slip_angle * 180/math.pi} degrees\nFO_slip_angle: {FO_slip_angle * 180/math.pi} degrees\nRO_slip_angle: {RO_slip_angle * 180/math.pi} degrees",)
            print(f"FI_load: {self.FI_load} pounds\nRI_load: {self.RI_load} pounds\nFO_load: {self.FO_load} pounds\nRO_load: {self.RO_load} pounds")
            print(f"FI_camber: {self.FI_camber} degrees\nRI_camber: {self.RI_camber} degrees\nFO_camber: {self.FO_camber} degrees\nRO_camber: {self.RO_camber} degrees")
            print(f"FI_displacement: {self.front_inner_displacement} in\nRI_displacement: {self.rear_inner_displacement} in\nFO_displacement: {self.front_outer_displacement} in\nRO_displacement: {self.rear_outer_displacement} in")
            print(f"FI_FY: {self.FI_FY} pounds\nRI_FY: {self.RI_FY} pounds\nFO_FY: {self.FO_FY} pounds\nRO_FY: {self.RO_FY} pounds")
            print(f"FI_FX: {self.FI_FX} pounds\nRI_FX: {self.RI_FX} pounds\nFO_FX: {self.FO_FX} pounds\nRO_FX: {self.RO_FX} pounds")
            print(f"RI_FX Max: {self.tires.FX_curves.get_max(self.RI_load, self.RI_camber) * FX_scale_factor} pounds\nRO_FX Max: {self.tires.FX_curves.get_max(self.RO_load, self.RO_camber) * FX_scale_factor} pounds")
            print(f"lat accel: {self.net_lat_accel} g's\naxial accel: {self.net_axial_accel} g's")
            print(f"total_torque: {total_torque_about_z} in pounds")
            print(f"total_aligning_torque: {total_aligning_torque} inch pounds")

        return self.Car_Data_Snippet(AX=self.net_axial_accel, AY=self.net_lat_accel, torque=total_torque_about_z, car_body_angle=car_angle,
                                     theta_accel=0,
                                     FO_load=self.FO_load, RO_load=self.RO_load, FI_load=self.FI_load, RI_load=self.RI_load,
                                     front_inner_displacement=self.front_inner_displacement, front_outer_displacement=self.front_outer_displacement,
                                     rear_outer_displacement=self.rear_outer_displacement, rear_inner_displacement=self.rear_inner_displacement,
                                     FO_camber=self.FO_camber, RI_camber=self.RI_camber, FI_camber=self.FI_camber, RO_camber=self.RO_camber,
                                     FO_FY=self.FO_FY, RI_FY=self.RI_FY, FI_FY=self.FI_FY, RO_FY=self.RO_FY,
                                     FO_FX=self.FO_FX, RI_FX=self.RI_FX, FI_FX=self.FI_FX, RO_FX=self.RO_FX,
                                     FI_slip=FI_slip_angle, RI_slip=RI_slip_angle, FO_slip=FO_slip_angle, RO_slip=RO_slip_angle)

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

        accel = None

        while (abs(input_AY - output_AY) > 0.0001 or abs(input_AX - output_AX) > 0.0001) or (input_AX == 0):
            # Change outputs to inputs
            input_AX, input_AY = output_AX, output_AY

            # Run accel function
            accel = self.accel(radius, car_angle, input_AY, input_AX, braking=braking, print_info=print_info, print_every_iteration=print_every_iteration)
            output_AX, output_AY, torque = accel.AX, accel.AY, accel.torque

            iterations+=1

            # Prevent infinite loop
            if iterations > 100:
                if not self.reached_max_iterations:
                    print(f"Max iterations reached in find_accurate_accel at least once.")
                    self.reached_max_iterations = True
                break

        if print_info or print_every_iteration:
            print(f"iterations: {iterations}")

        return self.Car_Data_Snippet(AX=output_AX, AY=output_AY, torque=torque, car_body_angle=car_angle, theta_accel=0,
                                     FO_load=accel.FO_load, RO_load=accel.RO_load, FI_load=accel.FI_load, RI_load=accel.RI_load,
                                     front_inner_displacement=accel.front_inner_displacement, front_outer_displacement=accel.front_outer_displacement,
                                     rear_outer_displacement=accel.rear_outer_displacement, rear_inner_displacement=accel.rear_inner_displacement,
                                     FO_camber=accel.FO_camber, RI_camber=accel.RI_camber, FI_camber=accel.FI_camber, RO_camber=accel.RO_camber,
                                     FO_FY=accel.FO_FY, RI_FY=accel.RI_FY, FI_FY=accel.FI_FY, RO_FY=accel.RO_FY,
                                     FO_FX=accel.FO_FX, RI_FX=accel.RI_FX, FI_FX=accel.FI_FX, RO_FX=accel.RO_FX,
                                     FI_slip=accel.FI_slip, RI_slip=accel.RI_slip, FO_slip=accel.FO_slip, RO_slip=accel.RO_slip)

    def create_accel_2D_array(self, n:int=20, print_info = False):
        """
        Fills in the r_carangle_2d_array with Car_Data_Snippet objects with each radius along the rows, and each car angle along
        the columns. Uses the find_accurate_accel function to calculate each AX and AY for each radius and car angle.
        :param n: Determines both the number of radii and car angles used to calculate AX and AY. Cannot go lower than 20.
        :return: None
        """

        self.AX_AY_array = []

        # Ensure n is not lower than 20. Prevents inaccurate calculations.
        if n < 20:
            n = 20

        # set up radius and car angle arrays
        self.radius_array = []
        self.car_angle_array = []
        self.radius_array = np.concatenate([self.radius_array, np.linspace(100, 1000, int(n/2))])
        self.radius_array = np.concatenate([self.radius_array, np.linspace(1050, 10000, int(n/4))])
        self.radius_array = np.concatenate([self.radius_array, np.linspace(11000, 100000, int(n/4))])
        self.car_angle_array = np.concatenate([self.car_angle_array, np.linspace(0, 45, n)])
        # print(f"Radii: {self.radius_array}")
        # print(f"Car angles: {self.car_angle_array}")

        # go through each radius
        for radius in self.radius_array:
            row = []
            # go through each car angle
            for c_angle in self.car_angle_array:
                # convert c_angle to radians
                c_angle *= math.pi/180

                # Compute accurate acceleration and torque for radius and c_angle (car angle) if the car is launching
                accel_launch = self.find_accurate_accel(radius, c_angle, print_info=print_info, print_every_iteration=False)
                # Compute accurate acceleration and torque for radius and c_angle (car angle) if the car is braking
                accel_brake = self.find_accurate_accel(radius, c_angle, braking=True, print_info=print_info, print_every_iteration=False)

                # add Car_Data_Snippet object to row of a singular radius
                row.append({"launch": accel_launch,"brake": accel_brake})

            # add row that contains Car_Data_Snippet objects to r_carangle_2d_array
            self.AX_AY_array.append(row)

        # print(car_angle_array)

        # Print out values of r_carangle_2d_array in readable format.
        # for r_index, radius_values in enumerate(self.AX_AY_array):
        #     print(f"Radius: {self.radius_array[r_index]} ----- ", end="")
        #     for index, data in enumerate(radius_values):
        #         print(f"{self.car_angle_array[index]} - AX: {data["launch"].AX}, AY: {data["launch"].AY}, Torque: {data["launch"].torque} \n FI: {data["launch"].FI_slip}, FO: {data["brake"].FO_slip}, RI: {data["launch"].RI_slip}, RO: {data["launch"].RO_slip}\n\n", end="")
        #     print("")

        print(f"[Generated 2D array]")
        return self.AX_AY_array

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
            if rad >= radius:
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

        car_data_snippet = None

        if r > 0:
            AY = v**2/r / 12 / 32.17 # g's
        else:
            # self.count+=1
            AY = 0

        if AY == 0:
            return self.AX_AY_array[len(self.radius_array)-1][0]["brake"]

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

            car_data_snippet = self.AX_AY_array[r_index][car_angle_array_index]["brake"]
            # car_data_snippet = self.find_accurate_accel(r, self.car_angle_array[car_angle_array_index] * math.pi/180, braking=True)

            output_AY = car_data_snippet.AY
            output_AX = car_data_snippet.AX

            # If output AY is starting to decrease with increased iterations of car_angle_array_index, maximum AY has been reached.
            if output_AY < prev_AY and count != 0:
                # Check to make sure that the car_angle_array_index is not too small for the radius.
                # This model tends to start behaving weirdly around the 150-inch radius for braking (due to realistic slip angles)
                # and gives smaller car body angles than is reasonable.
                if r < 200 and car_angle_array_index < int(len(self.car_angle_array)/4):
                    car_angle_array_index += 1
                    count += 1
                    continue

                break

            car_angle_array_index += 1
            count += 1

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
        output_AX -= drag # incorporating drag

        # print(f"{self.count}: using car angle {self.car_angle_array[car_angle_array_index-1]}, actual radius {r}, closest radius {self.radius_array[r_index]} -- AX: {output_AX}, AY: {AY}")

        # self.count+=1

        return self.Car_Data_Snippet(
            AX=output_AX, AY=AY, torque=car_data_snippet.torque, theta_accel=0,
            car_body_angle=self.car_angle_array[car_angle_array_index-1],
            FO_load=car_data_snippet.FO_load, RO_load=car_data_snippet.RO_load, FI_load=car_data_snippet.FI_load, RI_load=car_data_snippet.RI_load,
            front_inner_displacement=car_data_snippet.front_inner_displacement, front_outer_displacement=car_data_snippet.front_outer_displacement,
            rear_outer_displacement=car_data_snippet.rear_outer_displacement, rear_inner_displacement=car_data_snippet.rear_inner_displacement,
            FO_camber=car_data_snippet.FO_camber, RI_camber=car_data_snippet.RI_camber, FI_camber=car_data_snippet.FI_camber, RO_camber=car_data_snippet.RO_camber,
            FO_FY=car_data_snippet.FO_FY, RI_FY=car_data_snippet.RI_FY, FI_FY=car_data_snippet.FI_FY, RO_FY=car_data_snippet.RO_FY,
            FO_FX=car_data_snippet.FO_FX, RI_FX=car_data_snippet.RI_FX, FI_FX=car_data_snippet.FI_FX, RO_FX=car_data_snippet.RO_FX,
            FI_slip=car_data_snippet.FI_slip, RI_slip=car_data_snippet.RI_slip, FO_slip=car_data_snippet.FO_slip, RO_slip=car_data_snippet.RO_slip)

    # Calculates the positive axial acceleration of the car at a given radius and velocity.
    def curve_accel(self, r, v, transmission_gear ='optimal'):
        """
        Calculates the axial acceleration of the car at a given radius and velocity.
        :param r: The radius of the car at which to calculate the acceleration. (inches)
        :param v: The velocity of the car at which to calculate the acceleration. (in/s)
        :param transmission_gear: The gear the car is in.
        :return: The axial acceleration of the car at the given radius and velocity. (g's)
        """

        car_data_snippet = None

        if r > 0:
            AY = v**2/r / 12 / 32.17 # g's
        else:
            self.count+=1
            AY = 0

        if AY == 0:
            return self.AX_AY_array[len(self.radius_array)-1][0]["launch"]

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

            car_data_snippet = self.AX_AY_array[r_index][car_angle_array_index]["launch"]
            # car_data_snippet = self.find_accurate_accel(r, self.car_angle_array[car_angle_array_index] * math.pi/180)

            output_AY = car_data_snippet.AY
            output_AX = car_data_snippet.AX

            # If output AY is starting to decrease with increased iterations of car_angle_array_index, maximum AY has been reached.
            if output_AY < prev_AY and count != 0:
                # Check to make sure that the car_angle_array_index is not too small for the radius.
                # This model tends to start behaving weirdly around the 300-inch radius for launching (due to realistic slip angles)
                # and gives smaller car body angles than is reasonable.
                if r < 350 and car_angle_array_index < int(len(self.car_angle_array)/6):
                    car_angle_array_index += 1
                    count += 1
                    continue

                break

            car_angle_array_index += 1
            count += 1

        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        A_tire = output_AX # Tire traction G's
        A_tire -= drag # incorporating drag
        A_tire *= 32.17*12# converting from G's to in/s^2

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's
        A_engn -= drag # incorporating drag
        A_engn *= 32.17*12 # converting from G's to in/s^2

        # if A_engn == 0:
        #     print(f"v: {int(v*0.0568182)}, transmission gear: {transmission_gear}")

        self.count+=1

        final_AX = 0.0
        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_tire < A_engn or A_engn == abs(drag):
            final_AX = A_tire
        else:
            final_AX = A_engn

        final_AX /= 32.17 * 12 # Convert to g's

        # print(f"{self.count}: using car angle {self.car_angle_array[car_angle_array_index-1]}, radius {r} -- AX: {final_AX}, AY: {AY}")

        return self.Car_Data_Snippet(AX=final_AX, AY=AY, torque=car_data_snippet.torque, theta_accel=0,
                car_body_angle=self.car_angle_array[car_angle_array_index-1],
                FO_load=car_data_snippet.FO_load, RO_load=car_data_snippet.RO_load, FI_load=car_data_snippet.FI_load, RI_load=car_data_snippet.RI_load,
                front_inner_displacement=car_data_snippet.front_inner_displacement, front_outer_displacement=car_data_snippet.front_outer_displacement,
                rear_outer_displacement=car_data_snippet.rear_outer_displacement, rear_inner_displacement=car_data_snippet.rear_inner_displacement,
                FO_camber=car_data_snippet.FO_camber, RI_camber=car_data_snippet.RI_camber, FI_camber=car_data_snippet.FI_camber, RO_camber=car_data_snippet.RO_camber,
                FO_FY=car_data_snippet.FO_FY, RI_FY=car_data_snippet.RI_FY, FI_FY=car_data_snippet.FI_FY, RO_FY=car_data_snippet.RO_FY,
                FO_FX=car_data_snippet.FO_FX, RI_FX=car_data_snippet.RI_FX, FI_FX=car_data_snippet.FI_FX, RO_FX=car_data_snippet.RO_FX,
                FI_slip=car_data_snippet.FI_slip, RI_slip=car_data_snippet.RI_slip, FO_slip=car_data_snippet.FO_slip, RO_slip=car_data_snippet.RO_slip)

    def curve_gear_change(self, r, v):
        if r > 0:
            AY = v**2/r / 12 / 32.17 # g's
        else:
            AY = 0

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

            car_data_snippet = self.AX_AY_array[r_index][car_angle_array_index]["launch"]

            output_AY = car_data_snippet.AY
            output_AX = car_data_snippet.AX

            # If output AY is starting to decrease with increased iterations of car_angle_array_index, maximum AY has been reached.
            if output_AY < prev_AY and count != 0:
                # Check to make sure that the car_angle_array_index is not too small for the radius.
                # This model tends to start behaving weirdly around the 300-inch radius for launching (due to realistic slip angles)
                # and gives smaller car body angles than is reasonable.
                if r < 350 and car_angle_array_index < int(len(self.car_angle_array)/6):
                    car_angle_array_index += 1
                    count += 1
                    continue

                break

            car_angle_array_index += 1
            count += 1

        # Calculate AX for gear change
        self.RI_FX = self.C_rr * self.W_3
        self.RO_FX = self.C_rr * self.W_4
        self.FI_FX = self.C_rr * self.W_1
        self.FO_FX = self.C_rr * self.W_2
        FX_car = -(self.RO_FX + self.RI_FX + self.FI_FX + self.FO_FX)
        AX = FX_car / self.W_car

        accel = self.accel(self.radius_array[r_index], self.car_angle_array[car_angle_array_index - 1], AY, AX, braking=False)

        # apply drag
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)n

        accel.AX = AX - drag

        return accel

    def max_axial_accel(self):
        """
        Finds the maximum axial acceleration of the car along the x/longitudinal axis.
        :return: The maximum axial acceleration of the car in g's.
        """
        return self.find_accurate_accel(10000000, 0).AX

    def max_lateral_accel(self):
        """
        Finds the maximum lateral acceleration of the car along the y/lateral axis.
        :return: The maximum lateral acceleration of the car. (g's)
        """
        car_body_angle = 10 * math.pi / 180
        output_AY = 1.0
        prev_AY = 0.0
        while output_AY > prev_AY:
            if car_body_angle > 10 * math.pi / 180:
                prev_AY = output_AY

            snippet = self.find_accurate_accel(100000, car_body_angle)
            output_AY = snippet.AY

            car_body_angle+=0.001

        return prev_AY

    # DO NOT USE FOR MOST CASES. Read carefully.
    def max_lateral_accel_car_angle(self):
        """
        THIS IS NOT THE MAXIMUM CAR BODY ANGLE OF THE CAR.

        Finds the car body angle when the car reaches its maximum lateral acceleration.
        :return: The car body angle at the maximum lateral acceleration of the car. (radians)
        """
        car_body_angle = 10 * math.pi / 180
        output_AY = 1.0
        prev_AY = 0.0
        iteration_value = 0.001
        while output_AY > prev_AY:
            if car_body_angle > 10 * math.pi / 180:
                prev_AY = output_AY

            snippet = self.find_accurate_accel(100000, car_body_angle)
            output_AY = snippet.AY

            car_body_angle+=iteration_value

        return car_body_angle-iteration_value

    def compute_traction_curve(self):

        def lerp(x, x1, x2, y1, y2):
            return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

        start_traction_curve = time.perf_counter() # Keep track of how long it takes to compute the traction curve.

        launch_theta_force_array = np.linspace(0, 180, 181)
        theta_data_array = [self.Car_Data_Snippet for _ in range(len(launch_theta_force_array))]

        theta_data_array[0] = self.find_accurate_accel(1000000, 0)
        theta_data_array[0].AY = 0 # AY is 0 to 3 decimals, so AY is essentially just 0.
        theta_data_array[180] = self.find_accurate_accel(100000, 0, braking=True)

        car_body_angle = 0
        output_AY = 0
        output_AX = 0
        output_theta = 0
        theta_completed = 0
        brek = False
        for theta in range(1, int(len(launch_theta_force_array)/2)):
            # print(theta)

            snippet = None
            iterations = 0
            while output_theta < theta:
                car_body_angle += 0.00001

                if iterations < 5000:
                    snippet = self.find_accurate_accel(100000, car_body_angle, braking=False)
                else:
                    brek = True
                    break
                output_AY = snippet.AY
                output_AX = snippet.AX

                output_theta = math.atan2(output_AY, output_AX) * 180 / math.pi

                iterations+=1

            if brek:
                break

            theta_completed += 1

            # print(f'iterations {iterations}')
            # print(f"{output_theta} - AX: {snippet.AX}, AY: {snippet.AY}")
            # print(f"FI_FY: {snippet.FI_FY}, FO_FY: {snippet.FO_FY}, RI_FY: {snippet.RI_FY}, RO_FY: {snippet.RO_FY}\n")

            # Set vars that are inaccurate to 0
            snippet.theta_accel = theta
            snippet.FO_slip = 0
            snippet.RO_slip = 0
            snippet.FI_slip = 0
            snippet.RI_slip = 0

            theta_data_array[theta] = snippet

        # Interpolate the traction curve for the last few degrees of launching (roughly 85-90 degrees).
        x1, x2 = theta_data_array[theta_completed].AY, self.max_lateral_accel()
        y1, y2 = theta_data_array[theta_completed].AX, 0
        AY = theta_data_array[theta_completed].AY
        AX = theta_data_array[theta_completed].AX
        for theta in range(theta_completed+1, 90):
            # print(theta)

            theta_force = 0
            count = 0
            # Find the AX and AY that are needed to conform to the traction curve.
            while theta_force < theta:
                AX = lerp(AY, x1, x2, y1, y2)
                AY += 0.00001

                theta_force = math.atan2(AY, AX) * 180 / math.pi
                count+=1

            snippet = self.accel(100000, lerp(AY, x1, x2, theta_data_array[theta_completed].car_body_angle, self.max_lateral_accel_car_angle()), AY, AX)
            snippet.AY = AY
            snippet.AX = AX
            snippet.RI_FX = lerp(AX, y1, y2, theta_data_array[theta_completed].RI_FX, 0)
            snippet.RO_FX = lerp(AX, y1, y2, theta_data_array[theta_completed].RO_FX, 0)

            # Set vars that are inaccurate to 0
            snippet.theta_accel = theta
            snippet.FO_slip = 0
            snippet.RO_slip = 0
            snippet.FI_slip = 0
            snippet.RI_slip = 0

            # print(f"{theta_force} - AX: {snippet.AX}, AY: {snippet.AY}")
            # print(f"FI_FY: {snippet.FI_FY}, FO_FY: {snippet.FO_FY}, RI_FY: {snippet.RI_FY}, RO_FY: {snippet.RO_FY}\n")

            theta_data_array[theta] = snippet

        # Calculate traction curve at max lateral acceleration. (This is a little special, so it's done separately)
        snippet = self.accel(100000, self.max_lateral_accel_car_angle(), self.max_lateral_accel(), 0)
        snippet.AY = self.max_lateral_accel()
        snippet.AX = 0
        snippet.RI_FX = 0
        snippet.RO_FX = 0
        theta_data_array[90] = snippet

        output_AY = 0
        output_AX = 0
        output_theta = 1000
        car_body_angle = 0
        brek = False
        theta_completed = 180 # not actually, just need to set this to 181 for logic's sake in this next for loop
        for theta in range(int(len(launch_theta_force_array))-2, int(len(launch_theta_force_array)/2)+1, -1):
            # print(theta)

            snippet = None
            iterations = 0
            while output_theta > theta:
                car_body_angle += 0.00001

                if iterations < 5000:
                    snippet = self.find_accurate_accel(100000, car_body_angle, braking=True)
                else:
                    brek = True
                    break
                output_AY = snippet.AY
                output_AX = snippet.AX

                output_theta = math.atan2(output_AY, output_AX) * 180 / math.pi

                iterations += 1

            if brek:
                break

            theta_completed -= 1

            # Set vars that are inaccurate to 0
            snippet.theta_accel = theta
            snippet.FO_slip = 0
            snippet.RO_slip = 0
            snippet.FI_slip = 0
            snippet.RI_slip = 0

            # print(f"{output_theta} - AX: {snippet.AX}, AY: {snippet.AY}")
            # print(f"FI_FY: {snippet.FI_FY}, FO_FY: {snippet.FO_FY}, RI_FY: {snippet.RI_FY}, RO_FY: {snippet.RO_FY}\n")

            theta_data_array[theta] = snippet

        # Interpolate the traction curve for the last few degrees of braking (roughly 95-91 degrees).
        x1, x2 = theta_data_array[theta_completed].AY, self.max_lateral_accel()
        y1, y2 = theta_data_array[theta_completed].AX, 0
        AY = theta_data_array[theta_completed].AY
        AX = theta_data_array[theta_completed].AX
        for theta in range(theta_completed-1, 90, -1):
            # print(theta)

            theta_force = 1000
            count = 0
            # Find the AX and AY that are needed to conform to the traction curve.
            while theta_force > theta:
                AX = lerp(AY, x1, x2, y1, y2)
                AY += 0.00001

                theta_force = math.atan2(AY, AX) * 180 / math.pi
                count+=1

            snippet = self.accel(100000, lerp(AY, x1, x2, theta_data_array[theta_completed].car_body_angle, self.max_lateral_accel_car_angle()), AY, AX, braking=True)
            snippet.AY = AY
            snippet.AX = AX

            # Set vars that are inaccurate to 0
            snippet.theta_accel = theta
            snippet.FO_slip = 0
            snippet.RO_slip = 0
            snippet.FI_slip = 0
            snippet.RI_slip = 0

            theta_data_array[theta] = snippet

            # print(f"{theta_force} - AX: {snippet.AX}, AY: {snippet.AY}")
            # print(f"FI_FY: {snippet.FI_FY}, FO_FY: {snippet.FO_FY}, RI_FY: {snippet.RI_FY}, RO_FY: {snippet.RO_FY}\n")

        # Append all data to arrays
        for snippet in theta_data_array:
            self.traction_curve_snippets.append(snippet)

        for index in range(int(len(theta_data_array)/2)+1):
            self.launch_AY.append(theta_data_array[index].AY)
            self.launch_AX.append(theta_data_array[index].AX)

        for index in range(int(len(theta_data_array)/2), len(theta_data_array)):
            self.brake_AY.append(theta_data_array[index].AY)
            self.brake_AX.append(theta_data_array[index].AX)

        # print(f"launch")
        # print(f"AY: {self.launch_AY}\nAX: {self.launch_AX}")
        #
        # print(f"brake")
        # print(f"AY: {self.brake_AY}\nAX: {self.brake_AX}")

        end_traction_curve = time.perf_counter()
        print(f"[Computed traction curve]. Time taken: {end_traction_curve - start_traction_curve} seconds.")

    def plot_traction_curve(self):
        plt.plot(self.launch_AY, self.launch_AX, label="Launch")
        plt.plot(self.brake_AY, self.brake_AX, label="Brake")
        plt.xlabel("Lateral Acceleration (g's)")
        plt.ylabel("Axial Acceleration (g's)")
        plt.grid(True)
        plt.legend()
        plt.show()

    def plot_RI_FY(self):
        for index, radius in enumerate(self.radius_array):
            if index % 1 == 0:
                RI_FY = []
                for data in self.AX_AY_array[index]:
                    RI_FY.append(data["launch"].RI_FY)
                plt.plot(self.car_angle_array, RI_FY, label=f"{round(radius)} in")
        plt.xlabel("Car body angle (degrees)")
        plt.ylabel("RI_FY (pounds)")
        plt.grid(True)
        plt.legend()
        plt.show()

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
        self.compute_acceleration(self.resolution)

    def adjust_height(self, h):
        ratio = h / self.h
        self.h *= ratio
        self.H *= ratio
        self.z_rf *= ratio
        self.z_rr *= ratio
        # Recalculate AX_AY_array since height has changed
        self.compute_acceleration(self.resolution)

# Purpose of this class is to create pickles for autocross and endurance
class points:
    def __init__ (self):
        self.nds = []

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
#
#     print("created!")
#
# create_track_pickle("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim/config_data/track_points/Points for Autocross.rtf",
#                     "/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim/config_data/track_points/autocross_trk_points.pkl",
#                     True)

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

# def generate_lerped_snippet(AX, AY, x1, x2):
#     snippet = self.Car_Data_Snippet
#     snippet.AX = AX
#     snippet.AY = AY
#
#     snippet.torque = lerp(AY, x1, x2, theta_data_array[theta_completed-1].torque, theta_data_array[theta_completed].torque)
#     snippet.car_body_angle = lerp(AY, x1, x2, theta_data_array[theta_completed-1].car_body_angle, theta_data_array[theta_completed].car_body_angle)
#
#     snippet.FO_load = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_load, theta_data_array[theta_completed].FO_load)
#     snippet.FI_load = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_load, theta_data_array[theta_completed].FI_load)
#     snippet.RO_load = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_load, theta_data_array[theta_completed].RO_load)
#     snippet.RI_load = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_load, theta_data_array[theta_completed].RI_load)
#
#     snippet.front_outer_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].front_outer_displacement,
#         theta_data_array[theta_completed].front_outer_displacement
#     )
#     snippet.front_inner_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].front_inner_displacement,
#         theta_data_array[theta_completed].front_inner_displacement
#     )
#     snippet.rear_outer_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].rear_outer_displacement,
#         theta_data_array[theta_completed].rear_outer_displacement
#     )
#     snippet.rear_inner_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].rear_inner_displacement,
#         theta_data_array[theta_completed].rear_inner_displacement
#     )
#
#     snippet.FO_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_camber, theta_data_array[theta_completed].FO_camber)
#     snippet.FI_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_camber, theta_data_array[theta_completed].FI_camber)
#     snippet.RO_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_camber, theta_data_array[theta_completed].RO_camber)
#     snippet.RI_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_camber, theta_data_array[theta_completed].RI_camber)
#
#     snippet.FO_slip = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_slip, theta_data_array[theta_completed].FO_slip)
#     snippet.FI_slip = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_slip, theta_data_array[theta_completed].FI_slip)
#     snippet.RO_slip = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_slip, theta_data_array[theta_completed].RO_slip)
#     snippet.RI_slip = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_slip, theta_data_array[theta_completed].RI_slip)
#
#     snippet.FO_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_FY, theta_data_array[theta_completed].FO_FY)
#     snippet.FI_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_FY, theta_data_array[theta_completed].FI_FY)
#     snippet.RO_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_FY, theta_data_array[theta_completed].RO_FY)
#     snippet.RI_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_FY, theta_data_array[theta_completed].RI_FY)
#
#     snippet.FO_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_FX, theta_data_array[theta_completed].FO_FX)
#     snippet.FI_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_FX, theta_data_array[theta_completed].FI_FX)
#     snippet.RO_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_FX, theta_data_array[theta_completed].RO_FX)
#     snippet.RI_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_load, theta_data_array[theta_completed].RO_load)
#     snippet.RI_load = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_load, theta_data_array[theta_completed].RI_load)
#
#     snippet.front_outer_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].front_outer_displacement,
#         theta_data_array[theta_completed].front_outer_displacement
#     )
#     snippet.front_inner_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].front_inner_displacement,
#         theta_data_array[theta_completed].front_inner_displacement
#     )
#     snippet.rear_outer_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].rear_outer_displacement,
#         theta_data_array[theta_completed].rear_outer_displacement
#     )
#     snippet.rear_inner_displacement = lerp(
#         AY, x1, x2,
#         theta_data_array[theta_completed-1].rear_inner_displacement,
#         theta_data_array[theta_completed].rear_inner_displacement
#     )
#
#     snippet.FO_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_camber, theta_data_array[theta_completed].FO_camber)
#     snippet.FI_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_camber, theta_data_array[theta_completed].FI_camber)
#     snippet.RO_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_camber, theta_data_array[theta_completed].RO_camber)
#     snippet.RI_camber = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_camber, theta_data_array[theta_completed].RI_camber)
#
#     snippet.FO_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_FY, theta_data_array[theta_completed].FO_FY)
#     snippet.FI_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_FY, theta_data_array[theta_completed].FI_FY)
#     snippet.RO_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_FY, theta_data_array[theta_completed].RO_FY)
#     snippet.RI_FY = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_FY, theta_data_array[theta_completed].RI_FY)
#
#     snippet.FO_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FO_FX, theta_data_array[theta_completed].FO_FX)
#     snippet.FI_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].FI_FX, theta_data_array[theta_completed].FI_FX)
#     snippet.RO_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RO_FX, theta_data_array[theta_completed].RO_FX)
#     snippet.RI_FX = lerp(AY, x1, x2, theta_data_array[theta_completed-1].RI_FX, theta_data_array[theta_completed].RI_FX)
#
#     return snippet

# def interpolate_car_data_snippet(lower_car_data_snippet, upper_car_data_snippet, type):
#     new_snippet = self.Car_Data_Snippet
#
#     theta = math.floor(upper_car_data_snippet[type].theta_accel)
#
#     if type=="brake":
#         print(lower_car_data_snippet[type].AX)
#         print(upper_car_data_snippet[type].AX)
#
#     new_snippet.AX = lower_car_data_snippet[type].AX + (theta - lower_car_data_snippet[type].theta_accel) * (upper_car_data_snippet[type].AX - lower_car_data_snippet[type].AX) / (upper_car_data_snippet[type].theta_accel - lower_car_data_snippet[type].theta_accel)
#     new_snippet.AY = lower_car_data_snippet[type].AY + (theta - lower_car_data_snippet[type].theta_accel) * (upper_car_data_snippet[type].AY - lower_car_data_snippet[type].AY) / (upper_car_data_snippet[type].theta_accel - lower_car_data_snippet[type].theta_accel)
#
#     return new_snippet
#
# radius_array = np.linspace(100, 10000, 1000)
# velocity_array = np.linspace(0, 1230, 200)
#
# launch_theta_force_array = np.linspace(0, 180, 181)
# theta_data_array = [self.Car_Data_Snippet for _ in range(len(launch_theta_force_array))]
#
# max_lat = self.max_lateral_accel()
#
# car_data_snippet_array = [[{} for _ in range(len(velocity_array))] for _ in range(len(radius_array))] # len(radius_array) by len(velocity_array) array of Car_Data_Snippet objects
#
# for r_index, r in enumerate(radius_array):
#     for v_index, v in enumerate(velocity_array):
#
#         if r_index < 200:
#             # If the AY is more than the car can produce, then skip the rest of the iterations for this velocity.
#             AY = v**2/r / 12 / 32.17
#             if AY > max_lat:
#                 break
#
#             car_data_snippet_array[r_index][v_index] = {"launch": self.curve_accel(r, v), "brake":self.curve_brake(r, v)}
#
# # Set theta forces in car_data_snippets
# for data_row in car_data_snippet_array:
#     for data in data_row:
#         try:
#             data["launch"].AY == 0
#
#             data["launch"].theta_accel = math.atan2(data["launch"].AY, data["launch"].AX) * 180 / math.pi
#             data["brake"].theta_accel = math.atan2(data["brake"].AY, data["brake"].AX) * 180 / math.pi
#             print(f"theta: {data["launch"].theta_accel}, {data['brake'].theta_accel}")
#         except Exception:
#             break
#
# for theta in launch_theta_force_array:
#     highest_lower_theta_data = {"launch": self.Car_Data_Snippet, "brake": self.Car_Data_Snippet}
#     highest_upper_theta_data = {"launch": self.Car_Data_Snippet, "brake": self.Car_Data_Snippet}
#     highest_lower_theta_data["launch"].RO_FY = -100
#     highest_lower_theta_data["brake"].RO_FY = -100
#     highest_upper_theta_data["launch"].RO_FY = -100
#     highest_upper_theta_data["brake"].RO_FY = -100
#
#     print(f"{theta}")
#
#     if theta == 0:
#         theta_data_array[int(theta)] = self.accel(100000, 0, 0, self.max_axial_accel())
#         continue
#     elif theta == 180:
#         theta_data_array[int(theta)] = self.accel(100000, 0, 0, self.max_axial_accel(), braking=True)
#         continue
#     elif theta < 90:
#         # Check launch values
#         for data_row_index in np.arange(0, len(radius_array)):
#             for data in car_data_snippet_array[data_row_index]:
#                 # Check to make sure Car_Data_Snippet object was created.
#                 try:
#                     launch_data = data["launch"]
#                     # print(launch_data.theta_accel)
#
#                     if launch_data.theta_accel < theta and launch_data.theta_accel > theta-1:
#                         if launch_data.RO_FY > highest_lower_theta_data["launch"].RO_FY:
#                             print(f"found lower: {launch_data.theta_accel}")
#                             highest_lower_theta_data = data
#                     elif launch_data.theta_accel > theta and launch_data.theta_accel < theta+1:
#                         if launch_data.RO_FY > highest_upper_theta_data["launch"].RO_FY:
#                             print(f"found upper: {launch_data.theta_accel}")
#                             highest_upper_theta_data = data
#                 except Exception:
#                     pass
#     else:
#         # Check brake values
#         for data_row_index in np.arange(len(radius_array), 0):
#             for data in car_data_snippet_array[data_row_index]:
#                 # Check to make sure Car_Data_Snippet object was created.
#                 try:
#                     brake_data = data["brake"]
#
#                     if brake_data.theta_accel < theta and brake_data.theta_accel > theta-1:
#                         if brake_data.FO_FY > highest_lower_theta_data["brake"].FO_FY:
#                             print(f"found lower: {brake_data.theta_accel}")
#                             highest_lower_theta_data = data
#                     elif brake_data.theta_accel > theta and brake_data.theta_accel < theta+1:
#                         if brake_data.FO_FY > highest_upper_theta_data["brake"].FO_FY:
#                             print(f"found upper: {brake_data.theta_accel}")
#                             highest_upper_theta_data = data
#                 except Exception:
#                     pass
#
#     type = "launch" if theta < 90 else "brake"
#     data = interpolate_car_data_snippet(highest_lower_theta_data, highest_upper_theta_data, type)
#     theta_data_array[int(theta)] = data
#
#     # print(f"{theta}: AX: {data.AX}, AY: {data.AY}")

car = Car()
# car.plot_RI_FY()
for snippet in car.traction_curve_snippets:
    print(f"\n------------------- AY: {snippet.AY}, AX: {snippet.AX} -------------------")
    print(f"Force theta: {snippet.theta_accel}")
    print(f"FI_load: {snippet.FI_load} pounds\nRI_load: {snippet.RI_load} pounds\nFO_load: {snippet.FO_load} pounds\nRO_load: {snippet.RO_load} pounds")
    print(f"FI_camber: {snippet.FI_camber} degrees\nRI_camber: {snippet.RI_camber} degrees\nFO_camber: {snippet.FO_camber} degrees\nRO_camber: {snippet.RO_camber} degrees")
    print(f"FI_displacement: {snippet.front_inner_displacement} in\nRI_displacement: {snippet.rear_inner_displacement} in\nFO_displacement: {snippet.front_outer_displacement} in\nRO_displacement: {snippet.rear_outer_displacement} in")
    print(f"FI_FY: {snippet.FI_FY} pounds\nRI_FY: {snippet.RI_FY} pounds\nFO_FY: {snippet.FO_FY} pounds\nRO_FY: {snippet.RO_FY} pounds")
    print(f"FI_FX: {snippet.FI_FX} pounds\nRI_FX: {snippet.RI_FX} pounds\nFO_FX: {snippet.FO_FX} pounds\nRO_FX: {snippet.RO_FX} pounds")