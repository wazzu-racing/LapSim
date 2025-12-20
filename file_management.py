import os
from tkinter import filedialog
from pathlib import Path
import pickle

import drivetrain_model
import tire_model
from LapData import LapData
from car_model import car

class FileManager:

    def __init__(self):
        self.lapsim_data_file_path = Path.home()/"Documents"/"LAPSIM"/"Data"
        self.models_file_path = self.lapsim_data_file_path/"Models"
        self.tracks_file_path = self.lapsim_data_file_path/"Tracks"
        self.track_images_file_path = self.lapsim_data_file_path/"Track Images"

    def create_LAPSIM_folder_in_documents(self):
        # If the path already exists, stop running this function.
        if Path.exists(self.lapsim_data_file_path):
            return

        # Create folder directories in user's Documents folder.
        os.makedirs(self.lapsim_data_file_path, exist_ok=True)
        os.makedirs(self.models_file_path, exist_ok=True)
        os.makedirs(self.tracks_file_path, exist_ok=True)

        # Create tire model and put into user's documents folder.
        cornering_data = os.path.join("config_data", "cornering_data.dat")
        accel_data = os.path.join("config_data", "acceleration_data.dat")
        tires = tire_model.tire(cornering_data, accel_data)
        with open(os.path.join(self.models_file_path, "HOOSIER_18(18x6-10_R20).pkl"), 'wb') as f:
            pickle.dump(tires, f)

        # Create drivetrain model and put into user's documents folder.
        drivetrain = drivetrain_model.drivetrain(engine_data=os.path.join("config_data", "engine_array.csv"))
        with open(os.path.join(self.models_file_path, "DEFAULT_DRIVETRAIN(CBR_650).pkl"), 'wb') as f:
            pickle.dump(drivetrain, f)

        # Create car model and put into user's documents folder.
        racecar = car()
        with open(os.path.join(self.models_file_path, "CAR_73.pkl"), 'wb') as f:
            pickle.dump(racecar, f)

        # Create LapData files and put into user's documents folder.
        # Acceleration track
        with open(os.path.join("config_data", "track_points", "acceleration_trk_points.pkl"), "rb") as f:
            points = pickle.load(f)
            accel_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Acceleration_Track.pkl"), "wb") as fi:
                pickle.dump(accel_lap_data, fi)
        # Autocross track
        with open(os.path.join("config_data", "track_points", "autocross_trk_points.pkl"), "rb") as f:
            points = pickle.load(f)
            autocross_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Autocross_Track.pkl"), "wb") as fi:
                pickle.dump(autocross_lap_data, fi)
        # Endurance track
        with open(os.path.join("config_data", "track_points", "endurance_trk_points.pkl"), "rb") as f:
            points = pickle.load(f)
            endurance_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Endurance_Track.pkl"), "wb") as fi:
                pickle.dump(endurance_lap_data, fi)
        # Skidpad track
        with open(os.path.join("config_data", "track_points", "skidpad_trk_points.pkl"), "rb") as f:
            points = pickle.load(f)
            skidpad_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Skidpad_Track.pkl"), "wb") as fi:
                pickle.dump(skidpad_lap_data, fi)

        # If the files were not created successfully, then run this function again.
        if not self.files_written_successfully():
            print("Failed to write files, running again...")
            self.create_LAPSIM_folder_in_documents()

    def files_written_successfully(self):
        if not Path(os.path.join(self.models_file_path, "HOOSIER_18(18x6-10_R20).pkl")).exists():
            return False
        elif not Path(os.path.join(self.models_file_path, "DEFAULT_DRIVETRAIN(CBR_650).pkl")).exists():
            return False
        elif not Path(os.path.join(self.models_file_path, "CAR_73.pkl")).exists():
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Acceleration_Track.pkl")).exists():
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Autocross_Track.pkl")).exists():
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Endurance_Track.pkl")).exists():
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Skidpad_Track.pkl")).exists():
            return False
        return True


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

file_manager = FileManager()