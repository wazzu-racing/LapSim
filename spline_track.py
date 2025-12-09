import pickle

import numpy as np
import math
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import lapsim
import tkinter
import csv

from files import get_file_from_user
from lapsim import lapsim_data_storage

# Create UI global vars
track_root = None
track_fig = None
track_subplot = None
track_canvas = None
data_bools = [True, False, False, False, False]
data_label = None

x_array = []
y_array = []

class LapSimUI:

    # MAKE AN INIT FUNCTION FOR THIS CONSTRUCTOR TO CLEAR FIGURE WHEN CLOSING WINDOW
    def __init__(self):
        global track_root, track_fig, track_subplot, track_canvas, data_bools

        track_root = tkinter.Tk() # For window of graph and viewable values
        track_root.title("Graph")

        track_fig = Figure(figsize=(5, 4), dpi=100) # Adjust figsize and dpi as needed
        track_subplot = track_fig.add_subplot(111) # Add a track_subplot to the figure
        track_canvas = FigureCanvasTkAgg(track_fig, master=track_root)

        # Hide this window until ready to show
        track_root.withdraw()

        # Create a toplevel window for CSV download and graph download
        self.init_CSV_window()

        # initialize dir that file dialogs open to
        self.initial_dir = ""

        # Only allow the user to hide the LapSim UI and CSV windows, not close it
        track_root.protocol("WM_DELETE_WINDOW", self.close_LapsimUI_window)
        self.csv_window.protocol("WM_DELETE_WINDOW", self.close_CSV_window)

    def init_CSV_window(self):
        # Create a toplevel window for CSV download
        self.csv_window = tkinter.Toplevel()
        self.csv_window.title("Download CSV")

        self.csv_window.withdraw()

    def close_LapsimUI_window(self):
        global track_root, track_fig, track_subplot, track_canvas, x_array, y_array
        track_subplot.clear()
        track_root.withdraw()
        x_array = []
        y_array = []

    def close_CSV_window(self):
        self.csv_window.withdraw()

    def open_csv_window(self):
        # code copied from load_lapsim function to create data selection menu
        data_bools = [True, True, False, False, False, False, False]
        data_options = ["Time", "Acceleration", "Vertical Forces", "Lateral Forces", "Axial Forces", "Wheel Displacement", "Theta of Force on Car"]
        menu_button = tkinter.Menubutton(self.csv_window, text="Choose Data to Save", font=("Ariel", 12))

        # switch data_bools to tkinter BooleanVars
        for option in data_options:
            boolean = tkinter.BooleanVar()
            boolean.set(data_bools[data_options.index(option)])
            data_bools[data_options.index(option)] = boolean

        # Create checkbuttons and labels for each data option
        time_check = tkinter.Checkbutton(self.csv_window, text = data_options[0], variable = data_bools[0])
        accel_check = tkinter.Checkbutton(self.csv_window, text=data_options[1], variable=data_bools[1])
        vertical_force_check = tkinter.Checkbutton(self.csv_window, text=data_options[2], variable=data_bools[2])
        lateral_force_check = tkinter.Checkbutton(self.csv_window, text=data_options[3], variable=data_bools[3])
        axial_force_check = tkinter.Checkbutton(self.csv_window, text=data_options[4], variable=data_bools[4])
        wheel_displacement_check = tkinter.Checkbutton(self.csv_window, text=data_options[5], variable=data_bools[5])
        theta_force_check = tkinter.Checkbutton(self.csv_window, text=data_options[6], variable=data_bools[6])

        # Label to tell users forces are on tires
        forces_label = tkinter.Label(self.csv_window, text="*All forces are on tires.", font=("Ariel", 12), fg="white")

        # Place checkbuttons and labels in grid
        time_check.grid(row=1, column =1, padx=10, pady=5, sticky="W")
        accel_check.grid(row=2, column=1, padx=10, pady=5, sticky="W")
        vertical_force_check.grid(row=3, column=1, padx=10, pady=5, sticky="W")
        lateral_force_check.grid(row=4, column=1, padx=10, pady=5, sticky="W")
        axial_force_check.grid(row=5, column=1, padx=10, pady=5, sticky="W")
        wheel_displacement_check.grid(row=6, column=1, padx=10, pady=5, sticky="W")
        theta_force_check.grid(row=7, column=1, padx=10, pady=5, sticky="W")
        forces_label.grid(row=8, column=1, padx=10, pady=5, sticky="W")

        download_csv_button = tkinter.Button(self.csv_window, text="Download CSV", font=("Ariel", 12), bg="white", fg="black", command=lambda: self.download_csv(data_bools))
        download_csv_button.grid(row=9, column=1, padx=10, pady=10)

        self.csv_window.grid_rowconfigure(0, weight=1)
        self.csv_window.grid_rowconfigure(1, weight=0)
        self.csv_window.grid_rowconfigure(2, weight=0)
        self.csv_window.grid_rowconfigure(3, weight=0)
        self.csv_window.grid_rowconfigure(4, weight=0)
        self.csv_window.grid_rowconfigure(5, weight=0)
        self.csv_window.grid_rowconfigure(6, weight=0)
        self.csv_window.grid_rowconfigure(7, weight=0)
        self.csv_window.grid_rowconfigure(8, weight=0)
        self.csv_window.grid_rowconfigure(9, weight=0)
        self.csv_window.grid_rowconfigure(10, weight=1)
        self.csv_window.grid_columnconfigure(0, weight=1)
        self.csv_window.grid_columnconfigure(1, weight=0)
        self.csv_window.grid_columnconfigure(2, weight=1)

        self.csv_window.deiconify()

    def download_csv(self, arr_bool):
        print("Download CSV")

        user_file_loc = get_file_from_user(self, file_types=[("CSV File", "*.csv")], default_exension="*.csv")

        with(open(user_file_loc, "w", newline='')) as csv_file:
            writer = csv.writer(csv_file, dialect='unix')
            header_array = []
            writing_data = []
            for i in range(len(arr_bool)): # Initialize writing_data with empty lists for each selected data type
                writing_data.append([])
            for i in range(len(arr_bool)):
                if arr_bool[i].get():
                    match i:
                        case 0:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.time_array):
                                array = []
                                array.append(str(lapsim_data_storage.time_array[index]))
                                array_2.append(array)
                            writing_data[0] = array_2
                            header_array.extend(["Time"])
                        case 1:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.AX):
                                array = []
                                array.append(str(lapsim_data_storage.AX[index]))
                                array.append(str(lapsim_data_storage.AY[index]))
                                array_2.append(array)
                            writing_data[1] = array_2
                            header_array.extend(["Axial Acceleration", "Lateral Acceleration"])
                        case 2:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.W_out_f_array):
                                array = []
                                array.append(str(lapsim_data_storage.W_out_f_array[index]))
                                array.append(str(lapsim_data_storage.W_in_f_array[index]))
                                array.append(str(lapsim_data_storage.W_out_r_array[index]))
                                array.append(str(lapsim_data_storage.W_in_r_array[index]))
                                array_2.append(array)
                            writing_data[2] = array_2
                            header_array.extend(["Front outer vertical force", "Front inner vertical force", "Rear outer vertical force", "Rear inner vertical force"])
                        case 3:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.FY_out_f_array):
                                array = []
                                array.append(str(lapsim_data_storage.FY_out_f_array[index]))
                                array.append(str(lapsim_data_storage.FY_in_f_array[index]))
                                array.append(str(lapsim_data_storage.FY_out_r_array[index]))
                                array.append(str(lapsim_data_storage.FY_in_r_array[index]))
                                array_2.append(array)
                            writing_data[3] = array_2
                            header_array.extend(["Front outer Lateral force", "Front inner Lateral force", "Rear outer Lateral force", "Rear inner Lateral force"])
                        case 4:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.FX_out_f_array):
                                array = []
                                array.append(str(lapsim_data_storage.FX_out_f_array[index]))
                                array.append(str(lapsim_data_storage.FX_in_f_array[index]))
                                array.append(str(lapsim_data_storage.FX_out_r_array[index]))
                                array.append(str(lapsim_data_storage.FX_in_r_array[index]))
                                array_2.append(array)
                            writing_data[4] = array_2
                            header_array.extend(["Front outer Axial force", "Front inner Axial force", "Rear outer Axial force", "Rear inner Axial force"])
                        case 5:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.D_1_dis):
                                array = []
                                array.append(str(lapsim_data_storage.D_2_dis[index]))
                                array.append(str(lapsim_data_storage.D_1_dis[index]))
                                array.append(str(lapsim_data_storage.D_4_dis[index]))
                                array.append(str(lapsim_data_storage.D_3_dis[index]))
                                array_2.append(array)
                            writing_data[5] = array_2
                            header_array.extend(["Front outer vertical displacement", "Front inner vertical displacement", "Rear outer vertical displacement", "Rear inner vertical displacement"])
                        case 6:
                            array_2 = []
                            for index, i in enumerate(lapsim_data_storage.theta_accel):
                                array = []
                                array.append(str(lapsim_data_storage.theta_accel[index]))
                                array_2.append(array)
                            writing_data[6] = array_2
                            header_array.extend(["Theta of Force on Car"])

            writer.writerow(header_array)
            master_array = []
            # Loop through each value of every data point
            for index in range(len(lapsim_data_storage.AX)):
                # create array which contains every data point for one specific node (one row) and add to master array
                array = []
                for data_section in writing_data:
                    if data_section:
                        array.extend(data_section[index])
                # master array, where each index is a row of data points
                master_array.append(array)
            # write all rows to csv file
            writer.writerows(master_array)

    def load_lapsim(self, save_file_func=None):
        global track_root, track_subplot, track_canvas, data_bools, data_label

        track_root.deiconify() # Show the window

        data_bools = [True, True, False, False, False, False, False]

        data_options = ["Time", "Acceleration", "Vertical Forces", "Lateral Forces", "Axial Forces", "Wheel Displacement", "Theta of Force on Car"]

        menu_button = tkinter.Menubutton(track_root, text="Choose visible data", font=("Ariel", 12))

        menu_button.menu = tkinter.Menu(menu_button, tearoff=0)
        menu_button["menu"] = menu_button.menu

        for option in data_options:
            boolean = tkinter.BooleanVar()
            boolean.set(data_bools[data_options.index(option)])
            data_bools[data_options.index(option)] = boolean
            menu_button.menu.add_checkbutton(label=option, variable=boolean)
        menu_button.grid(row=1, column=2, padx=0, pady=0)

        data_label_frame = tkinter.Frame(track_root, width=400, height=500, bg='white')
        data_label_frame.grid(row=2, column=2, padx=0, pady=0)
        data_label_frame.pack_propagate(False)

        data_label = tkinter.Label(data_label_frame, text="", font=("Ariel", 12), bg="white", fg="black")
        data_label.grid(row=0, column=0, padx=0, pady=0, sticky="N")

        download_csv_button = tkinter.Button(data_label_frame, text="Download CSV", font=("Ariel", 12), bg="white", fg="black", command=self.open_csv_window)
        download_csv_button.grid(row=1, column=0, padx=0, pady=0)

        if save_file_func is not None:
            track_root.bind("<s>", lambda event: save_file_func())

    def load_track(self):
        global track_subplot, track_canvas, track_root

        track_subplot.axis('equal')
        track_subplot.grid()
        toolbar = NavigationToolbar2Tk(track_canvas, track_root, pack_toolbar=False)
        toolbar.grid(row=1, column=1, rowspan=2, sticky="N")
        toolbar.update()
        track_canvas.draw()
        track_canvas.get_tk_widget().grid(row=1, column=1, rowspan=2)

        track_root.rowconfigure(0, weight=1)
        track_root.rowconfigure(1, weight=0)
        track_root.rowconfigure(2, weight=0)
        track_root.rowconfigure(3, weight=1)
        track_root.columnconfigure(0, weight=1)
        track_root.columnconfigure(1, weight=0)
        track_root.columnconfigure(2, weight=0)
        track_root.columnconfigure(3, weight=1)

        track_root.mainloop()

