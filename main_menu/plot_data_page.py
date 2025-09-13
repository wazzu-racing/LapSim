import tkinter

from main_menu.plot_car_data_page import run_plot_car_data_page
from main_menu.plot_drivetrain_data_page import run_plot_drivetrain_data_page
from main_menu.plot_tire_data_page import run_import_tire_files_page

def run_plot_data_page(root):
    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Plot Data")

    # Make and pack "Plot Data" label
    label = tkinter.Label(root, text="Plot Data", font=("Ariel", 48), bg="Black")
    label.pack(pady=0)

    #  Make and pack "Plot Tire Data" button
    button = tkinter.Button(root, text="Plot Tire Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: run_import_tire_files_page(root))
    button.pack(pady=(50, 10))

    #  Make and pack "Plot Drivetrain Data" button
    button = tkinter.Button(root, text="Plot Drivetrain Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: run_plot_drivetrain_data_page(root))
    button.pack(pady=(0, 10))

    #  Make and pack "Plot Car Data" button
    button = tkinter.Button(root, text="Plot Car Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command= lambda: run_plot_car_data_page(root))
    button.pack(pady=(0, 0))

    root.mainloop()