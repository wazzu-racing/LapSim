import tkinter

import numpy as np
import pickle

class CarSettingsWindow:

    def __init__(self, car, car_file_path, save_car):
        self.root = tkinter.Tk() # For window of graph and viewable values
        self.root.title("Car Settings")

        self.save_car = save_car

        self.canvas = tkinter.Canvas(master=self.root)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = (tkinter.Scrollbar(self.root, orient="vertical", command=self.canvas.yview))
        scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=scrollbar.set)

        self.scrollable_frame = tkinter.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.car = car
        self.car_file_path = car_file_path

        # Variables for each entry on screen
        self.settings = {
            "front_left_wheel_weight": tkinter.DoubleVar(self.root, value=self.car.W_1),
            "front_right_wheel_weight": tkinter.DoubleVar(self.root, value=self.car.W_2),
            "rear_left_wheel_weight": tkinter.DoubleVar(self.root, value=self.car.W_3),
            "rear_right_wheel_weight": tkinter.DoubleVar(self.root, value=self.car.W_4),
            "length_of_wheelbase": tkinter.DoubleVar(self.root, value=self.car.l),
            "cg_height": tkinter.DoubleVar(self.root, value=self.car.h),
            "cg_to_roll_axis_height": tkinter.DoubleVar(self.root, value=self.car.H),
            "front_roll_axis_height": tkinter.DoubleVar(self.root, value=self.car.z_rf),
            "rear_roll_axis_height": tkinter.DoubleVar(self.root, value=self.car.z_rr),
            "front_track_width": tkinter.DoubleVar(self.root, value=self.car.t_f),
            "rear_track_width": tkinter.DoubleVar(self.root, value=self.car.t_r),
            "front_ride_rate": tkinter.DoubleVar(self.root, value=self.car.K_RF),
            "rear_ride_rate": tkinter.DoubleVar(self.root, value=self.car.K_RR),
            "front_roll_rate": tkinter.DoubleVar(self.root, value=self.car.K_rollF),
            "rear_roll_rate": tkinter.DoubleVar(self.root, value=self.car.K_rollR),
            "front_camber_rate": tkinter.DoubleVar(self.root, value=self.car.CMB_RT_F),
            "rear_camber_rate": tkinter.DoubleVar(self.root, value=self.car.CMB_RT_R),
            "front_static_camber": tkinter.DoubleVar(self.root, value=self.car.CMB_STC_F),
            "rear_static_camber": tkinter.DoubleVar(self.root, value=self.car.CMB_STC_R),
            "max_front_jounce": tkinter.DoubleVar(self.root, value=self.car.max_jounce_f),
            "max_rear_jounce": tkinter.DoubleVar(self.root, value=self.car.max_jounce_r)
        }

        # Grid each label and entries into window
        row = 1
        for name, var in self.settings.items():
            # Create a readable label from the key
            label_text = name.replace("_", " ").title()

            # Create label
            label = tkinter.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=1, padx=5, pady=5, sticky="w")

            # Create entry and bind it to the tkinter variable
            entry = tkinter.Entry(self.scrollable_frame, textvariable=var, width=15)
            entry.grid(row=row, column=2, padx=5, pady=5)

            row += 1  # move to next row

        # Set rows and columns for all widgets in window. This organizes widgets on screen.
        self.scrollable_frame.rowconfigure(0, weight=1)
        self.scrollable_frame.rowconfigure(1, weight=0)
        self.scrollable_frame.rowconfigure(2, weight=0)
        self.scrollable_frame.rowconfigure(3, weight=0)
        self.scrollable_frame.rowconfigure(4, weight=0)
        self.scrollable_frame.rowconfigure(5, weight=0)
        self.scrollable_frame.rowconfigure(6, weight=0)
        self.scrollable_frame.rowconfigure(7, weight=0)
        self.scrollable_frame.rowconfigure(8, weight=0)
        self.scrollable_frame.rowconfigure(9, weight=0)
        self.scrollable_frame.rowconfigure(10, weight=0)
        self.scrollable_frame.rowconfigure(11, weight=0)
        self.scrollable_frame.rowconfigure(12, weight=0)
        self.scrollable_frame.rowconfigure(13, weight=0)
        self.scrollable_frame.rowconfigure(14, weight=0)
        self.scrollable_frame.rowconfigure(15, weight=0)
        self.scrollable_frame.rowconfigure(16, weight=0)
        self.scrollable_frame.rowconfigure(17, weight=0)
        self.scrollable_frame.rowconfigure(18, weight=0)
        self.scrollable_frame.rowconfigure(19, weight=0)
        self.scrollable_frame.rowconfigure(20, weight=0)
        self.scrollable_frame.rowconfigure(21, weight=0)
        self.scrollable_frame.rowconfigure(22, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=0)
        self.scrollable_frame.columnconfigure(2, weight=0)
        self.scrollable_frame.columnconfigure(3, weight=1)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Hide this window until ready to show
        self.root.withdraw()

        # Only allow the user to hide the window, not close it
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    # Apply the changes that the user has made to the settings in the window to the car object and save it in the existing car pkl.
    def apply_changes(self):
        self.car.W_1 = self.settings["front_left_wheel_weight"].get()
        self.car.W_2 = self.settings["front_right_wheel_weight"].get()
        self.car.W_3 = self.settings["rear_left_wheel_weight"].get()
        self.car.W_4 = self.settings["rear_right_wheel_weight"].get()
        self.car.l = self.settings["length_of_wheelbase"].get()
        self.car.h = self.settings["cg_height"].get()
        self.car.H = self.settings["cg_to_roll_axis_height"].get()
        self.car.z_rf = self.settings["front_roll_axis_height"].get()
        self.car.z_rr = self.settings["rear_roll_axis_height"].get()
        self.car.t_f = self.settings["front_track_width"].get()
        self.car.t_r = self.settings["rear_track_width"].get()
        self.car.K_RF = self.settings["front_ride_rate"].get()
        self.car.K_RR = self.settings["rear_ride_rate"].get()
        self.car.K_rollF = self.settings["front_roll_rate"].get()
        self.car.K_rollR = self.settings["rear_roll_rate"].get()
        self.car.CMB_RT_F = self.settings["front_camber_rate"].get()
        self.car.CMB_RT_R = self.settings["rear_camber_rate"].get()
        self.car.CMB_STC_F = self.settings["front_static_camber"].get()
        self.car.CMB_STC_R = self.settings["rear_static_camber"].get()
        self.car.max_jounce_f = self.settings["max_front_jounce"].get()
        self.car.max_jounce_r = self.settings["max_rear_jounce"].get()

        # Converting roll rates to ft*lb/rad
        self.car.K_rollF *= 180/np.pi
        self.car.K_rollR *= 180/np.pi
        # weight over front track
        self.car.W_f = self.car.W_1 + self.car.W_2
        # weight over rear track
        self.car.W_r = self.car.W_3 + self.car.W_4
        # total weight of car (minus driver) (lbm)
        self.car.W_car = self.car.W_f + self.car.W_r
        # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
        self.car.W_bias = self.car.W_f/self.car.W_car
        # in, distance from CG to rear track
        self.car.b = self.car.l * self.car.W_bias
        # in, distance from CG to front track
        self.car.a = self.car.l - self.car.b
        # in, CG height to roll axis
        self.car.H = self.car.h - (self.car.a*self.car.z_rf + self.car.b*self.car.z_rr)/self.car.l

        self.car.compute_traction()

        if self.car_file_path:
            with(open(self.car_file_path, 'wb') as f):
                pickle.dump(obj=self.car, file=f)

    def open_window(self):
        self.root.deiconify() # Show the window

    def close_window(self):
        self.apply_changes()
        self.save_car()
        self.root.withdraw()