ui = LapSimUI() # Run LapSimUI to initialize base UI elements like track_root, track_canvas, etc.

class node():

    def __init__(self, x1, y1, x2, y2, car_rad):
        global track_subplot

        self.car_rad = car_rad
        self.v_min = 0

        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

        self.dist = ((x2-x1)**2 + (y2-y1)**2)**0.5
        self.shift = self.dist / 2

        self.prev_nd = None
        self.next_nd = None
        self.prev_arc = None
        self.next_arc = None
        self.vx = 1
        self.vy = 1

        self.update_shift()
    
    def update_shift(self):
        if self.shift > self.dist-self.car_rad:
            self.shift = self.dist-self.car_rad
        elif self.shift < self.car_rad:
            self.shift = self.car_rad
        
        self.x = self.x1 + (self.x2 - self.x1) * self.shift / self.dist
        self.y = self.y1 + (self.y2 - self.y1) * self.shift / self.dist

        if self.vx**2 + self.vy**2 < self.v_min **2:
            v = self.v_min /(self.vx**2 + self.vy**2)**0.5
            self.vx *= v
            self.vy *= v
    
    def start_shift(self):
        m1 = 0
        if self.x2 == self.x1:
            m1 = 9999
        else:
            m1 = (self.y2 - self.y1) / (self.x2 - self.x1)
        b1 = self.y1 - m1 * self.x1

        m2 = 0
        if self.next_nd.x2 + self.next_nd.x1 == self.prev_nd.x2 + self.prev_nd.x1:
            m2 = 9999
        else:
            m2 = (self.next_nd.y2 + self.next_nd.y1 - self.prev_nd.y2 - self.prev_nd.y1) / (self.next_nd.x2 + self.next_nd.x1 - self.prev_nd.x2 - self.prev_nd.x1)
        b2 = (self.next_nd.y1 + self.next_nd.y2)/2 - m2 * (self.next_nd.x1 + self.next_nd.x2)/2

        if (self.x2 == self.x1) or (m1 == m2):
            self.shift = self.dist/2
        else:
            self.shift = self.dist * ((b2-b1)/(m1-m2) - self.x1) / (self.x2 - self.x1)
        self.update_shift()
        
    def start_v(self):
        #if abs(self.x - self.prev_nd.x) < abs(self.next_nd.x - self.x):
        #    self.vx = (self.x - self.prev_nd.x) / 2**0.5
        #else:
        #    self.vx = (self.next_nd.x - self.x) / 2**0.5
        #
        #if abs(self.y - self.prev_nd.y) < abs(self.next_nd.y - self.y):
        #    self.vy = (self.y - self.prev_nd.y) / 2**0.5
        #else:
        #    self.vy = (self.next_nd.y - self.y) / 2**0.5 + 1

        self.vx = (self.next_nd.x - self.x + self.x - self.prev_nd.x) / 4
        self.vy = (self.next_nd.y - self.y + self.y - self.prev_nd.y) / 4

    def gradient(self):
        self.d_vx = self.next_arc.dcx[1] - self.prev_arc.dcx[2]
        self.d_vy = self.next_arc.dcy[1] - self.prev_arc.dcy[2]

        self.d_shift = ((self.next_arc.dcx[0] + self.next_arc.dcx[1] + self.prev_arc.dcx[2]) * (self.x2 - self.x1) +
                        (self.next_arc.dcy[0] + self.next_arc.dcy[1] + self.prev_arc.dcy[2]) * (self.y2 - self.y1)) / self.dist
        
        if ((self.shift >= self.dist) and (self.d_shift < 0)) or ((self.shift <= 0) and (self.d_shift > 0)):
            self.shift = 0

        




