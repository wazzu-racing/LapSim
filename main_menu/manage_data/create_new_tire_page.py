import tkinter
from tkinter import filedialog
import pickle as pkl

from main_menu.manage_data.files import get_save_files_folder_abs_dir
from tire_model import tire

# Widgets that are gridded once the user inputs the correct file
cornering_check = None
acceleration_check = None

# Widget that lets the user save the tire object
save_tire_button = None

# file paths that are used to create the new tire object.
cornering_file = ""
acceleration_file = ""

# Absolute path to saved_files folder.
initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The user selects a file and the path is stored in the appropriate variable
def select_file(is_cornering_file):
    global cornering_file, acceleration_file, cornering_check, acceleration_check, save_tire_button, initial_dir

    # Asks the user to choose a dat file to create the tire object with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("Data files", "*.dat")])
    # if the file_path is not nothing, the cornering/acceleration file is saved and the user is alerted that it is saved.
    if file_path:
        # Store the file path in the appropriate variable and show that the file has been imported
        if is_cornering_file:
            cornering_file = file_path
            cornering_check.grid(row=2, column=2, pady=(100, 10))
        # Store the file path in the appropriate variable and show that the file has been imported
        else:
            acceleration_file = file_path
            acceleration_check.grid(row=3, column=2, pady=(0, 0))
        # Enable plot button if both files are selected
        if cornering_file and acceleration_file:
            save_tire_button.configure(state="normal")
    else:
        print("No file selected")

# Saves the tire in a dir
def save_file(controller):
    global cornering_file, acceleration_file

    # Create and save tire object into saved_files dir using imported files
    Tire = tire(cornering_file, acceleration_file)

    # Ask the user where they want to store the tire object
    file_path = filedialog.asksaveasfilename(title="Save Tire Object", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    if file_path:
        # saving tire object
        with open(file_path, 'wb') as f:
            pkl.dump(Tire, f)

    # Close the create new tire window and go back to the plot tire data page
    controller.go_back()

class CreateNewTirePage(tkinter.Frame):

    def __init__(self, parent, controller):
        global cornering_check, acceleration_check, save_tire_button, cornering_file, acceleration_file

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Create New Tire")

        # Make and pack "Create New Tire" label
        label = tkinter.Label(self, text="Create New Tire", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1)

        #  Make and pack "Import Cornering Data" button
        cornering_button = tkinter.Button(self, text="Import Cornering Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(
            is_cornering_file=True))
        cornering_button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check button to import cornering data
        cornering_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green", )

        #  Make and pack "Import Acceleration Data" button
        acceleration_button = tkinter.Button(self, text="Import Acceleration Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(
            is_cornering_file=False))
        acceleration_button.grid(row=3, column=1, pady=(0, 10))

        # Make and pack check button to import acceleration data
        acceleration_check = tkinter.Label(self,text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Plot Data" button
        save_tire_button = tkinter.Button(self, text="Save Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: save_file(controller))
        save_tire_button.grid(row=4, column=1, pady=(100, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(4, weight=1)