import tkinter
from tkinter import filedialog

from lapsim_go_crazy import LapSimGoCrazy

class ImportTrackImagePage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        self.plot_button = None

        self.image_file = ""
        self.image_check = None

        # Initiate LapSimGoCrazy var
        self.lapsim_go_crazy = None

        # Make and pack "Import Image" label
        label = tkinter.Label(self, text="Import Track Image", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1)

        #  Make and pack "Import Image" button
        button = tkinter.Button(self, text="Import Image", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: self.select_file())
        button.grid(row=2, column=1, pady=(100, 10))

        # Make and pack check label widget for "Import Image" button above.
        self.image_check = tkinter.Label(self, text="File imported!", bg="Black", fg="SpringGreen2")

        #  Make and pack "Plot Track" button
        self.plot_button = tkinter.Button(self, text="Plot Track", bg="White",  fg="Black", highlightbackground="Black", font=("Ariel", 24), state="disabled", command=lambda: self.run_lapsim_go_crazy())
        self.plot_button.grid(row=3, column=1, pady=(100, 0))

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

    def run_lapsim_go_crazy(self):
        if self.lapsim_go_crazy is None:
            self.lapsim_go_crazy = LapSimGoCrazy(image_path=self.image_file)
        elif self.lapsim_go_crazy is not None and self.image_file != self.lapsim_go_crazy.image_path_saved:
            self.lapsim_go_crazy.go_crazy_root.destroy()
            self.lapsim_go_crazy = LapSimGoCrazy(image_path=self.image_file)
        self.lapsim_go_crazy.open_window()

    def select_file(self):
        # Asks the user to choose an image file to create the track with.
        file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("Image files", ("*.png","*.jpg","*.jpeg"))])
        # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
        if file_path: # Activate the plot button if a file has been selected.
            self.image_file = file_path
            self.image_check.grid(row=2, column=2, pady=(100, 10))
            self.plot_button.configure(state="normal")
        elif self.image_file != "": # If image file was imported, Activate the plot button.
            if not self.image_check.grid_info():
                self.image_check.grid(row=2, column=2, pady=(100, 10))
            self.plot_button.configure(state="normal")
        else:
            print("No file selected")