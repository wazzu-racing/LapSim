from matplotlib import pyplot as plt
from Models import trackModel


#with open('C:\\Users\\nbogd\\OneDrive\\Documents\\lapsim stuff - Copy\\trck.pkl', 'rb') as f:
#    points = pickle.load(f)

def plot_the_track():

    for i in range(len(points_x)):
        match i % 5:
            case 0: col = 'red'
            case 1: col = 'blue'
            case 2: col = 'green'
            case 3: col = 'black'
            case 4: col = 'violet'
        plt.plot(points_x[i], points_y[i], marker='o', color=col)
        plt.plot(points_x2[i], points_y2[i], marker='o', color=col)
    track.plot_track()
    plt.axis('equal')
    plt.show()

def plot_the_sim():
    t = track.plot_sim('single point')
    print(f'sim time: {t}')
    plt.xlabel('straight section, 50 ft')
    plt.ylabel('Velocity, in/s')
    plt.show()


points_x = [0,    246.3, 600.2, 668.7, 454.3, 676.5, 284.2, -26,    -178.2, -260.9, -170, -444.4, -554.68, -370]
points_y = [1000, 606.7, 548.9, 412,   206.1, -70,  -192.3, -242.5, -348.9, -92.4,  182.2, 374.7,  460.4,  823.4]

points_x2 = [0,   156.3, 400.2, 868.7, 584.3, 526.5, 284.2,  100,   -378.2, -460.9,  70,  -344.4, -454.68, -520]
points_y2 = [800, 556.7, 548.9, 462,   136.1, -20,   8.3, -342.5, -448.9, -92.4,  232.2, 574.7,  560.4,   973.4]

#points_x = [-700, -600.3, -300.2, -100.7, 200.3, 300.5, 284.2, -26, -178.2, -460.9, -670, -444.4, -504.68, -870]
#points_y = [1000, 832.7, 548.9, 700, 500, -70, -292.3, -242.5, -548.9, -292.4, 182.2, 374.7, 460.4, 623.4]

#points_x = points['p1x']
#points_y = points['p1y']
#points_x2 = points['p2x']
#points_y2 = points['p2y']


#with open('comp_track.pkl', 'rb') as f:
#    track = pickle.load(f)

track = trackModel.track(points_x, points_y, points_x2, points_y2)
plot_the_track()
track.adjust_course(80)
plot_the_track()
plot_the_sim()


#if input("save?: ") == 'y':
#    with open('C:\\Users\\nbogd\\OneDrive\\Documents\\lapsim stuff - Copy\\comp_track.pkl', 'wb') as f:
#        pickle.dump(track, f)
#    print('[Track Saved.]')
