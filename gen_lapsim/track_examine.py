import tkinter

import numpy as np
import pickle

from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gen_lapsim.spline_track import track

class Get_Straights:
    def parse_text_to_track_pkl(self, txt_path):
        """
        Parses data from a .rtf text file to create a track object in pickle format.

        :param txt_path: Path to the input text file containing track data.
        :type txt_path: str
        :param pkl_path: Path where the pickle file will be saved.
        :type pkl_path: str
        :param is_autocross: A flag indicating whether the track is for autocross. If True,
                             a certain number of nodes will be processed. Otherwise, the function
                             will assume that the track is for endurance and generate a certain
                             number of nodes for that track.
        :type is_autocross: bool
        :return: None
        """
        points_arr = [np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType())]

        arr_done_index = 0

        with open(txt_path, "r") as f:
            content = f.read()
        curr_num = ""
        writing = False
        for char in content:
            if char == '[':
                writing = True
            elif char == ']' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
                arr_done_index += 1
                writing = False
            elif char == ',' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
            elif char != " " and writing:
                curr_num += char

        self.points_x = points_arr[0].astype(float)
        self.points_y = points_arr[1].astype(float)
        self.points_x2 = points_arr[2].astype(float)
        self.points_y2 = points_arr[3].astype(float)

    def get_lens(self, min_length=8, min_radius=900):
        trk = track(self.points_x, self.points_y, self.points_x2, self.points_y2, None)
        trk.adjust_track([40, 30, 30, 80],[100, 30, 10, 5])
        self.arcs = trk.arcs

        self.len = []
        self.rad = []
        for i in self.arcs:
            new_len, new_rad = i.interpolate()
            self.len += new_len
            self.rad += new_rad

        self.index_arr, total_index = [], 0
        self.min_radius = 900
        self.min_length = int(min_length * self.arcs[0].elem / 10)
        streak = 0
        lengths, length_index = [], -1
        one_length = False
        for index, rad in enumerate(self.rad):
            if rad > self.min_radius:
                if not one_length:
                    # Remove the last array of lengths if it was not large enough.
                    if streak < self.min_length and lengths:
                        lengths.pop()
                        for _ in range(streak):
                            self.index_arr.pop()
                        length_index -= 1
                    else:
                        print(streak)

                    length_index += 1
                    lengths.append([])
                    lengths[length_index].append(self.len[index])
                    one_length = True
                    streak = 1
                else:
                    lengths[length_index].append(self.len[index])
                    streak+=1

                # Deal with total index stuff
                self.index_arr.append(total_index)

            else:
                one_length = False

            total_index += 1

        print(len(lengths))
        print(self.index_arr)

        sum_lens = []
        for i, length in enumerate(lengths):
            if len(length) >= self.min_length:
                print(length)
                sum_lens.append(np.sum(length))

        print(f"Average length: {np.average(sum_lens)/12} feet")

    def display(self):
        track_root = tkinter.Tk() # For window of graph and viewable values
        track_root.title("Graph")
        track_root.config(bg="gray13")

        track_fig = Figure(figsize=(7, 8), dpi=100) # Adjust figsize and dpi as needed
        track_subplot = track_fig.add_subplot(111) # Add a track_subplot to the figure
        track_canvas = FigureCanvasTkAgg(track_fig, master=track_root)

        track_subplot.axis('equal')
        track_subplot.grid()
        toolbar = NavigationToolbar2Tk(track_canvas, track_root, pack_toolbar=False)
        toolbar.grid(row=1, column=1, rowspan=2, sticky="N")
        toolbar.update()
        track_canvas.draw()
        track_canvas.get_tk_widget().grid(row=1, column=1, rowspan=2)

        total_index = 0
        for arc in self.arcs:
            for elem in range(arc.elem):
                if total_index in self.index_arr:
                    track_subplot.plot(arc.x[elem], arc.y[elem], marker="o", color="green")
                else:
                    track_subplot.plot(arc.x[elem], arc.y[elem],marker="o", color="black")
                total_index += 1

        track_root.mainloop()

    def run(self):
        self.parse_text_to_track_pkl("/Users/jacobmckee/Documents/Wazzu_Racing/Vehicle_Dynamics/Repos/LapSim/config_data/track_points/Points for Endurance.rtf")
        self.get_lens()
        self.display()


getL = Get_Straights()
getL.run()