import os

# Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
def get_save_files_folder_abs_dir():
    # Get path to main_menu directory
    working_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the index of the last slash in the working_dir string
    slash_index = 0
    for (index, char) in enumerate(working_dir):
        if char == "/":
            slash_index = index

    # Create path to saved_files directory
    lapsim_dir = working_dir[0:slash_index]
    return os.path.join(lapsim_dir, "saved_files")