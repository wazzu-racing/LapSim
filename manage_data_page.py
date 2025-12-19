import tkinter

class ManageDataPage(tkinter.Frame):

    def __init__(self, parent, controller):

        # Init to initialize itself as a Frame
        super().__init__(parent)

        # Make and pack "Manage Data" label
        label = tkinter.Label(self, text="Manage Data", font=("Ariel", 48), bg="Black", fg="White")
        label.grid(row=1, column=1, pady=0)

        #  Make and pack "Create a New Model" button
        button = tkinter.Button(self, text="Create a New Model", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("CreateNewCarPage"))
        button.grid(row=2, column=1, pady=(50, 5))

        #  Make and pack "Plot Data" button
        button = tkinter.Button(self, text="Plot Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("PlotDataPage"))
        button.grid(row=3, column=1, pady=(0, 10))

        # Configure grid to center all widgets
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
