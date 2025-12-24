import tkinter
from tkinter import filedialog
from tkinter import ttk
import pickle as pkl

from file_management.file_manager import file_manager

class PlotDrivetrainDataPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        # Widget that is gridded once the user inputs the correct file
        self.drivetrain_file_check = None

        # Widget that lets the user graph the data
        self.plot_button = None

        # Widget that appears once the user has selected the correct files
        self.dropdown = None

        # The file path of the drivetrain object used to make the graphs. Selected by the user.
        self.drivetrain_file_path = ""

        # Make and pack "Plot Drivetrain Data" label
        label = tkinter.Label(self, text="Plot Drivetrain Data", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Saved Drivetrain" button
        engine_array_button = tkinter.Button(self, text="Import Drivetrain", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: self.select_file(self))
        engine_array_button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Saved Engine" button above.
        self.drivetrain_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        #  Make and pack "Plot Data" button
        self.plot_button = tkinter.Button(self, text="Plot Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: self.plot_drivetrain_data(self.dropdown.get()))
        self.plot_button.grid(row=4, column=1, pady=(100, 0))

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

    # The user selects a file and the path is stored in the appropriate variable
    def select_file(self, root):
        # Open file dialog to select drivetrain file
        self.drivetrain_file_path = filedialog.askopenfilename(title="Open Drivetrain File", initialdir=file_manager.get_models_dir(), defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

        # If the path that the user chooses is not empty, then allow the user to plot data.
        if self.drivetrain_file_path:
            self.plot_button.configure(state="normal")
            self.reveal_dropdown(root)
            self.drivetrain_file_check.grid(row=2, column=2, pady=(100, 10))
        else:
            print("No file selected")

    # Function to plot drivetrain data with functions in drivetrain_model.py based on selected option.
    def plot_drivetrain_data(self, option):
        # Load drivetrain object from file
        drivetrain = pkl.load(open(self.drivetrain_file_path, 'rb'))

        # Match the users choice of graph with the graph's corresponding function.
        match option:
            case "Select graph":
                print("No option selected")
            case "Engine RPM to Engine Power Graph":
                drivetrain.engn_rpm_pwr_plot()

    # Function to reveal the dropdown menu to select graphs after a file has been successfully imported
    def reveal_dropdown(self, root):
        options = ["Select graph", "Engine RPM to Engine Power Graph"]
        self.dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
        self.dropdown.current(0)
        self.dropdown.grid(row=5, column=1, pady=(20, 0))