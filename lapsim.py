import numpy as np
from matplotlib import pyplot as plt
import pickle
pi = np.pi



# Importing Aero Model
with open('C:/Users/maxwe/Downloads/FSAE/2023-2024 Car/Repo/aero_model.pkl', 'rb') as file:
    aero_model = pickle.load(file)

aero_array = aero_model['aero_array'] # array to determine


# Importing Car Model
with open('C:/Users/maxwe/Downloads/FSAE/2023-2024 Car/Repo/car_model.pkl', 'rb') as f:
    car_model = pickle.load(f)

# total weight of car (minus driver) (lbm)
w_car = car_model['W_T']
# weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
w_bias = car_model['W_bias']
# weight over front track
W_f = car_model['W_f']
# weight over rear track
W_r = car_model['W_r']
# weight over front left wheel
W_1 = car_model['W_1']
# weight over front right wheel
W_2 = car_model['W_2']
# weight over rear left wheel
W_3 = car_model['W_3']
# weight over rear right wheel
W_4 = car_model['W_4']
# length of wheelbase (in)
l = car_model['l']
# in, distance from CG to front track
a = car_model['a']
# in, distance from CG to rear track
b = car_model['b']
# vertical center of gravity (in)
h = car_model['h']
# in, CG height to roll axis
H = car_model['H']
# in, roll axis height, front and rear
z_rf = car_model['z_rf']
z_rr = car_model['z_rr']
# Track widths, front and rear (in)
t_f = car_model['t_f']
t_r = car_model['t_r']
 # lb/in, ride rates, front and rear
K_RF = car_model['K_RF']
K_RR = car_model['K_RR']
# lb*ft/deg, roll rates, front and rear
K_rollF = car_model['K_rollF']
K_rollR = car_model['K_rollR']
 #deg/in, camber rates for front and rear
CMB_RT_F = car_model['CMB_RT_F']
CMB_RT_R = car_model['CMB_RT_R']
# deg, static camber rates for front and rear
CMB_STC_F = car_model['CMB_STC_F']
CMB_STC_R = car_model['CMB_STC_R']
# setting pi as a number
pi = 3.14159
# tire grip limit (G's)
tire_a_G = car_model['tire_a']
# tire grip limit (in/s^2)
tire_a_ins = tire_a_G*32.2*12
# engine acceleration array, index = mph(in/s^2)
a_array = car_model['a_array']
# Array to determine coefficient of friction for lateral and longitudinal accel.
cmbr_coeff_fy_df = car_model['cmbr_coeff_fy_df'] 
cmbr_coeff_fx_df = car_model['cmbr_coeff_fx_df']



