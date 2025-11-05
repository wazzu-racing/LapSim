import spline_track as spln
import pickle

txt_input = ''
while (txt_input != 'y') and (txt_input != 'n'):
    txt_input = input('load track?: ')

if txt_input == 'n':
    with open('Data/pkl/DEFAULT_NOT_GEN_TRACK(AUTOCROSS).pkl', 'rb') as f:
        points = pickle.load(f)

    points_x = points['p1x']
    points_y = points['p1y']
    points_x2 = points['p2x']
    points_y2 = points['p2y']

    trk = spln.track(points_x, points_y, points_x2, points_y2)
    print(trk.get_cost())
    trk.plot()
    #trk.adjust_track(1, 30)
    trk.adjust_track([40, 30, 30, 80], [100, 30, 10, 5])

    trk.plot()
    #print(trk.get_cost())

    step = 0.0001

    txt_input = ''
    while (txt_input != 'y') and (txt_input != 'n'):
        txt_input = input('save track?: ')
    if txt_input == 'y':
        with open('Data/pkl/tracks/autocross_trk.pkl', 'wb') as f:
            pickle.dump(trk, f)
        print('[Track Saved.]')
    else:
        print('[Track Discarded.]')

else:
    print('[Loading Track...]')
    with open('Data/pkl/tracks/autocross_trk.pkl', 'rb') as f:
            trk = pickle.load(f)
    with open('../Saved_Files/DEFAULT_CAR.pkl', 'rb') as f:
            car = pickle.load(f)
    trk.plot()
    trk.plt_sim(car)
    print(trk.t)




