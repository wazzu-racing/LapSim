import tkinter
from tkinter import filedialog
import pickle as pkl
import os

from main_menu.files import get_save_files_folder_abs_dir
from tire_model import tire

cornering_check = None
acceleration_check = None

save_tire_button = None

cornering_file = None
acceleration_file = None

back_function = None

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
def save_file():
    global cornering_file, acceleration_file

    # Create and save tire object into saved_files dir using imported files
    Tire = tire(cornering_file, acceleration_file)

    file_path = filedialog.asksaveasfilename(title="Save Tire Object", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    if file_path:
        # saving tire object
        with open(file_path, 'wb') as f:
            pkl.dump(Tire, f)

    # Close the create new tire window and go back to the import tire files page
    back_function()

def run_create_new_tire_page(root, function):
    global cornering_check, acceleration_check, save_tire_button, cornering_file, acceleration_file, back_function

    back_function = function

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Create New Tire")

    # Make and pack "Create New Tire" label
    label = tkinter.Label(root, text="Create New Tire", font=("Ariel", 48), bg="Black")
    label.grid(row=1, column=1)

    #  Make and pack "Import Cornering Data" button
    cornering_button = tkinter.Button(root, text="Import Cornering Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(
        is_cornering_file=True))
    cornering_button.grid(row=2, column=1, pady=(100, 10))

    # Make and pack check button to import cornering data
    cornering_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green", )

    #  Make and pack "Import Acceleration Data" button
    acceleration_button = tkinter.Button(root, text="Import Acceleration Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(
        is_cornering_file=False))
    acceleration_button.grid(row=3, column=1, pady=(0, 10))

    # Make and pack check button to import acceleration data
    acceleration_check = tkinter.Label(root,text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Plot Data" button
    save_tire_button = tkinter.Button(root, text="Save Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: save_file())
    save_tire_button.grid(row=4, column=1, pady=(100, 0))

    # Configure grid to center all widgets
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=0)
    root.grid_rowconfigure(4, weight=0)
    root.grid_rowconfigure(5, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=0)
    root.grid_columnconfigure(4, weight=1)

    root.mainloop()