class single_point:
    def __init__ (self, t_len_tot, t_rad, car, n):
        self.t_len_tot = np.array(t_len_tot)
        self.t_rad = np.array(t_rad)
        self.car = car
        self.n = n

    def run(self):
        # Importing Car Model
        with open(self.car, 'rb') as f:
            car_model = pickle.load(f)

        # total weight of car (minus driver) (lbm)
        w_car = car_model['W_T']
        # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
        w_bias = car_model['W_bias']
        # weight over front track
        W_f = car_model['W_f']
        # weight over rear track
        W_r = car_model['W_r']
        # weight over front left wheel
        W_1 = car_model['W_1']
        # weight over front right wheel
        W_2 = car_model['W_2']
        # weight over rear left wheel
        W_3 = car_model['W_3']
        # weight over rear right wheel
        W_4 = car_model['W_4']
        # length of wheelbase (in)
        l = car_model['l']
        # in, distance from CG to front track
        a = car_model['a']
        # in, distance from CG to rear track
        b = car_model['b']
        # vertical center of gravity (in)
        h = car_model['h']
        # in, CG height to roll axis
        H = car_model['H']
        # in, roll axis height, front and rear
        z_rf = car_model['z_rf']
        z_rr = car_model['z_rr']
        # Track widths, front and rear (in)
        t_f = car_model['t_f']
        t_r = car_model['t_r']
        # lb/in, ride rates, front and rear
        K_RF = car_model['K_RF']
        K_RR = car_model['K_RR']
        # lb*ft/deg, roll rates, front and rear
        K_rollF = car_model['K_rollF']
        K_rollR = car_model['K_rollR']
        #deg/in, camber rates for front and rear
        CMB_RT_F = car_model['CMB_RT_F']
        CMB_RT_R = car_model['CMB_RT_R']
        # deg, static camber rates for front and rear
        CMB_STC_F = car_model['CMB_STC_F']
        CMB_STC_R = car_model['CMB_STC_R']
        # tire grip limit (G's)
        tire_a_G = car_model['tire_a']
        # tire grip limit (in/s^2)
        tire_a_ins = tire_a_G*32.2*12
        # tire grip limit (G's)
        tire_a_G = car_model['tire_a']
        # tire grip limit (in/s^2)
        tire_a_ins = tire_a_G*32.2*12
        # engine acceleration array, index = mph, acceleration in (in/s^2)
        a_array = car_model['a_array']
        # Array to determine coefficient of friction for lateral and longitudinal accel.
        cmbr_coeff_fy_df = car_model['cmbr_coeff_fy_df'] 
        cmbr_coeff_fx_df = car_model['cmbr_coeff_fx_df']
        # Aerodynamic Drag Force, index = mph, Drag Force in (lbs)
        aero_array = car_model['aero_array'] 
        
        # Finding total length of track
        track = np.sum(self.t_len_tot)

        # discretizing track
        n = 500
        dx = track/n

        # nodespace
        nds = np.linspace(0,track,int(n+1))

        # Determining maximum lateral acceleration for every turn
        self.t_vel = np.sqrt(tire_a_ins*self.t_rad)

       # List showing radius at every node. Used to calculate maximum tangential acceleration
        self.nd_rad = np.zeros(int(n+1))

        # Each line sets the maximum velocity for each 
        self.arc_beginning_node = []
        for i in np.arange(len(self.t_len_tot)):
            self.nd_rad[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_rad[i]
            self.arc_beginning_node.append(int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)))
        self.arc_beginning_node.append(n+1)

        self.t_rad[-1] = self.t_rad[-2]

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0
        v1 = np.zeros(int(n+1))

        for i in np.arange(len(self.t_len_tot)):
            v1[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v1[0] = 0
        v1[-1] = v1[-2]

        for i in np.arange(n):
            # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
            a_tan_tire = np.sqrt(abs(tire_a_ins**2 - ((v1[i]**4)/(self.nd_rad[i]**2))))
            a_tan_engne = a_array[int(round(v1[int(i)]/17.6))]
            if a_tan_tire > a_tan_engne:
                a_tan = a_tan_engne
            else:
                a_tan = a_tan_tire
            aero_f = aero_array[int(round(v1[i]/17.6))]
            aero_a_G = aero_f/w_car
            aero_a_ins = aero_a_G*12*32.17
            a_tan += aero_a_ins
            if (np.sqrt(v1[int(i)]**2 + 2*a_tan*dx) < v1[int(i+1)]) or (v1[int(i+1)] == 0.):
                v1[int(i+1)] = np.sqrt(v1[int(i)]**2 + 2*a_tan*dx)

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n+1))
        for i in np.arange(len(self.t_len_tot)):
            v2[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v2[-1] = v2[-2]

        for i in np.arange(n,-1,-1):
            a_tan = np.sqrt(abs(tire_a_ins**2 - ((v2[i]**4)/(self.nd_rad[i]**2))))
            aero_f = aero_array[int(round(v2[i]/17.6))]
            aero_a_G = aero_f/w_car
            aero_a_ins = aero_a_G*12*32.17
            a_tan += aero_a_ins
            if (np.sqrt(v2[int(i)]**2 + 2*a_tan*dx) < v2[int(i-1)]) or (v2[int(i-1)] == 0.):
                v2[int(i-1)] = np.sqrt(v2[int(i)]**2 + 2*a_tan*dx)


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
        
        return nds/12, v3/17.6, t
    

    def arcEvaluator(self, starting_arc, ending_arc, new_t_len, new_t_rad):
        dx = self.dx

        new_nd_rad = np.zeros(int(np.sum(new_t_len)/dx))
        for i in np.arange(len(new_t_len)):
            new_nd_rad[int(np.ceil(np.sum(new_t_len[0:i])/dx)):int(np.ceil(np.sum(new_t_len[0:i+1])/dx))] = new_t_rad[i]

        starting_node = self.arc_beginning_node[starting_arc]
        ending_node = self.arc_beginning_node[ending_arc]
        new_ending_node = starting_node + len(new_nd_rad)

        n = self.n + len(new_nd_rad) + starting_node - ending_node
        track = np.sum(self.t_len_tot)
        nds = np.linspace(0,track,int(n+1))

        t_vel = self.t_vel
        t_len_tot = self.t_len_tot
        t_rad = self.t_rad

        t_vel[starting_arc:ending_arc] = np.sqrt(tire_a_ins*np.array(new_t_rad))
        t_len_tot[starting_arc:ending_arc] = new_t_len
        t_rad[starting_arc:ending_arc] = new_t_rad

        nd_rad = np.zeros(int(n+1))
        nd_rad[0:starting_node] = self.nd_rad[0:starting_node]
        nd_rad[starting_node:new_ending_node] = new_nd_rad
        nd_rad[new_ending_node:n] = self.nd_rad[ending_node:self.n]
        
        v1 = np.zeros(int(n+1))
        v1[0:starting_node] = self.v1[0:starting_node]
        v1[new_ending_node:n] = self.v1[ending_node:self.n]

        old_v1 = np.array(v1)
        old_v1[starting_node:new_ending_node] = np.inf

        v2 = np.zeros(int(n+1))
        v2[0:starting_node] = self.v2[0:starting_node]
        v2[new_ending_node:n] = self.v2[ending_node:self.n]

        old_v2 = v2
        old_v2[starting_node:new_ending_node] = np.inf

        nd_vel = np.zeros(n+1)
        for i in np.arange(0, len(t_rad)):
            nd_vel[int(np.ceil(np.sum(t_len_tot[0:i])/dx)):int(np.ceil(np.sum(t_len_tot[0:i+1])/dx))] = t_vel[i]
        nd_vel[0] = 1
        nd_vel[-1] = nd_vel[-2]
        
        for i in np.arange(starting_node-1, n):
            # the if statement below fixes a bug where the code stops working when running the loop for i = 0
            # I don't know what causes this bug or why it happens but changing skipping the itteration when i = 0 appears to fix it
            if i == 0:
                continue

            v1[0] = 0
            # Below section determines maximum longitudinal acceleration (a_tan) by selecting whichever is lower, engine accel. limit or tire grip limit as explained in word doc.
            if nd_rad[i] > 0:
                a_tan_tire = np.sqrt(abs(tire_a_ins**2 - ((v1[i]**4)/(nd_rad[i]**2))))
            else:
                a_tan_tire = tire_a_ins
            a_tan_engne = a_array[int(round(v1[int(i)]/17.6))]
            if a_tan_tire > a_tan_engne:
                a_tan = a_tan_engne
            else:
                a_tan = a_tan_tire
            if (np.sqrt(v1[int(i)]**2 + 2*a_tan*dx) < nd_vel[int(i+1)]) or (nd_vel[int(i+1)] == 0.):
                v1[int(i+1)] = np.sqrt(v1[int(i)]**2 + 2*a_tan*dx)
            else:
                v1[int(i+1)] = nd_vel[int(i+1)]
            if v1[i] > old_v2[i] and old_v1[i] > old_v2[i] and i > new_ending_node:
                break

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        for i in np.arange(new_ending_node, -1, -1):
            
            # sometimes i might start at a value equal to the length of v2
            # it is importatn to skip this itteration of the loop as otherwise the code will try to index non existing values of v2
            if i == len(v2):
                continue

            a_tan = np.sqrt(abs(tire_a_ins**2 - ((v2[i]**4)/(nd_rad[i]**2))))
            if (np.sqrt(v2[int(i)]**2 + 2*a_tan*dx) < nd_vel[int(i-1)]) or (nd_vel[int(i-1)] == 0.):
                v2[int(i-1)] = np.sqrt(v2[int(i)]**2 + 2*a_tan*dx)
            else:
                v2[int(i-1)] = nd_vel[int(i-1)]
            if v2[i] > old_v1[i] and old_v2[i] > old_v1[i] and i < starting_node:
                break

        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n+1))
        for i in np.arange(int(n+1)):
            if v1[i] < v2 [i]:
                v3[i] = (v1[int(i)])
            else:
                v3[i] = (v2[int(i)])

        # Determining the total time it takes to travel the track by rewriting the equation x = v * t as t = x /v
        t = 0
        for i in np.arange(1, len(v3)-2):
            if v3[i] == 0:
                v3[i] = (v3[i-1] + v3[i+1])/2
            t += dx/v3[i]
        #print(self.t - t)
        
        #plt.plot(nds[starting_node:new_ending_node], v3[starting_node:new_ending_node], color='blue')
        #plt.plot(nds[starting_node:ending_node], self.v3[starting_node:ending_node], color='orange')
        #plt.show()

        return self.t - t
    
