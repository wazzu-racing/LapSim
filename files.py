import os
from tkinter import filedialog


# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def get_save_files_folder_abs_dir():
    return os.path.join(os.getcwd(), "Data")

# Opens folder window to let the user pick where they want to save their file.
def get_file_from_user(self, file_types=[("Any file", "*.*")], default_exension=None):
    # Asks the user to choose an image file to create the track with.
    file_path = filedialog.asksaveasfilename(title="Select a place to save your file.", initialdir=self.initial_dir, filetypes=file_types, defaultextension=default_exension)
    # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
    if file_path:
        return file_path
    else:
        print("No file selected")
        return None