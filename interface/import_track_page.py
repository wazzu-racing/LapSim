import tkinter
from tkinter import filedialog
import pickle

from display_trk import DisplayTrack
from interface.file_management.file_manager import file_manager
from gen_lapsim.spline_track import LapSimUI

class ImportTrackPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.track_file = ""
        self.car_file = ""

        self.controller = controller

        # Will be set later
        self.lap_data = None

        # Will be set later
        self.display_track = None

        # Run LapSimUI to initialize base UI elements like track_root, track_canvas, etc.
        self.ui = LapSimUI(
            self.display_track)

        # Make and pack "Create or Import Track" label
        self.label = tkinter.Label(self, text="Import Track", font=("Ariel", 48), bg="Black", fg="White")
        self.label.grid(row=1, column=1)

        # Make and pack "Import Track" button
        self.button = tkinter.Button(self, text="Import Track", bg="White", fg="Black", highlightbackground="Black",
                                     font=("Ariel", 24), command=lambda: self.select_file(is_car_file=False))
        self.button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Track" button above.
        self.track_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

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

    # Prompt the user to select either a track file or a car file from their computer.
    def select_file(self, is_car_file=False):

        if self.track_check is None:
            self.initialize_first_widgets()

        if is_car_file:
            # Asks the user to choose a car file to create the LapData object with.
            file_path = filedialog.askopenfilename(title="Select a file", initialdir=file_manager.get_models_dir(),
                                                   filetypes=[("Pickle files", "*.pkl")])
        else:
            # Asks the user to choose a track file to create the LapData object with.
            file_path = filedialog.askopenfilename(title="Select a file", initialdir=file_manager.get_tracks_dir(),
                                                   filetypes=[("Pickle files", "*.pkl")])

        # if the file_path is not nothing, the car/track file is saved and the user is used to make the track object.
        if file_path:
            # Store the file path in the appropriate variable and show that the file has been imported
            if not is_car_file:
                # Load track data file
                with open(file_path, "rb") as f:
                    self.lap_data = pickle.load(f)
                self.lap_data.file_location = file_path  # save file path

                # if the track data file contains a generated track
                if self.lap_data.generated_track is not None:
                    self.show_run_lapsim_button()
                # if the track data file does not contain a generated track, allow user to import a car in order to generate track
                else:
                    self.show_import_car_widgets()

                # Make sure LapSimUI has the right lap_data var
                self.ui.lap_data = self.lap_data

                self.track_check.grid(row=2, column=2, pady=(100, 10))
            # Store the file path in the appropriate variable and show that the file has been imported
            else:
                self.car_file = file_path
                self.car_check.grid(row=3, column=2, pady=(0, 0))
                # save car into lap_data file
                car = pickle.load(open(self.car_file, "rb"))
                self.lap_data.car = car  # save car into lap_data file
                self.lap_data.car.file_location = self.car_file
            # Enable plot button if both files are selected
            if self.car_file and self.lap_data:
                self.show_run_lapsim_button()
        else:
            print("No file selected")

    # Shows the widgets associated with importing a car.
    def show_import_car_widgets(self):
        #  Make and pack "Import Car" button
        self.car_button = tkinter.Button(self, text="Import Car", bg="White", fg="Black", highlightbackground="Black",
                                         font=("Ariel", 24), command=lambda: self.select_file(is_car_file=True))
        self.car_button.grid(row=3, column=1, pady=(10, 0))

        # Make and pack check label widget for "Import Car" button above.
        self.car_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        # Creates and grids a new frame for the node-related widgets.
        self.node_frame = tkinter.Frame(self, borderwidth=0, highlightthickness=0, bg="Black")
        self.node_frame.grid(row=4, column=1)

        self.node_label = tkinter.Label(self.node_frame, text="Nodes:", bg="Black", fg="White", font=("Ariel", 16),
                                        borderwidth=0, highlightthickness=0)
        self.node_label.grid(row=0, column=0, pady=(10, 0))

        self.node_entry = tkinter.Entry(self.node_frame, bg="White", fg="Black", font=("Ariel", 12), width=10)
        self.node_entry.grid(row=0, column=1, pady=(10, 0))

        self.default_label = tkinter.Label(self, text="Default: 5000 nodes.", font=("Ariel", 10), bg="Black",
                                           fg="White")
        self.default_label.grid(row=5, column=1, pady=(0, 0))

    # Show the button that allows the user to run the lapsim.
    def show_run_lapsim_button(self):
        #  Make and pack "Run LapSim" button
        self.run_lapsim_button = tkinter.Button(self, text="Run LapSim", bg="White", fg="Black",
                                                highlightbackground="Black", font=("Ariel", 24),
                                                command=lambda: self.run_track())
        self.run_lapsim_button.grid(row=6, column=1, pady=(50, 0))

    # Reset everything in the window so there is no need to destroy the window then make it again.
    def reset_page(self):
        # Reset vars for data
        self.track_file = ""
        self.car_file = ""

        # Reset UI
        self.track_check.grid_forget()
        self.run_lapsim_button.grid_forget()
        try:
            self.car_button.grid_forget()
            self.car_check.grid_forget()
            self.node_frame.grid_forget()
            self.default_label.grid_forget()
        except Exception:
            pass

    # Create a DisplayTrack instance that will generate and/or show the track.
    def run_track(self):
        # If there is not already a display_track instance, create one.
        if self.display_track is None and self.lap_data.generated_track is None:
            self.display_track = DisplayTrack(ui_instance=self.ui, controller=self.controller,
                                              nodes=int(self.node_entry.get()) if self.node_entry.get() and int(
                                                  self.node_entry.get()) > 9 else 5000)
        elif self.display_track is None and self.lap_data.generated_track is not None:
            self.display_track = DisplayTrack(ui_instance=self.ui, controller=self.controller, nodes=self.lap_data.generated_track.sim.n)
        elif self.display_track is not None and self.lap_data.generated_track is None:
            self.display_track.nodes = int(self.node_entry.get()) if self.node_entry.get() and int(
                self.node_entry.get()) > 9 else 5000

        # Reset the page to minimize bugs
        self.reset_page()

        # load track and data that user selected
        self.display_track.run_lap_data(self.display_track, self.lap_data)
