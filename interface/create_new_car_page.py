import tkinter
from tkinter import filedialog
import pickle as pkl
import os
from pathlib import Path

from car_settings_window import CarSettingsWindow
from interface.file_management.file_manager import file_manager
from models import car_model


# The "CreateNewCarPage" page.
class CreateNewCarPage(tkinter.Frame):
    def __init__(self, parent, controller):
        global aero_array_check, tire_file_check, drivetrain_file_check, save_car_button, back_function

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.car = car_model.Car(False)

        # sets path vars to the default car
        self.tire_file_path = ""
        self.drivetrain_file_path = ""

        self.settings_window = CarSettingsWindow(car=self.car)

        # Make and pack "Create New Car" label
        self.label = tkinter.Label(self, text="Create New Car", font=("Ariel", 48), bg="Black", fg="White")
        self.label.grid(row=1, column=1)

        #  Make and pack "Import Tire File" button
        self.import_tire_file_button = tkinter.Button(self, text="Import Tire File", bg="White",  fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.select_file(file_type="pkl", file="tire_file"))
        self.import_tire_file_button.grid(row=2, column=1, pady=(0, 10))

        # Make check label to import Tire file
        self.tire_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        #  Make and pack "Import Drivetrain File" button
        self.import_drivetrain_file_button = tkinter.Button(self, text="Import Drivetrain File", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.select_file(file_type="pkl", file="drivetrain_file"))
        self.import_drivetrain_file_button.grid(row=3, column=1, pady=(0, 0))

        # Make check label to import drivetrain file
        self.drivetrain_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        # Make and pack button to change car settings
        self.car_settings_button = tkinter.Button(self, text="Car Settings", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.settings_window.open_window())
        self.car_settings_button.grid(row=4, column=1, pady=(10, 0))

        # Creates and grids a new frame for the node-related widgets.
        self.resolution_frame = tkinter.Frame(self, borderwidth=0, highlightthickness=0, bg="Black")
        self.resolution_frame.grid(row=5, column=1)

        self.resolution_label = tkinter.Label(self.resolution_frame, text="Resolution:", bg="Black", fg="White", font=("Ariel", 16),
                                        borderwidth=0, highlightthickness=0)
        self.resolution_label.grid(row=0, column=0, pady=(10, 0))

        self.resolution_entry = tkinter.Entry(self.resolution_frame, bg="White", fg="Black", font=("Ariel", 12), width=10)
        self.resolution_entry.grid(row=0, column=1, pady=(10, 0))

        self.default_label = tkinter.Label(self, text="Default: 50", font=("Ariel", 10), bg="Black",
                                           fg="White")
        self.default_label.grid(row=6, column=1, pady=(0, 0))

        #  Make and pack "Save Car" button
        self.save_car_button = tkinter.Button(self, text="Save Car", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="active", command=lambda: self.save_file(controller))
        self.save_car_button.grid(row=7, column=1, pady=(50, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=0)
        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)

    # The user selects a file to build the car with
    def select_file(self, file_type, file):
        # Determines which file the user has selected to create the car with, saves it, and shows the user that it has been saved.
        match file:
            case "tire_file":
                # Get file from user
                file_path = filedialog.askopenfilename(title="Select a file", initialdir=file_manager.get_models_dir(), filetypes=[("File", f"*.{file_type}")])
                if file_path:
                    self.tire_file_path = file_path
                    self.tire_file_check.grid(row=2, column=2, pady=(0, 10))
            case "drivetrain_file":
                # Get file from user
                file_path = filedialog.askopenfilename(title="Select a file", initialdir=file_manager.get_models_dir(), filetypes=[("File", f"*.{file_type}")])
                if file_path:
                    self.drivetrain_file_path = file_path
                    self.drivetrain_file_check.grid(row=3, column=2, pady=(0, 10))

        # If user inputs all three required files, the user is able to create the car object and save it.
        if self.tire_file_path and self.drivetrain_file_path:
            self.save_car_button.configure(state="normal")

    # Set the car var in this class instance to the car variable within the CarSettingsWindow instance.
    def set_window_settings_car_to_car(self):
        self.car = self.settings_window.car

    # Saves the car in a dir
    def save_file(self, controller):

        # Apply changes made by user to car object
        self.settings_window.apply_changes(car=self.car, resolution=int(self.resolution_entry.get()))
        self.car = self.settings_window.car

        # Create and save car object into saved_files dir using imported files after setting car_model paths equal to user selection
        self.aero_csv_file_path = file_manager.get_temp_folder_path(
            os.path.join(Path(__file__).resolve().parent.parent, "config_data", "DEFAULT_AERO_ARRAY.csv"))
        self.car.tire_file_path = self.tire_file_path
        self.car.drivetrain_file_path = self.drivetrain_file_path

        # Ask the user where they want to save the car object
        file_path = filedialog.asksaveasfilename(title="Save Car File", initialdir=file_manager.get_models_dir(), defaultextension=".pkl")

        if file_path:
            # saving car object
            with open(file_path, 'wb') as f:
                pkl.dump(self.car, f)

        self.reset_page()

        # Close the create new car window and go back a page
        controller.go_back()

    def reset_page(self):
        # Reset data vars
        self.tire_file_path = ""
        self.drivetrain_file_path = ""
        self.car = car_model.Car(False)
        self.settings_window.change_vars_to_car(self.car)

        # Reset UI
        self.tire_file_check.grid_forget()
        self.drivetrain_file_check.grid_forget()
        self.save_car_button.configure(state="disabled")