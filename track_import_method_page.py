import tkinter


class TrackImportMethodPage(tkinter.Frame):

    def __init__(self, parent, controller):
        # Init to initialize itself as a Frame
        super().__init__(parent)

        controller.title("Vehicle Dynamics - Choose Track Import Method")

        # Make and pack "Choose Track Import Method" label
        label = tkinter.Label(self, text="Choose Track Import Method", font=("Ariel", 48), bg="Black")
        label.grid(row=1, column=1)

        #  Make and pack "Import Generated Track" button
        button = tkinter.Button(self, text="Import Generated Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("ImportGeneratedTrackPage"))
        button.grid(row=2, column=1, pady=(100, 10))

        #  Make and pack "Import Not Generated Track" button
        car_button = tkinter.Button(self, text="Import Not Generated Track", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("ImportNotGeneratedTrackPage"))
        car_button.grid(row=3, column=1, pady=(10, 100))

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
