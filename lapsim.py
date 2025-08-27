import numpy as np
from matplotlib import pyplot as plt
import pickle
import car_model
import copy
pi = np.pi



class sm_bullshit:
    def __init__ (self, t_len_tot, t_rad, car, n):
        print(min(t_rad))
        x = np.sort(copy.deepcopy(t_rad))
        y = np.linspace(len(x), 0, len(x))
        #plt.plot(x, y)
        #plt.show()
        self.t_len_tot = np.array(t_len_tot)
        self.t_rad = np.array(t_rad)
        self.car = car
        self.n = n
    
    def run(self):
        # Finding total length of track
        track = np.sum(self.t_len_tot)
        
        max_corner = self.car.max_corner * 32.2 * 12

        # discretizing track
        n = self.n
        dx = track/n

        # nodespace
        nds = np.linspace(0,track,int(n+1))

        # Determining maximum lateral acceleration for every turn
        self.t_vel = np.sqrt(max_corner*self.t_rad)

        # List showing radius at every node. Used to calculate maximum tangential acceleration
        self.nd_rad = np.zeros(int(n+1))

        # Each line sets the maximum velocity for each 
        self.arc_beginning_node = []
        for i in np.arange(len(self.t_len_tot)):
            self.nd_rad[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_rad[i]
            self.arc_beginning_node.append(int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)))
        self.arc_beginning_node.append(n+1)

        self.t_rad[-1] = self.t_rad[-2]

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n+1))
        for i in np.arange(len(self.t_len_tot)):
            v2[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v2[-1] = v2[-2]

        for i in np.arange(n,-1,-1):
            a_tan = self.car.curve_brake(v2[int(i)], self.nd_rad[int(i)])
            if (np.sqrt(v2[int(i)]**2 - 2*a_tan*dx) < v2[int(i-1)]) or (v2[int(i-1)] == 0.):
                v2[int(i-1)] = np.sqrt(v2[int(i)]**2 - 2*a_tan*dx)
        
        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(int(n+1))

        for i in np.arange(len(self.t_len_tot)):
            v1[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v1[0] = 0
        v1[-1] = v1[-2]

        gear = 0 # transmission gear
        shift_time = self.car.drivetrain.shift_time # shifting time (seconds)
        shifting = False # Set to true while shifting
        for i in np.arange(n):
            # checks if car is braking by looking of v2 is smaller than v1 (car is breaking when the if statement is true)
            if v2[int(i+1)] <= v1[int(i)]:
                v1[int(i+1)] = v2[int(i+1)]
                gear = self.car.drivetrain.gear_vel[int(v1[int(i)]*0.0568182*10)] # changes to the optimal gear when braking
                shifting = False # sets to False so the car doesn't shift when it stops braking
            else:
                # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
                if (gear >= self.car.drivetrain.gear_vel[int(v1[int(i)]*0.0568182*10)]) and not shifting:
                    a_tan = self.car.curve_accel(v1[int(i)], self.nd_rad[int(i)], gear)
                else:
                    shifting = True
                    #a_tan = self.car.curve_idle(v1[int(i)])
                    a_tan = 0
                    shift_time -= dx / v1[int(i)]
                    if shift_time <= 0:
                        gear += 1
                        shift_time = self.car.drivetrain.shift_time
                        shifting = False
                if (np.sqrt(v1[int(i)]**2 + 2*a_tan*dx) < v1[int(i+1)]) or (v1[int(i+1)] == 0.):
                    v1[int(i+1)] = np.sqrt(v1[int(i)]**2 + 2*a_tan*dx)
        
        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n+1))
        for i in np.arange(int(n+1)):
            if v1[i] < v2 [i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(1, len(v2)-1):
            t += dx/np.average([v3[i], v3[i+1]])
        
        self.dx = dx
        self.n = n
        self.nds = nds
        self.v3 = v3
        self.v2 = v2
        self.v1 = v1
        self.t = t
        
        return nds/12, v1/17.6, t