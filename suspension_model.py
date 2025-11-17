from matplotlib import pyplot as plt
import numpy as np
from numpy import sin, cos, arccos
from numpy import linalg as la
import car_model
import copy
import csv

class vect:
    def __init__(self, p1, p2, mag):
        u = (p2 - p1) / la.norm(p2 - p1)
        self.mag = abs(mag)
        self.v = mag * u
        self.x = mag * u[0]
        self.y = mag * u[1]
        self.z = mag * u[2]

class vect2:
    def __init__(self, v):
        self.x = v[0]
        self.y = v[1]
        self.z = v[2]
        self.v = copy.deepcopy(v)
        self.mag = la.norm(v)


# front bottom suspension node on frame
nd_fb = np.array([5.94, 17.52, -0.888])
# rear bottom suspension node on frame
nd_rb = np.array([-6, 18.587, -1.594])
# front top suspension node on frame
nd_ft = np.array([5.5, 17.076, 1.745])
# rear top suspension node on frame
nd_rt = np.array([-6, 17.076, 1.614])
# bell crank pivot
nd_bc = np.array([3.058, 18.359, 9.58])
# pushrod connection on bell crank
nd_pc = np.array([4.072, 17.569, 10.206])
# shock connection on bell crank
nd_sc = np.array([2.651, 20.965, 10.16])
# shock connection on frame
nd_sf = np.array([-2.354, 20.859, 5.628])

