import os

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