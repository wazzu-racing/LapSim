import os
import sys
from tkinter import filedialog
from pathlib import Path

class FileManager:

    def __init__(self):
        self.lapsim_data_file_path = Path.home()/"Documents"/"LAPSIM"/"Data"
        self.models_file_path = self.lapsim_data_file_path/"Models"
        self.tracks_file_path = self.lapsim_data_file_path/"Tracks"

    # Returns the absolute directory of where the tracks folder is on the user's computer.
    def get_tracks_dir(self):
        return self.tracks_file_path

    # Returns the absolute directory of where the tracks folder is on the user's computer.
    def get_models_dir(self):
        return self.models_file_path

    # Opens folder window to let the user pick where they want to save their file.
    def get_file_from_user(self, file_types=[("Any file", "*.*")], default_exension=None):
        # Asks the user to choose an image file to create the track with.
        file_path = filedialog.asksaveasfilename(title="Select a place to save your file.", initialdir=self.get_tracks_dir(), filetypes=file_types, defaultextension=default_exension)
        # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
        if file_path:
            return file_path
        else:
            print("No file selected")
            return None

    # This function is used to get the relative path within the temp folder created by pyinstaller at runtime.
    def get_temp_folder_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

file_manager = FileManager()