class curve():

    def __init__(self, n1, n2, elem = 50):
        self.n1 = n1
        self.n2 = n2
        self.elem = elem

        self.s_dA = [[],[],[],[]]
        self.ds_dA = [[],[],[],[]]
        self.dds_dA = [[],[],[],[]]
            
        for t in np.linspace(0, 1, self.elem):
            self.s_dA[0].append(1 - 3*t + 3*t**2 - t**3)
            self.s_dA[1].append(3*t - 6*t**2 + 3*t**3)
            self.s_dA[2].append(3*t**2 - 3*t**3)
            self.s_dA[3].append(t**3)
            
            self.ds_dA[0].append(-3 + 6*t - 3*t**2)
            self.ds_dA[1].append(3 - 12*t + 9*t**2)
            self.ds_dA[2].append(6*t - 9*t**2)
            self.ds_dA[3].append(3*t**2)

            self.dds_dA[0].append(6 - 6*t)
            self.dds_dA[1].append(-12 + 18*t)
            self.dds_dA[2].append(6 - 18*t)
            self.dds_dA[3].append(6*t)

        self.compute()
    
    def compute(self):
        n1 = self.n1
        n2 = self.n2

        p1x, p1y = n1.x,           n1.y
        p2x, p2y = n1.x + n1.vx,   n1.y + n1.vy
        p3x, p3y = n2.x - n2.vx,   n2.y - n2.vy
        p4x, p4y = n2.x,           n2.y

        self.x, self.dx, self.ddx = [], [], []
        self.y, self.dy, self.ddy = [], [], []

        self.dcx = [0, 0, 0, 0]
        self.dcy = [0, 0, 0, 0]

        self.c = 0
        
        for i in range(0, self.elem):
            self.x.append(p1x * self.s_dA[0][i] + p2x * self.s_dA[1][i] + p3x * self.s_dA[2][i] + p4x * self.s_dA[3][i])
            self.y.append(p1y * self.s_dA[0][i] + p2y * self.s_dA[1][i] + p3y * self.s_dA[2][i] + p4y * self.s_dA[3][i])

            self.dx.append(p1x * self.ds_dA[0][i] + p2x * self.ds_dA[1][i] + p3x * self.ds_dA[2][i] + p4x * self.ds_dA[3][i])
            self.dy.append(p1y * self.ds_dA[0][i] + p2y * self.ds_dA[1][i] + p3y * self.ds_dA[2][i] + p4y * self.ds_dA[3][i])

            self.ddx.append(p1x * self.dds_dA[0][i] + p2x * self.dds_dA[1][i] + p3x * self.dds_dA[2][i] + p4x * self.dds_dA[3][i])
            self.ddy.append(p1y * self.dds_dA[0][i] + p2y * self.dds_dA[1][i] + p3y * self.dds_dA[2][i] + p4y * self.dds_dA[3][i])

            #self.c += abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**0.5 / (self.dx[i]**2 + self.dy[i]**2)**0.25 / self.elem
            #num = abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**0.5
            #dom = (self.dx[i]**2 + self.dy[i]**2)**0.25

            num = (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**2
            dom = (self.dx[i]**2 + self.dy[i]**2)**2.5

            self.c += num/dom * 1000/self.elem


            H = 1
            if self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i] < 0:
                H = -1
            
            for j in range(4):
                #d_num = (self.ds_dA[j][i] * self.ddy[i] - self.dds_dA[j][i] * self.dy[i]) / (2 * num * H)
                #d_dom = (self.ds_dA[j][i] * self.dx[i]) / (2 * dom**3)

                d_num = (self.ds_dA[j][i] * self.ddy[i] - self.dds_dA[j][i] * self.dy[i]) * (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]) * 2
                d_dom = 5 * (self.ds_dA[j][i] * self.dx[i]) * (self.dx[i]**2 + self.dy[i]**2)**1.5
                dc = (d_num * dom - d_dom * num) / dom**2
                self.dcx[j] += dc / self.elem
            
            for j in range(4):
                #d_num = (self.dds_dA[j][i] * self.dx[i] - self.ds_dA[j][i] * self.ddx[i]) / (2 * num * H)
                #d_dom = (self.ds_dA[j][i] * self.dy[i]) / (2 * dom**3)

                d_num = (self.dds_dA[j][i] * self.dx[i] - self.ds_dA[j][i] * self.ddx[i]) * (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]) * 2
                d_dom = 5 * (self.ds_dA[j][i] * self.dy[i]) * (self.dx[i]**2 + self.dy[i]**2)**1.5
                dc = (d_num * dom - d_dom * num) / dom**2
                self.dcy[j] += dc / self.elem

    def interpolate(self):
        len = []
        rad = []
        for i in range(0, self.elem):
            rad.append((self.dx[i]**2 + self.dy[i]**2)**1.5 / abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]))
            len.append((self.dx[i]**2 + self.dy[i]**2)**0.5 / self.elem)

        return(len, rad)
    
    def plot(self):
        track_subplot.plot(self.x, self.y)

