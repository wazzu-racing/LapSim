# The following program generates a curve consisting of two segments, each segment being of a specific radius and arclength
# The curve has specified starting and ending locations and angles.
# The first segment of the curve is reffered to as curve A, and the second as curve B.
# 
# For a curve to be generated, seven inputs are required.
#   - The first two of these inputs are the x and y coordinates of the curve
#   - The next input is the angle (in degrees) at which the curve starts (zero degrees points to the right, increasing this angle 
#     rotates it ccw)
#   - The fourth and fifth inputs respectively are the x and y coordinates where the curve must finish
#   - The sixth input is the angle the car is moving at when exiting the curve

cmpt_vel = 1

import numpy as np
from matplotlib import pyplot as plt
from gen_lapsim import lapsim

plt_resolution = 3

# quadratic formula equation, returns 2 outputs
quad_form = lambda A, B, C : ((-B + (B**2 - 4*A*C)**0.5)/(2*A),
                              (-B - (B**2 - 4*A*C)**0.5)/(2*A))

transform_vect = np.vectorize(lambda s, v, t : s * v + t)

class two_step_curve():

    def __init__ (self, Ax, Ay, A_theta, Bx, By, B_theta, scaler):
        # defining the starting positition of the curve
        self.Ax = Ax
        self.Ay = Ay
        # defines the direction (in radians) of the center of curve A from its starting position
        self.A_theta = A_theta + 3*np.pi/2
        # defines the ending position of the curve
        self.Bx = Bx
        self.By = By
        # defines the direction (in radians) of the center of curve B from its ending position
        self.B_theta = B_theta + np.pi/2

        self.A_B_ratio = 2**scaler

        # finds the 
        self.find_curve()


    def find_curve(self):
        # Unit vectors that definine the center of curves A and B from the start/end of the curve
        self.UAx = np.cos(self.A_theta) * self.A_B_ratio
        self.UAy = np.sin(self.A_theta) * self.A_B_ratio
        self.UBx = np.cos(self.B_theta)
        self.UBy = np.sin(self.B_theta)

        a = (self.UAx - self.UBx)**2 + (self.UAy - self.UBy)**2 - (1 + self.A_B_ratio)**2
        b = 2 * ((self.UAx - self.UBx)*(self.Ax - self.Bx) + (self.UAy - self.UBy)*(self.Ay - self.By))
        c = (self.Ax - self.Bx)**2 + (self.Ay - self.By)**2

        r1, r2 = quad_form(a, b, c)

        length_A1, length_B1, arc_angle_A1, arc_angle_B1 = self.get_arc_length(r1)
        length_A2, length_B2, arc_angle_A2, arc_angle_B2 = self.get_arc_length(r2)

        if length_A1 + length_B1 < length_A2 + length_B2:
            self.arc_length_A = float(length_A1)
            self.arc_length_B = float(length_B1)
            self.arc_angle_A = float(arc_angle_A1)
            self.arc_angle_B = float(arc_angle_B1)
            self.radius = float(r1)
            self.radius_A = float(abs(r1 * self.A_B_ratio))
            self.radius_B = float(abs(r1))
        else:
            self.arc_length_A = float(length_A2)
            self.arc_length_B = float(length_B2)
            self.arc_angle_A = float(arc_angle_A2)
            self.arc_angle_B = float(arc_angle_B2)
            self.radius = float(r2)
            self.radius_A = float(abs(r2 * self.A_B_ratio))
            self.radius_B = float(abs(r2))

    
    def get_arc_length(self, r):
        # Defines x and y coords of the point which curve A rotates around
        Ac_x = self.Ax + self.UAx * r
        Ac_y = self.Ay + self.UAy * r
        # Defines x and y coords of the point which curve B rotates around
        Bc_x = self.Bx + self.UBx * r
        Bc_y = self.By + self.UBy * r

        # Defines the starting angle of Curve A
        if r < 0:
            curve_A_start = self.A_theta
        else:
            curve_A_start = self.A_theta - np.pi

        # Defining the ending angle of Curve A
        curve_A_end = np.arccos((Bc_x - Ac_x) / abs(r + r * self.A_B_ratio))
        if Bc_y < Ac_y:
            curve_A_end = 2 * np.pi - curve_A_end

        # Finding the arclength of Curve A using the start and ending angle
        if r > 0: # If r1 is positive, the curve moves clockwise
            arc_angle_A = (curve_A_start - curve_A_end) % (2*np.pi)
        else: # If r1 is negative, the curve moves counterclockwise
            arc_angle_A = (curve_A_end - curve_A_start) % (2*np.pi)
        
        # Finding arc length of curve A
        arc_length_A = abs(arc_angle_A * r * self.A_B_ratio)

        # Defining the starting angle of Curve B
        curve_B_start = np.arccos((Ac_x - Bc_x) / abs(r + r * self.A_B_ratio))
        if Ac_y < Bc_y:
            curve_B_start = 2 * np.pi - curve_B_start
        
         # Defines the ending angle of Curve B
        if r < 0:
            curve_B_end = self.B_theta
        else:
            curve_B_end = self.B_theta - np.pi

        # Finding the arclength of Curve B using the start and ending angle
        if r < 0: # If r1 is positive, the curve moves counterclockwise
            arc_angle_B = (curve_B_start - curve_B_end) % (2*np.pi)
        else: # If r1 is negative, the curve moves clockwise
            arc_angle_B = (curve_B_end - curve_B_start) % (2*np.pi)
        
        # Finding arc length of curve B
        arc_length_B = abs(arc_angle_B * r)

        return arc_length_A, arc_length_B, arc_angle_A, arc_angle_B
    

    def plot_curve(self):
        if self.radius > 0:
            direction = 'cw'
        else:
            direction = 'ccw'
        
        # Defines x and y coords of the point which curve A rotates around
        Ac_x = self.Ax + self.UAx * self.radius
        Ac_y = self.Ay + self.UAy * self.radius
        
        # Defines the starting angle of Curve A
        if self.radius < 0:
            curve_A_start = self.A_theta
        else:
            curve_A_start = self.A_theta - np.pi
        
        self.plot_arc(Ac_x, Ac_y, curve_A_start, self.arc_angle_A, abs(self.radius) * self.A_B_ratio, direction)


        # Defines x and y coords of the point which curve B rotates around
        Bc_x = self.Bx + self.UBx * self.radius
        Bc_y = self.By + self.UBy * self.radius

        # Defines the ending angle of Curve B
        if self.radius < 0:
            curve_B_end = self.B_theta
        else:
            curve_B_end = self.B_theta - np.pi
        
        self.plot_arc(Bc_x, Bc_y, curve_B_end, self.arc_angle_B, abs(self.radius), direction)
        

    def plot_arc(self, x_center, y_center, start_angle, arc_angle, r, direction = 'ccw'):
        if direction == 'ccw':
            theta = np.linspace(start_angle, start_angle+arc_angle, int(arc_angle * r) * plt_resolution)
        elif direction == 'cw':
            theta = np.linspace(start_angle-arc_angle, start_angle, int(arc_angle * r) * plt_resolution)
        
        x = []
        y = []
        for i in theta:
            x.append(x_center + r * np.cos(i))
            y.append(y_center + r * np.sin(i))
        
        plt.plot(x, y)










