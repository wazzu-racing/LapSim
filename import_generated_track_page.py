import tkinter
from tkinter import filedialog

from display_trk import DisplayTrack
from files import get_save_files_folder_abs_dir

display_lap_button = None

generated_track_file = ""
generated_track_check = None

initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

def select_file(is_car_file=False):
    global display_lap_button, generated_track_file,generated_track_check, initial_dir

    # Asks the user to choose a pkl file to display the track object with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("Pickle files", "*.pkl")])
    # if the file_path is not nothing, the track file is saved and the track object can be displayed.
    if file_path:
        generated_track_file = file_path
        generated_track_check.grid(row=2, column=2, pady=(100, 0))
        display_lap_button.configure(state="normal")
    else:
        print("No file selected")

class ImportGeneratedTrackPage(tkinter.Frame):

    def __init__(self, parent, controller):
        global display_lap_button, generated_track_check

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Import Generated Track")

        # Make and pack "Import Generated Track"  label
        label = tkinter.Label(self, text="Import Track", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Generated Track" button
        button = tkinter.Button(self, text="Import Generated Track", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: select_file())
        button.grid(row=2, column=1, pady=(100, 0))

        # Make and pack check label widget for "Import Generated Track" button above.
        generated_track_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Run LapSim" button
        display_lap_button = tkinter.Button(self, text="Run LapSim", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: DisplayTrack(self, gen_track_file=generated_track_file))
        display_lap_button.grid(row=3, column=1, pady=(100, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)
