import numpy as np
import copy


class LapSimData:
    def __init__(self):
        # Array for time t
        self.time_array = [0]
        # Arrays for lateral and axial acceleration of car
        self.AY = []
        self.AX = []
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
        self.D_1_dis = []
        self.D_2_dis = []
        self.D_3_dis = []
        self.D_4_dis = []
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
        self.D_1_dis = np.zeros(int(n + 1))
        self.D_2_dis = np.zeros(int(n + 1))
        self.D_3_dis = np.zeros(int(n + 1))
        self.D_4_dis = np.zeros(int(n + 1))
        # theta of force on car
        self.theta_accel = np.zeros(int(n + 1))

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

    # Return a unit vector using the vector argument provided.
    def get_unit_vector(self, vector):
        return np.divide(vector, np.sqrt(np.sum(np.power(vector, 2))))

    # Get the magnitude of the argument vector provided.
    def get_magnitude(self, vector):
        return np.sqrt(np.sum(np.power(vector, 2)))


class four_wheel:

    def __init__(self, t_len_tot, t_rad, car, n):
        # print(min(t_rad))
        x = np.sort(copy.deepcopy(t_rad))
        y = np.linspace(len(x), 0, len(x))
        self.t_len_tot = np.array(t_len_tot)
        self.t_rad = np.array(t_rad)
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

        # Initialize data collection
        self.lapsim_data_storage.initialize(n)

        # Each line sets the maximum velocity for each 
        self.arc_beginning_node = []  # Stores the beginning node
        for i in np.arange(len(self.t_len_tot)):
            self.nd_rad[
            int(np.ceil(np.sum(self.t_len_tot[0:i]) / dx)):int(np.ceil(np.sum(self.t_len_tot[0:i + 1]) / dx))] = \
                self.t_rad[i]
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
            a_tan = self.car.curve_brake(v2[int(i)], self.nd_rad[int(i)])
            if (np.sqrt(v2[int(i)] ** 2 - 2 * a_tan * dx) < v2[int(i - 1)]) or (v2[int(i - 1)] == 0.):
                v2[int(i - 1)] = np.sqrt(v2[int(i)] ** 2 - 2 * a_tan * dx)
            a_tan /= (32.17 * 12)
            self.lapsim_data_storage.AX[int(i)] = a_tan

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

            # checks if car is braking by looking of v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i + 1)] <= v1[int(i)]:
                v1[int(i + 1)] = v2[int(i + 1)]
                gear = self.car.drivetrain.gear_vel[
                    int(v1[int(i)] * 0.0568182 * 10)]  # changes to the optimal gear when braking
                shifting = False  # sets to False so the car doesn't shift when it stops braking

                a_tan = self.car.curve_brake(v2[int(i)], self.nd_rad[int(i)])  # in/s^2

                # Make sure car does not go backwards when setting v2 for each index.
                if v2[int(i)] ** 2 + 2 * a_tan * dx >= 0:
                    v2[int(i + 1)] = np.sqrt(v2[int(i)] ** 2 + 2 * a_tan * dx)
                else:
                    v2[int(i + 1)] = v2[int(i)]

                a_tan /= (32.17 * 12)  # in g's
                a_lat = v2[int(i)] ** 2 / self.nd_rad[int(i)] / 32.2 / 12  # in g's
                self.car.accel(a_lat, a_tan)
                self.append_data_arrays(a_lat, a_tan, int(i))

            else:
                # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
                if (gear >= self.car.drivetrain.gear_vel[int(v1[int(i)] * 0.0568182 * 10)]) and not shifting:
                    a_tan = self.car.curve_accel(v1[int(i)], self.nd_rad[int(i)], gear)  # in in/s^2
                else:
                    shifting = True
                    a_tan = self.car.a_rr  # While shifting, the car has negative acceleration because of rolling resistance
                    shift_time -= dx / v1[int(i)]
                    if shift_time <= 0:
                        gear += 1
                        shift_time = self.car.drivetrain.shift_time
                        shifting = False
                if (np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * dx) < v1[int(i + 1)]) or (v1[int(i + 1)] == 0.):
                    v1[int(i + 1)] = np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * dx)
                    a_tan /= (32.17 * 12)  # in g's
                    a_lat = v1[int(i)] ** 2 / self.nd_rad[int(i)] / 32.2 / 12  # in g's
                    # print(f"Node {i}: axial accel: {a_tan}, lateral accel: {a_lat}")

                    # Calculate and record data
                    self.car.accel(a_lat, a_tan)
                    self.append_data_arrays(a_lat, a_tan, int(i))
                    # print(f"Node {i}: axial accel: {a_tan}, lateral accel: {a_lat}")

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

        self.dx = dx
        self.n = n
        self.nds = nds
        self.v3 = v3
        self.v2 = v2
        self.v1 = v1
        self.t = t

        # plt.plot(self.nds, self.W_out_f_array)
        # plt.show()

        # Print values for lateral and axial acceleration:
        # for index, i in enumerate(self.AY):
        #     print(i)

        # print("Axial accel (g):")
        # for i in self.AX:
        #     print(i)

        return nds / 12, v1 / 17.6, t

    # Append a data point to all arrays.
    def append_data_arrays(self, lat, axi, index):
        # Collect lateral and axial acceleration of car
        self.lapsim_data_storage.AX[index] = axi
        self.lapsim_data_storage.AY[index] = lat

        # lateral, axial, and vertical forces on tires
        self.lapsim_data_storage.FO_load_array[index] = self.car.W_out_f
        self.lapsim_data_storage.FI_load_array[index] = self.car.W_in_f
        self.lapsim_data_storage.RO_load_array[index] = self.car.W_out_r
        self.lapsim_data_storage.RI_load_array[index] = self.car.W_in_r
        self.lapsim_data_storage.FO_FY_array[index] = self.car.FY_out_f
        self.lapsim_data_storage.FI_FY_array[index] = self.car.FY_in_f
        self.lapsim_data_storage.RO_FY_array[index] = self.car.FY_out_r
        self.lapsim_data_storage.RI_FY_array[index] = self.car.FY_in_r
        self.lapsim_data_storage.FO_FX_array[index] = self.car.FX_out_f
        self.lapsim_data_storage.FI_FX_array[index] = self.car.FX_in_f
        self.lapsim_data_storage.RO_FX_array[index] = self.car.FX_out_r
        self.lapsim_data_storage.RI_FX_array[index] = self.car.FX_in_r

        # Vectors of forces on tires, arr[0] = axial, arr[1] = lateral, arr[2] = vertical
        self.lapsim_data_storage.FI_vector[index] = np.array([self.car.FX_in_f, self.car.FY_in_f, self.car.W_in_f])
        self.lapsim_data_storage.RI_vector[index] = np.array([self.car.FX_in_r, self.car.FY_in_r, self.car.W_in_r])
        self.lapsim_data_storage.FO_vector[index] = np.array([self.car.FX_out_f, self.car.FY_out_f, self.car.W_out_f])
        self.lapsim_data_storage.RO_vector[index] = np.array([self.car.FX_out_r, self.car.FY_out_r, self.car.W_out_r])
        self.lapsim_data_storage.FI_vector_mag[index] = self.lapsim_data_storage.get_magnitude(
            self.lapsim_data_storage.FI_vector[index])
        self.lapsim_data_storage.FO_vector_mag[index] = self.lapsim_data_storage.get_magnitude(
            self.lapsim_data_storage.FO_vector[index])
        self.lapsim_data_storage.RI_vector_mag[index] = self.lapsim_data_storage.get_magnitude(
            self.lapsim_data_storage.RI_vector[index])
        self.lapsim_data_storage.RO_vector_mag[index] = self.lapsim_data_storage.get_magnitude(
            self.lapsim_data_storage.RO_vector[index])
        self.lapsim_data_storage.FI_vector_dir[index] = np.array(
            self.lapsim_data_storage.get_unit_vector(self.lapsim_data_storage.FI_vector[index]))
        self.lapsim_data_storage.RI_vector_dir[index] = np.array(
            self.lapsim_data_storage.get_unit_vector(self.lapsim_data_storage.RI_vector[index]))
        self.lapsim_data_storage.FO_vector_dir[index] = np.array(
            self.lapsim_data_storage.get_unit_vector(self.lapsim_data_storage.FO_vector[index]))
        self.lapsim_data_storage.RO_vector_dir[index] = np.array(
            self.lapsim_data_storage.get_unit_vector(self.lapsim_data_storage.RO_vector[index]))

        # lapsim_data_storage vertical displacement of wheels
        self.lapsim_data_storage.D_1_dis[index] = self.car.D_1
        self.lapsim_data_storage.D_2_dis[index] = self.car.D_2
        self.lapsim_data_storage.D_3_dis[index] = self.car.D_3
        self.lapsim_data_storage.D_4_dis[index] = self.car.D_4

        # Angle of accel force of car
        self.lapsim_data_storage.theta_accel[index] = self.car.theta_accel
