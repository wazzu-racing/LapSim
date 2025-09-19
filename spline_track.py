import numpy as np
from matplotlib import pyplot as plt
import time
import lapsim
import pickle

car_rad = 29
v_min = 0
class node():
   
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

        self.dist = ((x2-x1)**2 + (y2-y1)**2)**0.5
        self.shift = self.dist / 2

        self.prev_nd = None
        self.next_nd = None
        self.prev_arc = None
        self.next_arc = None
        self.vx = 1
        self.vy = 1

        self.update_shift()
    
    def update_shift(self):
        if self.shift > self.dist-car_rad:
            self.shift = self.dist-car_rad
        elif self.shift < car_rad:
            self.shift = car_rad
        
        self.x = self.x1 + (self.x2 - self.x1) * self.shift / self.dist
        self.y = self.y1 + (self.y2 - self.y1) * self.shift / self.dist

        if self.vx**2 + self.vy**2 < v_min**2:
            v = v_min/(self.vx**2 + self.vy**2)**0.5
            self.vx *= v
            self.vy *= v
    
    def start_shift(self):
        m1 = 0
        if self.x2 == self.x1:
            m1 = 9999
        else:
            m1 = (self.y2 - self.y1) / (self.x2 - self.x1)
        b1 = self.y1 - m1 * self.x1

        m2 = 0
        if self.next_nd.x2 + self.next_nd.x1 == self.prev_nd.x2 + self.prev_nd.x1:
            m2 = 9999
        else:
            m2 = (self.next_nd.y2 + self.next_nd.y1 - self.prev_nd.y2 - self.prev_nd.y1) / (self.next_nd.x2 + self.next_nd.x1 - self.prev_nd.x2 - self.prev_nd.x1)
        b2 = (self.next_nd.y1 + self.next_nd.y2)/2 - m2 * (self.next_nd.x1 + self.next_nd.x2)/2

        if (self.x2 == self.x1) or (m1 == m2):
            self.shift = self.dist/2
        else:
            self.shift = self.dist * ((b2-b1)/(m1-m2) - self.x1) / (self.x2 - self.x1)
        self.update_shift()
        
    def start_v(self):
        #if abs(self.x - self.prev_nd.x) < abs(self.next_nd.x - self.x):
        #    self.vx = (self.x - self.prev_nd.x) / 2**0.5
        #else:
        #    self.vx = (self.next_nd.x - self.x) / 2**0.5
        #
        #if abs(self.y - self.prev_nd.y) < abs(self.next_nd.y - self.y):
        #    self.vy = (self.y - self.prev_nd.y) / 2**0.5
        #else:
        #    self.vy = (self.next_nd.y - self.y) / 2**0.5 + 1

        self.vx = (self.next_nd.x - self.x + self.x - self.prev_nd.x) / 4
        self.vy = (self.next_nd.y - self.y + self.y - self.prev_nd.y) / 4

    def gradient(self):
        self.d_vx = self.next_arc.dcx[1] - self.prev_arc.dcx[2]
        self.d_vy = self.next_arc.dcy[1] - self.prev_arc.dcy[2]

        self.d_shift = ((self.next_arc.dcx[0] + self.next_arc.dcx[1] + self.prev_arc.dcx[2]) * (self.x2 - self.x1) +
                        (self.next_arc.dcy[0] + self.next_arc.dcy[1] + self.prev_arc.dcy[2]) * (self.y2 - self.y1)) / self.dist
        
        if ((self.shift >= self.dist) and (self.d_shift < 0)) or ((self.shift <= 0) and (self.d_shift > 0)):
            self.shift = 0

        




