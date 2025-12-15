import tkinter

class PlotDataPage(tkinter.Frame):

    def __init__(self, parent, controller):
        # Init to initialize itself as a Frame
        super().__init__(parent)

        # Make and pack "Plot Data" label
        label = tkinter.Label(self, text="Plot Data", font=("Ariel", 48), bg="Black", fg="White")
        label.pack(pady=0)

        #  Make and pack "Plot Tire Data" button
        button = tkinter.Button(self, text="Plot Tire Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: controller.go_to_page("PlotTireDataPage"))
        button.pack(pady=(50, 10))

        #  Make and pack "Plot Drivetrain Data" button
        button = tkinter.Button(self, text="Plot Drivetrain Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("PlotDrivetrainDataPage"))
        button.pack(pady=(0, 10))

        #  Make and pack "Plot Car Data" button
        button = tkinter.Button(self, text="Plot Car Data", bg="White", fg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: controller.go_to_page("PlotCarDataPage"))
        button.pack(pady=(0, 0))

