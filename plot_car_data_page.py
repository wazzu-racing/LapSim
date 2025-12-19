import tkinter
from tkinter import filedialog
from tkinter import ttk
import pickle as pkl

from files import get_models_abs_dir

# Widget that is gridded once the user inputs the correct file
car_file_check = None

# Widget that lets the user graph the data
plot_button = None

# Widget that appears once the user has selected the correct files
dropdown = None

# The file path of the car object used to make the graphs. Selected by the user.
car_file_path = ""

# The user selects a file and the path is stored in the appropriate variable
def select_file(root):
    global car_file_path, car_file_check, plot_button

    # Open file dialog to select car file
    car_file_path = filedialog.askopenfilename(title="Open Car File", initialdir=get_models_abs_dir(), defaultextension=".pkl", filetypes=[("Pickle files", "*.pkl")])

    # If the path that the user chooses is not empty, then allow the user to plot data.
    if car_file_path:
        plot_button.configure(state="normal")
        reveal_dropdown(root)
        car_file_check.grid(row=2, column=2, pady=(100, 10))
    else:
        print("No file selected")

# Function to plot car data with functions in car_model.py based on selected option.
def plot_car_data(option):
    global car_file_path

    # Load car object from file
    car = pkl.load(open(car_file_path, 'rb'))
    car.file_location = car_file_path

    # Match the users choice of graph with the graph's corresponding function.
    match option:
        case "Select graph":
            print("No option selected")
        case "Axial acceleration to Lateral acceleration":
            car.traction_curve()

# Function to reveal the dropdown menu to select graphs after a file has been successfully imported
def reveal_dropdown(root):
    global dropdown

    options = ["Select graph", "Axial acceleration to Lateral acceleration"]
    dropdown = ttk.Combobox(root, values=options, font=("Ariel", 24), state="readonly")
    dropdown.current(0)
    dropdown.grid(row=5, column=1, pady=(20, 0))

class PlotCarDataPage(tkinter.Frame):

    def __init__(self, parent, controller):
        global car_file_check, plot_button, dropdown

        # Init to initialize itself as a Frame
        super().__init__(parent)

        # Make and pack "Plot Car Data" label
        label = tkinter.Label(self, text="Plot Car Data", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Saved Car" button
        engine_array_button = tkinter.Button(self, text="Import Car", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: select_file(self))
        engine_array_button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Saved Car" button above.
        car_file_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        #  Make and pack "Plot Data" button
        plot_button = tkinter.Button(self, text="Plot Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: plot_car_data(dropdown.get()))
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