import tkinter
from tkinter import filedialog
from tkinter import ttk
from create_new_tire_page import run_create_new_tire_page
import os
import pickle as pkl

from tire_model import tire

window = None

tire_file_path = ""

plot_button = None
dropdown = None
import_check_label = None

import_check = False

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
    global tire_file_path, plot_button

    tire_file_path = filedialog.askopenfilename(title="Open Tire File", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    if tire_file_path:
        plot_button.configure(state="normal")
        reveal_dropdown(root)
        import_check_label.grid(row=2, column=2, pady=(100, 10))
    else:
        print("No file selected")

# Function to plot tire data with functions in tire_model.py based on selected option.
def plot_tire_data(option):

    # Load tire object from file
    tire = pkl.load(open(tire_file_path, 'rb'))

    match option:
        case "Select file":
            print("No option selected")
        case "FX to Slip Ratio":
            tire.SR_FX_plot(0)
        case "FY to Slip Angle":
            tire.SA_FY_plot(0)
        case "MZ to Camber Angle 0°":
            tire.SA_MZ_plot(0)
        case "MZ to Camber Angle 2°":
            tire.SA_MZ_plot(2)
        case "MZ to Camber Angle 4°":
            tire.SA_MZ_plot(4)

def reveal_dropdown(root):
    global dropdown

    options = ["Select file", "FX to Slip Ratio", "FY to Slip Angle", "MZ to Camber Angle 0°", "MZ to Camber Angle 2°", "MZ to Camber Angle 4°"]
    dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
    dropdown.current(0)
    dropdown.grid(row=5, column=1, pady=(20, 0))

def run_import_tire_files_page(root):
    global plot_button, import_check_label, dropdown

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Plot Tire Data")

    # Make and pack "Import Tire Files" label
    label = tkinter.Label(root, text="Plot Tire Data", font=("Ariel", 48), bg="Black")
    label.grid(row=1, column=1)

    #  Make and pack "Import Saved Tire" button
    cornering_button = tkinter.Button(root, text="Import Saved Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(root))
    cornering_button.grid(row=2, column=1, pady=(100, 10))

    # Make and pack check label widget for "Import Saved Tire" button above.
    import_check_label = tkinter.Label(root, text="File imported!", bg="Black", fg="Green", )

    #  Make and pack "Import New Tire" button
    acceleration_button = tkinter.Button(root, text="Create New Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: run_create_new_tire_page(root, lambda: run_import_tire_files_page(root)))
    acceleration_button.grid(row=3, column=1, pady=(0, 10))

    #  Make and pack "Plot Data" button
    plot_button = tkinter.Button(root, text="Plot Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: plot_tire_data(dropdown.get()))
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
    root.grid_columnconfigure(4, weight=1)

    root.mainloop()