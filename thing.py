import pickle

from LapData import LapData

with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/acceleration_trk.pkl", "rb") as f:
    points = pickle.load(f)
    new_track_data = LapData(points)
    with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/acceleration_trk.pkl", "wb") as p:
        pickle.dump(new_track_data, p)

with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/autocross_trk.pkl", "rb") as j:
    points_2 = pickle.load(j)
    new_track_data = LapData(points_2)
    with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/autocross_trk.pkl", "wb") as p:
        pickle.dump(new_track_data, p)

with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/endurance_trk.pkl", "rb") as f:
    points_3 = pickle.load(f)
    new_track_data = LapData(points_3)
    with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/endurance_trk.pkl", "wb") as p:
        pickle.dump(new_track_data, p)

with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/skidpad_trk.pkl", "rb") as f:
    points_4 = pickle.load(f)
    new_track_data = LapData(points_4)
    with open("/Users/jacobmckee/Documents/Wazzu Racing/Vehicle Dynamics/Repos/LapSimWindowsFix/Data/pkl/Tracks/skidpad_trk.pkl", "wb") as p:
        pickle.dump(new_track_data, p)