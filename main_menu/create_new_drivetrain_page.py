import tkinter
from tkinter import filedialog
import pickle as pkl
import os

from drivetrain_model import drivetrain
from main_menu.files import get_save_files_folder_abs_dir

drivetrain_file_check = None
engine_array_file_path = ""

save_drivetrain_button = None

initial_dir = ""

back_function = None

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The user selects a file and the path is stored in the appropriate variable
def select_file():
    global engine_array_file_path, drivetrain_file_check, save_drivetrain_button

    # Asks the user to point to a csv file to create the drivetrain with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("CSV files", "*.csv")])
    # If file_path is not nothing, the file is saved, the user is shown that it has been saved, and they can create the drivetrain.
    if file_path:
        engine_array_file_path = file_path
        engine_array_check.grid(row=2, column=2, pady=(100, 10))
        save_drivetrain_button.configure(state="normal")
    else:
        print("No file selected")

# Saves the drivetrain in a dir
def save_file():
    global engine_array_file_path, initial_dir

    # Create and save tire object into saved_files dir using imported files
    train = drivetrain(engine_data=engine_array_file_path)

    # Ask the user where they want to store the drivetrain object
    file_path = filedialog.asksaveasfilename(title="Save Drivetrain File", initialdir=initial_dir, defaultextension=".pkl")

    if file_path:
        # saving tire object
        with open(file_path, 'wb') as f:
            pkl.dump(train, f)

    # Close the create new tire window and go back to the import tire files page
    back_function()

def run_create_new_drivetrain_page(root, function):
    global drivetrain_file_check, save_drivetrain_button, engine_array_file_path, back_function

    back_function = function

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Create New Drivetrain")

    # Make and pack "Create New Drivetrain" label
    label = tkinter.Label(root, text="Create New Drivetrain", font=("Ariel", 48), bg="Black")
    label.grid(row=1, column=1)

    #  Make and pack "Import Engine Array Data" button
    import_engine_array_button = tkinter.Button(root, text="Import Engine Array Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file())
    import_engine_array_button.grid(row=2, column=1, pady=(100, 10))

    # Make and pack check label to import engine array data
    engine_array_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Save Drivetrain" button
    save_drivetrain_button = tkinter.Button(root, text="Save Drivetrain", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: save_file())
    save_drivetrain_button.grid(row=3, column=1, pady=(100, 0))

    # Configure grid to center all widgets
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=0)
    root.grid_rowconfigure(4, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=0)
    root.grid_columnconfigure(3, weight=1)

    root.mainloop()