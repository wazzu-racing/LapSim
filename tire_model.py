from matplotlib import pyplot as plt
import scipy
import numpy as np
import csv
import pickle as pkl
import copy

# tire magic function
def magic_func(x, B, C, D, E):
    return D * np.sin(C * np.arctan(B*x - E * (B*x - np.arctan(B*x))))

class magic_curve():
    def __init__(self, x, y, center_vertical=False, data_cutoff=False, coeff=1):
        x = copy.deepcopy(x)
        y = copy.deepcopy(y) * coeff

        if data_cutoff:
            x = x[int(len(x)*0.15) : int(len(x)*0.85)]
            y = y[int(len(y)*0.15) : int(len(y)*0.85)]

        if center_vertical:
            # vertically centering the y data around the origin
            offset = (y.min() + y.max()) / 2
            y -= offset
        
        # centering the raw data curve horizontally
        center = 0
        for i in range(int(len(y)*0.5)):
            x0 = int(len(y)*0.5)
            y0 = y[x0]

            j = x0 + i
            if ((y[j] <= 0) and (y0 >= 0)) or ((y[j] >= 0) and (y0 <= 0)): # determines where y crosses the horizontal axis
                offset = x[j] # determining the horizontal offset from the origin
                x -= offset # shifting the domain such that the raw data curve intersects the origin
                center = j # index of center
                break

            j = x0 - i
            if ((y[j] <= 0) and (y0 >= 0)) or ((y[j] >= 0) and (y0 <= 0)): # determines where y crosses the horizontal axis
                offset = x[j] # determining the horizontal offset from the origin
                x -= offset # shifting the domain such that the raw data curve intersects the origin
                center = j # index of center
                break
        
        # determining slope around center using change in y over change in x through a section of data
        offset = int(len(x) * 0.015)
        x1 = x[center - offset]
        x2 = x[center + offset]

        n = 5
        y1 = np.average(y[center-offset-n : center-offset+n])
        y2 = np.average(y[center+offset-n : center+offset+n])
        #y1 = y[center - offset]
        #y2 = y[center + offset]

        slope = (y2 - y1) / (x2 - x1)

        # creating initial estimates for coeffecients
        E0 = 0.5
        D0 = y.max()
        C0 = -1.5
        B0 = slope / D0 / C0

        # evaluating coeffecients using curve_fit method from scipy
        popt, pcov = scipy.optimize.curve_fit(magic_func, x, y, p0=[B0, C0, D0, E0], bounds=([-np.inf, -np.inf, 0, 0], [np.inf, 0, np.inf, 1]))

        self.coeff = popt
        self.max = abs(popt[2])
    
    def eval(self, x):
        return magic_func(x, *self.coeff)



# stores a section of data and finds the average and standard devation of each list of data
class data_section():
    def __init__(self, data):
        self.data = data

        self.avg = [] # averages
        self.std_dev = [] # standard deviation

        for i in self.data:
            self.avg.append(sum(i)/len(i)) # finding averages

            # finding standard devation
            std_dev = 0
            for j in i:
                std_dev += (j - self.avg[-1])**2
            std_dev = (std_dev / (len(i)-1))**0.5
            self.std_dev.append(std_dev)