class four_wheel:
    def __init__ (self, t_len_tot, t_rad, car, n):
        self.t_len_tot = np.array(t_len_tot)
        self.t_rad = np.array(t_rad)
        self.car = car
        self.n = n
        self.a_x_lst = np.zeros(int(self.n+1)) # Creating empty lists to be filled with info
        self.a_y_lst = np.zeros(int(self.n+1))
        self.a_lst = np.zeros(int(self.n+1))
        self.W_in_f_lst = np.zeros(int(self.n+1))
        self.W_out_f_lst = np.zeros(int(self.n+1))
        self.W_in_r_lst = np.zeros(int(self.n+1))
        self.W_out_r_lst = np.zeros(int(self.n+1))
        self.cmb_in_f_lst = np.zeros(int(self.n+1))
        self.cmb_in_f_lst = np.zeros(int(self.n+1))
        self.cmb_out_f_lst = np.zeros(int(self.n+1))
        self.cmb_in_r_lst = np.zeros(int(self.n+1))
        self.cmb_out_r_lst = np.zeros(int(self.n+1))

    def run(self):
               # Importing Car Model
        with open(self.car, 'rb') as f:
            car_model = pickle.load(f)

        # total weight of car (minus driver) (lbm)
        w_car = car_model['W_T']
        # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
        w_bias = car_model['W_bias']
        # weight over front track
        W_f = car_model['W_f']
        # weight over rear track
        W_r = car_model['W_r']
        # weight over front left wheel
        W_1 = car_model['W_1']
        # weight over front right wheel
        W_2 = car_model['W_2']
        # weight over rear left wheel
        W_3 = car_model['W_3']
        # weight over rear right wheel
        W_4 = car_model['W_4']
        # length of wheelbase (in)
        l = car_model['l']
        # in, distance from CG to front track
        a = car_model['a']
        # in, distance from CG to rear track
        b = car_model['b']
        # vertical center of gravity (in)
        h = car_model['h']
        # in, CG height to roll axis
        H = car_model['H']
        # in, roll axis height, front and rear
        z_rf = car_model['z_rf']
        z_rr = car_model['z_rr']
        # Track widths, front and rear (in)
        t_f = car_model['t_f']
        t_r = car_model['t_r']
        # lb/in, ride rates, front and rear
        K_RF = car_model['K_RF']
        K_RR = car_model['K_RR']
        # lb*ft/deg, roll rates, front and rear
        K_rollF = car_model['K_rollF']
        K_rollR = car_model['K_rollR']
        #deg/in, camber rates for front and rear
        CMB_RT_F = car_model['CMB_RT_F']
        CMB_RT_R = car_model['CMB_RT_R']
        # deg, static camber rates for front and rear
        CMB_STC_F = car_model['CMB_STC_F']
        CMB_STC_R = car_model['CMB_STC_R']
        # in, maximum displacement in jounce for suspension, front and rear
        max_jounce_f = car_model['max_jounce_f']
        max_jounce_r = car_model['max_jounce_r']
        # in, maximum displacement in droop for suspension, front and rear
        max_droop_f = car_model['max_droop_f']
        max_droop_r = car_model['max_droop_r']
        # engine acceleration array, index = mph, acceleration in (in/s^2)
        a_array = car_model['a_array']
        # Array to determine coefficient of friction for lateral and longitudinal accel.
        cmbr_coeff_fy_df = car_model['cmbr_coeff_fy_df'] 
        cmbr_coeff_fx_df = car_model['cmbr_coeff_fx_df']
        # Aerodynamic Drag Force, index = mph, Drag Force in (lbs)
        aero_array = car_model['aero_array'] 

        # 1) Calculating Maximum Lateral Acceleration

        a_y_G = 1 # This value initiates the maximum lateral acceleration value
        err = 1 # initiating error for the 'while' loop    
        n0 = 0
        a_y_max_lst = []
        while err > 0.01:
            n0 += 1
            change_W_y_f = a_y_G*w_car/t_f*(H*K_rollF/(K_rollF+K_rollR)+b/l*z_rf) # calculating lateral weight transfer for front track
            change_W_y_r = a_y_G*w_car/t_r*(H*K_rollR/(K_rollF+K_rollR)+a/l*z_rr) # calculating lateral weight transfer for front track
            W_in_f = W_2 - change_W_y_f # calculating normal force acting on front inside tire
            W_out_f = W_2 + change_W_y_f # calculating normal force acting on front outside tire
            W_in_r = W_4 - change_W_y_r # calculating normal force acting on rear inside tire
            W_out_r = W_4 + change_W_y_r # calculating normal force acting on rear outside tire

            # With camber and normal force known, calculate maximum possible lateral and longitudinal forces for each wheel. Then,
            # create a friction ellipse for each wheel
            disp_in_f = (W_in_f - W_2)/K_RF # calculating vertical suspension displacement
            disp_out_f = (W_out_f - W_2)/K_RF
            disp_in_r = (W_in_r - W_2)/K_RR
            disp_out_r = (W_out_r - W_2)/K_RR

            cmb_in_f = CMB_RT_F*disp_in_f + CMB_STC_F + (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f) # calculating camber values, accounting for roll of frame
            cmb_out_f = CMB_RT_F*disp_out_f + CMB_STC_F - (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f)
            cmb_in_r = CMB_RT_R*disp_in_r + CMB_STC_R + (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)
            cmb_out_r = CMB_RT_R*disp_out_r + CMB_STC_R - (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)

            f_y_max_in_f = W_in_f*cmbr_coeff_fy_df[int(cmb_in_f/10),int(W_in_f)]  # calculating lateral coeff. friction/max lat. G's
            f_y_max_out_f = W_out_f*cmbr_coeff_fy_df[int(cmb_out_f/10),int(W_out_f)]
            f_y_max_in_r = W_in_r*cmbr_coeff_fy_df[int(cmb_in_r/10),int(W_in_r)]
            f_y_max_out_r = W_out_r*cmbr_coeff_fy_df[int(cmb_out_r/10),int(W_out_r)]

            # Add up all the max. potential lateral forces from each wheel, and divide by the weight of the car to find lateral acceleration in Gs
            f_y_max = f_y_max_in_f + f_y_max_out_f + f_y_max_in_r + f_y_max_out_r
            new_a_y_G = f_y_max/w_car
            a_y_max_lst.append(new_a_y_G)

            if n0 > 25:
                slope_1 = (a_y_max_lst[-1]-a_y_max_lst[-20])/20 # Slope of iterative values. If the slope is approximately zero, then the values have essentially converged
                if slope_1 > 1e-3: # If the slope is more than 1e-4, then there is a considerable slope that shows that the values aren't converging
                    raise SystemExit(f"\nMaximum Longitudinal Force isn't converging for turn of radius {self.nd_rad[i]} in and node {i}\nerr_new = {new_err}, err = {err}\n a_x_lst = {a_x_lst}\n W_in_f = {W_in_f} W_out_f = {W_out_f} W_in_r = {W_in_r} W_out_r = {W_out_r}\n a_y_max = {a_y_max_lst} a_y_G = {a_y_G}\n")
                    exit() 
                else:
                    new_a_x_G = np.average(a_y_max_lst[-6:-1]) # Takes the average of the last few a_x_G values and breaks the while loop
                    break            

            err = abs(new_a_y_G-a_y_G)
            a_y_G = new_a_y_G  

        max_a_y_G = a_y_G
        max_a_y_ins = max_a_y_G*32.17*12
        W_in_f_max_y = W_in_f
        W_out_f_max_y = W_out_f
        W_in_r_max_y = W_in_r
        W_out_r_max_y = W_out_r

        # 2) Determining Track Characteristics

        track = np.sum(self.t_len_tot)

        # discretizing track
        n = 500
        dx = track/n

        # nodespace
        nds = np.linspace(0,track,int(n+1))

        # Determining maximum lateral acceleration for every turn using equation a = v^2/r
        self.t_vel = np.sqrt(max_a_y_ins*self.t_rad)

        # List showing radius at every node. Used to calculate maximum tangential acceleration
        self.nd_rad = np.zeros(int(n+1))
        
        # Each line sets the maximum velocity for each 
        self.arc_beginning_node = []
        for i in np.arange(len(self.t_len_tot)):
            self.nd_rad[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_rad[i]
            self.arc_beginning_node.append(int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)))
        self.arc_beginning_node.append(n+1)

        self.t_rad[-1] = self.t_rad[-2]



        # 3) Calculating Velocities for the Lapsim

        # Determine the speed if the car accelerated for the entire length of the traffic, starting from 0 mph at node 0

        # Setting the maximum velocity for each arc
        v1 = np.zeros(int(n+1))

        for i in np.arange(len(self.t_len_tot)):
            v1[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v1[0] = 0
        v1[-1] = v1[-2]

        # Creating empty lists to be filled with info
        a1_x_lst = np.zeros(n)
        a1_y_lst = np.zeros(n)
        a1_lst = np.zeros(n)
        W1_in_f_lst = np.full(n, W_in_f_max_y)
        W1_out_f_lst = np.full(n, W_out_f_max_y)
        W1_in_r_lst = np.full(n, W_in_r_max_y)
        W1_out_r_lst = np.full(n, W_out_r_max_y)
        cmb1_in_f_lst = np.full(n, CMB_STC_F)
        cmb1_out_f_lst = np.full(n, CMB_STC_F)
        cmb1_in_r_lst = np.full(n, CMB_STC_R)
        cmb1_out_r_lst = np.full(n, CMB_STC_R)

        for i in np.arange(n):
            engine_a_ins = a_array[int(round(v1[i]/17.6))]
            engine_a_G = engine_a_ins/(32.17*12)
            a_x_G = engine_a_G # Initiate a_r_G (acceleration of the car in G's) by assuming that engine power is the limiting factor
            if self.nd_rad[i] > 0: # calculating radial acceleration of car
                a_y_ins = v1[i]**2 / self.nd_rad[i]
            else:
                a_y_ins = 0
            a_y_G = a_y_ins/(32.17*12)
            err = 1e10 # initiating error for the 'while' loop  
            a_x_lst = []
            a_y_max_lst = []
            n1 = 0
            while err > 0.0001:
                n1 += 1 # counting number of iterations
            # Using either engine acceleration or tire grip limit and lateral acceleration, find normal force acting on each wheel
                change_W_x = h/l*a_x_G*w_car # calculating longidutinal weight transfer
                change_W_y_f = a_y_G*w_car/t_f*(H*K_rollF/(K_rollF+K_rollR)+b/l*z_rf) # calculating lateral weight transfer for front track
                change_W_y_r = a_y_G*w_car/t_r*(H*K_rollR/(K_rollF+K_rollR)+a/l*z_rr) # calculating lateral weight transfer for front track
                W_in_f = W_2 - change_W_y_f - change_W_x/2 # calculating normal force acting on front inside tire
                W_out_f = W_2 + change_W_y_f - change_W_x/2 # calculating normal force acting on front outside tire
                W_in_r = W_4 - change_W_y_r + change_W_x/2# calculating normal force acting on rear inside tire
                W_out_r = W_4 + change_W_y_r + change_W_x/2# calculating normal force acting on rear outside tire

                # With camber and normal force known, calculate maximum possible lateral and longitudinal forces for each wheel. Then,
                # create a friction ellipse for each wheel
                disp_in_f = (W_in_f - W_2)/K_RF # calculating vertical suspension displacement
                disp_out_f = (W_out_f - W_2)/K_RF
                disp_in_r = (W_in_r - W_4)/K_RR
                disp_out_r = (W_out_r - W_4)/K_RR

                cmb_in_f = CMB_RT_F*disp_in_f + CMB_STC_F + (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f) # calculating camber values, accounting for roll of frame
                cmb_out_f = CMB_RT_F*disp_out_f + CMB_STC_F - (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f)
                cmb_in_r = CMB_RT_R*disp_in_r + CMB_STC_R + (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)
                cmb_out_r = CMB_RT_R*disp_out_r + CMB_STC_R - (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)

                if W_in_f < 0:
                    W_in_f = 0

                if W_out_f < 0:
                    W_out_f = 0

                if W_in_r < 0:
                    W_in_r = 0

                if W_out_r < 0:
                    W_out_r = 0

                f_x_max_in_f = W_in_f*cmbr_coeff_fx_df[int(cmb_in_f/10),int(W_in_f)] # calculating lonitudinal coeff. friction/max long. G's
                f_x_max_out_f = W_out_f*cmbr_coeff_fx_df[int(cmb_out_f/10),int(W_out_f)]
                f_x_max_in_r = W_in_r*cmbr_coeff_fx_df[int(cmb_in_r/10),int(W_in_r)]
                f_x_max_out_r = W_out_r*cmbr_coeff_fx_df[int(cmb_out_r/10),int(W_out_r)]

                f_y_max_in_f = W_in_f*cmbr_coeff_fy_df[int(cmb_in_f/10),int(W_in_f)]  # calculating lateral coeff. friction/max lat. G's
                f_y_max_out_f = W_out_f*cmbr_coeff_fy_df[int(cmb_out_f/10),int(W_out_f)]
                f_y_max_in_r = W_in_r*cmbr_coeff_fy_df[int(cmb_in_r/10),int(W_in_r)]
                f_y_max_out_r = W_out_r*cmbr_coeff_fy_df[int(cmb_out_r/10),int(W_out_r)]

                # Add up all the max. potential lateral forces from each wheel, and divide the actual total lateral force by the max.
                # potential lateral force.
                f_y_max = f_y_max_in_f + f_y_max_out_f + f_y_max_in_r + f_y_max_out_r
                a_y_max = f_y_max / w_car
                a_y_ratio = a_y_G / a_y_max

                if a_y_ratio > 1:
                    a_y_ratio = 1

                # Multiply the max. lateral force at each wheel by this fraction, and use the friction ellipse to find the potential long.
                # force. The equation for an ellipse is (x^2/a^2) + (y^2/b^2) = 1, where a = f_x and b = f_y
                f_y_in_f = f_y_max_in_f*a_y_ratio # calculating actual f_y values for each wheel
                f_y_out_f = f_y_max_out_f*a_y_ratio
                f_y_in_r = f_y_max_in_r*a_y_ratio
                f_y_out_r = f_y_max_out_r*a_y_ratio

                if f_y_max_in_f!=0: # All 4 of these if statments make f_x = 0 if f_y_max = 0
                    f_x_in_f = np.sqrt((1 - f_y_in_f**2 / f_y_max_in_f**2) * f_x_max_in_f**2)
                else:
                    f_x_in_f = 0

                if f_y_max_out_f!=0:
                    f_x_out_f = np.sqrt((1 - f_y_out_f**2 / f_y_max_out_f**2) * f_x_max_out_f**2)
                else:
                    f_x_out_f = 0

                if f_y_max_in_r!=0:
                    f_x_in_r = np.sqrt((1 - f_y_in_r**2 / f_y_max_in_r**2) * f_x_max_in_r**2)
                else:
                    f_x_in_r = 0

                if f_y_max_out_r!=0:
                    f_x_out_r = np.sqrt((1 - f_y_out_r**2 / f_y_max_out_r**2) * f_x_max_out_r**2)
                else:
                    f_x_out_r = 0

                f_x_r = f_x_in_r + f_x_out_r # calculates longitudinal forces acting on car. Only considers rear wheels because the car is rwd

                new_a_x_G = f_x_r/w_car

                a_x_lst.append(new_a_x_G)
                a_y_max_lst.append(a_y_max)

                if engine_a_G < new_a_x_G: # if the calculated traction limit acceleration (in G's) is less than than the engine power limite (in G's), acceleration is limited by tire grip limit so the loop will continue to iterate
                    new_a_x_G = engine_a_G
                    break

                new_err = abs(new_a_x_G-a_x_G)

                # Determining if a_x_G is converging or not
                if n1 > 25:
                    slope_1 = (a_y_max_lst[-1]-a_y_max_lst[-20])/20 # Slope of iterative values. If the slope is approximately zero, then the values have essentially converged
                    if slope_1 > 1e-3: # If the slope is more than 1e-4, then there is a considerable slope that shows that the values aren't converging
                        raise SystemExit(f"\nMaximum Longitudinal Force isn't converging for turn of radius {self.nd_rad[i]} in and node {i}\nerr_new = {new_err}, err = {err}\n a_x_lst = {a_x_lst}\n W_in_f = {W_in_f} W_out_f = {W_out_f} W_in_r = {W_in_r} W_out_r = {W_out_r}\n a_y_max = {a_y_max_lst} a_y_G = {a_y_G}\n")
                        exit() 
                    else:
                        new_a_x_G = np.average(a_x_lst[-6:-1]) # Takes the average of the last few a_x_G values and breaks the while loop
                        break
                
                err = new_err
                a_x_G = new_a_x_G
            
            if abs(disp_in_f) > max_droop_f or abs(disp_out_f) > max_jounce_f or abs(disp_in_r) > max_droop_r or abs(disp_out_f) > max_jounce_r:
                    raise SystemExit(f'\nSuspension displacement is beyond maximum specified displacement:\nfront inside displacement = {disp_in_f} in\nfront outside displacement = {disp_out_f} in\nrear inside displacement = {disp_in_r} in\nrear outside displacement = {disp_out_r} in\n')
            
            if W_in_f < 0 and W_in_r < 0: # Making sure that there are no negative normal forces (ie. the car is flipping)
                raise SystemExit("Car is flipping!")
                exit()

            a_x_ins = a_x_G*32.17*12

            aero_f = aero_array[int(round(v1[i]/17.6))]
            aero_a_G = aero_f/w_car
            aero_a_ins = aero_a_G*12*32.17
            a_x_ins -= aero_a_ins
            
            if (np.sqrt(v1[int(i)]**2 + 2*a_x_ins*dx) < v1[int(i+1)]) or (v1[int(i+1)] == 0.):
                v1[int(i+1)] = np.sqrt(v1[int(i)]**2 + 2*a_x_ins*dx)
                a1_x_lst[i] = a_x_G
                W1_in_f_lst[i] = W_in_f
                W1_out_f_lst[i] = W_out_f
                W1_in_r_lst[i] = W_in_r
                W1_out_r_lst[i] = W_out_r
                cmb1_in_f_lst[i] = cmb_in_f
                cmb1_out_f_lst[i] = cmb_out_f
                cmb1_in_r_lst[i] = cmb_in_r
                cmb1_out_r_lst[i] = cmb_out_r
            a1_y_lst[i] = a_y_G
            a1_lst[i] = np.sqrt(a1_x_lst[i]**2 + a1_y_lst[i]**2)
            

        # Determine the speed if the car deaccelerated for the entire length of the traffic, ending at 0 mph at node n
        v2 = np.zeros(int(n+1))
        for i in np.arange(len(self.t_len_tot)):
            v2[int(np.ceil(np.sum(self.t_len_tot[0:i])/dx)):int(np.ceil(np.sum(self.t_len_tot[0:i+1])/dx))] = self.t_vel[i]
        v2[-1] = v2[-2]

        # Creating empty lists to be filled with info
        a2_x_lst = np.zeros(n)
        a2_y_lst = np.zeros(n)
        a2_lst = np.zeros(n)
        W2_in_f_lst = np.full(n, W_in_f_max_y)
        W2_out_f_lst = np.full(n, W_out_f_max_y)
        W2_in_r_lst = np.full(n, W_in_r_max_y)
        W2_out_r_lst = np.full(n, W_out_r_max_y)
        cmb2_in_f_lst = np.full(n, CMB_STC_F)
        cmb2_out_f_lst = np.full(n, CMB_STC_F)
        cmb2_in_r_lst = np.full(n, CMB_STC_R)
        cmb2_out_r_lst = np.full(n, CMB_STC_R)


        for i in np.arange(n-1,-1,-1):
            a_x_G = 1 # Initiate a_r_G with the tire coefficient of friction
            if self.nd_rad[i] > 0: # calculating radial acceleration of car
                a_y_ins = v2[i]**2 / self.nd_rad[i]
            else:
                a_y_ins = 0
            a_y_G = a_y_ins/(32.17*12)
            err = 1 # initiating error for the 'while' loop    
            a_y_max_lst = []
            a_x_lst = []
            n2 = 0
            while err > 0.0001:
                n2 += 1
            # Using either engine acceleration or tire grip limit and lateral acceleration, find normal force acting on each wheel
                change_W_x = h/l*a_x_G*w_car # calculating longidutinal weight transfer
                change_W_y_f = a_y_G*w_car/t_f*(H*K_rollF/(K_rollF+K_rollR)+b/l*z_rf) # calculating lateral weight transfer for front track
                change_W_y_r = a_y_G*w_car/t_r*(H*K_rollR/(K_rollF+K_rollR)+a/l*z_rr) # calculating lateral weight transfer for front track
                W_in_f = W_2 - change_W_y_f + change_W_x/2 # calculating normal force acting on front inside tire
                W_out_f = W_2 + change_W_y_f + change_W_x/2 # calculating normal force acting on front outside tire
                W_in_r = W_4 - change_W_y_r - change_W_x/2 # calculating normal force acting on rear inside tire
                W_out_r = W_4 + change_W_y_r - change_W_x/2 # calculating normal force acting on rear outside tire

                # With camber and normal force known, calculate maximum possible lateral and longitudinal forces for each wheel. Then,
                # create a friction ellipse for each wheel
                disp_in_f = (W_in_f - W_2)/K_RF # calculating vertical suspension displacement
                disp_out_f = (W_out_f - W_2)/K_RF
                disp_in_r = (W_in_r - W_4)/K_RR
                disp_out_r = (W_out_r - W_4)/K_RR

                cmb_in_f = CMB_RT_F*disp_in_f + CMB_STC_F + (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f) # calculating camber values, accounting for roll of frame
                cmb_out_f = CMB_RT_F*disp_out_f + CMB_STC_F - (180/np.pi)*np.arctan((-disp_in_f+disp_out_f)/t_f)
                cmb_in_r = CMB_RT_R*disp_in_r + CMB_STC_R + (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)
                cmb_out_r = CMB_RT_R*disp_out_r + CMB_STC_R - (180/np.pi)*np.arctan((-disp_in_r+disp_out_r)/t_r)

                f_x_max_in_f = W_in_f*cmbr_coeff_fx_df[int(cmb_in_f/10),int(W_in_f)] # calculating lonitudinal coeff. friction/max long. G's
                f_x_max_out_f = W_out_f*cmbr_coeff_fx_df[int(cmb_out_f/10),int(W_out_f)]
                f_x_max_in_r = W_in_r*cmbr_coeff_fx_df[int(cmb_in_r/10),int(W_in_r)]
                f_x_max_out_r = W_out_r*cmbr_coeff_fx_df[int(cmb_out_r/10),int(W_out_r)]

                f_y_max_in_f = W_in_f*cmbr_coeff_fy_df[int(cmb_in_f/10),int(W_in_f)]  # calculating lateral coeff. friction/max lat. G's
                f_y_max_out_f = W_out_f*cmbr_coeff_fy_df[int(cmb_out_f/10),int(W_out_f)]
                f_y_max_in_r = W_in_r*cmbr_coeff_fy_df[int(cmb_in_r/10),int(W_in_r)]
                f_y_max_out_r = W_out_r*cmbr_coeff_fy_df[int(cmb_out_r/10),int(W_out_r)]

                # Add up all the max. potential lateral forces from each wheel, and divide the actual total lateral force by the max.
                # potential lateral force.
                f_y_max = f_y_max_in_f + f_y_max_out_f + f_y_max_in_r + f_y_max_out_r
                a_y_max = f_y_max/w_car
                a_y_ratio = a_y_G / a_y_max

                if a_y_ratio > 1:
                    a_y_ratio = 1

                # Multiply the max. lateral force at each wheel by this fraction, and use the friction ellipse to find the potential long.
                # force. The equation for an ellipse is (x^2/a^2) + (y^2/b^2) = 1, where a = f_x and b = f_y
                f_y_in_f = f_y_max_in_f*a_y_ratio # calculating actual f_y values for each wheel
                f_y_out_f = f_y_max_out_f*a_y_ratio
                f_y_in_r = f_y_max_in_r*a_y_ratio
                f_y_out_r = f_y_max_out_r*a_y_ratio

                if f_y_max_in_f!=0:
                    f_x_in_f = np.sqrt((1 - f_y_in_f**2 / f_y_max_in_f**2) * f_x_max_in_f**2)
                else:
                    f_x_in_f = 0

                if f_y_max_out_f!=0:
                    f_x_out_f = np.sqrt((1 - f_y_out_f**2 / f_y_max_out_f**2) * f_x_max_out_f**2)
                else:
                    f_x_out_f = 0

                if f_y_max_in_r!=0:
                    f_x_in_r = np.sqrt((1 - f_y_in_r**2 / f_y_max_in_r**2) * f_x_max_in_r**2)
                else:
                    f_x_in_r = 0

                if f_y_max_out_r!=0:
                    f_x_out_r = np.sqrt((1 - f_y_out_r**2 / f_y_max_out_r**2) * f_x_max_out_r**2)
                else:
                    f_x_out_r = 0
                
                f_x = f_x_in_f + f_x_out_f + f_x_in_r + f_x_out_r

                new_a_x_G = f_x/w_car

                a_x_lst.append(new_a_x_G)
                a_y_max_lst.append(a_y_max)

                # Determining if a_x_G is converging or not
                if n2 > 25:
                    slope_1 = (a_y_max_lst[-1]-a_y_max_lst[-20])/20 # Slope of iterative values. If the slope is approximately zero, then the values have essentially converged
                    if slope_1 > 1e-4: # If the slope is more than 1e-4, then there is a considerable slope that shows that the values aren't converging
                        raise SystemExit(f"\nMaximum Longitudinal Force isn't converging for turn of radius {self.nd_rad[i]} in and node {i}\nerr_new = {new_err}, err = {err}\n a_x_lst = {a_x_lst}\n W_in_f = {W_in_f} W_out_f = {W_out_f} W_in_r = {W_in_r} W_out_r = {W_out_r}\n a_y_max = {a_y_max_lst} a_y_G = {a_y_G}\n")
                        exit() 
                    else:
                        new_a_x_G = np.average(a_x_lst[-15:-1]) # Takes the average of the last few a_x_G values and breaks the while loop
                        break

                err = abs(new_a_x_G-a_x_G)
                a_x_G = new_a_x_G

            if abs(disp_in_f) > max_droop_f or abs(disp_out_f) > max_jounce_f or abs(disp_in_r) > max_droop_r or abs(disp_out_f) > max_jounce_r:
                    raise SystemExit(f'\nSuspension displacement is beyond maximum specified displacement:\nfront inside displacement = {disp_in_f} in\nfront outside displacement = {disp_out_f} in\nrear inside displacement = {disp_in_r} in\nrear outside displacement = {disp_out_r} in\n')
            
            if W_in_f < 0 and W_in_r < 0: # Making sure that there are no negative normal forces (ie. the car is flipping)
                raise SystemExit("Car is flipping!")
                exit()
                
            a_x_ins = a_x_G*32.17*12

            aero_f = aero_array[int(round(v2[i]/17.6))] # Adding Aero effects to Lapsim
            aero_a_G = aero_f/w_car
            aero_a_ins = aero_a_G*12*32.17
            a_x_ins += aero_a_ins

            if (np.sqrt(v2[int(i)]**2 + 2*a_x_ins*dx) < v2[int(i-1)]) or (v2[int(i-1)] == 0.):
                v2[int(i-1)] = np.sqrt(v2[int(i)]**2 + 2*a_x_ins*dx)
                a2_x_lst[i] = -a_x_G
                W2_in_f_lst[i] = W_in_f
                W2_out_f_lst[i] = W_out_f
                W2_in_r_lst[i] = W_in_r
                W2_out_r_lst[i] = W_out_r
                cmb2_in_f_lst[i] = cmb_in_f
                cmb2_out_f_lst[i] = cmb_out_f
                cmb2_in_r_lst[i] = cmb_in_r
                cmb2_out_r_lst[i] = cmb_out_r
            a2_y_lst[i] = a_y_G
            a2_lst[i] = (np.sqrt(a2_x_lst[i]**2 + a2_y_lst[i]**2))


        # Determine which value of the two above lists is lowest. This list is the theoretical velocity at each node to satisfy the stated assumptions
        v3 = np.zeros(int(n+1))
        self.a_x_lst = np.zeros(int(n+1)) # Creating empty lists to be filled with info
        self.a_y_lst = np.zeros(int(n+1))
        self.a_lst = np.zeros(int(n+1))
        self.W_in_f_lst = np.zeros(int(n+1))
        self.W_out_f_lst = np.zeros(int(n+1))
        self.W_in_r_lst = np.zeros(int(n+1))
        self.W_out_r_lst = np.zeros(int(n+1))
        self.cmb_in_f_lst = np.zeros(int(n+1))
        self.cmb_in_f_lst = np.zeros(int(n+1))
        self.cmb_out_f_lst = np.zeros(int(n+1))
        self.cmb_in_r_lst = np.zeros(int(n+1))
        self.cmb_out_r_lst = np.zeros(int(n+1))


        for i in np.arange(int(n+1)):
            if v1[i] < v2[i]:
                v3[i] = (v1[int(i)])
                self.a_x_lst[i] = a1_x_lst[i]
                self.a_y_lst[i] = a1_y_lst[i]
                self.a_lst[i] = a1_lst[i]
                self.W_in_f_lst[i] = W1_in_f_lst[i]
                self.W_out_f_lst[i] = W1_out_f_lst[i]
                self.W_in_r_lst[i] = W1_in_r_lst[i]
                self.W_out_r_lst[i] = W1_out_r_lst[i]
                self.cmb_in_f_lst = cmb1_in_f_lst[i]
                self.cmb_out_f_lst = cmb1_out_f_lst[i]
                self.cmb_in_r_lst = cmb1_in_r_lst[i]
                self.cmb_out_r_lst = cmb1_out_r_lst[i]
            else:
                v3[i] = (v2[int(i)])
                self.a_x_lst[i] = a2_x_lst[i-1]
                self.a_y_lst[i] = a2_y_lst[i-1]
                self.a_lst[i] = a2_lst[i-1]
                self.W_in_f_lst[i] = W2_in_f_lst[i-1]
                self.W_out_f_lst[i] = W2_out_f_lst[i-1]
                self.W_in_r_lst[i] = W2_in_r_lst[i-1]
                self.W_out_r_lst[i] = W2_out_r_lst[i-1]
                self.cmb_in_f_lst = cmb2_in_f_lst[i-1]
                self.cmb_out_f_lst = cmb2_out_f_lst[i-1]
                self.cmb_in_r_lst = cmb2_in_r_lst[i-1]
                self.cmb_out_r_lst = cmb2_out_r_lst[i-1]

        # Determining the total time it takes to travel the track by rewriting the equation v1 = v0 + a*t
        t = 0
        for i in np.arange(len(v2)-1):
            t += dx/np.average([v3[i+1],v3[i]])

        self.dx = dx
        self.n = n
        self.nds = nds
        self.v3 = v3
        self.v2 = v2
        self.v1 = v1
        self.t = t     

        return nds/12, v3/17.6, t
    
