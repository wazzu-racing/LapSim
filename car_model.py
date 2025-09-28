from matplotlib import pyplot as plt
import numpy as np
import pickle as pkl
import csv

from main_menu.manage_data.files import get_save_files_folder_abs_dir

aero_csv_file_path = f"{get_save_files_folder_abs_dir()}/aero_array.csv"
tire_file_path = f"{get_save_files_folder_abs_dir()}/18x6-10_R20.pkl"
drivetrain_file_path = f"{get_save_files_folder_abs_dir()}/drivetrain.pkl"

class car():
    global aero_csv_file_path, tire_file_path, drivetrain_file_path

    # weight over front left wheel
    W_1 = 185.7365 * 0.7223
    # weight over front right wheel
    W_2 = 185.7365 * 0.7223
    # weight over rear left wheel
    W_3 = 170.7635 * 0.7223
    # weight over rear right wheel
    W_4 = 170.7635 * 0.7223
    # length of wheelbase (in)
    l = 60.04
    # vertical center of gravity (in)
    h = 13
    # in, CG height to roll axis
    H = 10.521
    # in, roll axis height, front and rear
    z_rf = 2
    z_rr = 3
    # Track widths, front and rear (in)
    t_f = 61.3
    t_r = 59.09
    # lb/in, ride rates, front and rear
    K_RF = 189.5 # front
    K_RR = 207.38 # rear
    # lb*ft/deg, roll rates, front and rear (later converted to lb*ft/rad)
    K_rollF = 144439.94389901822
    K_rollR = 142041.8793828892
    #deg/in, camber rates for front and rear
    CMB_RT_F = 1.5
    CMB_RT_R = 1.25
    # deg, static camber rates for front and rear
    CMB_STC_F = 1
    CMB_STC_R = 1
    # in, maximum displacement in jounce for suspension, front and rear
    max_jounce_f = 1
    max_jounce_r = 1

    # Converting roll rates to ft*lb/rad
    K_rollF *= 180/np.pi
    K_rollR *= 180/np.pi
    # weight over front track
    W_f = W_1 + W_2
    # weight over rear track
    W_r = W_3 + W_4
    # total weight of car (minus driver) (lbm)
    W_car = W_f + W_r
    # weight bias, if less than 0.5, then the rear of the car will have more weight, if more than 0.5, then the front will have more weight
    W_bias = W_f/W_car
    # in, distance from CG to rear track
    b = l * W_bias
    # in, distance from CG to front track
    a = l - b
    # in, CG height to roll axis
    H = h - (a*z_rf + b*z_rr)/l

    # Weight forces on wheels
    W_out_f =0 # vertical force on front outer wheel
    W_in_f =0  # vertical force on front inner wheel
    W_out_r = 0 # vertical force on rear outer wheel
    W_in_r = 0  # vertical force on rear inner wheel
    #lateral forces on wheels
    FY_out_f = 0 # max possible lateral force from front outer wheel
    FY_in_f = 0  # max possible lateral force from front inner wheel
    FY_out_r = 0 # max possible lateral force from rear outer wheel
    FY_in_r = 0  # max possible lateral force from rear inner wheel
    # axial forces on wheels
    FX_out_f = 0 # max possible axial acceleration from front outer wheel
    FX_in_f = 0  # max possible axial acceleration from front inner wheel
    FX_out_r = 0 # max possible axial acceleration from rear outer wheel
    FX_in_r = 0  # max possible axial acceleration from rear inner wheel
    # in, displacement of tires in vertical based on change in weight on tires. Default to 0.
    D_1 = 0 # Front outer wheel vertical displacement in inches
    D_2 = 0 # Front inner wheel vertical displacement in inches
    D_3 = 0 # Rear outer wheel vertical displacement in inches
    D_4 = 0 # Rear inner wheel vertical displacement in inches

    # Set the aero_csv variable to the saved_files dir
    aero_csv = aero_csv_file_path
    # Set the tire_file variable to the saved_files dir
    tire_file = tire_file_path
    # Set the drivetrain_file variable to the saved_files dir
    drivetrain_file = drivetrain_file_path
    # aero csv file delimiter
    aero_delimiter = ';'

    # importing tire model
    with open(tire_file, 'rb') as f:
        tires = pkl.load(f)

    # importing drivetrain model
    with open(drivetrain_file, 'rb') as f:
        drivetrain = pkl.load(f)

    def __init__(self):
        self.aero_arr = [] # drag force acceleration (G's) emitted on vehicle (index = mph)
        with open(self.aero_csv, newline='') as f:
            reader = csv.reader(f, delimiter=self.aero_delimiter)
            for line in reader:
                for i in line:
                    self.aero_arr.append(float(i)/self.W_car)
        
        self.aero_arr.reverse()
        self.compute_traction()

        # future code for accounting for tire orientation
        '''
        min_crv = 70 # minimum curve radius (in) (ideally less than the smallest possible curve given the vehicle's steering geometry)
        max_crv = 1000 # maximum curve radius (in) (the radius at which error from large cruve approximations become negligable)
        d_crv = 5
        self.curves = np.linspace(min_crv, max_crv, int((max_crv-min_crv)/d_crv)+1)
        V_arr = np.linspace(0, 100, 101) * 17.6
        
        start_time = time.time()
        for r in self.curves:
            C_r_in = 0
            C_r_out = 0
            S_c = 0
            
            break_loop = False
            for V in V_arr:
                AY = V**2/r / 12 * 32.17 # total lateral force on car body

                while True:
                    S_c += 0.1
                    # slip angle of rear inner and outter tires respectively
                    if r == 0:
                        S_r_in = S_c
                        S_r_out = S_c
                    else:
                        S_r_in  = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a - np.cos(S_c)*self.t_r/2)))
                        S_r_out = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a + np.cos(S_c)*self.t_r/2)))

                    low = 0
                    high = 3
                    
                    for i in range(20):
                        
                        AX = (low + high) / 2

                        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
                        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)
                        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
                        W_shift_x = roll * self.H # lateral shift in center of mass (in)

                        W_f_out = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # force on front outter wheel
                        W_f_in = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # force on front inner wheel
                        W_r_out = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # force on rear outter wheel
                        W_r_in = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # force on rear inner wheel

                        C_f_out = abs(self.CMB_STC_F + (W_f_out-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
                        C_f_in = abs(self.CMB_STC_F + (W_f_in-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
                        C_r_out = abs(self.CMB_STC_R + (W_r_out-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
                        C_r_in = abs(self.CMB_STC_R + (W_r_in-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

                        FY_r_in = abs(self.tires.FY_curves.eval(S_r_in, W_r_in, C_r_in))
                        FY_r_out = abs(self.tires.FY_curves.eval(S_r_out, W_r_out, C_r_out))
                        FX_r_in = (1 - (FY_r_in / abs(self.tires.FY_curves.get_max(W_r_in, C_r_in)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_r_in, C_r_in))
                        FX_r_out = (1 - (FY_r_out / abs(self.tires.FY_curves.get_max(W_r_out, C_r_out)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_r_out, C_r_out))
                        MZ_r_in = abs(self.tires.aligning_torque.eval(S_r_in, W_r_in, C_r_in))
                        MZ_r_out = abs(self.tires.aligning_torque.eval(S_r_out, W_r_out, C_r_out))

                        if FY_r_in + FY_r_out < 0.7 * AY * self.W_car * (1-self.W_bias):
                            high = AX
                            continue

                        MZ_last =  0   
                        steeeeeeeeeer = 0      
                        for steer in range(20):
                            if r == 0:
                                S_f_in = S_c + steer
                                S_f_out = S_c + steer
                            else:
                                S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
                                S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))

                            FY_f_in = abs(self.tires.FY_curves.eval(S_f_in, W_f_in, C_f_in))
                            FY_f_out = abs(self.tires.FY_curves.eval(S_f_out, W_f_out, C_f_out))
                            MZ_f_in = abs(self.tires.aligning_torque.eval(S_f_in, W_f_in, C_f_in))
                            MZ_f_out = abs(self.tires.aligning_torque.eval(S_f_out, W_f_out, C_f_out))

                            MZ_tot = MZ_f_in + MZ_f_out + MZ_r_in + MZ_r_out + (FY_r_in + FY_r_out)*self.a - (FY_f_in + FY_f_out)*self.b
                            if MZ_tot < 0:
                                MZ_last = MZ_tot

                            else:
                                steeeeeeeeeer = ((steer-1) * MZ_tot - steer * MZ_last) / (MZ_tot + MZ_last)
                                break
                        
                        steer = steeeeeeeeeer
                        if r == 0:
                            S_f_in = S_c + steer
                            S_f_out = S_c + steer
                        else:
                            S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
                            S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))

                        FX_f_in = (1 - (FY_f_in / abs(self.tires.FY_curves.get_max(W_f_in, C_f_in)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_f_in, C_f_in))
                        FX_f_out = (1 - (FY_f_out / abs(self.tires.FY_curves.get_max(W_f_out, C_f_out)))**2)**0.5 * abs(self.tires.FX_curves.get_max(W_f_out, C_f_out))
                        
                        if FX_f_in + FX_f_out + FX_r_in + FX_r_out < AX * self.W_car:
                            high = AX
                        else:
                            low = AX


                    if S_c > 20:
                        break_loop = True
                        break

                # lateral forces of rear inner and outter tires respectively
                FY_r_in = self.tires.FY_curves.eval
                if break_loop:
                    break

            break
        print(time.time() - start_time)
        '''

    def compute_traction(self):
        # finding max cornering (lateral) acceleration
        low_guess = 0 # low estimate for max cornering (lateral) acceleration (g)
        high_guess = 3 # high estimate for max cornering (lateral) acceleration (g)

        # when the low and high estimates converge, the converging value is recorded as the max cornering (lateral) acceleration
        while high_guess - low_guess > 0.00001:
            guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering (lateral) acceleration
            out = self.accel(guess, 0)
            if out: # sets low estimate to the guess value if the car can handle cornering (lateral) acceleration equal to the guess value
                low_guess = guess
            else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
                high_guess = guess
        
        self.max_corner = guess # max cornering (lateral) acceleration (g)
        self.AY = np.linspace(0, self.max_corner, 100)
        self.A_accel = []
        self.A_brake = []
        for i in self.AY:
            self.A_accel.append(self.max_accel(i))
            self.A_brake.append(self.max_brake(i))
        self.max_corner -= 0.0001
        
    # Returns true if the car can generate the axial traction based on AY and AX. Returns false otherwise.
    # AY is magnitude of lateral acceleration, AX is magnitude of axial acceleration, both are measured in g's
    def accel(self, AY, AX, bitch = False):
        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        W_out_f = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # vertical force on front outter wheel in pounds
        W_in_f = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # vertical force on front inner wheel in pounds
        W_out_r = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # vertical force on rear outter wheel in pounds
        W_in_r = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # vertical force on rear inner wheel in pounds

        # Set variables to corresponding class variable
        self.W_out_f = W_out_f
        self.W_in_f = W_in_f
        self.W_out_r = W_out_r
        self.W_in_r = W_out_r

        # Set displacement vars to their values
        self.D_1 = (self.W_out_f - self.W_1) / self.K_RF # doesn't matter whether W_1 is the outer or inner tire at the moment since both front tires have the same weight.
        self.D_2 = (self.W_in_f - self.W_2) / self.K_RF # doesn't matter whether W_2 is the outer or inner tire at the moment since both front tires have the same weight.
        self.D_3 = (self.W_out_r - self.W_3) / self.K_RR # doesn't matter whether W_3 is the outer or inner tire at the moment since both rear tires have the same weight.
        self.D_4 = (self.W_in_r - self.W_4) / self.K_RR # doesn't matter whether W_4 is the outer or inner tire at the moment since both rear tires have the same weight.

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        for i in [W_out_f, W_in_f, W_out_r, W_in_r]:
            if i < 0: return False

        C_out_f = abs(self.CMB_STC_F + (W_out_f-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
        C_in_f = abs(self.CMB_STC_F + (W_in_f-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        C_out_r = abs(self.CMB_STC_F + (W_out_r-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        C_in_r = abs(self.CMB_STC_F + (W_in_r-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        FY_out_f = self.tires.traction('corner', W_out_f, C_out_f) # max possible lateral acceleration from front outter wheel in pounds
        FY_in_f = self.tires.traction('corner', W_in_f, C_in_f)    # max possible lateral acceleration from front inner wheel in pounds
        FY_out_r = self.tires.traction('corner', W_out_r, C_out_r) # max possible lateral acceleration from rear outter wheel in pounds
        FY_in_r = self.tires.traction('corner', W_in_r, C_in_r)    # max possible lateral acceleration from rear inner wheel in pounds

        # Set variables to corresponding class variable
        self.FY_out_f = FY_out_f
        self.FY_in_f = FY_in_f
        self.FY_out_r = FY_out_r
        self.FY_in_r = FY_in_r

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        if (FY_f > FY_out_f+FY_in_f) or (FY_r > FY_out_r+FY_in_r): return False

        if bitch:
            print((W_in_f + W_out_f) / (W_out_f + W_out_r + W_in_f + W_in_r))

        if AX == 0: return True # returning true if no axial acceleration

        f_factor = ((FY_out_f + FY_in_f)**2 - FY_f**2)**0.5 / (FY_out_f + FY_in_f)
        r_factor = ((FY_out_r + FY_in_r)**2 - FY_r**2)**0.5 / (FY_out_r + FY_in_r)

        FX_out_f = f_factor * self.tires.traction('accel', W_out_f, C_out_f) # max possible axial acceleration from front outter wheel in pounds
        FX_in_f = f_factor * self.tires.traction('accel', W_in_f, C_in_f)    # max possible axial acceleration from front inner wheel in pounds
        FX_out_r = r_factor * self.tires.traction('accel', W_out_r, C_out_r) # max possible axial acceleration from rear outter wheel in pounds
        FX_in_r = r_factor * self.tires.traction('accel', W_in_r, C_in_r)    # max possible axial acceleration from rear inner wheel in pounds

        # Set variables to corresponding class variable
        self.FX_out_f = FX_out_f
        self.FX_in_f = FX_in_f
        self.FX_out_r = FX_out_r
        self.FX_in_r = FX_in_r

        # Calculating max lateral acceleration from tire traction
        if AX > 0:
            FX = FX_out_r + FX_in_r
        else:
            FX = FX_out_f + FX_in_f + FX_out_r + FX_in_r
        
        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX): return False
        else: return True

    # modified accel function, currently unfinished. Will account for tire orientation
    def accel2(self, AY, AX, S_c, steer, r):
        W_f = self.W_f - self.h*self.W_car*AX/self.l # Vertical force on front track (lb)
        W_r = self.W_r + self.h*self.W_car*AX/self.l # Vertical force on rear track (lb)

        roll = (W_f*self.z_rf + W_r*self.z_rr)*AY / (self.K_rollF+self.K_rollR) # roll of car (rad)
        W_shift_x = roll * self.H # lateral shift in center of mass (in)

        W_f_out = W_f/2 + self.W_f/self.t_f*(W_shift_x + AY*self.h) # force on front outter wheel
        W_f_in = W_f/2 - self.W_f/self.t_f*(W_shift_x + AY*self.h)  # force on front inner wheel
        W_r_out = W_r/2 + self.W_r/self.t_r*(W_shift_x + AY*self.h) # force on rear outter wheel
        W_r_in = W_r/2 - self.W_r/self.t_r*(W_shift_x + AY*self.h)  # force on rear inner wheel

        # Ensuring that none of the wheel loads are below zero as this would mean the car is tipping
        for i in [W_f_out, W_f_in, W_r_out, W_r_in]:
            if i < 0: return False

        C_f_out = abs(self.CMB_STC_F + (W_f_out-self.W_f/2)/self.K_RF*self.CMB_RT_F) # camber of front outter wheel
        C_f_in = abs(self.CMB_STC_F + (W_f_in-self.t_f/2)/self.K_RF*self.CMB_RT_F)   # camber of front inner wheel
        C_r_out = abs(self.CMB_STC_R + (W_r_out-self.t_r/2)/self.K_RR*self.CMB_RT_R) # camber of rear outter wheel
        C_r_in = abs(self.CMB_STC_R + (W_r_in-self.t_r/2)/self.K_RR*self.CMB_RT_R)   # camber of rear inner wheel

        if r == 0:
            S_f_in = steer
            S_f_out = steer
            S_r_in = 0
            S_r_out = 0
        else:
            S_f_in  = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a - np.cos(S_c)*self.t_f/2)))
            S_f_out = steer - np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_f/2)/(r - np.sin(S_c)*self.a + np.cos(S_c)*self.t_f/2)))
            S_r_in  = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a - np.cos(S_c)*self.t_r/2)))
            S_r_out = np.rad2deg(S_c + np.arctan((np.cos(S_c)*self.a + np.sin(S_c)*self.t_r/2)/(r + np.sin(S_c)*self.a + np.cos(S_c)*self.t_r/2)))
        
        FY_f_in = abs(self.tires.FY_curves.eval(S_f_in, W_f_in, C_f_in))
        FY_f_out = abs(self.tires.FY_curves.eval(S_f_out, W_f_out, C_f_out))
        FY_r_in = abs(self.tires.FY_curves.eval(S_r_in, W_r_in, C_r_in))
        FY_r_out = abs(self.tires.FY_curves.eval(S_r_out, W_r_out, C_r_out))

        FY_f = AY * self.W_car * self.W_bias # minimum necessary lateral force from front tires
        FY_r = AY * self.W_car * (1-self.W_bias) # minimum necessary lateral force from rear tires

        # checking if the car can generate enough lateral force
        if (FY_f > FY_f_out+FY_f_in) or (FY_r > FY_r_out+FY_r_in): return False

        if AX == 0: return True # returning true if no axial acceleration

        f_factor = ((FY_f_out + FY_f_in)**2 - FY_f**2)**0.5 / (FY_f_out + FY_f_in)
        r_factor = ((FY_r_out + FY_r_in)**2 - FY_r**2)**0.5 / (FY_r_out + FY_r_in)

        # max possible axial acceleration from front outter wheel
        FX_out_f = np.tan(FY_f_out/abs(self.tires.FY_curves.max(W_f_out, C_f_out))) * abs(self.tires.FX_curves.get_max(W_f_out, C_f_out))
        FX_out_r = np.tan(FY_r_out/abs(self.tires.FY_curves.max(W_r_out, C_r_out))) * abs(self.tires.FX_curves.get_max(W_r_out, C_r_out))
        FX_in_f = np.tan(FY_f_in/abs(self.tires.FY_curves.max(W_f_in, C_f_in))) * abs(self.tires.FX_curves.get_max(W_f_in, C_f_in))
        FX_in_r = np.tan(FY_r_in/abs(self.tires.FY_curves.max(W_r_in, C_r_in))) * abs(self.tires.FX_curves.get_max(W_r_in, C_r_in))
        
        # Calculating max lateral acceleration from tire traction
        if AX > 0:
            FX = FX_out_r + FX_in_r
        else:
            FX = FX_out_f + FX_in_f + FX_out_r + FX_in_r
        
        # Checking if the car can generate the necessary axial tire traction
        if abs(FX/self.W_car) < abs(AX): return False
        else: return True


    # recursive function to find the max axial acceleration; AY is lateral acceleration; g's
    def max_accel(self, AY, low_guess = 0, high_guess = 2):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration

        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0001:
            return guess

        if self.accel(AY, guess): # sets low estimate to the guess value if the car can handle cornering acceleration equal to the guess value
            return self.max_accel(AY, guess, high_guess)
        else: # sets high estimate to the guess value if the car cannot handle cornering acceleration equal to the guess value
            return self.max_accel(AY, low_guess, guess)
    
    def max_brake(self, AY, low_guess = -3, high_guess = 0):
        guess = (low_guess + high_guess)/2 # using the average of the low and high estimates as a guess for the max cornering acceleration
        
        # returns the guess value if high and low estimates have converged
        if high_guess - low_guess < 0.0001:
            return guess

        if self.accel(AY, guess): # sets high estimate to the guess value if the car can handle breaking acceleration equal to the guess value
            return self.max_brake(AY, low_guess, guess)
        else: # sets low estimate to the guess value if the car cannot handle breaking acceleration equal to the guess value
            return self.max_brake(AY, guess, high_guess)
    
    # calculates the max axial acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_accel(self, v, r, transmission_gear='optimal'):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track
        
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        A_tire = 0
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY:
                # linearly interpolating self.A_brake to find the max axial acceleration at lateral acceleration AY
                A_tire = ((AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])*self.A_accel[i] + (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1])*self.A_accel[i-1] - self.get_drag(v * 0.0568182))
                break

        A_tire -= drag # incorporating drag
        A_tire *= 32.17 * 12 # Converting from G's to in/s^2

        A_engn = self.drivetrain.get_F_accel(int(v*0.0568182), transmission_gear) / self.W_car # engine acceleration G's
        A_engn -= drag # incorporating drag
        A_engn *= 32.17*12 # converting from G's to in/s^2

        # returns either tire or engine acceleration depending on which is the limiting factor
        if A_tire < A_engn:
            return A_tire
        else:
            return A_engn

    
    # calculates the max braking acceleration (in/s^2) along a curve of given radius while traveling at a given velocity
    # params: [v = vehicle_speed (in/s)] :: [r = curve_radius (in)]
    # set r to zero for a track straight track with no curvature
    def curve_brake(self, v, r):
        AY = 0
        if r > 0:
            AY = v**2/r / 12 / 32.17 # finding lateral acceleration using a = v^2/r and coverting from in/s^2 to G's
        else:
            AY = 0 # set AY to zero if curve radius is zero as this represents a straight track
        
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)

        A_tire = 0
        for i in range(1, len(self.AY)):
            if self.AY[i] >= AY:
                # linearly interpolating self.A_brake to find the braking acceleration at lateral acceleration AY
                A_tire = (AY-self.AY[i-1])/(self.AY[i]-self.AY[i-1])*self.A_brake[i] + (self.AY[i]-AY)/(self.AY[i]-self.AY[i-1] )*self.A_brake[i-1]
                break
        
        A_tire -= drag # incorporating drag
        A_tire *= 32.17 * 12 # Converting from G's to in/s^2
        
        return A_tire
    
    # returns drag acceleration (in/s^2) given vehicle speed
    # v = speed (in/s)
    def curve_idle(self, v):
        drag = self.get_drag(v * 0.0568182) # finding drag acceleration (G's)
        drag *= 32.17 * 12 # converting from G's to in/s^2
        return -drag # returns negative because drag slows the car
    
    # returns drag force in G's (index = speed of car (mph))
    def get_drag(self, mph):
        if mph >= len(self.aero_arr)-1: # check if car speed exceeds aero_arr size
            return self.aero_arr[-1] # return drag accel value for highest speed if max speed is exceeded
        else:
            # finding drag by linearly interpolating the aero array
            ratio = mph % 1
            return self.aero_arr[int(mph)]*(1-ratio) + self.aero_arr[int(mph)+1]*ratio
    
    def adjust_weight(self, w):
        ratio = w / self.W_car

        self.W_1 *= ratio
        self.W_2 *= ratio
        self.W_3 *= ratio
        self.W_4 *= ratio
        self.W_car *= ratio
        self.W_f *= ratio
        self.W_r *= ratio
        self.K_RF *= ratio
        self.K_RR *= ratio
        self.K_rollF *= ratio
        self.K_rollR *= ratio

        self.compute_traction()
    

    def adjust_height(self, h):
        ratio = h / self.h
        self.h *= ratio
        self.H *= ratio
        self.z_rf *= ratio
        self.z_rr *= ratio
        self.compute_traction()
        
    
    def traction_curve(self):
        plt.plot(self.AY, self.A_accel)
        plt.plot(self.AY, self.A_brake)
        plt.xlabel('Lateral Acceleration (g\'s)')
        plt.ylabel('Axial Acceleration (g\'s)')
        plt.grid()
        plt.show()

    def get_values(self):
        # For gas
        # print("GAS")
        # for index, lat in enumerate(self.AY):
        #     car.accel(self, AY=lat, AX=self.A_accel[index])
        #     car.append_data_arrays(self,lat=lat, axi=self.A_accel[index], index=0)
        # print(f"Lateral acceleration (g's): {self.AY}")
        # print(f"Axial acceleration (g's): {self.A_accel}")
        # print(f"Vertical: {racecar.W_out_r_array}")
        # print(f"Lateral: {racecar.FY_out_r_array}")
        # print(f"Axial: {racecar.FX_out_r_array}\n")

        def get_rid_of_zeros(array):
            new_array = []
            for i in range(len(array)):
                new_array.append(array[i][0])
            print(new_array)
            return new_array

        # For braking
        print("BRAKING")
        for index, lat in enumerate(self.AY):
            car.accel(self, AY=lat, AX=self.A_brake[index])
            car.append_data_arrays(self,lat=lat, axi=self.A_brake[index], index=0)
        print(f"Lateral acceleration (g's): {self.AY}")
        print(f"Axial acceleration (g's): {self.A_accel}")
        print(f"Vertical: {racecar.W_out_r_array}")
        print(f"Lateral: {racecar.FY_out_r_array}")
        print(f"Axial: {racecar.FX_out_r_array}")

        stuff = {"Lateral Acceleration: ": self.AY, "Axial Acceleration: ": self.A_accel, "Vertical force: ": get_rid_of_zeros(racecar.W_out_r_array), "Lateral force: ": get_rid_of_zeros(racecar.FY_out_r_array), "Axial force: ": get_rid_of_zeros(racecar.FX_out_r_array)}

        with open("brake_data.pkl", 'wb') as f:
            pkl.dump(stuff, f)

racecar = car()