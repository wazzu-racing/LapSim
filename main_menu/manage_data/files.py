import os
from tkinter import filedialog


# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def get_save_files_folder_abs_dir():
    # Get path to main_menu directory
    working_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the index of the second to last slash in the working_dir string
    slash_index_list = []
    for (index, char) in enumerate(working_dir):
        if char == "/":
            slash_index_list.append(index)
    second_to_last_slash = slash_index_list[len(slash_index_list)-2]

    # Create path to saved_files directory
    lapsim_dir = working_dir[0:second_to_last_slash]
    return os.path.join(lapsim_dir, "saved_files")

def get_file_from_user(self, file_types=[("Any file", "*.*")]):
    # Asks the user to choose an image file to create the track with.
    file_path = filedialog.asksaveasfilename(title="Select a place to save your file.", initialdir=self.initial_dir, filetypes=file_types)
    # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
    if file_path:
        return file_path
    else:
        print("No file selected")
        return None