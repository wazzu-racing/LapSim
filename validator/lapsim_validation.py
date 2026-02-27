import tkinter
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gen_lapsim.lapsim import LapSimData


class Validation_Track():

    def __init__(self, segments, car, sim_per_arc=1):

        self.car = car

        self.segments = segments
        self.segment_data = []
        self.sims_per_arc = sim_per_arc

        print(f"[Created validation track]")

    def run(self):
        self.segment_data = []
        for index, segment in enumerate(self.segments):
            self.segment_data.append(self.run_segment(segment, self.car))
        return self.segment_data

    def run_segment(self, segment, car):
        v3 = [] # velocity (in/s)
        t = [] # time (sec)
        lens = []
        rads = []
        for index, arc in enumerate(segment.arcs):
            for sim in range(self.sims_per_arc):
                lens.append(arc.length / self.sims_per_arc)
                rads.append(arc.radius)
            # print(f"\n------ Arc {index} ------")
            # print(f"length: {lens[index]}")
            # print(f"radius: {rads[index]}")

        ##############################################
        #                 LAPSIM CODE                #
        ##############################################

        lapsim_data_storage = LapSimData()
        lapsim_data_storage.initialize(len(lens))

        car_data_snippet = car.Car_Data_Snippet()

        # Finding total length of track
        track = np.sum(lens)

        max_corner = self.car.max_corner * 32.17 * 12 # to in/s^2

        n = len(segment.arcs * self.sims_per_arc)

        rads.append(rads[-1])
        lens.append(lens[-1])

        t_vels = np.sqrt(max_corner * np.array(rads))

        v2 = np.zeros(int(n + 1))
        for i in np.arange(n):
            v2[int(np.ceil(np.sum(lens[0:i]) / lens[int(i)])):int(np.ceil(np.sum(lens[0:i + 1]) / lens[int(i)]))] = t_vels[i]
        v2[-1] = v2[-2]

        for i in np.arange(n, -1, -1):
            car_data_snippet = self.car.curve_brake(rads[int(i)], v2[int(i)])
            a_tan = car_data_snippet.AX
            a_tan *= 32.17 * 12 # Convert to in/s^2

            potential_velocity = np.sqrt(v2[int(i)] ** 2 - 2 * a_tan * lens[int(i)])
            if (potential_velocity < v2[int(i - 1)]) or (v2[int(i - 1)] == 0.):
                v2[int(i - 1)] = potential_velocity

            # Fill AX array with braking acceleration at first.
            lapsim_data_storage.append_data_arrays(car_data_snippet, int(i))

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(n + 1)

        for i in np.arange(len(lens)):
            v1[i] = t_vels[i]
        v1[0] = segment.starting_velocity
        v1[-1] = v1[-2]

        # print(v1)

        for i in np.arange(n):
            # checks if the car is braking by looking if v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i + 1)] <= v1[int(i)]:
                v1[int(i + 1)] = v2[int(i + 1)]

                a_tan = lapsim_data_storage.AX[int(i)]
                a_tan *= 32.17 * 12 # Convert to in/s^2

                # Make sure car does not go backwards when setting v2 for each index.
                if v2[int(i)] ** 2 + 2 * a_tan * lens[int(i)] >= 0:
                    v2[int(i + 1)] = np.sqrt(v2[int(i)] ** 2 + 2 * a_tan * lens[int(i)])
                else:
                    v2[int(i + 1)] = v2[int(i)]

            else:
                car_data_snippet = None # Initialize car_data_snippet to None. This is filled with data later.
                car_data_snippet = self.car.curve_accel(rads[int(i)], v1[int(i)], 'optimal')
                a_tan = car_data_snippet.AX
                a_tan *= 32.17 * 12 # convert to in/s^2
                if (np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * lens[int(i)]) < v1[int(i + 1)]) or (v1[int(i + 1)] == 0.):
                    v1[int(i + 1)] = np.sqrt(v1[int(i)] ** 2 + 2 * a_tan * lens[int(i)])

                a_tan /= (32.17 * 12)  # convert to g's

                # Store data in lapsim_data_storage
                car_data_snippet.AX = a_tan
                AY = v1[int(i)]**2 / rads[int(i)] / 32.17 / 12
                lapsim_data_storage.append_data_arrays(car_data_snippet, int(i))

                # print(f"a_tan: {a_tan * 32.17 * 12}")

            lapsim_data_storage.total_distance[int(i)] = lens[int(i)] * i

        # print(v2)

        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        # print(f"\nV3:")
        v3 = np.zeros(int(n + 1))
        for i in np.arange(int(n + 1)):
            if v1[i] < v2[i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])
            # print(f"{v3[int(i)]} in/s")

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(0, len(v2) - 1):
            # calculate time between nodes by averaging the velocities of the nodes at the start and end of the selected time frame
            t += lens[int(i)] / np.average([v3[i], v3[i + 1]])
            lapsim_data_storage.time_array.append(t)
        # print(f"Time: {t} seconds")

        lapsim_data_storage.infect_force_thetas()
        lapsim_data_storage.round_all_arrays(decimals=3)

        # print("v2")
        # for i in np.arange(0, len(v2) - 1):
        #     print(v2[int(i)])
        # print("v1")
        # for i in np.arange(0, len(v1) - 1):
        #     print(v1[int(i)])

        return lapsim_data_storage

        lapsim_data_storage.infect_force_thetas()
        lapsim_data_storage.round_all_arrays(decimals=3)

    def plt_sim(self, car, nodes = 5000, start = 0, end = 0):
        # TODO
        pass
        # self.car = car
        #
        # # setup for position vs velocity plot
        # self.run_sim(car, nodes, start, end)
        # plt.title('Simulation Results:')
        # plt.xlabel('Position (ft)')
        # plt.ylabel('Vehicle Speed (mph)')
        # plt.grid()
        # plt.plot(self.nodes, self.v3)
        # plt.axis('equal')
        # plt.show()

    def plt_track(self, arcs):
        root = tkinter.Tk()
        root.title("Track")

        fig = plt.Figure(figsize=(10, 10))
        ax = fig.add_subplot(111)

        # Plot data
        for index in range(len(arcs)):
            if arcs[index].bad_data:
                ax.plot(self.arcs[index].x, self.arcs[index].y, color='red')
            else:
                ax.plot(self.arcs[index].x, self.arcs[index].y, color='green')
        ax.plot(self.arcs[-1].x, self.arcs[-1].y, color='red') # Last arc is assumed to be bad data

        canvas = FigureCanvasTkAgg(fig, root)
        toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=True)
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        toolbar.update()
        canvas.draw()

        root.mainloop()