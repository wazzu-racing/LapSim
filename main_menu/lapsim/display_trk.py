import spline_track as spln
import pickle

car_file = '/Users/jacobmckee/Documents/Wazzu Racing/LapSim/saved_files/car.pkl'

points_file = '/Users/jacobmckee/Documents/Wazzu Racing/LapSim/autocross_pts.pkl'

save_file = '/Users/jacobmckee/Documents/Wazzu Racing/LapSim/autocross_trk.pkl'

# loading points
with open(points_file, 'rb') as f:
    points = pickle.load(f)

with open(car_file, 'rb') as f:
    car = pickle.load(f)

# defining different points
points_x = points['p1x']
points_y = points['p1y']
points_x2 = points['p2x']
points_y2 = points['p2y']


# creating track object
trk = spln.track(points_x, points_y, points_x2, points_y2)
print(trk.get_cost())

#run sim to get data
trk.run_sim(car, end=89)

trk.plot() # displaying unoptimized track

# optimizing track
trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

trk.plot() # displaying optimized track

# saving track. Type 'y' to save, 'n' to discard
txt_input = ''
while (txt_input != 'y') and (txt_input != 'n'):
    txt_input = input('save track?: ')
if txt_input == 'y':
    with open(save_file, 'wb') as f:
        pickle.dump(trk, f)
    print('[Track Saved.]')
else:
    print('[Track Discarded.]')