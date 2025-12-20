import tkinter
from copy import deepcopy
from tkinter import filedialog

import numpy as np
import pickle

from LapData import LapData
from file_management import file_manager


class CarSettingsWindow:

    def __init__(self, display_track = None, lap_data = None, car = None):
        self.root = tkinter.Toplevel() # For winsow of graph and viewable values
        self.root.title("Car Settings")

        self.display_track = display_track

        self.lap_data = lap_data

        self.entries_list = []

        self.generate_report = tkinter.BooleanVar()
        self.generate_report.set(True)

        self.changed_car_model = False

        self.canvas = tkinter.Canvas(master=self.root, width=500, height=500)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = (tkinter.Scrollbar(self.root, orient="vertical", command=self.canvas.yview))
        scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=scrollbar.set)

        self.scrollable_frame = tkinter.Frame(self.canvas, width=500, height=500)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="center")

        if car is not None:
            self.car = car
            self.car_file_path = self.car.file_location
        else:
            self.car = lap_data.car
            self.car_file_path = lap_data.car.file_location

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
            "max_rear_jounce": tkinter.DoubleVar(self.root, value=self.car.max_jounce_r),
            "rolling_resistance_coefficient":tkinter.DoubleVar(self.root, value=self.car.C_rr),
        }

        # Units for each variable per row
        self.units = ["", "lbs", "lbs", "lbs", "lbs", "in", "in", "in", "in", "in", "in", "in", "lb/in", "lb/in", "lb*ft/deg","lb*ft/deg", "deg/in", "deg/in", "deg", "deg", "in", "in", "unitless"]

        # Grid each label and entries into window
        row = 1
        for name, var in self.settings.items():
            # Create a readable label from the key
            label_text = name.replace("_", " ").title()
            label_text += f" ({self.units[row]})"

            # Create label
            label = tkinter.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=1, padx=5, pady=5, sticky="w")

            # Create entry and bind it to the tkinter variable
            entry = tkinter.Entry(self.scrollable_frame, textvariable=var, width=15)
            entry.grid(row=row, column=2, padx=5, pady=5)
            self.entries_list.append(entry)

            row += 1  # move to next row

        if display_track is not None:
            change_car_button = tkinter.Button(self.scrollable_frame, text="Change Car", command= lambda: self.get_car_file())
            change_car_button.grid(row=23, column=1, pady=(50, 0), sticky="N")

            self.change_car_label = tkinter.Label(self.scrollable_frame, text="Car imported!", fg="SpringGreen2")
            self.change_car_label.grid(row=23, column=2, pady=(50, 0), sticky="W")
            self.change_car_label.grid_remove()

            self.generate_report_toggle = tkinter.Checkbutton(self.scrollable_frame, text="Generate REPORT", variable=self.generate_report)
            self.generate_report_toggle.grid(row=24, column=2, pady=(50, 0), sticky="N")

        apply_and_reload_button = tkinter.Button(self.scrollable_frame, text="Apply and Reload", command= lambda: self.apply_changes_and_run_lapsim() if display_track is not None else self.apply_changes())
        apply_and_reload_button.grid(row=24, column=1, pady=(50, 0), sticky="N")

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
        self.scrollable_frame.rowconfigure(22, weight=0)
        self.scrollable_frame.rowconfigure(23, weight=0)
        self.scrollable_frame.rowconfigure(24, weight=0)
        self.scrollable_frame.rowconfigure(25, weight=0)
        self.scrollable_frame.rowconfigure(26, weight=1)
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
    def apply_changes(self, save_car_file = False):
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
        self.car.K_rollF = self.settings["front_roll_rate"].get() * np.pi/180
        self.car.K_rollR = self.settings["rear_roll_rate"].get() * np.pi/180
        self.car.CMB_RT_F = self.settings["front_camber_rate"].get()
        self.car.CMB_RT_R = self.settings["rear_camber_rate"].get()
        self.car.CMB_STC_F = self.settings["front_static_camber"].get()
        self.car.CMB_STC_R = self.settings["rear_static_camber"].get()
        self.car.max_jounce_f = self.settings["max_front_jounce"].get()
        self.car.max_jounce_r = self.settings["max_rear_jounce"].get()
        self.car.C_rr = self.settings["rolling_resistance_coefficient"].get()

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

        if save_car_file:
            if self.car_file_path:
                with(open(self.car_file_path, 'wb') as f):
                    pickle.dump(obj=self.car, file=f)

        self.close_window()

    def change_vars_to_car(self, car):
        self.car = car
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
            "max_rear_jounce": tkinter.DoubleVar(self.root, value=self.car.max_jounce_r),
            "rolling_resistance_coefficient":tkinter.DoubleVar(self.root, value=self.car.C_rr),
        }
        index = 0
        for key, value in self.settings.items():
            self.entries_list[index].grid_forget()
            self.entries_list[index].config(textvariable=self.settings[key])
            self.entries_list[index].grid(row=index+1, column=2, padx=5, pady=5)
            index += 1

    def get_car_file(self):
        file = filedialog.askopenfilename(title="Pick a car file", initialdir=file_manager.get_models_dir(), filetypes=[("Pickle file", "*.pkl")], defaultextension=".pkl")
        if file:
            with open(file, "rb") as f:
                self.car = pickle.load(f)
                print(f"t_f: {self.car.t_f}")
            self.change_vars_to_car(self.car)
            self.change_car_label.grid()
            self.changed_car_model = True

    def open_window(self):
        self.change_vars_to_car(self.lap_data.car)
        self.root.deiconify() # Show the window

    def close_window(self):
        try:
            self.change_car_label.grid_remove()
        except Exception:
            pass
        self.root.withdraw()
        self.root.withdraw()

    def apply_changes_and_run_lapsim(self):
        # Make a prev_lap_data var that stores the data in this current track so that we can access it later for the REPORT
        prev_lap_data = LapData(self.lap_data.points)
        prev_lap_data.generated_track = self.lap_data.generated_track
        prev_lap_data.generated_track.sim.lapsim_data_storage = deepcopy(self.lap_data.generated_track.sim.lapsim_data_storage)
        prev_lap_data.car = deepcopy(self.car)

        self.apply_changes(save_car_file=False)
        self.lap_data.car = self.car
        self.change_vars_to_car(self.car)
        # If the user wants to generate a REPORT, pass prev_lap_data, etc. arguments into create_and_show_notgenerated_track func
        if self.generate_report.get():
            self.display_track.create_and_show_notgenerated_track(display_track=self.display_track, lap_data=self.lap_data, prev_lap_data=prev_lap_data, generate_report=self.generate_report.get(), changed_car_model=self.changed_car_model)
        # User does not want to generate a REPORT
        else:
            self.display_track.create_and_show_notgenerated_track(display_track=self.display_track, lap_data=self.lap_data)