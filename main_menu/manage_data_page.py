import tkinter

from main_menu.plot_data_page import run_plot_data_page


def run_manage_data_page(root):
    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Vehicle Dynamics - Manage Data")
    
    # Make and pack "Manage Data" label
    label = tkinter.Label(root, text="Manage Data", font=("Ariel", 48), bg="Black")
    label.pack(pady=0)

    #  Make and pack "Plot Data" button
    button = tkinter.Button(root, text="Plot Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: run_plot_data_page(root))
    button.pack(pady=(50, 10))

    root.mainloop()