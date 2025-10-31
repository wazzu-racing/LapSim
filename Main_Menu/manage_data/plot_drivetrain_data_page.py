import tkinter
from tkinter import filedialog
from tkinter import ttk
import pickle as pkl

from Main_Menu.manage_data.files import get_save_files_folder_abs_dir

# Widget that is gridded once the user inputs the correct file
drivetrain_file_check = None

# Widget that lets the user graph the data
plot_button = None

# Widget that appears once the user has selected the correct files
dropdown = None

# The file path of the drivetrain object used to make the graphs. Selected by the user.
drivetrain_file_path = ""

# Absolute path to saved_files folder.
initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

# The user selects a file and the path is stored in the appropriate variable
def select_file(root):
    global drivetrain_file_path, drivetrain_file_check, plot_button

    # Open file dialog to select drivetrain file
    drivetrain_file_path = filedialog.askopenfilename(title="Open Drivetrain File", initialdir=initial_dir, defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    # If the path that the user chooses is not empty, then allow the user to plot data.
    if drivetrain_file_path:
        plot_button.configure(state="normal")
        reveal_dropdown(root)
        drivetrain_file_check.grid(row=2, column=2, pady=(100, 10))
    else:
        print("No file selected")

# Function to plot drivetrain data with functions in drivetrain_model.py based on selected option.
def plot_drivetrain_data(option):
    global drivetrain_file_path

    # Load drivetrain object from file
    drivetrain = pkl.load(open(drivetrain_file_path, 'rb'))

    # Match the users choice of graph with the graph's corresponding function.
    match option:
        case "Select graph":
            print("No option selected")
        case "Engine RPM to Engine Power Graph":
            drivetrain.engn_rpm_pwr_plot()

# Function to reveal the dropdown menu to select graphs after a file has been successfully imported
def reveal_dropdown(root):
    global dropdown

    options = ["Select graph", "Engine RPM to Engine Power Graph"]
    dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
    dropdown.current(0)
    dropdown.grid(row=5, column=1, pady=(20, 0))

class PlotDrivetrainDataPage(tkinter.Frame):

    def __init__(self, parent, controller):
        global drivetrain_file_check, plot_button, dropdown

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Plot Drivetrain Data")

        # Make and pack "Plot Drivetrain Data" label
        label = tkinter.Label(self, text="Plot Drivetrain Data", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1)

        #  Make and pack "Import Saved Drivetrain" button
        engine_array_button = tkinter.Button(self, text="Import Saved Drivetrain", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(self))
        engine_array_button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Saved Engine" button above.
        drivetrain_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Create New Drivetrain" button
        engine_array_button = tkinter.Button(self, text="Create New Drivetrain", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("CreateNewDrivetrainPage"))
        engine_array_button.grid(row=3, column=1, pady=(0, 10))

        #  Make and pack "Plot Data" button
        plot_button = tkinter.Button(self, text="Plot Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: plot_drivetrain_data(dropdown.get()))
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
        self.grid_columnconfigure(3, weight=1)