class curve():

    def __init__(self, n1, n2, elem = 50):
        self.n1 = n1
        self.n2 = n2
        self.elem = elem

        self.s_dA = [[],[],[],[]]
        self.ds_dA = [[],[],[],[]]
        self.dds_dA = [[],[],[],[]]
            
        for t in np.linspace(0, 1, self.elem):
            self.s_dA[0].append(1 - 3*t + 3*t**2 - t**3)
            self.s_dA[1].append(3*t - 6*t**2 + 3*t**3)
            self.s_dA[2].append(3*t**2 - 3*t**3)
            self.s_dA[3].append(t**3)
            
            self.ds_dA[0].append(-3 + 6*t - 3*t**2)
            self.ds_dA[1].append(3 - 12*t + 9*t**2)
            self.ds_dA[2].append(6*t - 9*t**2)
            self.ds_dA[3].append(3*t**2)

            self.dds_dA[0].append(6 - 6*t)
            self.dds_dA[1].append(-12 + 18*t)
            self.dds_dA[2].append(6 - 18*t)
            self.dds_dA[3].append(6*t)

        self.compute()
    
    def compute(self):
        n1 = self.n1
        n2 = self.n2

        p1x, p1y = n1.x,           n1.y
        p2x, p2y = n1.x + n1.vx,   n1.y + n1.vy
        p3x, p3y = n2.x - n2.vx,   n2.y - n2.vy
        p4x, p4y = n2.x,           n2.y

        self.x, self.dx, self.ddx = [], [], []
        self.y, self.dy, self.ddy = [], [], []

        self.dcx = [0, 0, 0, 0]
        self.dcy = [0, 0, 0, 0]

        self.c = 0
        
        for i in range(0, self.elem):
            self.x.append(p1x * self.s_dA[0][i] + p2x * self.s_dA[1][i] + p3x * self.s_dA[2][i] + p4x * self.s_dA[3][i])
            self.y.append(p1y * self.s_dA[0][i] + p2y * self.s_dA[1][i] + p3y * self.s_dA[2][i] + p4y * self.s_dA[3][i])

            self.dx.append(p1x * self.ds_dA[0][i] + p2x * self.ds_dA[1][i] + p3x * self.ds_dA[2][i] + p4x * self.ds_dA[3][i])
            self.dy.append(p1y * self.ds_dA[0][i] + p2y * self.ds_dA[1][i] + p3y * self.ds_dA[2][i] + p4y * self.ds_dA[3][i])

            self.ddx.append(p1x * self.dds_dA[0][i] + p2x * self.dds_dA[1][i] + p3x * self.dds_dA[2][i] + p4x * self.dds_dA[3][i])
            self.ddy.append(p1y * self.dds_dA[0][i] + p2y * self.dds_dA[1][i] + p3y * self.dds_dA[2][i] + p4y * self.dds_dA[3][i])

            #self.c += abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**0.5 / (self.dx[i]**2 + self.dy[i]**2)**0.25 / self.elem
            #num = abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**0.5
            #dom = (self.dx[i]**2 + self.dy[i]**2)**0.25

            num = (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i])**2
            dom = (self.dx[i]**2 + self.dy[i]**2)**2.5

            self.c += num/dom * 1000/self.elem


            H = 1
            if self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i] < 0:
                H = -1
            
            for j in range(4):
                #d_num = (self.ds_dA[j][i] * self.ddy[i] - self.dds_dA[j][i] * self.dy[i]) / (2 * num * H)
                #d_dom = (self.ds_dA[j][i] * self.dx[i]) / (2 * dom**3)

                d_num = (self.ds_dA[j][i] * self.ddy[i] - self.dds_dA[j][i] * self.dy[i]) * (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]) * 2
                d_dom = 5 * (self.ds_dA[j][i] * self.dx[i]) * (self.dx[i]**2 + self.dy[i]**2)**1.5
                dc = (d_num * dom - d_dom * num) / dom**2
                self.dcx[j] += dc / self.elem
            
            for j in range(4):
                #d_num = (self.dds_dA[j][i] * self.dx[i] - self.ds_dA[j][i] * self.ddx[i]) / (2 * num * H)
                #d_dom = (self.ds_dA[j][i] * self.dy[i]) / (2 * dom**3)

                d_num = (self.dds_dA[j][i] * self.dx[i] - self.ds_dA[j][i] * self.ddx[i]) * (self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]) * 2
                d_dom = 5 * (self.ds_dA[j][i] * self.dy[i]) * (self.dx[i]**2 + self.dy[i]**2)**1.5
                dc = (d_num * dom - d_dom * num) / dom**2
                self.dcy[j] += dc / self.elem
        
    def interpolate(self):
        len = []
        rad = []
        for i in range(0, self.elem):
            rad.append((self.dx[i]**2 + self.dy[i]**2)**1.5 / abs(self.dx[i] * self.ddy[i] - self.dy[i] * self.ddx[i]))
            len.append((self.dx[i]**2 + self.dy[i]**2)**0.5 / self.elem)

        return(len, rad)
    
    def plot(self):
        plt.plot(self.x, self.y)
        #plt.plot(self.dx, self.dy)
    



