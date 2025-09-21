import tkinter
from tkinter import filedialog

display_track_button = None

def select_file(is_cornering_file):
    global cornering_file, acceleration_file, cornering_check, acceleration_check, save_tire_button, initial_dir

    # Asks the user to choose a dat file to create the tire object with.
    file_path = filedialog.askopenfilename(title="Select a file", initialdir=initial_dir, filetypes=[("Data files", "*.dat")])
    # if the file_path is not nothing, the cornering/acceleration file is saved and the user is alerted that it is saved.
    if file_path:
        cornering_file = file_path
        cornering_check.grid(row=2, column=2, pady=(100, 10))
        save_tire_button.configure(state="normal")
    else:
        print("No file selected")

class ImportTrackPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Import Track")

        # Make and pack "Create or Import Track" label
        label = tkinter.Label(self, text="Import Track", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1, pady=0)

        #  Make and pack "Import Track" button
        button = tkinter.Button(self, text="Import Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page(""))
        button.grid(row=3, column=1, pady=(0, 10))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