def node_forces(FX, FY, FZ):
    maximum = 3
    minimum = -3
    end_loop = False

    for i in range(15):
        if i == 14: end_loop = True

        # Length of bottom A-arm
        L_b = 18.587
        # Length of top A-arm
        L_t = 18.08

        L_c = 19.32760171663979
        L_sp = la.norm(nd_sf - nd_sc)
        L1 = 4.66
        L2 = 2.36
        L3 = 5.134

        def rotate(v, theta):
            R = np.matrix([[cos(theta), sin(theta), 0],
                        [-sin(theta), cos(theta), 0],
                        [0, 0, 1]])
            return np.array(R * np.matrix(v).T).flatten()

        # unit vectors for bell crank coordinate system
        u1 = (nd_pc - nd_bc) / la.norm(nd_pc - nd_bc)
        u3 = np.cross((nd_sc - nd_bc), u1)
        u3 = u3 / la.norm(u3)
        u2 = np.cross(u1, u3)

        # matrix for converting from global to bell crank coordinate system
        bc_to_global = np.matrix([u1, u2, u3]).T
        global_to_bc = la.inv(bc_to_global)

        def to_bc(v): return np.array(global_to_bc * np.matrix(v-nd_bc).T).flatten()
        def to_global(v): return np.array(bc_to_global * np.matrix(v).T).flatten() + nd_bc
        def to_global_v(v): return np.array(bc_to_global * np.matrix(v).T).flatten()

        nd_sf_bc = to_bc(nd_sf)
        nd_pc_bc = to_bc(nd_pc)
        nd_sc_bc = to_bc(nd_sc)

        z1 = (minimum + maximum) / 2
        y1 = nd_fb[1] - (L_b**2 - (nd_fb[2] - z1)**2)**0.5
        theta = arccos((nd_ft[1] - y1) / ((nd_ft[1] - y1)**2 + (nd_ft[2] - z1)**2)**0.5) + arccos(((nd_ft[1]-y1)**2 + (nd_ft[2]-z1)**2 + L3**2 - L_t**2)/(2*L3*((nd_ft[1]-y1)**2 + (nd_ft[2]-z1)**2)**0.5))
        y2 = y1 + L3 * cos(theta)
        z2 = z1 + L3 * sin(theta)

        theta = arccos((y2 - y1) / ((y2 - y1)**2 + (z2 - z1)**2)**0.5) - arccos((L2**2 + L3**2 - L1**2) / (2 * L2 * L3))
        y3 = y1 + L2 * cos(theta)
        z3 = z1 + L2 * sin(theta)

        b1 = np.array([0, y1, z1])
        b2 = np.array([0, y2, z2])
        b3 = np.array([0, y3, z3])

        nd_b3_bc = to_bc(b3)

        max = np.pi/6
        min = -np.pi/6
        theta = 0
        for i in range(15):
            theta = (max+min)/2
            sc = rotate(nd_sc_bc, theta)
            pc = rotate(nd_pc_bc, theta)
            if la.norm(pc - nd_b3_bc) > L_c:
                min = theta
            else:
                max = theta
        F_sp = (L_sp - la.norm(sc - nd_sf_bc)) * 250
        # system matrix for bellcrank
        F_c_x = (nd_b3_bc[0]-pc[0])/L_c
        F_c_y = (nd_b3_bc[1]-pc[1])/L_c
        M_c = F_c_x * pc[1] - F_c_y * pc[0]
        A = np.array([[1, 0, F_c_x], # FX
                      [0, 1, F_c_y], # FY
                      [0, 0, M_c  ]])# MZ

        F_sp_x = F_sp * (sc[0]-nd_sf_bc[0])/la.norm(sc - nd_sf_bc)
        F_sp_y = F_sp * (sc[1]-nd_sf_bc[1])/la.norm(sc - nd_sf_bc)
        M_sp = F_sp_x * sc[1] - F_sp_y * sc[0]

        B = np.array([[-F_sp_x], 
                      [-F_sp_y], 
                      [-M_sp  ]])

        x = la.solve(A, B).flatten()
        F_pr = x[2]
        F_bc_v = to_global_v(np.array([-x[0], -x[1], 0]))
        F_sp_v = to_global_v(np.array([-F_sp_x, -F_sp_y, 0]))
        pc = to_global(pc)

        mag = la.norm(nd_fb - b1)
        FX_fb = (nd_fb[0] - b1[0]) / mag
        FY_fb = (nd_fb[1] - b1[1]) / mag
        FZ_fb = (nd_fb[2] - b1[2]) / mag
        MX_fb = 0
        MY_fb = 0

        mag = la.norm(nd_rb - b1)
        FX_rb = (nd_rb[0] - b1[0]) / mag
        FY_rb = (nd_rb[1] - b1[1]) / mag
        FZ_rb = (nd_rb[2] - b1[2]) / mag
        MX_rb = 0
        MY_rb = 0

        mag = la.norm(nd_ft - b2)
        FX_ft = (nd_ft[0] - b2[0]) / mag
        FY_ft = (nd_ft[1] - b2[1]) / mag
        FZ_ft = (nd_ft[2] - b2[2]) / mag
        MX_ft = FY_ft * (b2[2] - b1[2]) - FZ_ft * (b2[1] - b1[1])
        MY_ft = FX_ft * (b2[2] - b1[2])

        mag = la.norm(nd_rt - b2)
        FX_rt = (nd_rt[0] - b2[0]) / mag
        FY_rt = (nd_rt[1] - b2[1]) / mag
        FZ_rt = (nd_rt[2] - b2[2]) / mag
        MX_rt = FY_rt * (b2[2] - b1[2]) - FZ_rt * (b2[1] - b1[1])
        MY_rt = FX_rt * (b2[2] - b1[2])

        mag = la.norm(pc - b3)
        FX_p = (pc[0] - b3[0]) / mag
        FY_p = (pc[1] - b3[1]) / mag
        FZ_p = (pc[2] - b3[2]) / mag
        MX_p = FY_p * (b3[2] - b1[2]) - FZ_p * (b3[1]-b1[1])
        MY_p = FX_p * (b3[2] - b1[2])

        A = [[FX_fb, FX_ft, FX_rb, FX_rt, FX_p], # FX
             [FY_fb, FY_ft, FY_rb, FY_rt, FY_p], # FY
             [FZ_fb, FZ_ft, FZ_rb, FZ_rt, FZ_p], # FZ
             [MX_fb, MX_ft, MX_rb, MX_rt, MX_p], # MX
             [MY_fb, MY_ft, MY_rb, MY_rt, MY_p]] # MY
        
        

        B = [[-FX],
             [-FY],
             [-FZ],
             [FY*5.63],
             [0]]


        y = la.solve(A, B).flatten()

        if abs(y[4] - F_pr) < 0.5:
            end_loop = True
        elif y[4] > F_pr:
            maximum = z1
        else:
            minimum = z1
        
        if end_loop:
            #print(A)
            #print(B)
            #print(y)
            vvect_fb = vect(nd_fb, b1, y[0])
            vvect_ft = vect(nd_ft, b2, y[1])
            vvect_rb = vect(nd_rb, b1, y[2])
            vvect_rt = vect(nd_rt, b2, y[3])
            vvect_bc = vect2(F_bc_v)
            vvect_sp = vect2(F_sp_v)
            return vvect_fb, vvect_ft, vvect_rb, vvect_rt, vvect_bc, vvect_sp
        





car = car_model.car()

tc_x = np.concatenate((car.A_accel, np.flip(car.A_brake[1:-1])))
tc_y = np.concatenate((car.AY, np.flip(car.AY[1:-1])))
angles = []
for i in range(len(tc_x)):
    angles.append(np.arctan2(tc_y[i], tc_x[i]) * 180 / np.pi)

AX = []
AY = []
angle_step = 10
A_angles = np.linspace(0, 180, int(180/10+1))
for i in A_angles:
    for j in range(len(angles)):
        if i <= angles[j]:
            ratio = (i - angles[j]) / (angles[j+1] - angles[j])
            AX.append(tc_x[j] * (1 - ratio) + tc_x[j+1] * ratio)
            AY.append(tc_y[j] * (1 - ratio) + tc_y[j+1] * ratio)
            break

