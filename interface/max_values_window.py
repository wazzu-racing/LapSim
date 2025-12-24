import tkinter

class MaxValuesWindow:

    def __init__(self, lap_data):
        self.root = tkinter.Toplevel()
        self.root.title("MAX VALUES")
        self.root.attributes("-topmost", True)

        self.canvas = tkinter.Canvas(master=self.root, width=500, height=500)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Make The scrollbar and put it in the canvas.
        scrollbar = (tkinter.Scrollbar(self.root, orient="vertical", command=self.canvas.yview))
        scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=scrollbar.set)

        # Make a frame and put it in self.canvas.
        self.scrollable_frame = tkinter.Frame(self.canvas, width=500, height=500)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Units for each var in LapSimData
        self.data_units = ["sec", "g's","g's","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","lbs","in","in","in","in"]

        self.lap_data = lap_data

        # Array that stores the labels that present max values to users.
        self.max_value_labels = []

        row = 1
        # Display the max values
        max_values = self.lap_data.generated_track.sim.lapsim_data_storage.find_max_values()
        for index, data_point in enumerate(self.lap_data.generated_track.sim.lapsim_data_storage.max_value_names):
            # If the index zero, that is time so just say "Time: blah blah" and not "Max time: blah blah" cause that makes no sense.
            if index != 0:
                label_text = data_point.replace("_", " ") + f" ({self.data_units[index]})" + ": "
            else:
                label_text = "Time" + f" ({self.data_units[index]})" + ": "
            label_text += str(round(max_values[data_point], 2))

            # Create label
            label = tkinter.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=1, padx=5, pady=5, sticky="W")

            self.max_value_labels.append(label)

            row += 1

        # Configure rows for all labels.
        self.scrollable_frame.rowconfigure(0, weight=1)
        for i in range(row):
            self.scrollable_frame.rowconfigure(i+1, weight=0)
        self.scrollable_frame.rowconfigure(row+1, weight=1)

        # configure columns.
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=0)
        self.scrollable_frame.columnconfigure(2, weight=0)
        self.scrollable_frame.columnconfigure(3, weight=1)

        # Allow user to scroll.
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Hide this window until ready to show
        self.root.withdraw()

        # Only allow the user to hide the window, not close it
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    # Update max value labels with new data in the argument new_lap_data.
    def update_max_value_labels(self, new_lap_data):
        max_values = new_lap_data.generated_track.sim.lapsim_data_storage.find_max_values()
        for index, label in enumerate(self.max_value_labels):
            if index != 0:
                label_text = new_lap_data.generated_track.sim.lapsim_data_storage.max_value_names[index].replace("_", " ") + f" ({self.data_units[index]})" + ": "
            else:
                label_text = "Time" + f" ({self.data_units[index]})" + ": "
            label_text += str(round(max_values[new_lap_data.generated_track.sim.lapsim_data_storage.max_value_names[index]], 2))

            label.config(text=label_text)

    def open_window(self):

        self.root.deiconify() # Show the window

    def close_window(self):
        self.root.withdraw()