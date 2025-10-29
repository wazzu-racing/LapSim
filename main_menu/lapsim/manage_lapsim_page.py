import pickle
import tkinter
from tkinter import filedialog

import car_model
from main_menu.lapsim.lapsim_go_crazy import LapSimGoCrazy
from main_menu.manage_data.files import get_save_files_folder_abs_dir

class ManageLapSimPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.initial_dir = ""

        # Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
        self.initial_dir = get_save_files_folder_abs_dir()

        controller.title("Vehicle Dynamics - Manage LapSim")

        # Make and pack "Manage LapSim" label
        label = tkinter.Label(self, text="Manage LapSim", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1, pady=0)

        #  Make and pack "Create Track" button
        button = tkinter.Button(self, text="Create Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: (controller.go_to_page("ImportTrackImagePage")))
        button.grid(row=2, column=1, pady=(50, 10))

        #  Make and pack "Edit Track" button
        button = tkinter.Button(self, text="Edit Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: self.run_lapsim_go_crazy())
        button.grid(row=3, column=1, pady=(0, 10))

        #  Make and pack "Run LapSim" button
        button = tkinter.Button(self, text="Run LapSim", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("TrackImportMethodPage"))
        button.grid(row=4, column=1, pady=(0, 10))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

    def run_lapsim_go_crazy(self):
        track_file = self.get_file_from_user()
        if track_file is not None:
            LapSimGoCrazy(track_file=track_file)

    def get_file_from_user(self):
        # Asks the user to choose an image file to create the track with.
        file_path = filedialog.askopenfilename(title="Select the track", initialdir=self.initial_dir, filetypes=[("Pickle files", "*.pkl")])
        # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
        if file_path:
            return file_path
        else:
            print("No file selected")
            return None