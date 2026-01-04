import pickle
import numpy as np
import matplotlib.pyplot as plt

###############################################################################
# This script stores all dimensions and variables for the Aerodynamic Affects #
###############################################################################

# Importing the maximum lateral force list using PICKLE
with open('C:/Users/maxwe/Downloads/FSAE/2023-2024 Car/Repo/tire_model.pkl', 'rb') as f:
    tire_model = pickle.load(f)

CD = 0.494040343 # Coefficient of Drag
CL = 0.166186145 # Coefficient of Lift
FA = 0.865 # Frontal Area, in^2
D = 1.205 # lb/in^3, density of air

def drgFrcCalc(CD, D, FA, v):
    return CD*FA*D*v**2 / 2

vel_array_mph = np.arange(101) # mph, array from 0 - 99 mph
vel_array_ins = vel_array_mph*0.44707 # m/s, array from 0 - 99 mph but converted to m/s
aero_array_N = drgFrcCalc(CD, D, FA, vel_array_ins) # N, drag force where the index is in mph (lbs)
aero_array_lb = aero_array_N*0.2248 # converting N back to lbs
print(vel_array_mph)
print(aero_array_lb)

# Defining the variables in a dictionary
variables = {'aero_array': aero_array_lb}

# Pickling the dictionary
with open('aero_model.pkl', 'wb') as f:
    pickle.dump(variables, f)
