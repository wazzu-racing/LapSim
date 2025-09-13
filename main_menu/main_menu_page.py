import os
import tkinter
from PIL import Image, ImageTk

from main_menu.manage_data_page import run_manage_data_page

# For testing and debugging purposes, set this to True if running the main menu page
# Set to False when running another page from this file
running_from_main = True

root = tkinter.Tk()
root.geometry("1000x500")
root.configure(bg="Black")

def run_main_menu_main():
    # Set window title
    root.title("Vehicle Dynamics - Main Menu")

    # Get the directory of relative path to images
    dir_path = os.path.dirname(os.path.realpath(__file__))
    image_path = os.path.join(dir_path, "images", "wazzu_racing_logo.PNG")

    # Create and pack the Wazzu Racing image
    pil_image = Image.open(image_path)
    tk_image = ImageTk.PhotoImage(pil_image)

    image_label = tkinter.Label(root, image=tk_image, bg="Black")
    image_label.pack(pady=(100, 0))

    # Make and pack "Vehicle Dynamics" label
    label = tkinter.Label(root, text="Vehicle Dynamics", font=("Ariel", 48), bg="Black")
    label.pack(pady=0)

    #  Make and pack "Manage Data" button
    button = tkinter.Button(root, text="Manage Data", bg="Black", highlightbackground="Black", font=("Ariel", 24), command=lambda: run_manage_data_page(root))
    button.pack(pady=(50, 10))

    #  Make and pack "LapSim" button
    button = tkinter.Button(root, text="LapSim", bg="Black", highlightbackground="Black", font=("Ariel", 24))
    button.pack(pady=0)

    # Start the Tkinter event loop
    root.mainloop()

# if running main menu directly, run the main menu
if running_from_main:
    run_main_menu_main()

# if running another page (for testing), run that page
if not running_from_main:
    import_tire_files_page.run_import_tire_files_page(root)