AX.append(car.A_brake[0])
AY.append(0)


#node_forces(100, 150, 200)
#vect_fb, vect_ft, vect_rb, vect_rt, vect_bc, vect_sp = node_forces(0, 0, 238)
#vect_ifb, vect_ift, vect_irb, vect_irt, vect_ibc, vect_isp = node_forces(0, 0, 0)
max_mag = 0
j = 0


theta = []
peak_angles = [10, 60, 90, 150]
a_freq = np.zeros(len(A_angles))
with open('Accel Data - Autocross, accel, endurance.csv', 'r') as file:
    reader = csv.reader(file)
    i = 0
    theta_accel = []
    theta_auto = []
    theta_endur = []
    for row in reader:
        i += 1
        if i <= 2:
            continue
        theta_accel.append(np.arctan2(float(row[0]), float(row[1])) * 180 / np.pi)
        #theta_auto.append(np.arctan2(float(row[2]), float(row[3])) * 180 / np.pi)
        theta_endur.append(np.arctan2(float(row[4]), float(row[5])) * 180 / np.pi)

    theta = np.concatenate((theta_accel, theta_endur))

    # finding local maxima and minima
    poi = [0]
    for j in range(1, len(theta)-1):
        if ((theta[j-1] < theta[j] > theta[j+1]) or (theta[j-1] > theta[j] < theta[j+1])):
            poi.append(j)
    # removing insignificant peaks
    i = 0

    while i < len(poi)-1:
        if abs(theta[poi[i+1]] - theta[poi[i]]) < 5:
            poi.pop(i+1)
            poi.pop(i)
        else:
            i += 1
    
    # adding points where function is not continuous
    new_points = []
    for j in range(1, len(theta)-1):
        if abs(theta[j] - theta[j+1]) > 20:
            new_points.append(j)
            new_points.append(j+1)
    
    # adding new points to poi
    for k in new_points:
        if k not in poi:
            poi.append(k)
    
    # adding poi angles to frequency array
    for i in poi:
        a_freq[int(theta[i]/angle_step+0.5)] += 1
    
    x = np.linspace(0, len(theta), len(theta))
    plt.plot(x, theta)
    x = []
    y = []
    for i in poi:
        x.append(i)
        y.append(theta[i])
    plt.scatter(x, y, color='red')
    plt.show()

    # adding points at specified angles of interest
    for j in range(1, len(theta)-1):
        for k in peak_angles:
            if theta[j] < k <= theta[j+1]:
                a_freq[k//angle_step] += 1

with open('angle_dataset.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['sample', 'angle (deg)'])
    for i in range(len(theta)):
        writer.writerow([i+1, theta[i]])


with open('subframe_forces.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    nodes = ['front back control arm', 'front top control arm', 'rear back control arm', 'rear top control arm', 'bell  crank mount', 'shock mount']
    
    header = ['angle (deg)', 'Frequency', '-----']
    for i in nodes:
        for j in ['x', 'y', 'z']:
            header.append(f'outter {i} {j}')
    
    header.append('-----')
    for i in nodes:
        for j in ['x', 'y', 'z']:
            header.append(f'inner {i} {j}')
    
    header.append('-----')
    header.append('wheel x out')
    header.append('wheel y out')
    header.append('wheel z out')
    header.append('-----')
    header.append('wheel x in')
    header.append('wheel y in')
    header.append('wheel z in')
    writer.writerow(header)

    Forces = [[], [], [], [], [], []]
    Leg = ['fb', 'ft', 'rb', 'rt', 'bc', 'sp']

    for i in range(len(A_angles)):
        W_f = car.W_f - car.h*car.W_car*AX[i]/car.l # Vertical force on front track (lb)
        W_r = car.W_r + car.h*car.W_car*AX[i]/car.l # Vertical force on rear track (lb)

        roll = (W_f*car.z_rf + W_r*car.z_rr)*AY[i] / (car.K_rollF+car.K_rollR) # roll of car (rad)
        W_shift_x = roll * car.H # lateral shift in center of mass (in)

        W_out_r = W_r/2 + car.W_r/car.t_r*(W_shift_x + AY[i]*car.h) # force on rear outter wheel
        W_in_r  = W_r/2 - car.W_r/car.t_r*(W_shift_x + AY[i]*car.h)  # force on rear inner wheel
        W_out_f = W_f/2 + car.W_f/car.t_f*(W_shift_x + AY[i]*car.h) # force on front outter wheel
        W_in_f  = W_f/2 - car.W_f/car.t_f*(W_shift_x + AY[i]*car.h)  # force on front inner wheel

        C_out_r = abs(car.CMB_STC_F + (W_out_r-car.t_r/2)/car.K_RR*car.CMB_RT_R) # camber of rear outter wheel
        C_in_r = abs(car.CMB_STC_F + (W_in_r-car.t_r/2)/car.K_RR*car.CMB_RT_R)   # camber of rear inner wheel
        C_out_f = abs(car.CMB_STC_F + (W_out_f-car.t_f/2)/car.K_RR*car.CMB_RT_F) # camber of front outter wheel
        C_in_f = abs(car.CMB_STC_F + (W_in_f-car.t_f/2)/car.K_RR*car.CMB_RT_F)   # camber of front inner wheel


        FY_out_r = car.tires.traction('corner', W_out_r, C_out_r) # max possible lateral acceleration from rear outter wheel
        FY_in_r = car.tires.traction('corner', W_in_r, C_in_r)    # max possible lateral acceleration from rear inner wheel
        FY_out_f = car.tires.traction('corner', W_out_f, C_out_f) # max possible lateral acceleration from front outter wheel
        FY_in_f = car.tires.traction('corner', W_in_f, C_in_f)    # max possible lateral acceleration from front inner wheel

        FY_r = AY[i] * car.W_car * (1-car.W_bias) # minimum necessary lateral force from rear tires
        FY_r_max = FY_out_r + FY_in_r
        FY_f = AY[i] * car.W_car * car.W_bias # minimum necessary lateral force from front tires
        FY_f_max = FY_out_f + FY_in_f

        FY_out_r *= FY_r / FY_r_max
        FY_in_r *= FY_r / FY_r_max
        FY_out_f *= FY_f / FY_f_max
        FY_in_f *= FY_f / FY_f_max

        r_factor = 0
        if FY_r_max**2 - FY_r**2 > 0:
            r_factor = (FY_r_max**2 - FY_r**2)**0.5 / FY_r_max
        
        f_factor = 0
        if FY_f_max**2 - FY_f**2 > 0:
            f_factor = (FY_f_max**2 - FY_f**2)**0.5 / FY_f_max
        
        FX_out_r = r_factor * car.tires.traction('accel', W_out_r, C_out_r) # max possible axial acceleration from rear outter wheel
        FX_in_r = r_factor * car.tires.traction('accel', W_in_r, C_in_r)    # max possible axial acceleration from rear inner wheel
        FX_out_f = f_factor * car.tires.traction('accel', W_out_f, C_out_f) # max possible axial acceleration from front outter wheel
        FX_in_f = f_factor * car.tires.traction('accel', W_in_f, C_in_f)    # max possible axial acceleration from front inner wheel

        if AX[i] < 0:
            FX_out_r = -FX_out_r
            FX_in_r = -FX_in_r
            FX_out_f = -FX_out_f
            FX_in_f = -FX_in_f
        
        v_fb, v_ft, v_rb, v_rt, v_bc, v_sp = node_forces(FX_out_r, FY_out_r, W_out_r)
        arr_out = []
        for j in [v_fb, v_ft, v_rb, v_rt, v_bc, v_sp]:
            arr_out.append(j.x)
            arr_out.append(j.y)
            arr_out.append(j.z)
        
        v_fb, v_ft, v_rb, v_rt, v_bc, v_sp = node_forces(FX_in_r, -FY_in_r, W_in_r)
        arr_in = []
        for j in [v_fb, v_ft, v_rb, v_rt, v_bc, v_sp]:
            arr_in.append(j.x)
            arr_in.append(j.y)
            arr_in.append(j.z)
        
        arr_hubs = []
        for j in [FX_out_r, FY_out_r, W_out_r, '-----', FX_in_r, FY_in_r, W_in_r]:
            arr_hubs.append(j)

        arr = [A_angles[i]] + [a_freq[i]] + ['-----'] + arr_out + ['-----'] + arr_in + ['-----'] + arr_hubs
        writer.writerow(arr)


'''arr = [['Outer Bottom Front Suspension Node:', vect_fb],
       ['Outer Top Front Suspension Node:', vect_ft],
       ['Outer Bottom Rear Suspension Node:', vect_rb],
       ['Outer Top Rear Suspension Node:', vect_rt],
       ['Outer Bell Crank Pivot:', vect_bc],
       ['Outer Shock Mount:', vect_sp],
       ['Inner Bottom Front Suspension Node:', vect_ifb],
       ['Inner Top Front Suspension Node:', vect_ift],
       ['Inner Bottom Rear Suspension Node:', vect_irb],
       ['Inner Top Rear Suspension Node:', vect_irt],
       ['Inner Bell Crank Pivot:', vect_ibc],
       ['Inner Shock Mount:', vect_isp]]

for i in arr:
    print(i[0])
    v = i[1]
    print(f'Total Force Magnitude = {v.mag}')
    print(f'Force x = {v.x}')
    print(f'Force y = {v.y}')
    print(f'Force z = {v.z}')
    print()'''