def get_data_string(self, data_bools, index):
    content = ""
    if data_bools[0].get():
        content += f"Time: {round(lapsim_data_storage.time_array[index], 2)} sec\n\n"
    if data_bools[1].get():
        content += f"Lateral Acceleration: {round(lapsim_data_storage.AY[index], 2)} g's\nAxial Acceleration: {round(lapsim_data_storage.AX[index], 2)}g's\n\n"
    if data_bools[2].get():
        content += f"Vertical force on front outer tire: {round(lapsim_data_storage.W_out_f_array[index], 2)} lbs\nVertical force on front inner tire: {round(lapsim_data_storage.W_in_f_array[index], 2)} lbs\nVertical force on rear outer tire: {round(lapsim_data_storage.W_out_r_array[index], 2)} lbs\nVertical force on rear inner tire: {round(lapsim_data_storage.W_in_r_array[index], 2)} lbs\n\n"
    if data_bools[3].get():
        content += f"Lateral force on front outer tire: {round(lapsim_data_storage.FY_out_f_array[index], 2)} lbs\nLateral force on front inner tire: {round(lapsim_data_storage.FY_in_f_array[index], 2)} lbs\nLateral force on rear outer tire: {round(lapsim_data_storage.FY_out_r_array[index], 2)} lbs\nLateral force on rear inner tire: {round(lapsim_data_storage.FY_in_r_array[index], 2)} lbs\n\n"
    if data_bools[4].get():
        content += f"Axial force on front outer tire: {round(lapsim_data_storage.FX_out_f_array[index], 2)} lbs\nAxial force on front inner tire: {round(lapsim_data_storage.FX_in_f_array[index], 2)} lbs\nAxial force on rear outer tire: {round(lapsim_data_storage.FX_out_r_array[index], 2)} lbs\nAxial force on rear inner tire: {round(lapsim_data_storage.FX_in_r_array[index], 2)} lbs\n\n"
    if data_bools[5].get():
        content += f"Vertical displacement of front outer tire: {round(lapsim_data_storage.D_1_dis[index], 2)} in\nVertical displacement of front inner tire: {round(lapsim_data_storage.D_2_dis[index], 2)} in\nVertical displacement of rear outer tire: {round(lapsim_data_storage.D_3_dis[index], 2)} in\nVertical displacement of rear inner tire: {round(lapsim_data_storage.D_4_dis[index], 2)} in\n\n"
    if data_bools[6].get():
        content += f"Theta of Force on Car: {round(lapsim_data_storage.theta_accel[index], 2)} deg\n\n"
    content += f"\n\"Outer\" refers to the tires on the outside of the turn;\n \"Inner\" refers to the tires on the inside of the turn."
    return content

