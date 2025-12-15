import tkinter
from tkinter import filedialog
import pickle as pkl
import os

from car_settings_window import CarSettingsWindow
from files import get_save_files_folder_abs_dir
import car_model

# Absolute path to saved_files folder.
initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The "CreateNewCarPage" page.
class CreateNewCarPage(tkinter.Frame):
    def __init__(self, parent, controller):
        global aero_array_check, tire_file_check, drivetrain_file_check, save_car_button, back_function

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.car = car_model.car()

        # sets path vars to the default car
        self.tire_file_path = f"{get_save_files_folder_abs_dir()}/18x6-10_R20.pkl"
        self.drivetrain_file_path = f"{get_save_files_folder_abs_dir()}/DEFAULT_DRIVETRAIN.pkl"

        self.settings_window = CarSettingsWindow(car=self.car)

        # Make and pack "Create New Car" label
        self.label = tkinter.Label(self, text="Create New Car", font=("Ariel", 48), bg="Black", fg="White")
        self.label.grid(row=1, column=1)

        #  Make and pack "Import Tire File" button
        self.import_tire_file_button = tkinter.Button(self, text="Import Tire File", bg="White",  fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.select_file(file_type="pkl", file="tire_file"))
        self.import_tire_file_button.grid(row=2, column=1, pady=(0, 10))

        # Make check label to import Tire file
        self.tire_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Import Drivetrain File" button
        self.import_drivetrain_file_button = tkinter.Button(self, text="Import Drivetrain File", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.select_file(file_type="pkl", file="drivetrain_file"))
        self.import_drivetrain_file_button.grid(row=3, column=1, pady=(0, 0))

        # Make check label to import drivetrain file
        self.drivetrain_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        # Make and pack button to change car settings
        self.car_settings_button = tkinter.Button(self, text="Car Settings", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.settings_window.open_window())
        self.car_settings_button.grid(row=4, column=1, pady=(10, 0))

        #  Make and pack "Save Car" button
        self.save_car_button = tkinter.Button(self, text="Save Car", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: self.save_file(controller))
        self.save_car_button.grid(row=5, column=1, pady=(50, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)

    # The user selects a file to build the car with
    def select_file(self, file_type, file):
        # Get file from user
        file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("File", f"*.{file_type}")])
        # If users chosen path is not nothing
        if file_path:
            # Determines which file the user has selected to create the car with, saves it, and shows the user that it has been saved.
            match file:
                case "tire_file":
                    self.tire_file_path = file_path
                    self.tire_file_check.grid(row=2, column=2, pady=(0, 10))
                case "drivetrain_file":
                    self.drivetrain_file_path = file_path
                    self.drivetrain_file_check.grid(row=3, column=2, pady=(0, 10))

            # If user inputs all three required files, the user is able to create the car object and save it.
            if self.tire_file_path and self.drivetrain_file_path:
                self.save_car_button.configure(state="normal")

        else:
            print("No file selected")

    def set_window_settings_car_to_car(self):
        self.car = self.settings_window.car

    # Saves the car in a dir
    def save_file(self, controller):
        global initial_dir, racecar

        # Apply changes made by user to car object
        self.settings_window.apply_changes()
        self.car = self.settings_window.car

        # Create and save car object into saved_files dir using imported files after setting car_model paths equal to user selection
        self.car.aero_csv_file_path = os.path.join("Data", "csv", "DEFAULT_AERO_ARRAY.csv")
        self.car.tire_file_path = self.tire_file_path
        self.car.drivetrain_file_path = self.drivetrain_file_path

        # Ask the user where they want to save the car object
        file_path = filedialog.asksaveasfilename(title="Save Car File", initialdir=initial_dir, defaultextension=".pkl")

        if file_path:
            # saving tire object
            with open(file_path, 'wb') as f:
                pkl.dump(self.car, f)

        self.reset_page()

        # Close the create new tire window and go back to the import tire files page
        controller.go_back()

    def reset_page(self):
        # Reset data vars
        self.tire_file_path = ""
        self.drivetrain_file_path = ""
        self.car = car_model.car()
        self.settings_window.change_vars_to_car(self.car)

        # Reset UI
        self.tire_file_check.grid_forget()
        self.drivetrain_file_check.grid_forget()
        self.save_car_button.configure(state="disabled")