class curve_set():
    def __init__(self, parent, data_type, x_data, y_data, curve_domain, center_vertical=False, data_cutoff=False, coeff=1):
        if (data_type == 'corner') or (data_type == 'cornering'):
            titles = parent.corner_titles
            loads = parent.corner_loads
            cambers = parent.corner_camber_angles
            data_sets = parent.corner_data_sets
        elif (data_type == 'accel') or (data_type == 'acceleration'):
            titles = parent.accel_titles
            loads = parent.accel_loads
            cambers = parent.accel_camber_angles
            data_sets = parent.accel_data_sets
        else:
            raise SystemExit('Invalid Data type.')
        
        x_index = titles.index(x_data)
        y_index = titles.index(y_data)
        self.curves = []

        for i in cambers:
            self.curves.append([])
            for j in loads:
                if (data_type == 'corner') or (data_type == 'cornering'):
                    section = data_sets[parent.find_section('cornering', [['IA', i], ['FZ', -j]], [['P', 9, 99]])]
                elif (data_type == 'accel') or (data_type == 'acceleration'):
                    section = data_sets[parent.find_section('accel', [['IA', i], ['FZ', -j], ['SA', 0], ['P', 12]])]
                
                x = section.data[x_index]
                y = section.data[y_index] * coeff
                self.curves[-1].append(magic_curve(x, y, center_vertical, data_cutoff))
        
        self.loads = loads
        self.cambers = cambers
        self.curve_domain = curve_domain
        
    def eval(self, x, load, camber):
        ld_list = [0] + self.loads
        for i in range(len(ld_list)-1):
            if (i >= len(ld_list)-2) or (ld_list[i+1] >= load):
                nxt_ld = i
                prv_ld = i-1
                ld_R = (load - ld_list[i]) / (ld_list[i+1] - ld_list[i]) # equals 1 when load == nxt_ld
                break                                                    # equals 0 when load == prv_ld
        
        for i in range(len(self.cambers)-1):
            if (i >= len(self.cambers)-2) or (self.cambers[i+1] >= camber):
                nxt_cmbr = i+1
                prv_cmbr = i
                cmbr_R = (camber - self.cambers[i]) / (self.cambers[i+1] - self.cambers[i]) # equals 1 when camber == nxt_cmbr
                break                                                                       # equals 0 when camber == prv_cmbr
        
        output = 0
        output += self.curves[nxt_cmbr][nxt_ld].eval(x) * cmbr_R * ld_R
        output += self.curves[prv_cmbr][nxt_ld].eval(x) * (1-cmbr_R) * ld_R
        if prv_ld >= 0:
            output += self.curves[nxt_cmbr][prv_ld].eval(x) * cmbr_R * (1-ld_R)
            output += self.curves[prv_cmbr][prv_ld].eval(x) * (1-cmbr_R) * (1-ld_R)
        
        return output
    
    def get_max(self, load, camber):
        ld_list = [0] + self.loads
        for i in range(len(ld_list)-1):
            if (i >= len(ld_list)-2) or (ld_list[i+1] >= load):
                nxt_ld = i
                prv_ld = i-1
                ld_R = (load - ld_list[i]) / (ld_list[i+1] - ld_list[i]) # equals 1 when load == nxt_ld
                break                                                    # equals 0 when load == prv_ld
        
        for i in range(len(self.cambers)-1):
            if (i >= len(self.cambers)-2) or (self.cambers[i+1] >= camber):
                nxt_cmbr = i+1
                prv_cmbr = i
                cmbr_R = (camber - self.cambers[i]) / (self.cambers[i+1] - self.cambers[i]) # equals 1 when camber == nxt_cmbr
                break                                                                       # equals 0 when camber == prv_cmbr
        
        output = 0
        output += self.curves[nxt_cmbr][nxt_ld].coeff[2] * cmbr_R * ld_R
        output += self.curves[prv_cmbr][nxt_ld].coeff[2] * (1-cmbr_R) * ld_R
        if prv_ld >= 0:
            output += self.curves[nxt_cmbr][prv_ld].coeff[2] * cmbr_R * (1-ld_R)
            output += self.curves[prv_cmbr][prv_ld].coeff[2] * (1-cmbr_R) * (1-ld_R)
        
        return output

    def plot_curve(self, load, camber, x='none'):
        if x == 'none':
            x = self.curve_domain
        load_indx = self.loads.index(load)
        cmbr_indx = self.cambers.index(camber)
        curve = self.curves[cmbr_indx][load_indx]
        plt.plot(x, curve.eval(x))
        

        

        


