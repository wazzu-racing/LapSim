import os
import tkinter
from tkinter import filedialog
import pickle

from display_trk import DisplayTrack
import display_trk
from files import get_save_files_folder_abs_dir

run_lapsim_button = None

track_file = ""
track_check = None

car_file = ""
car_check = None

initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

def select_file(is_car_file=False):
    global run_lapsim_button, track_file, car_file, track_check, car_check, initial_dir

    # Asks the user to choose a pkl file to create the track object with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("Pickle files", "*.pkl")])
    # if the file_path is not nothing, the car/track file is saved and the user is used to make the track object.
    if file_path:
        # Store the file path in the appropriate variable and show that the file has been imported
        if is_car_file:
            car_file = file_path
            car_check.grid(row=3, column=2, pady=(0, 0))
        # Store the file path in the appropriate variable and show that the file has been imported
        else:
            track_file = file_path
            track_check.grid(row=2, column=2, pady=(100, 10))
        # Enable plot button if both files are selected
        if car_file and track_file:
            run_lapsim_button.configure(state="normal")
    else:
        print("No file selected")

class ImportNotGeneratedTrackPage(tkinter.Frame):

    def __init__(self, parent, controller):
        global run_lapsim_button, track_check, car_check

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.save_func = ""

        controller.title("Vehicle Dynamics - Import Track")

        # Make and pack "Create or Import Track" label
        label = tkinter.Label(self, text="Import Track", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Track" button
        button = tkinter.Button(self, text="Import Track", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: select_file())
        button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Track" button above.
        track_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Import Car" button
        car_button = tkinter.Button(self, text="Import Car", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: select_file(is_car_file=True))
        car_button.grid(row=3, column=1, pady=(10, 0))

        # Make and pack check label widget for "Import Car" button above.
        car_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        node_frame = tkinter.Frame(self, borderwidth=0, highlightthickness=0, bg="Black")
        node_frame.grid(row=4, column=1)

        node_label = tkinter.Label(node_frame, text="Nodes:", bg="Black", fg="White", font=("Ariel", 16), borderwidth=0, highlightthickness=0)
        node_label.grid(row=0, column=0, pady=(10,0))

        self.node_entry = tkinter.Entry(node_frame, bg="White", fg="Black", font=("Ariel", 12), width=10)
        self.node_entry.grid(row=0, column=1, pady=(10,0))

        default_label = tkinter.Label(self, text="Default: 5000 nodes.", font=("Ariel", 10), bg="Black", fg="White")
        default_label.grid(row=5, column=1, pady=(0,0))

        #  Make and pack "Run LapSim" button
        run_lapsim_button = tkinter.Button(self, text="Run LapSim", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: self.run_notgenerated_track())
        run_lapsim_button.grid(row=6, column=1, pady=(50, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)