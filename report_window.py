import tkinter

from sympy.polys.densebasic import dmp_apply_pairs


class ReportWindow:

    def __init__(self, prev_lap_data, new_lap_data, changed_car_model=False):
        self.root = tkinter.Toplevel()
        self.root.title("REPORT")
        self.root.attributes("-topmost", True)

        self.canvas = tkinter.Canvas(master=self.root, width=500, height=500)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = (tkinter.Scrollbar(self.root, orient="vertical", command=self.canvas.yview))
        scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=scrollbar.set)

        self.scrollable_frame = tkinter.Frame(self.canvas, width=500, height=500)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Variables for previous data
        self.prev_settings = {
            "front_left_wheel_weight": prev_lap_data.car.W_1,
            "front_right_wheel_weight": prev_lap_data.car.W_2,
            "rear_left_wheel_weight": prev_lap_data.car.W_3,
            "rear_right_wheel_weight": prev_lap_data.car.W_4,
            "length_of_wheelbase": prev_lap_data.car.l,
            "cg_height": prev_lap_data.car.h,
            "cg_to_roll_axis_height": prev_lap_data.car.H,
            "front_roll_axis_height": prev_lap_data.car.z_rf,
            "rear_roll_axis_height": prev_lap_data.car.z_rr,
            "front_track_width": prev_lap_data.car.t_f,
            "rear_track_width": prev_lap_data.car.t_r,
            "front_ride_rate": prev_lap_data.car.K_RF,
            "rear_ride_rate": prev_lap_data.car.K_RR,
            "front_roll_rate": prev_lap_data.car.K_rollF,
            "rear_roll_rate": prev_lap_data.car.K_rollR,
            "front_camber_rate": prev_lap_data.car.CMB_RT_F,
            "rear_camber_rate": prev_lap_data.car.CMB_RT_R,
            "front_static_camber": prev_lap_data.car.CMB_STC_F,
            "rear_static_camber": prev_lap_data.car.CMB_STC_R,
            "max_front_jounce": prev_lap_data.car.max_jounce_f,
            "max_rear_jounce": prev_lap_data.car.max_jounce_r,
            "rolling_resistance_coefficient": prev_lap_data.car.C_rr,
        }

        # Variables for new data
        self.new_settings = {
            "front_left_wheel_weight": new_lap_data.car.W_1,
            "front_right_wheel_weight": new_lap_data.car.W_2,
            "rear_left_wheel_weight": new_lap_data.car.W_3,
            "rear_right_wheel_weight": new_lap_data.car.W_4,
            "length_of_wheelbase":new_lap_data.car.l,
            "cg_height":new_lap_data.car.h,
            "cg_to_roll_axis_height": new_lap_data.car.H,
            "front_roll_axis_height": new_lap_data.car.z_rf,
            "rear_roll_axis_height": new_lap_data.car.z_rr,
            "front_track_width": new_lap_data.car.t_f,
            "rear_track_width": new_lap_data.car.t_r,
            "front_ride_rate": new_lap_data.car.K_RF,
            "rear_ride_rate":new_lap_data.car.K_RR,
            "front_roll_rate": new_lap_data.car.K_rollF,
            "rear_roll_rate": new_lap_data.car.K_rollR,
            "front_camber_rate": new_lap_data.car.CMB_RT_F,
            "rear_camber_rate": new_lap_data.car.CMB_RT_R,
            "front_static_camber": new_lap_data.car.CMB_STC_F,
            "rear_static_camber": new_lap_data.car.CMB_STC_R,
            "max_front_jounce": new_lap_data.car.max_jounce_f,
            "max_rear_jounce": new_lap_data.car.max_jounce_r,
            "rolling_resistance_coefficient":new_lap_data.car.C_rr,
        }

        # Units for each variable per row
        self.settings_units = ["lbs", "lbs", "lbs", "lbs", "in", "in", "in", "in", "in", "in", "in", "lb/in", "lb/in", "lb*ft/deg", "lb*ft/deg", "deg/in", "deg/in", "deg", "deg", "in", "in", "unitless"]
        # Units for each var in LapSimData
        self.data_units = ["sec", "g's","g's","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","in","in","in","in"]

        # Subtitle for new max values
        car_changes_label = tkinter.Label(self.scrollable_frame, text="New Max Values", font=("TkDefaultFont", 13, "bold"))
        car_changes_label.grid(row=1, column=1, sticky="W")

        row = 2
        # Display the changes in max values
        prev_max_values = prev_lap_data.generated_track.sim.lapsim_data_storage.find_max_values()
        new_max_values = new_lap_data.generated_track.sim.lapsim_data_storage.find_max_values()
        for index, data_point in enumerate(prev_lap_data.generated_track.sim.lapsim_data_storage.max_value_names):
            if index != 0:
                label_text = data_point.replace("_", " ") + f" ({self.data_units[index]})" + ": "
            else:
                label_text = "Time" + f" ({self.data_units[index]})" + ": "
            label_text += str(round(new_max_values[data_point], 2))

            # Create label
            label = tkinter.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=1, padx=5, pady=5, sticky="W")

            # Create colored value difference label
            data_difference = new_max_values[data_point] - prev_max_values[data_point]
            difference_label_text = f" {"+" if data_difference >= 0 else ""}{round(data_difference, 2)}"

            difference_color = "SpringGreen2" if data_difference >= 0 else "Red"
            difference_label = tkinter.Label(self.scrollable_frame, text=difference_label_text, fg=difference_color)
            difference_label.grid(row=row, column=2, padx=5, pady=5, sticky="W")

            row += 1

        # Subtitle for users changes to car settings
        car_changes_label = tkinter.Label(self.scrollable_frame, text="User's Changes", font=("TkDefaultFont", 13, "bold"))
        car_changes_label.grid(row=row, column=1, pady=(20, 0), sticky="W")

        row+=1

        if changed_car_model:
            # Create label
            label = tkinter.Label(self.scrollable_frame, text="Changed to another car model")
            label.grid(row=row, column=1, padx=5, pady=5, sticky="W")
            row+=1

        # Grid each label and entries into window
        for index, setting in enumerate(self.prev_settings):
            if round(self.prev_settings[setting],2 ) != round(self.new_settings[setting], 2):
                # Create a readable label from the key
                label_text = setting.replace("_", " ").title()
                label_text += f" ({self.settings_units[index]}): "
                label_text += f"{self.prev_settings[setting]} -> {self.new_settings[setting]}"

                # Create label
                label = tkinter.Label(self.scrollable_frame, text=label_text)
                label.grid(row=row, column=1, padx=5, pady=5, sticky="W")

                row += 1  # move to next row

        self.scrollable_frame.rowconfigure(0, weight=1)
        for i in range(row):
            self.scrollable_frame.rowconfigure(i+1, weight=0)
        self.scrollable_frame.rowconfigure(row+1, weight=1)

        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=0)
        self.scrollable_frame.columnconfigure(2, weight=0)
        self.scrollable_frame.columnconfigure(3, weight=1)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Hide this window until ready to show
        self.root.withdraw()

        # Only allow the user to hide the window, not close it
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def open_window(self):
        self.root.deiconify() # Show the window

    def close_window(self):
        self.root.withdraw()