from pydoc import safeimport

from main_menu.lapsim import spline_track as spln
import pickle

from main_menu.lapsim.lapsim_go_crazy import bind_go_crazy_keys
from main_menu.manage_data.files import get_file_from_user, get_save_files_folder_abs_dir

class DisplayTrack:

    def __init__(self, frame, pts_file=None, cr_file=None, gen_track_file=None):

        self.trk = None

        # Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
        self.initial_dir = get_save_files_folder_abs_dir()

        if not gen_track_file and pts_file and cr_file:
            print("[Generating Track...]")

            # loading points
            with open(pts_file, 'rb') as f:
                points = pickle.load(f)

            with open(cr_file, 'rb') as f:
                car = pickle.load(f)

            # defining different points
            points_x = points['p1x']
            points_y = points['p1y']
            points_x2 = points['p2x']
            points_y2 = points['p2y']

            # creating track object
            self.trk = spln.track(points_x, points_y, points_x2, points_y2)
            print(self.trk.get_cost())

            #run sim to get data
            self.trk.run_sim(car)

            self.trk.plot(self.save_track) # displaying unoptimized track

            # optimizing track
            self.trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

            self.trk.plot(self.save_track) # displaying optimized track
        elif gen_track_file:
            with open(gen_track_file, 'rb') as f:
                track = pickle.load(f)
            track.plot(self.save_track)

    def save_track(self):
        print("[Saving Track...]")
        file = get_file_from_user(self, file_types=[("Pickle files", "*.pkl")])
        if file:
            with open(file, 'wb') as f:
                pickle.dump(obj=self.trk, file=f)