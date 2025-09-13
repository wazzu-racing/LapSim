import tkinter
from tkinter import filedialog
from tkinter import ttk
import os
import pickle as pkl

from main_menu.create_new_drivetrain_page import run_create_new_drivetrain_page

engine_array_check = None
plot_button = None
dropdown = None

drivetrain_file_path = ""

initial_dir = ""

def set_initial_dir():
    global initial_dir

    # Get path to main_menu directory
    working_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the index of the last slash in the working_dir string
    slash_index = 0
    for (index, char) in enumerate(working_dir):
        if char == "/":
            slash_index = index

    # Create path to saved_files directory
    lapsim_dir = working_dir[0:slash_index]
    initial_dir = os.path.join(lapsim_dir, "saved_files")

set_initial_dir()

# The user selects a file and the path is stored in the appropriate variable
def select_file(root):
    global drivetrain_file_path, engine_array_check, plot_button

    # Open file dialog to select drivetrain file
    drivetrain_file_path = filedialog.askopenfilename(title="Open Drivetrain File", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    if drivetrain_file_path:
        plot_button.configure(state="normal")
        reveal_dropdown(root)
        engine_array_check.grid(row=2, column=2, pady=(100, 10))
    else:
        print("No file selected")

# Function to plot drivetrain data with functions in drivetrain_model.py based on selected option.
def plot_drivetrain_data(option):
    global drivetrain_file_path

    # Load tire object from file
    drivetrain = pkl.load(open(drivetrain_file_path, 'rb'))

    match option:
        case "Select file":
            print("No option selected")
        case "Engine RPM to Engine Power Graph":
            drivetrain.engn_rpm_pwr_plot()

# Function to reveal the dropdown menu to select graphs after a file has been successfully imported
def reveal_dropdown(root):
    global dropdown

    options = ["Select file", "Engine RPM to Engine Power Graph"]
    dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
    dropdown.current(0)
    dropdown.grid(row=5, column=1, pady=(20, 0))

def run_plot_drivetrain_data_page(root):
    global engine_array_check, plot_button, dropdown

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Plot Drivetrain Data")

    # Make and pack "Plot Drivetrain Data" label
    label = tkinter.Label(root, text="Plot Drivetrain Data", font=("Ariel", 48), bg="Black")
    label.grid(row=1, column=1)

    #  Make and pack "Import Saved Engine" button
    engine_array_button = tkinter.Button(root, text="Import Saved Engine", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(root))
    engine_array_button.grid(row=2, column=1, pady=(100, 10))

    # Make and pack check label widget for "Import Saved Engine" button above.
    engine_array_check = tkinter.Label(root, text="File imported!", bg="Black", fg="Green")

    #  Make and pack "Create New Engine" button
    engine_array_button = tkinter.Button(root, text="Create New Engine", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: run_create_new_drivetrain_page(root, lambda: run_plot_drivetrain_data_page(root)))
    engine_array_button.grid(row=3, column=1, pady=(0, 10))

    #  Make and pack "Plot Data" button
    plot_button = tkinter.Button(root, text="Plot Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: plot_drivetrain_data(dropdown.get()))
    plot_button.grid(row=4, column=1, pady=(100, 0))

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