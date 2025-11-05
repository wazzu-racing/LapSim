import tkinter
from tkinter import filedialog
from tkinter import ttk
import pickle as pkl

from files import get_save_files_folder_abs_dir

# Widget that is gridded once the user inputs the correct file
tire_file_check = None

# Widget that lets the user graph the data
plot_button = None

# Widget that appears once the user has selected the correct files
dropdown = None

# The file path of the tire object used to make the graphs. Selected by the user.
tire_file_path = ""

# Absolute path to saved_files folder.
initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The user selects a file and the path is stored in the appropriate variable
def select_file(root):
    global tire_file_path, plot_button

    # Open file dialog to select tire file
    tire_file_path = filedialog.askopenfilename(title="Open Tire File", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    # If the path that the user chooses is not empty, then allow the user to plot data.
    if tire_file_path:
        plot_button.configure(state="normal")
        reveal_dropdown(root)
        tire_file_check.grid(row=2, column=2, pady=(100, 10))
    else:
        print("No file selected")

# Function to plot tire data with functions in tire_model.py based on selected option.
def plot_tire_data(option):

    # Load tire object from file
    tire = pkl.load(open(tire_file_path, 'rb'))

    # Match the users choice of graph with the graph's corresponding function.
    match option:
        case "Select graph":
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

    options = ["Select graph", "FX to Slip Ratio", "FY to Slip Angle", "MZ to Camber Angle 0°", "MZ to Camber Angle 2°", "MZ to Camber Angle 4°"]
    dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
    dropdown.current(0)
    dropdown.grid(row=5, column=1, pady=(20, 0))

class PlotTireDataPage(tkinter.Frame):

    def __init__(self, parent, controller):
        global plot_button, tire_file_check, dropdown

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Plot Tire Data")

        # Make and pack "Import Tire Files" label
        label = tkinter.Label(self, text="Plot Tire Data", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1)

        #  Make and pack "Import Saved Tire" button
        cornering_button = tkinter.Button(self, text="Import Saved Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(self))
        cornering_button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Saved Tire" button above.
        tire_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green", )

        #  Make and pack "Import New Tire" button
        acceleration_button = tkinter.Button(self, text="Create New Tire", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("CreateNewTirePage"))
        acceleration_button.grid(row=3, column=1, pady=(0, 10))

        #  Make and pack "Plot Data" button
        plot_button = tkinter.Button(self, text="Plot Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: plot_tire_data(dropdown.get()))
        plot_button.grid(row=4, column=1, pady=(100, 0))

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
        self.grid_columnconfigure(4, weight=1)