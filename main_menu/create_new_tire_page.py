import tkinter
from tkinter import filedialog
import pickle as pkl
import os
from pathlib import Path

from tire_model import tire

cornering_check = None
acceleration_check = None

save_tire_button = None

cornering_file = None
acceleration_file = None

back_function = None

# The user selects a file and the path is stored in the appropriate variable
def select_file(is_cornering_file):
    global cornering_file, acceleration_file, cornering_check, acceleration_check, save_tire_button

    file_path = filedialog.askopenfilename(title="Select a file", initialdir="/Users/jacobmckee/Documents/Wazzu Racing/LapSim", filetypes=[("Data files", "*.dat")])
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

def save_file():

    # Create and save tire object into saved_files dir using imported files
    Tire = tire(cornering_file, acceleration_file)

    # Get path to main_menu directory
    working_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the index of the last slash in the working_dir string
    slash_index = 0
    for (index, char) in enumerate(working_dir):
        if char == "/":
            slash_index = index

    # Create path to saved_files directory and open save dialog in that directory
    lapsim_dir = working_dir[0:slash_index]
    initial_dir = os.path.join(lapsim_dir, "saved_files")
    file_path = filedialog.asksaveasfilename(title="Save Tire Object", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

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