import math

import numpy as np
import copy

from gen_lapsim.spline_track import curve


class LapSimData:
    def __init__(self):
        # Array for time t
        self.time_array = [0]
        # Arrays for lateral and axial acceleration of car
        self.AY = [] # Positive AY is turning right, negative AY is turning left.
        self.AX = []
        #Array for car body angle
        self.car_body_angle = []
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
        self.rear_inner_displacement  = []
        self.front_outer_displacement = []
        self.rear_outer_displacement  = []
        # Angle of accel force of car
        self.theta_accel = []

        self.max_value_names = ["max_time", "max_AY", "max_AX", "max_FI_load", "max_FO_load", "max_RI_load",
                                "max_RO_load", "max_FI_FY", "max_FO_FY", "max_RI_FY", "max_RO_FY", "max_FI_FX",
                                "max_FO_FX", "max_RI_FX", "max_RO_FX", "max_FI_vector_mag", "max_FO_vector_mag",
                                "max_RI_vector_mag", "max_RO_vector_mag", "front_inner_displacement", "rear_inner_displacement",
                                "front_outer_displacement", "rear_outer_displacement"]

    # Initialize all of the arrays in LapSimData
    def initialize(self, n):
        # array for time elapsed
        self.time_array = [0]
        # Collect lateral and axial acceleration
        self.AX = np.zeros(int(n + 1))
        self.AY = np.zeros(int(n + 1))
        # Collect car body angle
        self.car_body_angle = np.zeros(int(n + 1))
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
        self.rear_inner_displacement  = np.zeros(int(n + 1))
        self.front_outer_displacement = np.zeros(int(n + 1))
        self.rear_outer_displacement  = np.zeros(int(n + 1))
        # theta of force on car
        self.theta_accel = np.zeros(int(n + 1))

    # Append a data point to all arrays.
    def append_data_arrays(self, car_data_snippet, index):
        # Collect lateral and axial acceleration of car
        self.AX[index] = car_data_snippet.AX
        self.AY[index] = car_data_snippet.AY

        # Collect car body angle
        self.car_body_angle[index] = car_data_snippet.car_body_angle

        # lateral, axial, and vertical forces on tires
        self.FO_load_array[index] = car_data_snippet.FO_load
        self.FI_load_array[index] = car_data_snippet.FI_load
        self.RO_load_array[index] = car_data_snippet.RO_load
        self.RI_load_array[index] = car_data_snippet.RI_load
        self.FO_FY_array[index] = car_data_snippet.FO_FY
        self.FI_FY_array[index] = car_data_snippet.FI_FY
        self.RO_FY_array[index] = car_data_snippet.RO_FY
        self.RI_FY_array[index] = car_data_snippet.RI_FY
        self.FO_FX_array[index] = car_data_snippet.FO_FX
        self.FI_FX_array[index] = car_data_snippet.FI_FX
        self.RO_FX_array[index] = car_data_snippet.RO_FX
        self.RI_FX_array[index] = car_data_snippet.RI_FX

        # Vectors of forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.FI_vector[index] = np.array([car_data_snippet.FI_FX,car_data_snippet.FI_FY, car_data_snippet.FI_load])
        self.RI_vector[index] = np.array([car_data_snippet.RI_FX, car_data_snippet.RI_FY, car_data_snippet.RI_load])
        self.FO_vector[index] = np.array([car_data_snippet.FO_FX,car_data_snippet.FO_FY,car_data_snippet.FO_load])
        self.RO_vector[index] = np.array([car_data_snippet.RO_FX,car_data_snippet.RO_FY,car_data_snippet.RO_load])
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
        self.front_inner_displacement[index] = car_data_snippet.front_inner_displacement
        self.rear_inner_displacement[index] = car_data_snippet.rear_inner_displacement
        self.front_outer_displacement[index] = car_data_snippet.front_outer_displacement
        self.rear_outer_displacement[index] = car_data_snippet.rear_outer_displacement

        # Angle of accel force of car
        self.theta_accel[index] = car_data_snippet.theta_accel

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
                           "max_RO_vector_mag": np.max(self.RO_vector_mag), "front_inner_displacement": np.max(self.front_inner_displacement),
                           "rear_inner_displacement": np.max(self.rear_inner_displacement), "front_outer_displacement": np.max(self.front_outer_displacement),
                           "rear_outer_displacement": np.max(self.rear_outer_displacement)}

        return max_values_dict

    def round_all_arrays(self, decimals=3):
        self.time_array = np.round(np.array(self.time_array), decimals=decimals)

        # Collect lateral and axial acceleration of car
        self.AX = np.round(np.array(self.AX), decimals=decimals)
        self.AY = np.round(np.array(self.AY), decimals=decimals)

        # Collect car body angle
        self.car_body_angle = np.round(np.array(self.car_body_angle), decimals=decimals)

        # lateral, axial, and vertical forces on tires
        self.FO_load_array = np.round(np.array(self.FO_load_array), decimals=decimals)
        self.FI_load_array = np.round(np.array(self.FI_load_array), decimals=decimals)
        self.RO_load_array = np.round(np.array(self.RO_load_array), decimals=decimals)
        self.RI_load_array = np.round(np.array(self.RI_load_array), decimals=decimals)
        self.FO_FY_array = np.round(np.array(self.FO_FY_array), decimals=decimals)
        self.FI_FY_array = np.round(np.array(self.FI_FY_array), decimals=decimals)
        self.RO_FY_array = np.round(np.array(self.RO_FY_array), decimals=decimals)
        self.RI_FY_array = np.round(np.array(self.RI_FY_array), decimals=decimals)
        self.FO_FX_array = np.round(np.array(self.FO_FX_array), decimals=decimals)
        self.FI_FX_array = np.round(np.array(self.FI_FX_array), decimals=decimals)
        self.RO_FX_array = np.round(np.array(self.RO_FX_array), decimals=decimals)
        self.RI_FX_array = np.round(np.array(self.RI_FX_array), decimals=decimals)

        # Vectors of forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.FI_vector = np.round(np.array(self.FI_vector), decimals=decimals)
        self.RI_vector = np.round(np.array(self.RI_vector), decimals=decimals)
        self.FO_vector = np.round(np.array(self.FO_vector), decimals=decimals)
        self.RO_vector = np.round(np.array(self.RO_vector), decimals=decimals)
        self.FI_vector_mag = np.round(np.array(self.FI_vector_mag), decimals=decimals)
        self.FO_vector_mag = np.round(np.array(self.FO_vector_mag), decimals=decimals)
        self.RI_vector_mag = np.round(np.array(self.RI_vector_mag), decimals=decimals)
        self.RO_vector_mag = np.round(np.array(self.RO_vector_mag), decimals=decimals)
        self.FI_vector_dir = np.round(np.array(self.FI_vector_dir), decimals=decimals)
        self.RI_vector_dir = np.round(np.array(self.RI_vector_dir), decimals=decimals)
        self.FO_vector_dir = np.round(np.array(self.FO_vector_dir), decimals=decimals)
        self.RO_vector_dir = np.round(np.array(self.RO_vector_dir), decimals=decimals)

        # lapsim_data_storage vertical displacement of wheels
        self.front_inner_displacement = np.round(np.array(self.front_inner_displacement), decimals=decimals)
        self.rear_inner_displacement = np.round(np.array(self.rear_inner_displacement), decimals=decimals)
        self.front_outer_displacement = np.round(np.array(self.front_outer_displacement), decimals=decimals)
        self.rear_outer_displacement = np.round(np.array(self.rear_outer_displacement), decimals=decimals)

        # Angle of accel force of car
        self.theta_accel = np.round(np.array(self.theta_accel), decimals=decimals)

    # Fill the theta_accel array.
    def make_force_thetas(self):
        for index, AX in enumerate(self.AX):
            self.theta_accel[index] = math.atan2(abs(self.AY[index]), AX) * 180/math.pi
        self.infect_force_theta()

    # Give force thetas a direction (+ = turning right, - = turning left)
    def infect_force_theta(self):
        for index, AY in enumerate(self.AY):
            self.theta_accel[index] = math.atan2(AY, self.AX[index]) * 180 / math.pi

    # Return a unit vector using the vector argument provided.
    def get_unit_vector(self, vector):
        return np.divide(vector, np.sqrt(np.sum(np.power(vector, 2))))

    # Get the magnitude of the argument vector provided.
    def get_magnitude(self, vector):
        return np.sqrt(np.sum(np.power(vector, 2)))


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
        dx = track / n

        print(f"nodes n: {n}")

        # nodespace
        nds = np.linspace(0, track, int(n + 1))

        # Determining maximum tangential velocity for every turn given maximum lateral acceleration; length = # of arcs in track
        self.t_vel = np.sqrt(max_corner * self.t_rad)

        # List showing radius at every node. Used to calculate maximum tangential acceleration
        self.nd_rad = np.zeros(int(n + 1))

        self.nturn_dirs = np.empty(int(n + 1), dtype=curve.Turn)

        # Initialize data collection
        self.lapsim_data_storage.initialize(n)

        # Each line sets the maximum velocity for each 
        self.arc_beginning_node = []  # Stores the beginning node
        for i in np.arange(len(self.t_len_tot)):
            start_index = int(np.ceil(np.sum(self.t_len_tot[0:i]) / dx)) # Get index from 0 to n
            end_index = int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / dx)) # Get index from 0 to n + 1

            self.nd_rad[start_index:end_index] = self.t_rad[i]
            self.nturn_dirs[start_index:end_index] = self.turn_dirs[i]

            self.arc_beginning_node.append(int(np.ceil(np.sum(self.t_len_tot[0:i]) / dx)))
        self.arc_beginning_node.append(n + 1)

        self.t_rad[-1] = self.t_rad[-2]

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n + 1))
        for i in np.arange(len(self.t_len_tot)):
            v2[int(np.ceil(np.sum(self.t_len_tot[0:i]) / dx)):int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / dx))] = \
                self.t_vel[i]
        v2[-1] = v2[-2]

        for i in np.arange(n, -1, -1):
            car_data_snippet = self.car.curve_brake(self.nd_rad[int(i)], v2[int(i)])
            a_tan = car_data_snippet.AX
            a_tan *= 32.17 * 12 # Convert to in/s^2

            potential_velocity = np.sqrt(v2[int(i)] ** 2 - 2 * a_tan * dx)
            if (potential_velocity < v2[int(i - 1)]) or (v2[int(i - 1)] == 0.):
                v2[int(i - 1)] = potential_velocity

            # Add directional AY. (- = turning left, + = turning right)
            if self.nturn_dirs[int(i)] == curve.Turn.LEFT:
                car_data_snippet.AY = -car_data_snippet.AY

            # Fill AX array with braking acceleration at first.
            self.lapsim_data_storage.append_data_arrays(car_data_snippet, int(i))

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(int(n + 1))

        for i in np.arange(len(self.t_len_tot)):
            v1[int(np.ceil(np.sum(self.t_len_tot[0:i]) / dx)):int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / dx))] = \
                self.t_vel[i]
        v1[0] = 0
        v1[-1] = v1[-2]

        gear = 0  # transmission gear
        shift_time = self.car.drivetrain.shift_time  # shifting time (seconds)
        shifting = False  # Set to true while shifting
        for i in np.arange(n):

            # checks if the car is braking by looking if v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i + 1)] <= v1[int(i)]:
                v1[int(i + 1)] = v2[int(i + 1)]
                gear = self.car.drivetrain.gear_vel[int(v1[int(i)] * 0.0568182 * 10)]  # changes to the optimal gear when braking
                shifting = False  # sets to False so the car doesn't shift when it stops braking

                a_tan = self.lapsim_data_storage.AX[int(i)]
                a_tan *= 32.17 * 12 # Convert to in/s^2

                # Make sure car does not go backwards when setting v2 for each index.
                if v2[int(i)] ** 2 + 2 * a_tan * dx >= 0:
                    v2[int(i + 1)] = np.sqrt(v2[int(i)] ** 2 + 2 * a_tan * dx)
                else:
                    v2[int(i + 1)] = v2[int(i)]

            else:
                car_data_snippet = None # Initialize car_data_snippet to None. This is filled with data later.
                # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
                if (gear >= self.car.drivetrain.gear_vel[int(v1[int(i)] * 0.0568182 * 10)]) and not shifting:
                    car_data_snippet = self.car.curve_accel(self.nd_rad[int(i)], v1[int(i)], gear)
                    a_tan = car_data_snippet.AX
                    a_tan *= 32.17 * 12 # convert to in/s^2
                    # if car_data_snippet.AX == 0:
                    #     print("Equals 0")
                else:
                    # Store data when the car is changing gears
                    car_data_snippet = self.car.accel_updated(
                        self.car.find_closest_radius_index(self.nd_rad[int(i)]), self.lapsim_data_storage.car_body_angle[int(i)-1],
                        v1[int(i)]**2 / self.nd_rad[int(i)] / 32.17 / 12, self.car.a_rr + self.car.curve_idle(v1[int(i)]), changing_gears=True)
                    # Handle shifting logic
                    shifting = True
                    a_tan = car_data_snippet.AX * 32.17 * 12 + self.car.curve_idle(v1[int(i)])  # While shifting, the car has negative acceleration because of rolling resistance
                    shift_time -= dx / v1[int(i)]
                    if shift_time <= 0:
                        gear += 1
                        shift_time = self.car.drivetrain.shift_time
                        shifting = False
                if (np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * dx) < v1[int(i + 1)]) or (v1[int(i + 1)] == 0.):
                    v1[int(i + 1)] = np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * dx)

                a_tan /= (32.17 * 12)  # convert to g's

                # Store data in lapsim_data_storage
                car_data_snippet.AX = a_tan
                AY = v1[int(i)]**2 / self.nd_rad[int(i)] / 32.17 / 12
                car_data_snippet.AY = -AY if self.nturn_dirs[int(i)] == curve.Turn.LEFT else AY
                self.lapsim_data_storage.append_data_arrays(car_data_snippet, int(i))

        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n + 1))
        for i in np.arange(int(n + 1)):
            if v1[i] < v2[i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(0, len(v2) - 1):
            # calculate time between nodes by averaging the velocities of the nodes at the start and end of the selected time frame
            t += dx / np.average([v3[i], v3[i + 1]])
            self.lapsim_data_storage.time_array.append(t)
        print(f"Time: {t} seconds")

        self.lapsim_data_storage.make_force_thetas()
        self.lapsim_data_storage.round_all_arrays(decimals=3)

        self.dx = dx
        self.n = n
        self.nds = nds
        self.v3 = v3
        self.v2 = v2
        self.v1 = v1
        self.t = t

        # for i in range(len(self.lapsim_data_storage.AX)):
        #     print(f"{i}: using car angle {self.lapsim_data_storage.car_body_angle[i]}, radius {self.nd_rad[i]} -- AX: {self.lapsim_data_storage.AX[i]}, AY: {self.lapsim_data_storage.AY[i]}")

        # print("AX:")
        # for i in range(len(self.lapsim_data_storage.AX)):
        #     print(f"{self.lapsim_data_storage.AX[i]}")
        #
        # print("AY:\n\n\n\n\n\n")
        # for i in range(len(self.lapsim_data_storage.AY)):
        #     print(f"{self.lapsim_data_storage.AY[i]}")

        # for i in range(len(self.lapsim_data_storage.AX)):
        #     print(f"{i}: for AX {self.lapsim_data_storage.AX[i]}, AY {self.lapsim_data_storage.AY[i]}: {self.lapsim_data_storage.theta_accel[i]}")

        # plt.plot(self.nds, self.W_out_f_array)
        # plt.show()

        # Print values for lateral and axial acceleration:
        # for index, i in enumerate(self.AY):
        #     print(i)

        # print("Axial accel (g):")
        # for i in self.AX:
        #     print(i)

        return nds / 12, v1 / 17.6, t
