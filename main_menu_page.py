import os
import tkinter
import matplotlib as mat

from PIL import Image, ImageTk

from import_track_image_page import ImportTrackImagePage
from import_track_page import ImportTrackPage
from loading_window import LoadingWindow
from create_new_car_page import CreateNewCarPage
from manage_data_page import ManageDataPage
from manage_tracks_page import ManageTracksPage
from plot_car_data_page import PlotCarDataPage
from plot_data_page import PlotDataPage
from plot_drivetrain_data_page import PlotDrivetrainDataPage

import platform

from plot_tire_data_page import PlotTireDataPage


# PageStack holds all the Frames that hold the widgets for each page.
class PageStack(tkinter.Tk):
    def __init__(self):
        # Init to initxialize itself as a Tk
        super().__init__()

        # Make sure that plots open in a new window and not in the tkinter window.
        mat.use('TkAgg')

        # Basic setup
        self.title("LAPSIM")
        self.geometry("1000x500")
        self.configure(bg="Black")

        # Create a container frame for each page
        container = tkinter.Frame(self, bg="Black")
        container.pack(expand=True)

        # Stores all pages available in the LAPSIM
        self.pages = (MainMenuPage, ManageDataPage, PlotDataPage, PlotDrivetrainDataPage, PlotCarDataPage, PlotTireDataPage, CreateNewCarPage, ManageTracksPage, ImportTrackPage, ImportTrackImagePage)
        # Stores the current page as a string
        self.current_page = "MainMenuPage"
        # Stores the page hierarchy that the user is current at.
        self.page_history = []

        # stores the pages
        self.frames = {}
        for F in self.pages:
            # Basic Setup for each page
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            frame.configure(bg="Black")
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.kill_window)

        # If the user right clicks or presses the escape key, the previous page is raised to the top of PageStack
        self.bind("<Escape>", self.go_back)
        # Mac has a different right-click bind than Windows and Linux
        if platform.system() == "Darwin":
            self.bind("<ButtonPress-2>", self.go_back)
        else:
            self.bind("<ButtonPress-3>", self.go_back)

        self.protocol("WM_DELETE_WINDOW", self.kill_window)

    # Forces the window to close when the user presses X in the upper right corner.
    def kill_window(self):
        self.destroy()
        os._exit(0)

    # Raises the frame that corresponds with the page_name to the top of PageStack
    def go_to_page(self, page_name):
        # raise the frame selected by inputting a page_name string
        frame = self.frames[page_name]
        frame.tkraise()
        self.current_page = page_name
        self.page_history.append(page_name)

    # Go back to the previous page
    def go_back(self, event=None):     # Since binding go_back requires it to take in an event parameter, go_back must have an event parameter.
        # Check to make sure that there are pages to go back to.
        if len(self.page_history) > 1:
            # lower the current frame to show previous frame
            frame = self.frames[self.current_page]
            frame.lower()
            # Remove page that user just backed out of from page_history then set current page to the new page the user is on.
            self.page_history.pop()
            self.current_page = self.page_history[-1]

# The "MainMenuPage" page.
class MainMenuPage(tkinter.Frame):
    def __init__(self, parent, controller):
        # Init to initialize itself as a Frame
        super().__init__(parent)

        # Get the directory of relative path to images
        image_path = "Images/wazzu_racing_logo.PNG"

        # Create and pack the Wazzu Racing image
        pil_image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(master=self, image=pil_image)

        image_label = tkinter.Label(self, image=self.tk_image, bg="Black")
        image_label.grid(row=1, column=1, pady=(0, 0))

        # Make and pack "Vehicle Dynamics" label
        label = tkinter.Label(self, text="LAPSIM", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=2, column=1, pady=(0, 20))

        # Make and pack "LapSim" button
        button = tkinter.Button(self, text="Run LapSim", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("ImportTrackPage"))
        button.grid(row=3, column=1, pady=0)

        # Make and pack "Manage Data" button
        button = tkinter.Button(self, text="Manage Tracks", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("ManageTracksPage"))
        button.grid(row=4, column=1, pady=(5, 0))

        # Make and pack "Manage Data" button
        button = tkinter.Button(self, text="Manage Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("ManageDataPage"))
        button.grid(row=5, column=1, pady=(5, 0))

        advanced_label = tkinter.Label(self, text="(ADVANCED)", fg="red", bg = "black", font=("Ariel", 12))
        advanced_label.grid(row=6, column=1, pady=(0, 0))

        version_frame = tkinter.Frame(self, bg="Black")
        version_frame.grid(row=7, column=1, pady=(0, 0))

        version_label = tkinter.Label(version_frame, text="v1 (2026.0.0)", fg="white", bg = "black")
        version_label.grid(row=0, column=0, pady=(100, 0), padx=(0, 800), sticky="se")

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=0)
        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)