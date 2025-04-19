import numpy as np
from matplotlib import pyplot as plt
import spline_track as spln
import pickle

with open('C:\\Users\\nbogd\\OneDrive\\Documents\\lapsim stuff - Copy\\trck.pkl', 'rb') as f:
    points = pickle.load(f)

points_x = points['p1x']
points_y = points['p1y']
points_x2 = points['p2x']
points_y2 = points['p2y']


trk = spln.track(points_x, points_y, points_x2, points_y2)
print(trk.get_cost())
for i in range(len(points_x)):
    plt.plot(points_x[i], points_y[i], marker='o') 
    plt.plot(points_x2[i], points_y2[i], marker='o')
trk.plot()
plt.axis('equal')
plt.show()
#trk.adjust_track(1, 30)
trk.adjust_track(30, 100)
trk.adjust_track(30, 30)
trk.adjust_track(15, 10)

trk.plot()
#print(trk.get_cost())

step = 0.0001


for i in range(len(points_x)):
    plt.plot(points_x[i], points_y[i], marker='o') 
    plt.plot(points_x2[i], points_y2[i], marker='o')


plt.axis('equal')
plt.show()