class tire():
    def __init__(self, cornering_data_file, acceleration_data_file = None):

        ''' =============================================== '''
        ''' ========== Initiating Cornering Data ========== '''
        ''' =============================================== '''

        self.corner_file = cornering_data_file
        self.accel_file = acceleration_data_file
        corner_data = []   # empty array to store cornering data value
        corner_titles = [] # empty array for the titles of each cornering dataset
        corner_units = []  # empty array for units of each cornering dataset

        # organizing cornering into a 2D array
        with open(cornering_data_file, newline='') as dat_file:
            reader = csv.reader(dat_file, delimiter='\t')

            # going through the reader line by line appending data to corner_data array
            i = 0
            for line in reader:
                i += 1
                if i <= 3:
                    if i == 2:
                        corner_titles = line # defining titles using second line in reader
                    elif i == 3:
                        corner_units = line # defining units using third line in reader
                else:
                    corner_data.append(np.array(line).astype(float)) # appending all lines after line 3 to the corner_data
        
        # transposing corner_data: this makes each row correspond to the equal index titles and units in corner_titles and corner_units
        corner_data = np.transpose(corner_data)

        '''=================================================================================================================================
        This next part of the code looks for useful sections of the data where tests are being conducted and no warm up stuff is happening
        These useful sections are typically characterized by slip angle sweeps from 0 to 12 to -12 to 0 degrees. To find these sections the 
        code records index values for sections of the data where the slip angle is approximately -12, -4, 0, 4, or 12 deg along with the
        approximate slip angle of each section. A set of consecutive datasets of slip angles 0, 4, 12, 4, 0, -4, -12, -4, 0, in that order,
        signifies a set of useful data beginning at the data set of slip angle 12 deg and ending at the dataset of slip angle -12 deg.

        The sequence of slip angle values within consecutive datasets may occasionally differ but typically can be found by looking for slip
        angles of magnitude 0, 4, and 12 deg.
        ================================================================================================================================='''

        indx = corner_titles.index('SA') # finding index for slip angle

        # the array arr records sections of data where slip angle values are approximately -12, -4, 0, 4, or 12 deg
        # each row in arr represents a seperate section of data
        # the first value in each row represents the approximate slip angle value of the data within that section, either -12, -4, 0, 4, or 12 deg
        # the second value represents the index within corner_dat where this section begins
        # the third value represents the index within corner_dat where this section ends
        arr = [[], [], []]

        # set to True when after appending to arr[1] to mark beginning of set but still waiting to find end of set to append to arr[2]
        appending = False 
        for i in range(len(corner_data[indx])):            
            # checks to make sure a new set of data is not currently being added to arr
            if not appending:
                # checks if slip angle values are within the necessary ranges to mark a new set of data in arr
                # appends the approximate slip angle value and sets appending to True if slip angle is near -12, -4, 0, 4, or 12 deg
                if -0.1 < corner_data[indx, i] < 0.1:
                    arr[0].append(0)
                    appending = True
                elif 11.8 < corner_data[indx, i]:
                    arr[0].append(12)
                    appending = True
                elif -11.8 > corner_data[indx, i]:
                    arr[0].append(-12)
                    appending = True
                elif -4.5 < corner_data[indx, i] < -3.5:
                    arr[0].append(-4)
                    appending = True
                elif 3.5 < corner_data[indx, i] < 4.5:
                    arr[0].append(4)
                    appending = True
                
                # records starting value of new dataset in arr[1] if a new set was created
                if appending: arr[1].append(i)
            
            # checks if slip angle value are no longer near -12, -4, 0, 4, or 12 deg
            if appending and not ((-0.1 < corner_data[indx, i] < 0.1) or (corner_data[indx, i] > 11.8) or (corner_data[indx, i] < -11.8) or (-4.5 < corner_data[indx, i] < -3.5) or (3.5 < corner_data[indx, i] < 4.5)):
                arr[2].append(i)  # records the index for the end of the dataset if slip angle values have changed
                appending = False # sets appending to False if slip angle values have changed

        arr[2].append(len(corner_data[indx])) # appending the ending index of the final dataset

        sequence = [0, 4, 12, 4, 0, -4, -12, -4, 0] # the sequence of slip angles to be searched for
        self.corner_set_index = [] # an empty list to store the start and ending indexes of all sections of useful data
        half = int((len(sequence)-1)/2) # half the length of the 'sequence' list

        # searching through arr to find a section that matches sequence and appending to self.set_index when a match is found
        for i in range(half, len(arr[0])-half):
            if arr[0][i-half : i+1+half] == sequence:
                self.corner_set_index.append([int((arr[1][i-2] + arr[2][i-2])/2), int((arr[1][i+2] + arr[2][i+2])/2)])
        
        # creating a list of data_section objects for each set of useful data
        self.corner_data_sets = []
        for i in self.corner_set_index:
            self.corner_data_sets.append(data_section(corner_data[0:len(corner_data), i[0]:i[1]]))

        '''
        finding applied loads used for testing:
        There are five applied loads for each cornering test, each a multiple of 50 lb and used multiple times in each test
        using the average recorded load for each section of useful data these five load valeus are found
        '''

        indx = corner_titles.index('FZ') # finding index for applied load
        # creating list of average applied loads
        averages = []
        for i in self.corner_data_sets:
            averages.append(-i.avg[indx])
        averages = np.sort(averages)

        # array to store applied loads for cornering tests
        corner_loads = []
        for i in range(5):
            corner_loads.append(50*round((np.average(averages[int(i*len(averages)/5) : int((1+i)*len(averages)/5)]))/50))
        
        self.corner_data = corner_data
        self.corner_titles = corner_titles
        self.corner_units = corner_units
        self.corner_loads = corner_loads
        self.corner_camber_angles = [0, 2, 4]
        
        self.FY_curves = curve_set(self, 'corner', 'SA', 'FY', np.linspace(-20, 20, 101), coeff=0.5)
        self.aligning_torque = curve_set(self, 'corner', 'SA', 'MZ', np.linspace(-15, 15, 101), center_vertical=True, data_cutoff=True)

        self.max_lateral_forces = []
        for i in range(len(self.corner_camber_angles)):
            self.max_lateral_forces.append([])
            for j in range(len(corner_loads)):
                self.max_lateral_forces[-1].append(self.FY_curves.curves[i][j].coeff[2])



        ''' ================================================== '''
        ''' ========== Initiating Acceleration Data ========== '''
        ''' ================================================== '''

        if acceleration_data_file == None: pass # skips the rest of the function if acceleration data is missing
        
        accel_data = []   # empty array to store acceleration data value
        accel_titles = [] # empty array for the titles of each acceleration dataset
        accel_units = []  # empty array for units of each acceleration dataset

        # organizing acceleration data into a 2D array
        with open(acceleration_data_file, newline='') as dat_file:
            reader = csv.reader(dat_file, delimiter='\t')

            # going through the reader line by line appending data to acceleration_data array
            i = 0
            for line in reader:
                i += 1
                if i <= 3:
                    if i == 2:
                        accel_titles = line # defining titles using second line in reader
                    elif i == 3:
                        accel_units = line # defining units using third line in reader
                else:
                    accel_data.append(np.array(line).astype(float)) # appending all lines after line 3 to acceleration_data
        
        # transposing acceleration_data: this makes each row correspond to the equal index titles and units in accel_titles and accel_units
        accel_data = np.transpose(accel_data)

        '''====================================================================================================================================
        This next part of the code looks for useful sections of the data where tests are being conducted and no warm up stuff is happening
        These useful sections are typically characterized by slip ratio sweeps from 0 to 0.15 to -0.15 to 0 degrees. To find these sections the 
        code records index values for sections of the data where the slip angle is approximately -0.15, 0, or 0.15 deg along with the
        approximate slip angle of each section. A set of consecutive datasets of slip angles 0 to 0.15 to 0 to -0.15 to 0 to 0.15 to 0 in that 
        order, signifies a set of useful data beginning at the data set of slip angle 12 deg and ending at the dataset of slip angle -12 deg.
        ====================================================================================================================================='''

        indx = accel_titles.index('SR') # finding index for slip ratio

        # the array arr records sections of data where slip ratio values are approximately -0.15, 0, or 0.15 deg
        # each row in arr represents a seperate section of data
        # the first value in each row represents the approximate slip ratio value of the data within that section, either -0.15, 0, or 0.15 deg
        # the second value represents the index within accel_dat where this section begins
        # the third value represents the index within accel_dat where this section ends
        arr = [[], [], []]

        # set to True when after appending to arr[1] to mark beginning of set but still waiting to find end of set to append to arr[2]
        appending = False 
        for i in range(len(accel_data[indx])):            
            # checks to make sure a new set of data is not currently being added to arr
            if not appending:
                # checks if slip ratio values are within the necessary ranges to mark a new set of data in arr
                # appends the approximate slip ratio value and sets appending to True if slip ratio is near -0.15, 0, or 0.15 deg
                if -0.05 < accel_data[indx, i] < 0.03:
                    arr[0].append(0)
                    appending = True
                elif 0.09 < accel_data[indx, i]:
                    arr[0].append(0.15)
                    appending = True
                elif -0.15 > accel_data[indx, i]:
                    arr[0].append(-0.15)
                    appending = True
                
                # records starting value of new dataset in arr[1] if a new set was created
                if appending: arr[1].append(i)
            
            # checks if slip ratio value are no longer near -0.15, 0, or 0.15 deg
            if appending and (((arr[0][-1] == 0) and not (-0.06 < accel_data[indx, i] < 0.04)) or ((arr[0][-1] == 0.15) and not (0.085 < accel_data[indx, i])) or ((arr[0][-1] == -0.15) and not (-0.014 > accel_data[indx, i]))):
                arr[2].append(i)  # records the index for the end of the dataset if slip ratio values have changed
                appending = False # sets appending to False if slip ratio values have changed

        arr[2].append(len(accel_data[indx])) # appending the ending index of the final dataset
        #sequence = [0, 0.15, 0, -0.15, 0, 0.15, 0] # the sequence of slip ratios to be searched for
        sequence = [0.15, 0, -0.15, 0, 0.15] # alternative sequence for 18x6-10 R20
        self.accel_set_index = [] # an empty list to store the start and ending indexes of all sections of useful data
        half = int((len(sequence)-1)/2) # half the length of the 'sequence' list

        # searching through arr to find a section that matches sequence and appending to self.set_index when a match is found
        for i in range(half, len(arr[0])-half):
            if arr[0][i-half : i+1+half] == sequence:
                self.accel_set_index.append([int(arr[2][i-2]), int((arr[1][i] + arr[2][i])/2)])
        
        # creating a list of data_section objects for each set of useful data
        self.accel_data_sets = []
        for i in self.accel_set_index:
            self.accel_data_sets.append(data_section(accel_data[0:len(accel_data), i[0]:i[1]]))
        
        
        '''
        finding applied loads used for testing:
        There are four applied loads for each acceleration test, each a multiple of 50 lb and used multiple times in each test
        using the average recorded load for each section of useful data these four load values are found
        '''

        indx = accel_titles.index('FZ') # finding index for applied load
        # creating list of average applied loads
        averages = []
        for i in self.accel_data_sets:
            averages.append(-i.avg[indx])
        averages = np.sort(averages)

        # array to store applied loads for acceleration tests
        accel_loads = []
        for i in range(4):
            accel_loads.append(50*round((np.median(averages[int(i*len(averages)/4) : int((1+i)*len(averages)/4)]))/50))
        self.accel_data = accel_data
        self.accel_titles = accel_titles
        self.accel_units = accel_units
        self.accel_loads = accel_loads
        self.accel_camber_angles = [0, 2, 4]

        self.FX_curves = curve_set(self, 'accel', 'SR', 'FX', np.linspace(-0.3, 0.3, 101), coeff=0.6)

        self.max_axial_forces = []
        for i in range(len(self.accel_camber_angles)):
            self.max_axial_forces.append([])
            for j in range(len(accel_loads)):
                self.max_axial_forces[-1].append(self.FX_curves.curves[i][j].coeff[2])
    





    '''=======================================================================================================
    function find_section: finds the best data section based off of inputted parameters

    equivalent is a list of inputs. Each value in the list is another list of two entries
    first entry is the title of a data set, ex: 'SA', 'FZ', 'IA'
    second list entry is the desired value for the data in the specified dataset
    the function will try to find a dataset where the values in the specified datset match the specified value
    may be set to as an empty list if no values need to be matched: equivalent=[]
    ex: equivalent = [['FZ', 150], ['V', 25], ['IA', 2]]

    lim is another list of inputs. Each value of the list is another list of three entires
    first entry is the title of a data set, ex: 'ET', 'V', 'SR'
    second list entry is the minimum value for data in the specified dataset
    third list entry is the maximum value for data in the specified dataset
    the function will only output datasets where all values are within the specified ranges
    may be set to as an empty list if no values need to be matched: lim=[]
    ex: lim = [['ET', 0, 250], ['V', 30, 99999], ['P', 40, 90]]

    set_type may be set to either corner or accel
    ======================================================================================================='''
    def find_section(self, set_type, equivalent=[], lim=[]):
        if set_type == 'cornering' or set_type == 'corner':
            sets = self.corner_data_sets
            titles = self.corner_titles
        elif set_type == 'acceleration' or set_type == 'accel':
            sets = self.accel_data_sets
            titles = self.accel_titles
        else:
            raise SystemExit(f'Invalid set type: \'{set_type}\'')
        
        # cost represents how bad a dataset is. The dataset with lowest cost will be returned
        cost = np.zeros(len(sets))

        # finding sets that dont fit in the boundaries specified by lim
        for i in lim:
            indx = titles.index(i[0])
            for j in range(len(sets)):
                for k in sets[j].data[indx]:
                    if not(i[1] < k < i[2]):
                        cost[j] = 999999999999999

        # adding additional cost to sets based off of how much data diverges from ideal values specified in the 'equivalent' parameter
        for i in equivalent:
            indx = titles.index(i[0])
            i_cost = np.zeros(len(sets))
            for j in range(len(cost)):
                i_cost[j] += (sets[j].avg[indx] - i[1])**2
            cost_mag = sum(i_cost)
            for j in range(len(cost)):
                cost[j] += i_cost[j] / cost_mag
        
        # finding dataset with lowest cost
        sect = 0
        for i in range(1, len(cost)):
            if cost[i] < cost[sect]:
                sect = i
        
        return sect
    
    def plot_data(self, set_type, x_axis, y_axis, set_num):
        if set_type == 'cornering' or set_type == 'corner':
            x_indx = self.corner_titles.index(x_axis)
            y_indx = self.corner_titles.index(y_axis)
            dataset = self.corner_data_sets[set_num]
            x_data = dataset.data[x_indx]
            y_data = dataset.data[y_indx]
            x_title = f'{self.corner_titles[x_indx]} ({self.corner_units[x_indx]})'
            y_title = f'{self.corner_titles[y_indx]} ({self.corner_units[y_indx]})'
        elif set_type == 'acceleration' or set_type == 'accel':
            x_indx = self.accel_titles.index(x_axis)
            y_indx = self.accel_titles.index(y_axis)
            dataset = self.accel_data_sets[set_num]
            x_data = dataset.data[x_indx]
            y_data = dataset.data[y_indx]
            x_title = f'{self.accel_titles[x_indx]} ({self.accel_units[x_indx]})'
            y_title = f'{self.accel_titles[y_indx]} ({self.accel_units[y_indx]})'
        else:
            raise SystemExit(f'Invalid set type: \'{set_type}\'')
        
        plt.plot(x_data, y_data)
        plt.xlabel(x_title)
        plt.ylabel(y_title)
        plt.grid()



    # finds the maximum magnitude of values of a given dataset in a given section of data
    def find_max(self, set_type, section, dataset):
        if set_type == 'cornering' or set_type == 'corner':
            data = self.corner_data_sets[section].data[self.corner_titles.index(dataset)]
        elif set_type == 'acceleration' or set_type == 'accel':
            data = self.accel_data_sets[section].data[self.accel_titles.index(dataset)]
        else:
            raise SystemExit(f'Invalid set type: \'{set_type}\'')

        num = 0
        for i in data:
            if abs(i) > num:
                num = abs(i)

        return num
    
    

    def traction(self, set_type, load, camber):
        if set_type == 'cornering' or set_type == 'corner':
            forces = copy.deepcopy(self.max_lateral_forces)
            loads_arr = copy.deepcopy(self.corner_loads)
            camber_arr = copy.deepcopy(self.corner_camber_angles)
        elif set_type == 'acceleration' or set_type == 'accel':
            forces = copy.deepcopy(self.max_axial_forces)
            loads_arr = copy.deepcopy(self.accel_loads)
            camber_arr = copy.deepcopy(self.accel_camber_angles)
        else:
            raise SystemExit(f'Invalid set type: \'{set_type}\'')
        
        # Extending dataset for higher loads by maintaining the slope created from the highest 2 loads
        interpolation_load = 600
        for i in range(len(forces)):
            j = forces[i]
            forces[i] = [0] + j + [interpolation_load * (j[-1]/loads_arr[-1] + (j[-1]/loads_arr[-1] - j[-2]/loads_arr[-2]) / (loads_arr[-1]-loads_arr[-2]) * (interpolation_load-loads_arr[-1]))]
            #forces[i] = [0] + j + [(j[-1] + (j[-1]-j[-2]) / (loads_arr[-1]-loads_arr[-2]) * (interpolation_load-loads_arr[-1]))]
        loads_arr = [0] + loads_arr + [interpolation_load]

        camber = abs(camber)
        if load <= 0:
            return 0

        for i in range(len(loads_arr)):
            if loads_arr[i+1] >= load:
                # index of the highest loads_arr value less than load
                i_l = i
                # equals zero when camber = camber_arr[i_c]; equals 1 when camber = camber_arr[i_c+1]
                l_bias = (load-loads_arr[i])/(loads_arr[i+1]-loads_arr[i])
                break
        
        for i in range(len(camber_arr)):
            if camber_arr[i+1] >= camber:
                # index of the highest camber_arr value less than camber
                i_c = i
                # equals zero when camber = camber_arr[i_c]; equals 1 when camber = camber_arr[i_c+1]
                c_bias = (camber-camber_arr[i])/(camber_arr[i+1]-camber_arr[i]) 
                break
        
        return ((forces[i_c][i_l]*(1-l_bias) + forces[i_c][i_l+1]*l_bias)*(1-c_bias) + (forces[i_c+1][i_l]*(1-l_bias) + forces[i_c+1][i_l+1]*l_bias)*c_bias) * 1.1
    
    ''' ======================================================= '''
    ''' ========== Cornering Data Graphing Functions ========== '''
    ''' ======================================================= '''
    def lateral_force_plot(self):
        leg = []
        for i in range(len(self.max_lateral_forces)):
            plt.plot(self.corner_loads, self.max_lateral_forces[i])
            leg.append(f'Camber = {self.corner_camber_angles[i]}')
        
        plt.xlabel(f'Applied Load ({self.corner_units[self.corner_titles.index('FZ')]})')
        plt.ylabel(f'Max Lateral Force ({self.corner_units[self.corner_titles.index('FY')]})')
        plt.grid()
        plt.legend(leg)
        plt.show()
    
    def lateral_coeff_plot(self):
        leg = []
        for i in range(len(self.max_lateral_forces)):
            plt.plot(self.corner_loads, np.array(self.max_lateral_forces[i])/np.array(self.corner_loads))
            leg.append(f'Camber = {self.corner_camber_angles[i]}')
        
        plt.xlabel(f'Applied Load ({self.corner_units[self.corner_titles.index('FZ')]})')
        plt.ylabel(f'Lateral Friction Coeffecient')
        plt.grid()
        plt.legend(leg)
        plt.show()
    
    def SA_FY_plot(self, camber):
        leg = []
        for i in self.corner_loads:
            self.FY_curves.plot_curve(i, camber)
            leg.append(f'{i} {self.corner_units[self.corner_titles.index('FZ')]}')
        
        plt.xlabel(f'Slip Angle')
        plt.ylabel(f'FY ({self.accel_units[self.corner_titles.index('FY')]})')
        plt.grid()
        plt.legend(leg)
        plt.show()

    def SA_MZ_plot(self, camber):
        leg = []
        for i in self.corner_loads:
            self.aligning_torque.plot_curve(i, camber)
            leg.append(f'{i} {self.corner_units[self.corner_titles.index('FZ')]}')
        
        plt.title(f'Slip Angle vs Alinging Torque')
        plt.xlabel(f'Slip Angle ({self.accel_units[self.corner_titles.index('SA')]})')
        plt.ylabel(f'MZ ({self.accel_units[self.corner_titles.index('MZ')]})')
        plt.grid()
        plt.legend(leg)
        plt.show()
    
    ''' ========================================================== '''
    ''' ========== Acceleration Data Graphing Functions ========== '''
    ''' ========================================================== '''
    def axial_force_plot(self):
        leg = []
        for i in range(len(self.max_axial_forces)):
            plt.plot(self.accel_loads, self.max_axial_forces[i])
            leg.append(f'Camber = {self.accel_camber_angles[i]}')
        
        plt.xlabel(f'Applied Load ({self.accel_units[self.accel_titles.index('FZ')]})')
        plt.ylabel(f'Max Axial Force ({self.accel_units[self.accel_titles.index('FY')]})')
        plt.grid()
        plt.legend(leg)
        plt.show()
    
    def axial_coeff_plot(self):
        leg = []
        for i in range(len(self.max_axial_forces)):
            plt.plot(self.accel_loads, np.array(self.max_axial_forces[i])/np.array(self.accel_loads))
            leg.append(f'Camber = {self.accel_camber_angles[i]}')
        
        plt.xlabel(f'Applied Load ({self.accel_units[self.accel_titles.index('FZ')]})')
        plt.ylabel(f'Axial Friction Coeffecient')
        plt.grid()
        plt.legend(leg)
        plt.show()
    
    def SR_FX_plot(self, camber):
        leg = []
        for i in self.accel_loads:
            self.FX_curves.plot_curve(i, camber)
            leg.append(f'{i} {self.accel_units[self.accel_titles.index('FZ')]}')
        
        plt.xlabel(f'Slip Ratio')
        plt.ylabel(f'FX ({self.accel_units[self.accel_titles.index('FX')]})')
        plt.grid()
        plt.legend(leg)
        plt.show()


if False:
    cornering_data = 'C:\\Users\\nbogd\\OneDrive\\Documents\\lapsimStuffCopy\\tire stuff\\RunData_Cornering_ASCII_USCS_Round9\\A2356run32.dat'
    accel_data = 'C:\\Users\\nbogd\\OneDrive\\Documents\\lapsimStuffCopy\\tire stuff\\RunData_DriveBrake_ASCII_USCS_Round9\\A2356run72.dat'

    wheel = tire(cornering_data, accel_data)
    wheel.SA_MZ_plot(0)