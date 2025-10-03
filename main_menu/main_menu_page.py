import os
import tkinter
from doctest import master

from PIL import Image, ImageTk

from main_menu.lapsim.import_track_image_page import ImportTrackImagePage
from main_menu.lapsim.import_track_page import ImportTrackPage
from main_menu.lapsim.manage_lapsim_page import ManageLapSimPage
from main_menu.manage_data.create_new_car_page import CreateNewCarPage
from main_menu.manage_data.create_new_drivetrain_page import CreateNewDrivetrainPage
from main_menu.manage_data.create_new_tire_page import CreateNewTirePage
from main_menu.manage_data.manage_data_page import ManageDataPage
from main_menu.manage_data.plot_car_data_page import PlotCarDataPage
from main_menu.manage_data.plot_data_page import PlotDataPage
from main_menu.manage_data.plot_drivetrain_data_page import PlotDrivetrainDataPage
from main_menu.manage_data.plot_tire_data_page import PlotTireDataPage

# PageStack holds all the Frames that hold the widgets for each page.
class PageStack(tkinter.Tk):
    def __init__(self):
        # Init to initialize itself as a Tk
        super().__init__()

        # Basic setup
        self.title("Vehicle Dynamics - Main Menu")
        self.geometry("1000x500")
        self.configure(bg="Black")

        # Create a container frame for each page
        container = tkinter.Frame(self)
        container.pack(expand=True)

        # Stores the current page as a string
        self.current_page = "MainMenuPage"
        # Stores the page hierarchy that the user is current at.
        self.page_history = []

        # stores the pages
        self.frames = {}
        for F in (MainMenuPage, ManageDataPage, PlotDataPage, PlotTireDataPage, PlotDrivetrainDataPage, PlotCarDataPage, CreateNewTirePage, CreateNewDrivetrainPage, CreateNewCarPage, ManageLapSimPage, ImportTrackPage, ImportTrackImagePage):
            # Basic Setup for each page
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            frame.configure(bg="Black")
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # If the user right clicks or presses the escape key, the previous page is raised to the top of PageStack
        self.bind("<ButtonPress-2>", self.go_back)
        self.bind("<Escape>", self.go_back)

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

        # Set window title
        controller.title("Vehicle Dynamics - Main Menu")

        # Get the directory of relative path to images
        dir_path = os.path.dirname(os.path.realpath(__file__))
        image_path = os.path.join(dir_path, "images", "wazzu_racing_logo.PNG")

        # Create and pack the Wazzu Racing image
        pil_image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(master=self, image=pil_image)

        image_label = tkinter.Label(self, image=self.tk_image, bg="Black")
        image_label.grid(row=1, column=1, pady=(0, 0))

        # Make and pack "Vehicle Dynamics" label
        label = tkinter.Label(self, text="Vehicle Dynamics", font=("Ariel", 48), bg="Black")
        label.grid(row=2, column=1, pady=0)

        # Make and pack "Manage Data" button
        button = tkinter.Button(self, text="Manage Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("ManageDataPage"))
        button.grid(row=3, column=1, pady=(50, 10))

        # Make and pack "LapSim" button
        button = tkinter.Button(self, text="LapSim", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("ManageLapSimPage"))
        button.grid(row=4, column=1, pady=0)

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

page_stack = PageStack()
page_stack.go_to_page("MainMenuPage")
page_stack.mainloop()