class track():

    def __init__(self, p1x, p1y, p2x, p2y):
        self.nds = []
        for i in range(len(p1x)):
            self.nds.append(node(p1x[i], p1y[i], p2x[i], p2y[i]))
        
        for i in range(-1, len(self.nds)-1):
            self.nds[i].prev_nd = self.nds[i-1]
            self.nds[i].next_nd = self.nds[i+1]
            self.nds[i].start_shift()
        
        for i in self.nds:
            i.start_v()

        self.arcs = []
        for i in self.nds:
            self.arcs.append(curve(i, i.next_nd))
            i.next_arc = self.arcs[-1]
            i.next_nd.prev_arc = self.arcs[-1]
        
    def plot(self):
        for i in self.arcs:
            i.plot()
        
        for i in range(len(self.nds)):
            nd = self.nds[i]
            match i % 5:
                case 0: col = 'blue'
                case 1: col = 'red'
                case 2: col = 'black'
                case 3: col = 'magenta'
                case 4: col = 'orange'
            plt.plot(self.nds[i].x1, self.nds[i].y1, marker='o', color=col, markersize=3)
            plt.plot(self.nds[i].x2, self.nds[i].y2, marker='o', color=col, markersize=3)
        
        plt.axis('equal')
        plt.show()
    
    def get_cost(self):
        cost = 0
        for i in self.arcs:
            cost += i.c
        return cost

    def adjust_track(self, itterations, step):
        s = []
        for i in range(len(itterations)):
            for j in range(itterations[i]):
                s += [step[i]]

        for k in range(len(s)):
            step = s[k]

            grad_mag = 0
            for i in self.nds:
                i.gradient()
                grad_mag += i.d_vx**2 + i.d_vy**2 + i.d_shift**2            
            
            grad_mag = grad_mag**0.5

            for i in self.nds:
                i.vx -= i.d_vx / grad_mag * step
                i.vy -= i.d_vy / grad_mag * step
                i.shift -= i.d_shift / grad_mag * step
            self.update_track()

            char = 100
            progress_bar = ' ['
            for j in range(char):
                if j / char * len(s) >= k+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((k+1.1) * 100 / len(s))) + '%\tcost = ' + str(self.get_cost())
            print(progress_bar, end='\r')
        print()
    
    def run_sim(self, car, nodes = 5000, start = 0, end = 0):
        if end == 0:
            end = len(self.arcs)
        
        self.len = []
        self.rad = []
        for i in self.arcs[start:end]:
            new_len, new_rad = i.interpolate()
            self.len += new_len
            self.rad += new_rad
        #print(np.sum(self.len))
        self.sim = lapsim.four_wheel(self.len, self.rad, car, nodes)
        self.nodes, self.v3, self.t = self.sim.run()
        print(f'Total Travel Time: {self.t}')

    def update_track(self):
        for i in self.nds:
            i.update_shift()
        for i in self.arcs:
            i.compute()

    def plt_sim(self, car, nodes = 5000, start = 0, end = 0):
        self.run_sim(car, nodes, start, end)
        plt.title('Simulation Results:')
        plt.xlabel('Position (ft)')
        plt.ylabel('Vehicle Speed (mph)')
        plt.grid()
        plt.plot(self.nodes, self.v3)

        # sub = plt.subplots()
        # plot = sub.plot(self.nodes, self.v3)
        # annot = sub.annotate("", accel=(0,0), text=(20,20), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),arrowprops=dict(arrowstyle="->"))
        #
        # def update_annot(lat, axi):
        #     annot.xy = (lat, axi)
        #     text = f"Lateral acceleration: {lat:.2f}\nAxial Acceleration: {axi:.2f}"
        #     annot.set_text(text)
        #
        # def on_hover(event):
        #     if event.inaxes == sub:
        #         # Find the nearest data point
        #         contains, info = plot.contains(event)
        #         if contains:
        #             ind = info['ind'][0] # Get the index of the closest point
        #
        #             # Find corresponding lateral and axial acceleration with node the user is hovering over
        #             lat = 0
        #             axi = 0
        #             for l in car.lat_accel:
        #                 if l[1] == ind:
        #                     lat = l[0]
        #                     break
        #             for a in car.axi_accel:
        #                 if a[1] == ind:
        #                     axi = a[1]
        #                     break
        #
        #             update_annot(lat, axi)
        #             annot.set_visible(True)
        #             sub.canvas.draw_idle()
        #         else:
        #             if annot.get_visible():
        #                 annot.set_visible(False)
        #                 sub.canvas.draw_idle()

        plt.show()
    
    def refine_track(self):
        self.run_sim('single_point')

        elem = 50
        t_step = 10
        m_step = 3
        grad = np.zeros(len(self.nds))
        mag_grad = 0
        for i in range(1, len(self.nds)-1):
            self.nds[i].vx += 10
            new_arc1 = curve(self.nds[i-1], self.nds[i])
            new_arc2 = curve(self.nds[i], self.nds[i+1])
            new_len1, new_rad1 = new_arc1.interpolate()
            new_len2, new_rad2 = new_arc2.interpolate()
            self.nds[i].vx -= 10
            grad[i] += self.sim.arcEvaluator(i*50-50, i*50+50, new_len1+new_len2, new_rad1+new_rad2)
            mag_grad += grad[i]**2

            char = 100
            progress_bar = ' ['
            for j in range(char):
                if j*2 / char * len(self.nds) >= i+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((i + 1.1)/2 * 100 / len(self.nds))) + '%'
            print(progress_bar, end='\r')

        grad = np.zeros(len(self.nds))
        mag_grad = 0
        for i in range(1, len(self.nds)-1):
            self.nds[i].vy += 10
            new_arc1 = curve(self.nds[i-1], self.nds[i])
            new_arc2 = curve(self.nds[i], self.nds[i+1])
            new_len1, new_rad1 = new_arc1.interpolate()
            new_len2, new_rad2 = new_arc2.interpolate()
            self.nds[i].vy -= 10
            grad[i] += self.sim.arcEvaluator(i*50-50, i*50+50, new_len1+new_len2, new_rad1+new_rad2)
            mag_grad += grad[i]**2

            progress_bar = ' ['
            for j in range(char):
                if (j+char)/2 / char * len(self.nds) >= i+1: progress_bar += '-'
                else: progress_bar += '#'
            progress_bar += '] ' + str(int((i + char + 2.1)/2 * 100 / len(self.nds))) + '%'
            print(progress_bar, end='\r')
        print()
        
        mag_grad **= 0.5
        for i in range(len(self.nds)):
            self.nds[i].vy += grad[i] / mag_grad * m_step
        self.update_track()
        #print(grad)
            

            


