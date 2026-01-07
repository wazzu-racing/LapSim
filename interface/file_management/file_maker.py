import os
from pathlib import Path
import pickle

import numpy as np

from gen_lapsim.spline_track import node
from gen_lapsim.spline_track import track
from models import tire_model, drivetrain_model
from interface.LapData import LapData
from .file_manager import file_manager
from models.car_model import Car

class FileMaker:

    def __init__(self):
        self.project_root_dir = Path(__file__).resolve().parent.parent.parent

        self.lapsim_data_file_path = Path.home()/"Documents"/"LAPSIM"/"Data"
        self.models_file_path = self.lapsim_data_file_path/"Models"
        self.tracks_file_path = self.lapsim_data_file_path/"Tracks"

    def create_LAPSIM_folder_in_documents(self):
        # If the path already exists, stop running this function.
        if Path.exists(self.lapsim_data_file_path):
            return

        # Create pickle files that store the nodes of the autocross and endurance tracks using .rtf files.
        self.create_track_pickle(txt_path=file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "Points for Autocross.rtf")), pkl_path=file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "autocross_trk_points.pkl")), is_autocross=True)
        self.create_track_pickle(txt_path=file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "Points for Endurance.rtf")), pkl_path=file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "endurance_trk_points.pkl")), is_autocross=False)

        # Create folder directories in user's Documents folder.
        os.makedirs(self.lapsim_data_file_path, exist_ok=True)
        os.makedirs(self.models_file_path, exist_ok=True)
        os.makedirs(self.tracks_file_path, exist_ok=True)

        # Create tire model and put into user's documents folder.
        cornering_data = file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "cornering_data.dat"))
        accel_data = file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "acceleration_data.dat"))
        tires = tire_model.tire(cornering_data, accel_data)
        with open(os.path.join(self.models_file_path, "HOOSIER_18(18x6-10_R20).pkl"), 'wb') as f:
            pickle.dump(tires, f)

        # Create drivetrain model and put into user's documents folder.
        engine_data = file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "engine_array.csv"))
        drivetrain = drivetrain_model.drivetrain(engine_data=engine_data)
        with open(os.path.join(self.models_file_path, "DEFAULT_DRIVETRAIN(CBR_650).pkl"), 'wb') as f:
            pickle.dump(drivetrain, f)

        # Create car model and put into user's documents folder.
        racecar = Car(tire_path=os.path.join(self.models_file_path, "HOOSIER_18(18x6-10_R20).pkl"), drivetrain_path=os.path.join(self.models_file_path, "DEFAULT_DRIVETRAIN(CBR_650).pkl"))
        print("reached")
        with open(os.path.join(self.models_file_path, "CAR_73.pkl"), 'wb') as f:
            pickle.dump(racecar, f)

        # Create LapData files and put into user's documents folder.
        # Acceleration track
        with open(file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "acceleration_trk_points.pkl")), "rb") as f:
            points = pickle.load(f)
            accel_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Acceleration_Track.pkl"), "wb") as fi:
                pickle.dump(accel_lap_data, fi)
        # Autocross track
        with open(file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "autocross_trk_points.pkl")), "rb") as f:
            points = pickle.load(f)
            autocross_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Autocross_Track.pkl"), "wb") as fi:
                pickle.dump(autocross_lap_data, fi)
        # Endurance track
        with open(file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "endurance_trk_points.pkl")), "rb") as f:
            points = pickle.load(f)
            endurance_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Endurance_Track.pkl"), "wb") as fi:
                pickle.dump(endurance_lap_data, fi)
        # Skidpad track
        with open(file_manager.get_temp_folder_path(os.path.join(self.project_root_dir, "config_data", "track_points", "skidpad_trk_points.pkl")), "rb") as f:
            points = pickle.load(f)
            skidpad_lap_data = LapData(points)
            with open(os.path.join(self.tracks_file_path, "Skidpad_Track.pkl"), "wb") as fi:
                pickle.dump(skidpad_lap_data, fi)

        # If the files were not created successfully, then run this function again.
        if not self.files_written_successfully():
            print("Failed to write files, running again...")
            self.create_LAPSIM_folder_in_documents()

    # Checks if the files were written correctly by checking each individual file.
    def files_written_successfully(self):
        if not Path(os.path.join(self.models_file_path, "HOOSIER_18(18x6-10_R20).pkl")).exists():
            print("Failed to write HOOSIER_18(18x6-10_R20).pkl")
            return False
        elif not Path(os.path.join(self.models_file_path, "DEFAULT_DRIVETRAIN(CBR_650).pkl")).exists():
            print("Failed to write DEFAULT_DRIVETRAIN(CBR_650).pkl")
            return False
        elif not Path(os.path.join(self.models_file_path, "CAR_73.pkl")).exists():
            print("Failed to write CAR_73.pkl")
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Acceleration_Track.pkl")).exists():
            print("Failed to write Acceleration_Track.pkl")
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Autocross_Track.pkl")).exists():
            print("Failed to write Autocross_Track.pkl")
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Endurance_Track.pkl")).exists():
            print("Failed to write Endurance_Track.pkl")
            return False
        elif not Path(os.path.join(self.tracks_file_path, "Skidpad_Track.pkl")).exists():
            print("Failed to write Skidpad_Track.pkl")
            return False
        return True

    # Purpose of this class is to create pickles for autocross and endurance
    class points:
        def __init__ (self):
            self.nds = []

    def create_track_pickle(self, txt_path, pkl_path, is_autocross):
        points_arr = [np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType()), np.array([], dtype=np.dtypes.StringDType())]

        arr_done_index = 0

        with open(txt_path, "r") as f:
            content = f.read()
        curr_num = ""
        writing = False
        for char in content:
            if char == '[':
                writing = True
            elif char == ']' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
                arr_done_index += 1
                writing = False
            elif char == ',' and writing:
                points_arr[arr_done_index] = np.append(points_arr[arr_done_index], curr_num)
                curr_num = ""
            elif char != " " and writing:
                curr_num += char

        points_x = points_arr[0].astype(float)
        points_y = points_arr[1].astype(float)
        points_x2 = points_arr[2].astype(float)
        points_y2 = points_arr[3].astype(float)

        track = self.points()

        rang = 97 if is_autocross else 129
        for i in range(rang):
            n = node(points_x[i], points_y[i], points_x2[i], points_y2[i])
            track.nds.append(n)

        with open(pkl_path, "wb") as f:
            pickle.dump(track, f)


file_maker = FileMaker()

# racecar = Car()
#
# print(f"Total runtime: {racecar.end - racecar.start} seconds")
#
# with open(file_manager.get_temp_folder_path(os.path.join(Path(__file__).resolve().parent.parent.parent, "config_data", "track_points", "autocross_trk_points.pkl")), "rb") as f:
#     points_trk = pickle.load(f)
#
# points_x = []
# points_y = []
# points_x2 = []
# points_y2 = []
# for node in points_trk.nds:
#     points_x.append(node.x1)
#     points_y.append(node.y1)
#     points_x2.append(node.x2)
#     points_y2.append(node.y2)
#
# track = track(points_x, points_y, points_x2, points_y2, racecar)
# track.adjust_track([40, 30, 30, 80],[100, 30, 10, 5])
# track.run_sim(racecar)