class track():

    global x_array, y_array

    def __init__(self, p1x, p1y, p2x, p2y, car):
        global x_array, y_array

        self.car = car

        # Get the minimum distance the CG of the car needs from the apex of the turn
        self.car_rad = np.max([self.car.t_r, self.car.t_f])/2

        self.len = []

        self.nds = []
        for i in range(len(p1x)):
            self.nds.append(node(p1x[i], p1y[i], p2x[i], p2y[i], self.car_rad))
        print(f"nodes: {len(self.nds)}")

        for i in range(-1, len(self.nds)-1):
            self.nds[i].prev_nd = self.nds[i-1]
            self.nds[i].next_nd = self.nds[i+1]
            self.nds[i].start_shift()

        for i in self.nds:
            i.start_v()

        self.arcs = []

        for i in self.nds:
            self.arcs.append(curve(i, i.next_nd))
            i.next_arc = self.arcs[-1]
            i.next_nd.prev_arc = self.arcs[-1]

        # Keeps track of locations of data nodes
        x_array = []
        y_array = []

        print(f"created track")

    def k_closest(self, points, mouse_pos):
        closest_point = None
        closest_dist = float('inf')
        closest_index = None

        # Push points onto the heap, maintaining the size at most k
        for index, point in enumerate(points):
            distance = math.sqrt((point[0] - mouse_pos[0])**2 + (point[1] - mouse_pos[1])**2)
            if closest_dist > distance:
                closest_dist = distance
                closest = point
                closest_index = index

        return closest_index

    def plot(self, save_file_func=None):
        global data_bools, track_canvas, track_subplot, track_root, track_fig, data_label

        print("plotting")

        for i in self.arcs:
            i.plot() # Plot lines on graph (path of car)

        arc_lengths = []
        for arc in self.arcs:
            lengths, _ = arc.interpolate()
            arc_lengths.append(sum(lengths))

        total_track_length = sum(arc_lengths)
        total_data_node_count = len(self.sim.nds)
        distance_between_nodes = total_track_length / total_data_node_count
        remainder_length = 0
        prev_node_location = 0
        for index, arc in enumerate(self.arcs):
            lengths, _ = arc.interpolate()
            arc_length = sum(lengths)
            # array of cumulative distances along the arc
            cum = np.cumsum(lengths) # shape ~ (len(arc.x),) hehe

            # Carry remainder from previous arc into this one
            effective_length = remainder_length + arc_length

            # How many whole node spacings fit in this arc when including the carried remainder?
            num_nodes_in_arc = math.floor(effective_length / distance_between_nodes)

            # How far to the first node from the start of this arc
            remainder_length_from_prev = effective_length - arc_length
            node_offset = distance_between_nodes - remainder_length_from_prev

            # Compute new remainder to carry to the next arc
            remainder_length = effective_length - num_nodes_in_arc * distance_between_nodes

            # Map percent of arcs to arc vars 'x' array and 'y' array using arc_length.
            for j in range(num_nodes_in_arc):
                # target arc-length from start of this arc
                node_location = node_offset + j * distance_between_nodes
                if node_location <= 0: # if node location is before the start of the arc, skip this iteration and advance to the next location
                    continue
                if node_location > arc_length: # if node location is past the length of the arc
                    break

                # Find index to use for arc.x and arc.y positions where cumulative length of arc roughly equals node_location
                node_index = round(len(arc.x) * (j/num_nodes_in_arc))

                if node_index ==0:
                    prev_node_location = 0.0
                    ds = lengths[0]
                    t = 0.0 if ds == 0 else (node_location - prev_node_location) / ds
                    x = arc.x[0] + t * (arc.x[1] - arc.x[0])
                    y = arc.y[0] + t * (arc.y[1] - arc.y[0])
                elif node_index >= len(arc.x):
                    x = arc.x[-1]
                    y = arc.y[-1]
                else:
                    # linear interpolation between samples node_index-1 and node_index for smoother placement
                    prev_node_location = cum[node_index-1]
                    ds = lengths[node_index] # grab small portion of arc
                    t = 0.0 if ds == 0 else (node_location - prev_node_location) / ds # get slope of previous node location compared to this node location.
                    # Set final x and y coordinates for the node
                    if not node_index+1 >= len(arc.x): # If the node index is at the end of the arc, just use the end of the arc.
                        x = arc.x[node_index] + t * (arc.x[node_index+1] - arc.x[node_index]) # Add previous node x value onto approximated additional x value.
                        y = arc.y[node_index] + t * (arc.y[node_index+1] - arc.y[node_index]) # Add previous node y value onto approximated additional y value.
                    else:
                        x = arc.x[-1]
                        y = arc.y[-1]

                if len(x_array) < len(self.sim.nds): # Make sure that the amount of data nodes does not exceed the amount of simulation nodes.
                    x_array.append(x)
                    y_array.append(y)
                    # track_subplot.plot(x, y, marker='o', color='black', markersize=1)

        for i in range(len(self.nds)):
            nd = self.nds[i]
            match i % 5:
                case 0: col = 'blue'
                case 1: col = 'red'
                case 2: col = 'black'
                case 3: col = 'magenta'
                case 4: col = 'orange'
            if i != 0:
                track_subplot.plot(self.nds[i].x1, self.nds[i].y1, marker='o', color=col, markersize=3)
                track_subplot.plot(self.nds[i].x2, self.nds[i].y2, marker='o', color=col, markersize=3)
            else: # Large pink dots mark where the track begins
                track_subplot.plot(self.nds[i].x1, self.nds[i].y1, marker='o', color='pink', markersize=6)
                track_subplot.plot(self.nds[i].x2, self.nds[i].y2, marker='o', color='pink', markersize=6)

        # Load lapsim ui
        ui.load_lapsim(save_file_func)

        # Function that converts the position of the users mouse into data from the nearest data node
        def on_hover(event):

            if event.inaxes == track_subplot:
                # Find the nearest data point
                contains, info = track_subplot.contains(event)
                if contains:
                    x = event.xdata
                    y = event.ydata

                    # If not -1, the algorithm below found a relatively close by data node to extract information from and the index of that information is this (within arrays found in append_data_arrays).
                    closest_index = -1

                    points = []
                    for i in range(len(x_array)):
                        points.append((x_array[i], y_array[i]))

                    closest_index = self.k_closest(points, (x, y))

                    # Find corresponding lateral and axial acceleration with node the user is hovering over
                    if closest_index != -1: # Check to see if the algorithm above found a suitable data node.
                        data_label.config(text=get_data_string(self, data_bools, closest_index))

                    # Draw dot that indicates which data node the user is gathering information from
                    track_subplot.lines[-1].remove()
                    track_subplot.plot(x_array[closest_index], y_array[closest_index], marker='o', color='black', markersize=5)
                    track_canvas.draw()

        # Connect the mouse movement event to the on_hover function
        track_canvas.mpl_connect("motion_notify_event", on_hover)

        ui.load_track()

    def get_cost(self):
        cost = 0
        for i in self.arcs:
            cost += i.c
        return cost

    def adjust_track(self, itterations, step):
        s = []
        for i in range(len(itterations)):
            for j in range(itterations[i]):
                s += [step[i]]

        for k in range(len(s)):
            step = s[k]

            grad_mag = 0
            for i in self.nds:
                i.gradient()
                grad_mag += i.d_vx**2 + i.d_vy**2 + i.d_shift**2

            grad_mag = grad_mag**0.5

            for i in self.nds:
                i.vx -= i.d_vx / grad_mag * step
                i.vy -= i.d_vy / grad_mag * step
                i.shift -= i.d_shift / grad_mag * step
            self.update_track()

            char = 100
            progress_bar = ' ['
            for j in range(char):
                if j / char * len(s) >= k+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((k+1.1) * 100 / len(s))) + '%\tcost = ' + str(self.get_cost())
            print(progress_bar, end='\r')
        print()

    def run_sim(self, car, nodes = 5000, start = 0, end = 0):
        self.car = car

        if end == 0:
            end = len(self.arcs)

        self.len = []
        self.rad = []
        for i in self.arcs[start:end]:
            new_len, new_rad = i.interpolate()
            self.len += new_len
            self.rad += new_rad
        #print(np.sum(self.len))
        self.sim = lapsim.four_wheel(self.len, self.rad, car, nodes)
        self.nodes, self.v3, self.t = self.sim.run()
        # print(f'Total Travel Time: {self.t}')
    def update_track(self):
        for i in self.nds:
            i.update_shift()
        for i in self.arcs:
            i.compute()

    def plt_sim(self, car, nodes = 5000, start = 0, end = 0):
        self.car = car

        # setup for position vs velocity plot
        self.run_sim(car, nodes, start, end)
        track_subplot.set_title('Simulation Results:')
        track_subplot.set_xlabel('Position (ft)')
        track_subplot.set_ylabel('Vehicle Speed (mph)')
        track_subplot.grid()
        track_subplot.plot(self.nodes, self.v3)
        track_subplot.axis('equal')
        track_canvas.draw()
        track_canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        track_root.mainloop()
    
    def refine_track(self):
        self.run_sim('single_point')

        elem = 50
        t_step = 10
        m_step = 3
        grad = np.zeros(len(self.nds))
        mag_grad = 0
        for i in range(1, len(self.nds)-1):
            self.nds[i].vx += 10
            new_arc1 = curve(self.nds[i-1], self.nds[i])
            new_arc2 = curve(self.nds[i], self.nds[i+1])
            new_len1, new_rad1 = new_arc1.interpolate()
            new_len2, new_rad2 = new_arc2.interpolate()
            self.nds[i].vx -= 10
            grad[i] += self.sim.arcEvaluator(i*50-50, i*50+50, new_len1+new_len2, new_rad1+new_rad2)
            mag_grad += grad[i]**2

            char = 100
            progress_bar = ' ['
            for j in range(char):
                if j*2 / char * len(self.nds) >= i+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((i + 1.1)/2 * 100 / len(self.nds))) + '%'
            print(progress_bar, end='\r')

        grad = np.zeros(len(self.nds))
        mag_grad = 0
        for i in range(1, len(self.nds)-1):
            self.nds[i].vy += 10
            new_arc1 = curve(self.nds[i-1], self.nds[i])
            new_arc2 = curve(self.nds[i], self.nds[i+1])
            new_len1, new_rad1 = new_arc1.interpolate()
            new_len2, new_rad2 = new_arc2.interpolate()
            self.nds[i].vy -= 10
            grad[i] += self.sim.arcEvaluator(i*50-50, i*50+50, new_len1+new_len2, new_rad1+new_rad2)
            mag_grad += grad[i]**2

            progress_bar = ' ['
            for j in range(char):
                if (j+char)/2 / char * len(self.nds) >= i+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((i + char + 2.1)/2 * 100 / len(self.nds))) + '%'
            print(progress_bar, end='\r')
        print()
        
        mag_grad **= 0.5
        for i in range(len(self.nds)):
            self.nds[i].vy += grad[i] / mag_grad * m_step
        self.update_track()
        #print(grad)
            

            


