import tkinter
from tkinter import filedialog
import pickle as pkl

from main_menu.files import get_save_files_folder_abs_dir
from car_model import car
import car_model

car_file_check = None
tire_file_check = None
drivetrain_file_check = None

# sets path vars to the default car
aero_array_file_path = f"{get_save_files_folder_abs_dir()}/aero_array.csv"
tire_file_path = f"{get_save_files_folder_abs_dir()}/18x6-10_R20.pkl"
drivetrain_file_path = f"{get_save_files_folder_abs_dir()}/drivetrain.pkl"

save_car_button = None

initial_dir = ""

back_function = None

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The user selects a file to build the car with
def select_file(file_type, file):
    global aero_array_file_path, tire_file_path, drivetrain_file_path, car_file_check, tire_file_check, drivetrain_file_check, save_car_button

    # Get file from user
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("File", f"*.{file_type}")])
    # If users chosen path is not nothing
    if file_path:
        # Determines which file the user has selected to create the car with, saves it, and shows the user that it has been saved.
        match file:
            case "aero_array":
                aero_array_file_path = file_path
                aero_array_check.grid(row=2, column=2, pady=(100, 10))
            case "tire_file":
                tire_file_path = file_path
                tire_file_check.grid(row=3, column=2, pady=(0, 10))
            case "drivetrain_file":
                drivetrain_file_path = file_path
                drivetrain_file_check.grid(row=4, column=2, pady=(0, 10))

        # If user inputs all three required files, the user is able to create the car object and save it.
        if aero_array_file_path and tire_file_path and drivetrain_file_path:
            save_car_button.configure(state="normal")

    else:
        print("No file selected")

# Saves the car in a dir
def save_file():
    global aero_array_file_path, initial_dir

    # Create and save car object into saved_files dir using imported files after setting car_model paths equal to user selection
    car_model.aero_csv_file_path = aero_array_file_path
    car_model.tire_file_path = tire_file_path
    car_model.drivetrain_file_path = drivetrain_file_path

    racecar = car()

    # Ask the user where they want to save the car object
    file_path = filedialog.asksaveasfilename(title="Save Car File", initialdir=initial_dir, defaultextension=".pkl")

    if file_path:
        # saving tire object
        with open(file_path, 'wb') as f:
            pkl.dump(racecar, f)

    # Close the create new tire window and go back to the import tire files page
    back_function()

def run_create_new_car_page(root, function):
    global car_file_check, tire_file_check, drivetrain_file_check, save_car_button, back_function

    back_function = function

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Create New Car")

    # Make and pack "Create New Car" label
    label = tkinter.Label(root, text="Create New Car", font=("Ariel", 48), bg="Black")
    label.grid(row=1, column=1)

    #  Make and pack "Import Aero Array Data" button
    import_aero_array_button = tkinter.Button(root, text="Import Aero Array Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(file_type="csv", file="aero_array"))
    import_aero_array_button.grid(row=2, column=1, pady=(100, 10))

    # Make and pack check label to import aero array data
    aero_array_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Import Tire File" button
    import_tire_file_button = tkinter.Button(root, text="Import Tire File", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(file_type="pkl", file="tire_file"))
    import_tire_file_button.grid(row=3, column=1, pady=(0, 10))

    # Make and pack check label to import Tire file
    tire_file_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Import Drivetrain File" button
    import_drivetrain_file_button = tkinter.Button(root, text="Import Drivetrain File", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(file_type="pkl", file="drivetrain_file"))
    import_drivetrain_file_button.grid(row=4, column=1, pady=(0, 0))

    # Make and pack check label to import drivetrain file
    drivetrain_file_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Save Car" button
    save_car_button = tkinter.Button(root, text="Save Car", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: save_file())
    save_car_button.grid(row=5, column=1, pady=(100, 0))

    # Configure grid to center all widgets
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=0)
    root.grid_rowconfigure(4, weight=0)
    root.grid_rowconfigure(5, weight=0)
    root.grid_rowconfigure(6, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=0)
    root.grid_columnconfigure(3, weight=1)

    root.mainloop()