class track():

    def __init__ (self, x1, y1, x2, y2):
        self.gate_x1 = x1 + [x1[0]]
        self.gate_y1 = y1 + [y1[0]]
        self.gate_x2 = x2 + [x2[0]]
        self.gate_y2 = y2 + [y2[0]]
        self.gate_impact = np.linspace(0.5, 0.5, len(self.gate_x1))
        self.points_x = np.zeros(len(self.gate_impact))
        self.points_y = np.zeros(len(self.gate_impact))
        for i in range(len(self.points_x)):
            self.points_x[i] = (self.gate_x1[i] + self.gate_x2[i]) / 2
            self.points_y[i] = (self.gate_y1[i] + self.gate_y2[i]) / 2
        self.points = len(x1)
        self.angles = np.zeros(len(self.points_x))
        self.radius_adjustment = np.zeros(self.points)

        for i in range(1, len(self.points_x)):
            self.angles[i] = np.arccos((self.points_x[i] - self.points_x[i-1]) / ((self.points_x[i] - self.points_x[i-1])**2 + (self.points_y[i] - self.points_y[i-1])**2)**0.5)
            if self.points_y[i-1] > self.points_y[i]:
                self.angles[i] = 2*np.pi - self.angles[i]
        
        self.create_segments()

    def create_segments(self):
        self.points_x = np.zeros(len(self.gate_impact))
        self.points_y = np.zeros(len(self.gate_impact))
        for i in range(len(self.points_x)):
            self.points_x[i] = self.gate_x1[i]*self.gate_impact[i] + self.gate_x2[i]*(1-self.gate_impact[i])
            self.points_y[i] = self.gate_y1[i]*self.gate_impact[i] + self.gate_y2[i]*(1-self.gate_impact[i])
        
        self.track_segments = []
        for i in range(len(self.angles)-1):
            self.track_segments.append(two_step_curve(self.points_x[i], self.points_y[i], self.angles[i], self.points_x[i+1], self.points_y[i+1], self.angles[i+1], self.radius_adjustment[i]))
        #self.track_segments.append(two_step_curve(self.points_x[-1], self.points_y[-1], self.angles[-1], self.points_x[0], self.points_y[0], self.angles[0], self.radius_adjustment[-1]))

        self.arc_lengths = []
        self.arc_radii = []
        for i in self.track_segments:
            self.arc_lengths.append(i.arc_length_A)
            self.arc_lengths.append(i.arc_length_B)
            self.arc_radii.append(i.radius_A)
            self.arc_radii.append(i.radius_B)

        self.track_length = np.sum(self.arc_lengths)


    def plot_track(self):
        for i in self.track_segments:
            i.plot_curve()

    def run_sim(self, sim_type):
        #self.update_arc_info()
        match sim_type:
            case 'single point':
                sim = lapsim.single_point(self.arc_lengths, self.arc_radii)   
                return sim.run()

    def plot_sim(self, sim_type):
        s, v, t = self.run_sim(sim_type)
        plt.plot(s, v)
        return t
    
        
    

















    def adjust_course(self, itterations):
        #best_angles = [] # stores whichever track angles provided the best results across all itterations
        best_radii = []  # stores whichever radius adjustments have provided the best results across all itterations
        best_time = np.inf # stores the lowest lap time across all simulation results

        for i in range(itterations):

            # runs the sim
            sim = lapsim.single_point(self.arc_lengths, self.arc_radii)
            nds, v3, t = sim.run()

            # checks if the current itteration preforms better than the best itteration so far
            if t < best_time:
                # updating best itteration info
                best_angles = np.array(self.angles)
                best_radii = np.array(self.radius_adjustment)
                best_gates = np.array(self.gate_impact)
                best_time = t

            # this next portion of the code in the for loop below goes through every node angle and reavulates the lap time
            # with a slight change in each angle to determine how changing the angle effects the lap time. All the lap times
            # with the new angles are stored in an array and then the angles of the entire track are adjusted using a gradient
            # descent algorithm.
            angle_step = 0.1
            movement_step = 0.05 * cmpt_vel # this variable determines the magnitude of how much the angles will change with each itteration
            dt = np.zeros(len(self.angles))
            for i in range(0, len(self.angles)):

                new_arc_radii = [0, 0, 0, 0]    # stores the arc radii of the new segments
                new_arc_lengths = [0, 0, 0, 0]  # stores arc lengths of new segments

                # generates a two step curve with the new angle at the current node for the first two segments
                if i >= 1:
                    new_two_step_arc = two_step_curve(self.points_x[i-1], self.points_y[i-1], self.angles[i-1], self.points_x[i], self.points_y[i], self.angles[i]+angle_step, self.radius_adjustment[i-1])
                    new_arc_radii[0] = new_two_step_arc.radius_A
                    new_arc_radii[1] = new_two_step_arc.radius_B
                    new_arc_lengths[0] = new_two_step_arc.arc_length_A
                    new_arc_lengths[1] = new_two_step_arc.arc_length_B

                # generates a two step curve with the new angle at the current node for the last two segments
                if i <= len(self.angles)-2:
                    new_two_step_arc = two_step_curve(self.points_x[i], self.points_y[i], self.angles[i]+angle_step, self.points_x[(i+1)%(self.points+1)], self.points_y[(i+1)%(self.points+1)], self.angles[(i+1)%(self.points+1)], self.radius_adjustment[i])
                    new_arc_radii[2] = new_two_step_arc.radius_A
                    new_arc_radii[3] = new_two_step_arc.radius_B
                    new_arc_lengths[2] = new_two_step_arc.arc_length_A               
                    new_arc_lengths[3] = new_two_step_arc.arc_length_B

                starting_arc = i * 2 - 2
                if starting_arc < 0:
                    starting_arc = 0
                    new_arc_lengths = new_arc_lengths[2:4]
                    new_arc_radii = new_arc_radii[2:4]
                
                ending_arc = i * 2 + 2
                if ending_arc > len(self.arc_lengths):
                    ending_arc = len(self.arc_lengths)
                    new_arc_lengths = new_arc_lengths[0:2]
                    new_arc_radii = new_arc_radii[0:2]

                # evaluates the change in lap time when incorporating the segments with the new angle
                # dt[i] is an approximation of the partial derivative of the lap time in respect to angle i
                # this makes dt an approximation of the gradient of the lap time in respect to the node angles
                dt[i] = sim.arcEvaluator(starting_arc, ending_arc, new_arc_lengths, new_arc_radii)
                
            print(t)

            # finds the magnitude of the gradient vector dt
            mag_dt = (np.sum(dt**2))**0.5

            # moves all angles in the direction of gradient vector dt but magnitude of movement_step
            self.angles += dt/mag_dt*movement_step

            self.create_segments()

            # below is the same algorithm as the one above but adjusting the radius_adjustment perameter of the track instead of the node angles
            radius_step = 0.02
            movement_step = 0.015 * cmpt_vel
            dt = np.zeros(len(self.radius_adjustment))
            for i in range(0, len(self.angles)-1):

                new_arc_radii = [0, 0]
                new_arc_lengths = [0, 0]

                new_two_step_arc = two_step_curve(self.points_x[i], self.points_y[i], self.angles[i], self.points_x[i+1], self.points_y[i+1], self.angles[i+1], self.radius_adjustment[i] + radius_step)
                new_arc_radii[0] = new_two_step_arc.radius_A
                new_arc_radii[1] = new_two_step_arc.radius_B
                new_arc_lengths[0] = new_two_step_arc.arc_length_A               
                new_arc_lengths[1] = new_two_step_arc.arc_length_B

                starting_arc = i * 2
                ending_arc = i * 2 + 2
                    
                dt[i] = sim.arcEvaluator(starting_arc, ending_arc, new_arc_lengths, new_arc_radii)
                

            mag_dt = (np.sum(dt**2))**0.5
            self.radius_adjustment += dt/mag_dt*movement_step



            gate_step = 0.03
            movement_step = 0.07 * cmpt_vel
            og_step = movement_step
            dt = np.zeros(len(self.gate_impact))
            for i in range(0, len(self.angles)):
                new_arc_radii = [0, 0, 0, 0]    # stores the arc radii of the new segments
                new_arc_lengths = [0, 0, 0, 0]  # stores arc lengths of new segments
                new_x = self.gate_x1[i]*(self.gate_impact[i]+gate_step) + self.gate_x2[i]*(1-self.gate_impact[i]-gate_step)
                new_y = self.gate_y1[i]*(self.gate_impact[i]+gate_step) + self.gate_y2[i]*(1-self.gate_impact[i]-gate_step)
              
                # generates a two step curve with the new angle at the current node for the first two segments
                if i >= 1:
                    new_two_step_arc = two_step_curve(self.points_x[i-1], self.points_y[i-1], self.angles[i-1], new_x, new_y, self.angles[i], self.radius_adjustment[i-1])
                    new_arc_radii[0] = new_two_step_arc.radius_A
                    new_arc_radii[1] = new_two_step_arc.radius_B
                    new_arc_lengths[0] = new_two_step_arc.arc_length_A
                    new_arc_lengths[1] = new_two_step_arc.arc_length_B

                # generates a two step curve with the new angle at the current node for the last two segments
                if i <= len(self.angles)-2:
                    new_two_step_arc = two_step_curve(new_x, new_y, self.angles[i], self.points_x[(i+1)%(self.points+1)], self.points_y[(i+1)%(self.points+1)], self.angles[(i+1)%(self.points+1)], self.radius_adjustment[i])
                    new_arc_radii[2] = new_two_step_arc.radius_A
                    new_arc_radii[3] = new_two_step_arc.radius_B
                    new_arc_lengths[2] = new_two_step_arc.arc_length_A               
                    new_arc_lengths[3] = new_two_step_arc.arc_length_B

                starting_arc = i * 2 - 2
                if starting_arc < 0:
                    starting_arc = 0
                    new_arc_lengths = new_arc_lengths[2:4]
                    new_arc_radii = new_arc_radii[2:4]
                
                ending_arc = i * 2 + 2
                if ending_arc > len(self.arc_lengths):
                    ending_arc = len(self.arc_lengths)
                    new_arc_lengths = new_arc_lengths[0:2]
                    new_arc_radii = new_arc_radii[0:2]
                
                # evaluates the change in lap time when incorporating the segments with the new angle
                # dt[i] is an approximation of the partial derivative of the lap time in respect to angle i
                # this makes dt an approximation of the gradient of the lap time in respect to the node angles
                dt[i] = sim.arcEvaluator(starting_arc, ending_arc, new_arc_lengths, new_arc_radii)

                if dt[i] > 0 and self.gate_impact[i] >= 1:
                    dt[i] = 0
                    movement_step -= og_step / len(self.gate_impact)
                elif dt[i] < 0 and self.gate_impact[i] <= 0:
                    dt[i] = 0
                    movement_step -= og_step / len(self.gate_impact)
                

            mag_dt = (np.sum(dt**2))**0.5
            for i in range(len(self.gate_impact)):
                self.gate_impact[i] += dt[i]/mag_dt*movement_step
                if self.gate_impact[i] > 1:
                    self.gate_impact[i] = 1
                elif self.gate_impact[i] < 0:
                    self.gate_impact[i] = 0

        # sets all track perameters to the stored peramters which provided the best results
        self.angles = best_angles
        self.radius_adjustment = best_radii
        self.gate_impact = best_gates
        print(best_time)
        self.create_segments()