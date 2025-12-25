import numpy as np
from matplotlib import pyplot as plt
import pickle as pkl
import lapsim as lpsm
from models.drivetrain_model import drivetrain

# with open('endurance_trk.pkl', 'rb') as f:
#     endurance = pkl.load(f)ß

with open('Data/Tracks/autocross_trk.pkl', 'rb') as f:
    autocross = pkl.load(f)

with open('/saved_files/DEFAULT_CAR.pkl', 'rb') as f:
    car = pkl.load(f)
car.file_location = '/saved_files/DEFAULT_CAR.pkl'

times = []
weights = []

if False:
    r = 15.25/2 # m
    r *= 39.3701
    r += 26
    d = r * 3.1415926535897 * 2
    car.adjust_weight(550)
    for i in range(8, 29):
        car.adjust_height(i/2)
        a = car.max_corner * 32.2 * 12
        print(car.max_corner)
        v = (a*r)**0.5
        t = d/v
        print(t)
        times.append(t)
        weights.append(i/2)
    plt.plot(weights, times)
    plt.title('Center of Mass Height vs Acceleration Time')
    plt.xlabel('Center of Mass Height (in)')
    plt.ylabel('Acceleration Time (s)')
    plt.grid()
    plt.show()

if False:
    for i in range(660, 470, -20):
        car.adjust_weight(i)
        car.adjust_height(14/713*i)
        track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 0], car, 5000)
        nds, v3, t = track.run()
        print(t)
        times.append(t)
        weights.append(i)
    plt.plot(weights, times)
    plt.title('Vehicle Weight vs Acceleration Time')
    plt.xlabel('Vehicle Weight (lb)')
    plt.ylabel('Acceleration Time (s)')
    plt.grid()
    plt.show()

if False:
    track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 0], car, 5000)
    nds, v3, t = track.run()
    print(t)

if False:
    drives = np.linspace(2, 6, 41)
    #track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 0], car_model.car(final_drive = 4), 1500)
    times = []
    #track.car = car_model.car(final_drive = 3)
    for i in drives:
        car.drivetrain = drivetrain(i)
        car.drivetrain.shift_time = 0.5
        track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 9999999999999999], car, 500)
        nds, v3, t = track.run()
        print(f'final drive = {i}\tacceleration time = {t}')
        times.append(t)

    plt.plot(drives, times)
    plt.title('Final drive vs Acceleration Time')
    plt.xlabel('Final drive')
    plt.ylabel('Acceleration Time (s)')
    plt.grid()
    plt.show()

if False:
    drives = np.linspace(2, 6, 41)
    #track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 0], car_model.car(final_drive = 4), 1500)
    times = []
    #track.car = car_model.car(final_drive = 3)
    for i in drives:
        car.drivetrain = drivetrain(i)
        endurance.run_sim(car)
        t = endurance.t
        print(f'final drive = {i}\tEndurance time = {t}')
        times.append(t)

    plt.plot(drives, times)
    plt.title('Final drive vs Endurance Time')
    plt.xlabel('Final drive')
    plt.ylabel('Acceleration Time (s)')
    plt.grid()
    plt.show()

if False:
    drives = np.linspace(2, 6, 41)
    #track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 0], car_model.car(final_drive = 4), 1500)
    times = []
    #track.car = car_model.car(final_drive = 3)
    for i in drives:
        car.drivetrain = drivetrain(i)
        autocross.run_sim(car, end = 89)
        t = autocross.t
        print(f'final drive = {i}\tAutocross time = {t}')
        times.append(t)

    plt.plot(drives, times)
    plt.title('Final drive vs Autocross Time')
    plt.xlabel('Final drive')
    plt.ylabel('Autocross Time (s)')
    plt.grid()
    plt.show()

if False:
    car.drivetrain = drivetrain(3.1)
    car.drivetrain.shift_time = 0.5
    track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [0, 0, 0, 9999999999999999], car, 500)
    nds, v3, t = track.run()
    plt.plot(nds, v3)
    plt.xlabel('Position (ft)')
    plt.ylabel('Vehicle Speed (mph)')
    plt.grid()
    plt.show()

if False:
    track = lpsm.four_wheel([246*3, 246*3, 246*3, 246*3], [99999999, 99999999, 99999999, 99999999], car_model.car(final_drive = 4.8), 1500)
    times = []
    #track.car = car_model.car(final_drive = 3)
    nds, v3, t = track.run()
    print(t)

    plt.plot(nds, v3)
    plt.title('Distance vs Velocity (Acceleration)')
    plt.xlabel('Distance (ft)')
    plt.ylabel('Speed (mph)')
    plt.grid()
    plt.show()

if False:
    print(len(autocross.arcs))
    autocross.run_sim(car, nodes = 10000, end = 89)
    #plt.plot(nds, v3)
    #plt.show()

# plt.grid()
# plt.xlabel('Distance (ft)')
# plt.ylabel('Speed (mph)')
# plt.title('Autocross Time')
# autocross.plt_sim(car, end = 89)