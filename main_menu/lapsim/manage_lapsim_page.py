import tkinter

from main_menu.lapsim.create_import_track_page import CreateImportTrackPage


class ManageLapSimPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Manage LapSim")

        # Make and pack "Manage LapSim" label
        label = tkinter.Label(self, text="Manage LapSim", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1, pady=0)

        #  Make and pack "Create Track" button
        button = tkinter.Button(self, text="Create Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("CreateImportTrackPage"))
        button.grid(row=2, column=1, pady=(50, 10))

        #  Make and pack "Display Track" button
        button = tkinter.Button(self, text="Display Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: ())
        button.grid(row=3, column=1, pady=(0, 10))

        #  Make and pack "Run LapSim" button
        button = tkinter.Button(self, text="Run LapSim", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: ())
        button.grid(row=4, column=1, pady=(0, 10))

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
