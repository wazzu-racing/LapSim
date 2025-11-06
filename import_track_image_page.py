import tkinter
from tkinter import filedialog

from lapsim_go_crazy import LapSimGoCrazy
from files import get_save_files_folder_abs_dir

plot_button = None

image_file = ""
image_check = None

initial_dir = ""

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def set_initial_dir():
    global initial_dir

    initial_dir = get_save_files_folder_abs_dir()

set_initial_dir()

def select_file():
    global image_file, image_check, plot_button, initial_dir

    # Asks the user to choose an image file to create the track with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("Image files", ("*.png","*.jpg","*.jpeg"))])
    # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
    if file_path:
        # enable plot button if file is selected
        image_file = file_path
        image_check.grid(row=2, column=2, pady=(100, 10))
        plot_button.configure(state="normal")
    else:
        print("No file selected")

class ImportTrackImagePage(tkinter.Frame):

    def __init__(self, parent, controller):
        global plot_button, image_file, image_check

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Import Track Image")

        # Make and pack "Import Image" label
        label = tkinter.Label(self, text="Import Track Image", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Image" button
        button = tkinter.Button(self, text="Import Image", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: select_file())
        button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Image" button above.
        image_check = tkinter.Label(self, text="File imported!", bg="Black", fg="Green")

        #  Make and pack "Plot Track" button
        plot_button = tkinter.Button(self, text="Plot Track", bg="White",  fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: LapSimGoCrazy(image_path=image_file))
        plot_button.grid(row=3, column=1, pady=(100, 0))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)
