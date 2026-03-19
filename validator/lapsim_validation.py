import tkinter
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

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

        t_vels = np.sqrt(car.max_corner * np.array(rads))
        # print(t_vels)

        # Finding total length of track
        track = np.sum(lens)

        max_corner = self.car.max_corner * 32.17 * 12 # to in/s^2

        n = len(segment.arcs * self.sims_per_arc)

        rads.append(rads[-1])
        lens.append(lens[-1])

        t_vels = np.sqrt(max_corner * np.array(rads))

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n + 1))
        for i in np.arange(len(lens)):
            v2[int(np.ceil(np.sum(lens[0:i]) / lens[int(i)])):int(np.ceil(np.sum(lens[0:i + 1]) / lens[int(i)]))] = \
                t_vels[i]
        v2[-1] = v2[-2]

        for i in np.arange(n, -1, -1):
            snippet = self.car.curve_brake(v2[int(i)], rads[int(i)])
            snippet.AX *= 32.17 * 12
            if (np.sqrt(v2[int(i)] ** 2 - 2 * snippet.AX * lens[int(i)]) < v2[int(i - 1)]) or (v2[int(i - 1)] == 0.):
                v2[int(i - 1)] = np.sqrt(v2[int(i)] ** 2 - 2 * snippet.AX * lens[int(i)])
            snippet.AX /= (32.17 * 12)
            lapsim_data_storage.AX[int(i)] = snippet.AX
        # print(v2)

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(int(n + 1))

        for i in np.arange(len(lens)):
            v1[i] = t_vels[i]
        v1[0] = segment.starting_velocity
        v1[-1] = v1[-2]

        for i in np.arange(n):

            # checks if car is braking by looking of v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i + 1)] <= v1[int(i)]:
                v1[int(i + 1)] = v2[int(i + 1)]

                snippet = self.car.curve_brake(v2[int(i)], rads[int(i)])  # in/s^2
                snippet.AX *= 32.17 * 12

                # Make sure car does not go backwards when setting v2 for each index.
                if v2[int(i)] ** 2 + 2 * snippet.AX * lens[int(i)] >= 0:
                    v2[int(i + 1)] = np.sqrt(v2[int(i)] ** 2 + 2 * snippet.AX * lens[int(i)])
                else:
                    v2[int(i + 1)] = v2[int(i)]

                snippet.AX /= (32.17 * 12)  # in g's
                lapsim_data_storage.append_data_arrays(snippet, int(i)) # Positive AY is turning right, negative AY is turning left.

            else:
                # Calculate axial acceleration
                snippet = self.car.curve_accel(v1[int(i)], rads[int(i)]) # AX in g's

                # Figure out if the maximum possible acceleration currently is not enough to satisfy the next velocity.
                # If it does not satisfy the next velocity, then replace that next velocity with the velocity produced
                # from the current axial acceleration.
                snippet.AX *= 32.17 * 12 # convert to in/s^2
                if (np.sqrt(v1[int(i)] ** 2 + 2 * snippet.AX * lens[i]) < v1[int(i + 1)]) or (v1[int(i + 1)] == 0.):
                    v1[int(i + 1)] = np.sqrt(v1[int(i)] ** 2 + 2 * snippet.AX * lens[i])
                snippet.AX /= (32.17 * 12) # convert back to g's

                lapsim_data_storage.append_data_arrays(snippet, int(i)) # Positive AY is turning right, negative AY is turning left.

        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n + 1))
        for i in np.arange(int(n + 1)):
            if v1[i] < v2[i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])
            lapsim_data_storage.velocity[i] = v3[i]
        # print(v3)

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(0, len(v2) - 1):
            t += lens[int(i)] / np.average([v3[i], v3[i + 1]])
            lapsim_data_storage.time_array.append(t)

        # print("NEW SEGMENT")
        # print(f"starting velocity: {segment.starting_velocity} in/s")
        # for index, vel in enumerate(lapsim_data_storage.velocity):
        #     print(f"{lapsim_data_storage.AX[index]} g's at {vel} in/s")

        return lapsim_data_storage

        lapsim_data_storage.infect_force_thetas()
        lapsim_data_storage.round_all_arrays(decimals=3)

    def plt_sim(self):
        tk = tkinter.Tk()
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        count = 0
        for data in self.segment_data:
            ax.plot(np.linspace(count, len(data.velocity)+count, len(data.velocity))+count, data.velocity)
            count += len(data.velocity)
        tk.mainloop()

    def plt_track(self, arcs):
        # Does not work; need to fix
        pass
        # root = tkinter.Tk()
        # root.title("Track")
        #
        # fig = plt.Figure(figsize=(10, 10))
        # ax = fig.add_subplot(111)
        #
        # # Plot data
        # for index in range(len(arcs)):
        #     if arcs[index].bad_data:
        #         ax.plot(self.arcs[index].x, self.arcs[index].y, color='red')
        #     else:
        #         ax.plot(self.arcs[index].x, self.arcs[index].y, color='green')
        # ax.plot(self.arcs[-1].x, self.arcs[-1].y, color='red') # Last arc is assumed to be bad data
        #
        # canvas = FigureCanvasTkAgg(fig, root)
        # toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=True)
        # canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        # toolbar.update()
        # canvas.draw()
        #
        # root.mainloop()