import spline_track as spln
import pickle

from car_model import car
from lapsim import lapsim_data_storage

from files import get_file_from_user, get_save_files_folder_abs_dir

# racecar = car()
# with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Models/CAR_73.pkl", "wb") as f:
#     pickle.dump(racecar, f)

class DisplayTrack:

    def __init__(self, frame, pts_file=None, cr_file=None, gen_track_file=None, nodes = 5000):

        print("[Displaying Track...]")

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
            try: # try-except to account for different point storage formats (this first one is the newer format)
                points_x = points['p1x']
                points_y = points['p1y']
                points_x2 = points['p2x']
                points_y2 = points['p2y']
            except TypeError: # Older format - not in use anymore but kept for backwards compatibility
                points_x = []
                points_y = []
                points_x2 = []
                points_y2 = []
                for i in points.nds:
                    points_x.append(i.x1)
                    points_y.append(i.y1)
                    points_x2.append(i.x2)
                    points_y2.append(i.y2)

            # creating track object
            self.trk = spln.track(points_x, points_y, points_x2, points_y2)

            #run sim to get data
            self.trk.run_sim(car, nodes=nodes)

            # optimizing track
            if len(points_x) > 10:
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