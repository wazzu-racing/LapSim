import csv
import os
import subprocess
import tkinter
from enum import Enum

import numpy as np
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gen_lapsim.lapsim import LapSimData
from lapsim_validation import Validation_Track
from models.car_model import car
class Validation:

    raw_AX = []
    raw_AY = []

    class DataType(Enum):
        AX = 0
        AY = 1
        AZ = 2
        ROLL = 3
        YAW = 4
        FO_dis = 5
        FI_dis = 6
        RO_dis = 7
        RI_dis = 8
        FO_load = 9
        FI_load = 10
        RO_load = 11
        RI_load = 12
        RPM = 13

    class Data_Node:
        def __init__(self, AX, AY, roll, yaw, front_left_dis, front_right_dis, rear_left_dis, rear_right_dis, rpm, distance):
            self.AX = AX
            self.AY = AY
            self.roll = roll # radians
            self.yaw = yaw # radians
            self.front_left_shock = front_left_dis # inches
            self.front_right_shock = front_right_dis # inches
            self.rear_left_shock = rear_left_dis # inches
            self.front_left_dis = 0
            self.front_right_dis = 0
            self.rear_left_dis = 0
            self.rear_right_dis = 0
            self.rpm = rpm
            self.distance_along_segment = distance

        AX: float = 0
        AY: float = 0
        AZ: float = 0
        roll: float = 0
        yaw: float = 0
        front_left_shock: float = 0
        front_right_shock: float = 0
        rear_left_shock: float = 0
        rear_right_shock: float = 0
        rpm: float = 0

        distance_along_segment: float = 0
        arc: Validation.Arc
        distance_since_arc_start: float = 0

    class Arc:
        class Turn(Enum):
            LEFT = 0
            RIGHT = 1

        arc_id : int = 0
        segment_id : int = 0
        start_x :float = 0
        start_y:float = 0
        end_x:float = 0
        end_y:float = 0
        radius:float = 0
        length: float = 0
        time: float = 0
        segment: Validation.Segment

        distance_along_segment: float = 0
        data_nodes: list[Validation.Data_Node] = []
        turn: Turn = Turn.LEFT

        def find_data_node_distance_ratio(self, distance_along_arc, sims_per_arc):
            if distance_along_arc == 118.3858907:
                pass
            distance = 0
            count = 0
            while distance < distance_along_arc:
                distance += self.length / sims_per_arc
                count += 1

            distance_before_len = (self.length / sims_per_arc) * (count-1)
            distance_along_len = distance_along_arc - distance_before_len
            # print(distance_along_len / (self.length / sims_per_arc))
            return distance_along_len / (self.length / sims_per_arc)

        # Finds the simulation point that happens BEFORE the data node. Returns the index
        def find_sim_node_index(self, distance_along_arc, sims_per_arc):
            distance = 0
            count = 0
            while distance < distance_along_arc:
                distance += self.length / sims_per_arc
                count += 1
            # Guard code to not let the index go past the actual length of the arc
            if distance > self.length:
                return count-2
            else:
                return count-1 if count > 0 else 0 # Make sure to return at least 0.

    class Segment:
        def __init__(self, id, start_x, start_y, end_x, end_y, arcs):
            self.segment_id = id
            self.start_x = start_x
            self.start_y = start_y
            self.end_x = end_x
            self.end_y = end_y
            self.arcs = arcs
            self.starting_velocity = 0
            self.spline_points = [] # Contains tuples of (x, y)
            self.data_nodes = []

            self.compute_arc_segment_distances()

        segment_id : int = 0
        start_x :float = 0
        start_y:float = 0
        end_x:float = 0
        end_y:float = 0
        time: float = 0 # seconds
        spline_points: list[tuple] # Contains tuples of (x, y)
        starting_velocity : float
        arcs: list[Validation.Arc]
        data_nodes: list[Validation.Data_Node]
        distance_travelled: float = 0

        def compute_arc_segment_distances(self):
            self.compute_arc_distances()
            self.compute_segment_distance()

        def compute_segment_distance(self):
            distance = 0
            for arc in self.arcs:
                distance += arc.length
            self.distance_travelled = distance

        def compute_arc_distances(self):
            distance = 0
            for arc in self.arcs:
                arc.distance_along_segment = distance
                distance += arc.length

        def calculate_distance_differences(self):
            # Clear data nodes in arcs
            for arc in self.arcs:
                arc.data_nodes = []
            # Calculate data nodes and arcs relative to each other
            for data_node in self.data_nodes:
                arc, arc_index = self.arcs[0], 0
                total_length = self.arcs[0].length
                while data_node.distance_along_segment > total_length:
                    if arc_index == len(self.arcs)-1: # If at the end of arcs, use that arc
                        break
                    arc_index += 1
                    arc = self.arcs[arc_index]
                    total_length += arc.length
                data_node.arc = self.arcs[arc_index]
                self.arcs[arc_index].data_nodes.append(data_node)

                # Clamp data node to the end of the segment
                if data_node.distance_along_segment < data_node.arc.segment.distance_travelled:
                    data_node.distance_since_arc_start = data_node.distance_along_segment - self.arcs[arc_index].distance_along_segment
                else:
                    data_node.distance_since_arc_start = data_node.arc.length

    arcs = [] # The curves between every single point
    segments = [] # Collections of arcs. This is "good" data. Only contains a segment where there is both velocity and spline data.
    lapsim_data = [] # Data collected by running the lapsim. Contains segments number of LapSimData objects.
    lerped_data = [] # Data collected by interpolating data from the lapsim to match the position of data acq data.

    def parse_arc_data(self, csv_path):

        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        curr_segment_id, prev_segment_id = 1, 1

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            curr_segment_id = int(line[0])

            if curr_segment_id != prev_segment_id and len(self.arcs) != 0:
                self.arcs[-1].bad_data = True

            arc = self.Arc()

            arc.segment_id = curr_segment_id
            arc.arc_id = int(line[1])
            arc.radius = float(line[4])
            arc.start_x = float(line[7])
            arc.start_y = float(line[8])
            arc.end_x = float(line[9])
            arc.end_y = float(line[10])
            arc.length = float(line[11])
            arc.turn = self.Arc.Turn.LEFT if line[12] == "left" else self.Arc.Turn.RIGHT

            self.arcs.append(arc)

            prev_segment_id = curr_segment_id

        self.convert_arcs_to_segments()

        # for arc in self.arcs:
        #     print(f"id: {arc.segment_id}, start_x: {arc.start_x}, start_y: {arc.start_y}, end_x: {arc.end_x}, end_y: {arc.end_y},")

    def parse_velocity_data(self, csv_path):

        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            # Adds a segment if there is none yet
            self.segments[self.get_segment_index(int(line[0]))].starting_velocity = float(line[2])

    def parse_data_nodes(self, csv_path):

        def calculate_segment_time():
            for index, segment in enumerate(self.segments):
                time = 0
                for arc in segment.arcs:
                    # print(f"arc {arc.arc_id}: {arc.time} secs")
                    time += arc.time
                # print(f"{index}")
                self.segments[index].time = time
                # print(f"segment {segment.segment_id}: {segment.time} secs")

        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        prev_segment_id, prev_arc_id = 1, 1
        curr_segment_id, curr_arc_id = 1, 1
        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            data_node = Validation.Data_Node(AX=float(line[13]), AY=float(line[14]), roll=float(line[16]), yaw=float(line[17]), front_left_dis=float(line[18]),
                                             front_right_dis=float(line[19]),rear_right_dis=float(line[20]),
                                             rear_left_dis=float(line[21]),rpm=float(line[22]),
                                             distance=float(line[4]))
            self.segments[self.get_segment_index(int(line[0]))].data_nodes.append(data_node)
            self.segments[self.get_segment_index(int(line[0]))].arcs[self.get_arc_index(int(line[1]), int(line[0]))].data_nodes.append(data_node)
            self.segments[self.get_segment_index(int(line[0]))].arcs[self.get_arc_index(int(line[1]), int(line[0]))].time = float(line[3])

        calculate_segment_time()

    def parse_acceleration_data(self, csv_path):
        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

        raw_AX, raw_AY = [0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8], [0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8, 0, 3, 5, 7, 8]
        np_raw_AX, np_raw_AY = np.array(raw_AX), np.array(raw_AY)

        window_size = 11 # Must be odd to have the moving average be centered on the current value

        moving_average_AX = np.convolve(np_raw_AX, np.ones(window_size) / window_size, mode='same')
        moving_average_AX = moving_average_AX[window_size/2:]

        # TODO: Parse acceleration data into raw_AX and raw_AY and put it into data_nodes REMEMBER THE ARRAY IS SMALLER NOW

    def parse_spline_data(self, csv_path):
        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            segment_index = self.get_segment_index(int(line[0]))
            if segment_index is not None:
                self.segments[segment_index].spline_points.append((float(line[2]), float(line[3])))

    def convert_arcs_to_segments(self):
        if not self.arcs:
            self.parse_arc_data("validator/output/04_arcs.csv")

        curr_id, prev_id = self.arcs[0].segment_id, self.arcs[0].segment_id
        start_x, end_x = -1, -1
        start_y, end_y = -1, -1
        arcs = []
        for index, arc in enumerate(self.arcs):
            curr_id = arc.segment_id

            if curr_id != prev_id:
                end_x = self.arcs[index-1].end_x
                end_y = self.arcs[index-1].start_y
                segment = self.Segment(prev_id, start_x, start_y, end_x, end_y, arcs)
                self.segments.append(segment)

                # reset data
                start_x, start_y, end_x, end_y = -1, -1, -1, -1 # reset
                arcs = []

            if start_x == -1:
                start_x = arc.start_x
                start_y = arc.start_y

            if arc == self.arcs[-1]:
                arcs.append(arc)
                end_x = arc.end_x
                end_y = arc.end_y
                segment = self.Segment(curr_id, start_x, start_y, end_x, end_y, arcs)
                self.segments.append(segment)

            arcs.append(arc)
            prev_id = curr_id

        for arc in self.arcs:
            arc.segment = self.segments[self.get_segment_index(arc.segment_id)]

        # for segment in self.segments:
        #     print(f"id: {segment.segment_id}, start_x: {segment.start_x}, start_y: {segment.start_y}, end_x: {segment.end_x}, end_y: {segment.end_y}")

    def get_segment_index(self, segment_id):
        for index, segment in enumerate(self.segments):
            if segment.segment_id == segment_id:
                return index
        return None

    def get_arc_index(self, arc_id, segment_id):
        for segment in self.segments:
            for index, arc in enumerate(segment.arcs):
                if arc.arc_id == arc_id:
                    return index
        return None

    def filter_inaccurate_segments(self, max_arc_length, min_segment_length=0):
        # count = 0
        # for seg_index, segment in enumerate(self.segments):
        #     if len(segment.arcs) < min_segment_length:
        #         self.segments.pop(seg_index)
        #         count+=1
        #         continue
        #     for arc_index, arc in enumerate(segment.arcs):
        #         if arc.length > max_arc_length:
        #             self.segments.pop(seg_index)
        #             count+=1
        #             break
        delete_segments = []
        for seg_index, segment in enumerate(self.segments):
            if len(segment.arcs) < min_segment_length:
                delete_segments.append(segment)
                continue
            for arc_index, arc in enumerate(segment.arcs):
                if arc.length > max_arc_length:
                    delete_segments.append(segment)
                    break
        for segment in delete_segments:
            self.segments.remove(segment)
        print("Filtered {} segments. {} segments remaining.".format(len(delete_segments), len(self.segments)))

    def calculate_correlation_coefficient(self, data:DataType):
        mean_sim, mean_real = 0, 0

        # Calculate the mean of both sim and real data
        sum_real, sum_sim = 0, 0

        numerator = []
        denominator = []
        den_sim_comp, den_real_comp = [], []

        match data:
            case self.DataType.FO_dis:
                # Calculate real mean
                for dis in self.FO_dis_real:
                    sum_real += dis
                mean_real = sum_real / len(self.FO_dis_real)
                # Calculate sim mean
                for dis in self.FO_dis_sim:
                    sum_sim += dis
                mean_sim = sum_sim / len(self.FO_dis_sim)

                # Calculate Pearson Correlation Coefficient (x = sim, y = real)
                for index, dis in enumerate(self.FO_dis_sim):
                    numerator.append((dis - mean_sim) * (self.FO_dis_real[index] - mean_real))
                    den_sim_comp.append((dis - mean_sim)**2)
                    den_real_comp.append((self.FO_dis_real[index] - mean_real)**2)

                return np.sum(numerator) / np.sqrt(np.sum(den_sim_comp) * np.sum(den_real_comp))

            case self.DataType.FI_dis:
                # Calculate real mean
                for dis in self.FI_dis_real:
                    sum_real += dis
                mean_real = sum_real / len(self.FI_dis_real)
                # Calculate sim mean
                for dis in self.FI_dis_sim:
                    sum_sim += dis
                mean_sim = sum_sim / len(self.FI_dis_sim)

                # Calculate Pearson Correlation Coefficient (x = sim, y = real)
                for index, dis in enumerate(self.FI_dis_sim):
                    numerator.append((dis - mean_sim) * (self.FI_dis_real[index] - mean_real))
                    den_sim_comp.append((dis - mean_sim)**2)
                    den_real_comp.append((self.FI_dis_real[index] - mean_real)**2)
                    denominator.append(den_sim_comp[-1] * den_real_comp[-1])

                return np.sum(numerator) / np.sqrt(np.sum(den_sim_comp) * np.sum(den_real_comp))

            case self.DataType.RO_dis:
                # Calculate real mean
                for dis in self.RO_dis_real:
                    sum_real += dis
                mean_real = sum_real / len(self.RO_dis_real)
                # Calculate sim mean
                for dis in self.RO_dis_sim:
                    sum_sim += dis
                mean_sim = sum_sim / len(self.RO_dis_sim)

                # Calculate Pearson Correlation Coefficient (x = sim, y = real)
                for index, dis in enumerate(self.RO_dis_sim):
                    numerator.append((dis - mean_sim) * (self.RO_dis_real[index] - mean_real))
                    den_sim_comp.append((dis - mean_sim)**2)
                    den_real_comp.append((self.RO_dis_real[index] - mean_real)**2)
                    denominator.append(den_sim_comp[-1] * den_real_comp[-1])

                return np.sum(numerator) / np.sqrt(np.sum(den_sim_comp) * np.sum(den_real_comp))

            case self.DataType.RI_dis:
                # Calculate real mean
                for dis in self.RI_dis_real:
                    sum_real += dis
                mean_real = sum_real / len(self.RI_dis_real)
                # Calculate sim mean
                for dis in self.RI_dis_sim:
                    sum_sim += dis
                mean_sim = sum_sim / len(self.RI_dis_sim)

                # Calculate Pearson Correlation Coefficient (x = sim, y = real)
                for index, dis in enumerate(self.RI_dis_sim):
                    numerator.append((dis - mean_sim) * (self.RI_dis_real[index] - mean_real))
                    den_sim_comp.append((dis - mean_sim)**2)
                    den_real_comp.append((self.RI_dis_real[index] - mean_real)**2)
                    denominator.append(den_sim_comp[-1] * den_real_comp[-1])

                return np.sum(numerator) / np.sqrt(np.sum(den_sim_comp) * np.sum(den_real_comp))

            case self.DataType.RPM:
                # Calculate real mean
                for dis in self.rpm_real:
                    sum_real += dis
                mean_real = sum_real / len(self.rpm_real)
                # Calculate sim mean
                for dis in self.rpm_sim:
                    sum_sim += dis
                mean_sim = sum_sim / len(self.rpm_sim)

                # Calculate Pearson Correlation Coefficient (x = sim, y = real)
                for index, dis in enumerate(self.rpm_sim):
                    numerator.append((dis - mean_sim) * (self.rpm_real[index] - mean_real))
                    den_sim_comp.append((dis - mean_sim)**2)
                    den_real_comp.append((self.rpm_real[index] - mean_real)**2)
                    denominator.append(den_sim_comp[-1] * den_real_comp[-1])

                return np.sum(numerator) / np.sqrt(np.sum(den_sim_comp) * np.sum(den_real_comp))

    def calculate_forces(self):

        # Static values for shock potentiometers
        static_FL_shock = 1.552
        static_FR_shock = 1.092
        static_RL_shock = 0.784

        # Motion Ratios for front and rear
        MR_F = 1
        MR_R = 1.1786

        FO_load_real = []
        FI_load_real = []
        RI_load_real = []
        RO_load_real = []

        for segment in self.segments:
            FO_load_real.append([])
            FI_load_real.append([])
            RI_load_real.append([])
            RO_load_real.append([])
            for data_node in segment.data_nodes:

                front_right_dis = (data_node.front_right_shock - static_FR_shock) * MR_F
                front_left_dis = (data_node.front_left_shock - static_FL_shock) * MR_F
                rear_left_dis = (data_node.rear_left_shock - static_RL_shock) * MR_R

                if data_node.arc.turn == self.Arc.Turn.LEFT:
                    # Calculate wheel displacement
                    FO_dis = front_right_dis
                    FI_dis = front_left_dis
                    RO_dis = None
                    RI_dis = rear_left_dis
                    data_node.front_right_dis = front_right_dis
                    data_node.front_left_dis = front_left_dis
                    data_node.rear_left_dis = rear_left_dis

                    # Calculate the loads on each tire
                    FO_load_real[-1].append(self.racecar.W_2 + FO_dis * self.racecar.K_RF)
                    FI_load_real[-1].append(self.racecar.W_1 + FI_dis * self.racecar.K_RF)
                    RI_load_real[-1].append(self.racecar.W_3 + RI_dis * self.racecar.K_RR)
                    RO_load_real[-1].append(self.racecar.W_car - (FO_load_real[-1][-1] + FI_load_real[-1][-1] + RI_load_real[-1][-1]))
                else:
                    # Calculate wheel displacement
                    FO_dis = front_left_dis
                    FI_dis = front_right_dis
                    RO_dis = rear_left_dis
                    RI_dis = None
                    data_node.front_right_dis = front_right_dis
                    data_node.front_left_dis = front_left_dis
                    data_node.rear_left_dis = rear_left_dis

                    # Calculate the loads on each tire
                    FO_load_real[-1].append(self.racecar.W_1 + FO_dis * self.racecar.K_RF)
                    FI_load_real[-1].append(self.racecar.W_2 + FI_dis * self.racecar.K_RF)
                    RO_load_real[-1].append(self.racecar.W_3 + RO_dis * self.racecar.K_RR)
                    RI_load_real[-1].append(self.racecar.W_car - (FO_load_real[-1][-1] + FI_load_real[-1][-1] + RO_load_real[-1][-1]))

                print(f"\nINSTANCE:" + "left turn" if data_node.arc.turn == self.Arc.Turn.LEFT else "right turn")
                print(f"FO_load: {FO_load_real[-1][-1]}\nFI_load: {FI_load_real[-1][-1]}\nRI_load: {RI_load_real[-1][-1]}\nRO_load: {RO_load_real[-1][-1]}")

        return FO_load_real, FI_load_real, RO_load_real, RI_load_real

    def graph(self, graph_type:DataType):

        tk = tkinter.Tk()
        fig = Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, tk)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, tk)
        canvas.get_tk_widget().pack()
        toolbar.update()

        match graph_type:
            case self.DataType.AX:
                # Plot both sim and real AX
                len_AX = np.linspace(0, len(self.AX_sim), len(self.AX_sim))
                len_AX_r = np.linspace(0, len(self.AX_real), len(self.AX_real))
                print(self.AX_sim)
                ax.plot(len_AX, self.AX_sim, label='sim_AX')
                ax.plot(len_AX_r, self.AX_real, label='real_AX')
            case self.DataType.AY:
                # Plot both sim and real AY
                len_AY = np.linspace(0, len(self.AY_sim), len(self.AY_sim))
                len_AY_r = np.linspace(0, len(self.AY_real), len(self.AY_real))
                ax.plot(len_AY, self.AY_sim, label='sim_AY')
                ax.plot(len_AY_r, self.AY_real, label='real_AY')
            case self.DataType.FO_dis:
                # Plot both sim and real FO dis
                len_FO = np.linspace(0, len(self.FO_dis_sim), len(self.FO_dis_sim))
                len_FO_r = np.linspace(0, len(self.FO_dis_real), len(self.FO_dis_real))
                ax.plot(len_FO, self.FO_dis_sim, label='sim_FO_dis')
                ax.plot(len_FO_r, self.FO_dis_real, label='real_FO_dis')
            case self.DataType.FI_dis:
                # Plot both sim and real FI dis
                len_FI = np.linspace(0, len(self.FI_dis_sim), len(self.FI_dis_sim))
                len_FI_r = np.linspace(0, len(self.FI_dis_real), len(self.FI_dis_real))
                ax.plot(len_FI, self.FI_dis_sim, label='sim_FI_dis')
                ax.plot(len_FI_r, self.FI_dis_real, label='real_FI_dis')
            case self.DataType.RO_dis:
                # Plot both sim and real RO dis
                len_RO = np.linspace(0, len(self.RO_dis_sim), len(self.RO_dis_sim))
                len_RO_r = np.linspace(0, len(self.RO_dis_real), len(self.RO_dis_real))
                ax.plot(len_RO, self.RO_dis_sim, label='sim_RO_dis')
                ax.plot(len_RO_r, self.RO_dis_real, label='real_RO_dis')
            case self.DataType.RI_dis:
                # Plot both sim and real RI dis
                len_RI = np.linspace(0, len(self.RI_dis_sim), len(self.RI_dis_sim))
                len_RI_r = np.linspace(0, len(self.RI_dis_real), len(self.RI_dis_real))
                ax.plot(len_RI, self.RI_dis_sim, label='sim_RI_dis')
                ax.plot(len_RI_r, self.RI_dis_real, label='real_RI_dis')
            case self.DataType.FO_load:
                # Plot both sim and real FO load
                len_FO = np.linspace(0, len(self.FO_load_sim), len(self.FO_load_sim))
                len_FO_r = np.linspace(0, len(self.FO_load_real), len(self.FO_load_real))
                ax.plot(len_FO, self.FO_load_sim, label='sim_load_FO')
                ax.plot(len_FO_r, self.FO_load_real, label='real_load_FO')
            case self.DataType.FI_load:
                # Plot both sim and real FI load
                len_FI = np.linspace(0, len(self.FI_load_sim), len(self.FI_load_sim))
                len_FI_r = np.linspace(0, len(self.FI_load_real), len(self.FI_load_real))
                ax.plot(len_FI, self.FI_load_sim, label='sim_load_FI')
                ax.plot(len_FI_r, self.FI_load_real, label='real_load_FI')
            case self.DataType.RO_load:
                # Plot both sim and real RO load
                len_RO = np.linspace(0, len(self.RO_load_sim), len(self.RO_load_sim))
                len_RO_r = np.linspace(0, len(self.RO_load_real), len(self.RO_load_real))
                ax.plot(len_RO, self.RO_load_sim, label='sim_load_RO')
                ax.plot(len_RO_r, self.RO_load_real, label='real_load_RO')
            case self.DataType.RI_load:
                # Plot both sim and real RI load
                len_RI = np.linspace(0, len(self.RI_load_sim), len(self.RI_load_sim))
                len_RI_r = np.linspace(0, len(self.RI_load_real), len(self.RI_load_real))
                ax.plot(len_RI, self.RI_load_sim, label='sim_load_RI')
                ax.plot(len_RI_r, self.RI_load_real, label='real_load_RI')
            case self.DataType.RPM:
                # Plot both sim and real RPM
                len_rpm = np.arange(0, len(self.rpm_sim))
                len_rpm_r = np.linspace(0, len(self.rpm_real))
                ax.plot(len_rpm, self.rpm_sim, label='rpm_sim')
                ax.plot(len_rpm_r, self.rpm_real, label='rpm_real')
        ax.legend()
        tk.mainloop()

    def convert_units(self):
        for arc in self.arcs:
            # Convert from meters to inches
            arc.start_x *= 39.3701
            arc.start_y *= 39.3701
            arc.end_x *= 39.3701
            arc.end_y *= 39.3701
            arc.radius *= 39.3701
            arc.length *= 39.3701
        for segment in self.segments:
            # Convert from meters to inches
            segment.start_x *= 39.3701
            segment.start_y *= 39.3701
            segment.end_x *= 39.3701
            segment.end_y *= 39.3701
            segment.spline_points = np.multiply(segment.spline_points, 39.3701)
            segment.distance_travelled *= 39.3701
            # Convert from mph to in/s
            segment.starting_velocity *= 17.6
            for data_node in segment.data_nodes:
                data_node.AX *= 0.10197162129779283
                data_node.AY *= 0.10197162129779283
                data_node.AZ *= 0.10197162129779283
                data_node.roll *= np.pi/180
                data_node.yaw *= np.pi/180
                data_node.distance_along_segment *= 39.3701

    def parse_data(self):
        validator.parse_arc_data("validator/output/04_arcs.csv")
        validator.parse_spline_data("validator/output/03_spline_points.csv")
        validator.parse_velocity_data("validator/output/05_velocities.csv")
        validator.parse_data_nodes("validator/output/06_arc_points_detailed.csv")
        # validator.parse_acceleration_data("")

    def run_validation(self, sims_per_arc=1, get_error=True):

        self.racecar = car()

        # Get the average error for one data point. Does not take -1's into account.
        def get_average_error(error_arr):
            sum = 0
            subtraction_count = 0
            for error in error_arr:
                if error is not None:
                    sum += error
                else:
                    subtraction_count+=1
            return sum/(len(error_arr)-subtraction_count)

        def lerp(x, x1, x2, y1, y2):
            return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

        self.parse_data()
        self.convert_units()
        self.filter_inaccurate_segments(max_arc_length=500, min_segment_length=3)

        # Compute numbers for data nodes (places where actual data is collected by data acq)
        for segment in self.segments:
            segment.compute_arc_segment_distances()
            segment.calculate_distance_differences()

        # self.segments = [self.segments[2]]

        print(f"data nodes in segment: {len(self.segments[0].data_nodes)}")

        val_track = Validation_Track(self.segments, self.racecar, sims_per_arc)
        self.lapsim_data = val_track.run()

        # Lerp sim data to match the position of real data
        for seg_index, segment in enumerate(self.segments):
            count = 0
            self.lerped_data.append(LapSimData())
            self.lerped_data[-1].initialize(len(segment.data_nodes))
            self.lerped_data[-1].time_array[0] = self.lapsim_data[seg_index].time_array[-1] # Store time var
            # print(f"arcs: {len(segment.arcs)}")
            for arc_index, arc in enumerate(segment.arcs):
                # print(f"data nodes in arc: {arc.data_nodes}")
                for data_index, data_node in enumerate(arc.data_nodes):
                    # print(f"Arc length: {arc.length}")
                    # print(f"data node distance along arc: {data_node.distance_since_arc_start}")
                    self.lerped_data[-1].AX[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].AX[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].AX[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].AY[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].AY[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].AY[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].rpm[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].rpm[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].rpm[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])

                    self.lerped_data[-1].front_outer_displacement[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].front_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].front_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].rear_outer_displacement[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].rear_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].rear_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].front_inner_displacement[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].front_inner_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].front_inner_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].rear_inner_displacement[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].rear_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].rear_outer_displacement[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])

                    self.lerped_data[-1].FI_load_array[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].FI_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].FI_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].FO_load_array[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].FO_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].FO_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].RI_load_array[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].RI_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].RI_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    self.lerped_data[-1].RO_load_array[count] = lerp(arc.find_data_node_distance_ratio(data_node.distance_since_arc_start, sims_per_arc), 0, 1, self.lapsim_data[seg_index].RO_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc)], self.lapsim_data[seg_index].RO_load_array[arc_index*sims_per_arc + arc.find_sim_node_index(data_node.distance_since_arc_start, sims_per_arc) + 1])
                    count += 1

        # Store all data in arrays suitable for writing to a csv
        # Indices are segments
        self.time_sim, self.time_real, self.time_error = [], [], []
        # Indices are data nodes
        self.rpm_sim, self.rpm_real, self.rpm_error = [], [], []
        self.arc_id, self.segment_id = [], []

        self.AX_sim, self.AY_sim = [], []
        self.AX_real, self.AY_real = [], []
        self.AX_error, self.AY_error = [], []

        self.FO_dis_sim, self.RO_dis_sim, self.FI_dis_sim, self.RI_dis_sim = [], [], [], []
        self.FO_dis_real, self.RO_dis_real, self.FI_dis_real, self.RI_dis_real = [], [], [], []
        self.FO_dis_error, self.RO_dis_error, self.FI_dis_error, self.RI_dis_error = [], [], [], []

        self.FO_load_sim, self.RO_load_sim, self.FI_load_sim, self.RI_load_sim = [], [], [], []
        self.FO_load_real_temp, self.FI_load_real_temp, self.RO_load_real_temp, self.RI_load_real_temp = self.calculate_forces()
        self.FO_load_real, self.FI_load_real, self.RO_load_real, self.RI_load_real = [], [], [], []
        self.FO_load_error, self.RO_load_error, self.FI_load_error, self.RI_load_error = [], [], [], []
        for seg_index, segment in enumerate(self.segments):
            print(self.lerped_data[seg_index].AX)
            # Store time only once per segment, since only the time from the beginning to the end of the segment is collected.
            self.time_sim.append(self.lerped_data[seg_index].time_array[0])
            self.time_real.append(segment.time)
            self.time_error.append(((self.time_sim[-1] - self.time_real[-1])/self.time_real[-1])*100 if self.time_real[-1] != 0 else None)
            for data_index, data_node in enumerate(segment.data_nodes):
                # Segment ID
                self.segment_id.append(data_node.arc.segment_id)
                # Arc ID
                self.arc_id.append(data_node.arc.arc_id)
                # AX
                AX_err = ((self.lerped_data[seg_index].AX[data_index] - data_node.AX)/data_node.AX)*100 if data_node.AX != 0 else None
                self.AX_sim.append(self.lerped_data[seg_index].AX[data_index])
                self.AX_real.append(data_node.AX)
                self.AX_error.append(AX_err)
                # AY
                AY_err = ((self.lerped_data[seg_index].AY[data_index] - data_node.AY)/data_node.AY)*100 if data_node.AY != 0 else None
                self.AY_sim.append(self.lerped_data[seg_index].AY[data_index])
                self.AY_real.append(data_node.AY)
                self.AY_error.append(AY_err)
                # FO_dis
                front_outer_dis = data_node.front_right_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.front_left_dis
                front_outer_error = ((self.lerped_data[seg_index].front_outer_displacement[data_index] - front_outer_dis)/front_outer_dis)*100 if front_outer_dis != 0 else None
                self.FO_dis_sim.append(self.lerped_data[seg_index].front_outer_displacement[data_index])
                self.FO_dis_real.append(front_outer_dis)
                self.FO_dis_error.append(front_outer_error)
                # RO_dis
                rear_outer_dis = None if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.rear_left_dis
                rear_outer_error = ((self.lerped_data[seg_index].rear_outer_dis[data_index] - rear_outer_dis)/rear_outer_dis)*100 if rear_outer_dis != None and rear_outer_dis != 0 else None
                self.RO_dis_sim.append(self.lerped_data[seg_index].rear_outer_displacement[data_index])
                self.RO_dis_real.append(rear_outer_dis)
                self.RO_dis_error.append(rear_outer_error)
                # FI_dis
                front_inner_dis = data_node.front_left_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.front_right_dis
                front_inner_error = ((self.lerped_data[seg_index].front_inner_displacement[data_index] - front_inner_dis)/front_inner_dis)*100 if front_inner_dis != 0 else None
                self.FI_dis_sim.append(self.lerped_data[seg_index].front_inner_displacement[data_index])
                self.FI_dis_real.append(front_inner_dis)
                self.FI_dis_error.append(front_inner_error)
                # RI_dis
                rear_inner_dis = data_node.rear_left_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else None
                rear_inner_error = ((self.lerped_data[seg_index].rear_inner_displacement[data_index] - rear_inner_dis)/rear_inner_dis)*100 if rear_inner_dis != None and rear_inner_dis != 0 else None
                self.RI_dis_sim.append(self.lerped_data[seg_index].rear_inner_displacement[data_index])
                self.RI_dis_real.append(rear_inner_dis)
                self.RI_dis_error.append(rear_inner_error)
                # FO_load
                front_outer_load = self.FO_load_real_temp[seg_index][data_index]
                front_outer_load_error = ((self.lerped_data[seg_index].FO_load_array[data_index] - front_outer_load)/front_outer_load)*100 if front_outer_load != 0 else None
                self.FO_load_sim.append(self.lerped_data[seg_index].FO_load_array[data_index])
                self.FO_load_real.append(front_outer_load)
                self.FO_dis_error.append(front_outer_error)
                # RO_load
                rear_outer_load = self.RO_load_real_temp[seg_index][data_index]
                rear_outer_load_error = ((self.lerped_data[seg_index].RO_load_array[data_index] - rear_outer_load)/rear_outer_load)*100 if rear_outer_load != 0 else None
                self.RO_load_sim.append(self.lerped_data[seg_index].RO_load_array[data_index])
                self.RO_load_real.append(rear_outer_load)
                self.RO_dis_error.append(rear_outer_error)
                # FI_load
                front_inner_load = self.FI_load_real_temp[seg_index][data_index]
                front_inner_load_error = ((self.lerped_data[seg_index].FI_load_array[data_index] - front_inner_load)/front_inner_load)*100 if front_inner_load != 0 else None
                self.FI_load_sim.append(self.lerped_data[seg_index].FI_load_array[data_index])
                self.FI_load_real.append(front_inner_load)
                self.FI_dis_error.append(front_inner_error)
                # RI_load
                rear_inner_load = self.RI_load_real_temp[seg_index][data_index]
                rear_inner_load_error = ((self.lerped_data[seg_index].RI_load_array[data_index] - rear_inner_load)/rear_inner_load)*100 if rear_inner_load != 0 else None
                self.RI_load_sim.append(self.lerped_data[seg_index].RI_load_array[data_index])
                self.RI_load_real.append(rear_inner_load)
                self.RI_dis_error.append(rear_inner_error)
                # rpm
                rpm_err = ((self.lerped_data[seg_index].rpm[data_index] - data_node.rpm) / data_node.rpm) * 100 if data_node.rpm != 0 else None
                self.rpm_sim.append(self.lerped_data[seg_index].rpm[data_index])
                self.rpm_real.append(data_node.rpm)
                self.rpm_error.append(rpm_err)

        if get_error:
            average_time_error = round(get_average_error(self.time_error), 1) if self.time_error else None
            average_AX_error = round(get_average_error(self.AX_error), 1) if self.AX_error else None
            average_AY_error = round(get_average_error(self.AY_error), 1) if self.AY_error else None
            average_FO_dis_error = round(get_average_error(self.FO_dis_error), 1) if self.FO_dis_error else None
            average_RO_dis_error = round(get_average_error(self.RO_dis_error), 1) if self.RO_dis_error else None
            average_FI_dis_error = round(get_average_error(self.FI_dis_error), 1) if self.FI_dis_error else None
            average_RI_dis_error = round(get_average_error(self.RI_dis_error), 1) if self.RI_dis_error else None
            print(f"\n---------------OVERALL REPORT---------------\nAverage Time error: {average_time_error}%\nAverage AX error: {average_AX_error}%\nAverage AY error: {average_AY_error}%\nAverage FO error: {average_FO_dis_error}%\nAverage RO error: {average_RO_dis_error}%\nAverage FI error: {average_FI_dis_error}%\nAverage RI error: {average_RI_dis_error}%\n")

        # Remove unrealistically large RPM
        # for index, error in enumerate(self.rpm_error):
        #     if error is not None and error > 100000:
        #         self.rpm_error[index] = None
        # average_rpm_error = round(get_average_error(self.rpm_error), 1) if self.rpm_error else None

        # Write data into csv
        f = open(os.path.join(os.getcwd(), "validation.csv"), "w")
        writer = csv.writer(f)
        writer.writerow(["Segment #", "Arc #", "Time Sim", "Time Real", "Time Error", "FO Sim", "FO Real", "FO Error", "RO Sim", "RO Real", "RO Error", "FI Sim", "FI Real", "FI Error", "RI Sim", "RI Real", "RI Error", "RPM sim", "RPM real", "RPM error"])
        prev_segment_id = 0
        time_index = 0
        for index, AX in enumerate(self.AX_sim):
            if self.segment_id[index] != prev_segment_id:
                writer.writerow([f"Segment {self.segment_id[index]}",f"",f"{self.time_sim[time_index]} secs", f"{self.time_real[time_index]} secs", f"{self.time_error[time_index]}%"])

                time_index+=1
                prev_segment_id = self.segment_id[index]

            writer.writerow([f"Segment {self.segment_id[index]}", f"Arc {self.arc_id[index]}", None, None, None,  f"{self.FO_dis_sim[index]} in", f"{self.FO_dis_real[index]} in", f"{self.FO_dis_error[index]}%", f"{self.RO_dis_sim[index]} in", f"{self.RO_dis_real[index]} in", f"{self.RO_dis_error[index]}%", f"{self.FI_dis_sim[index]} in", f"{self.FI_dis_real[index]} in", f"{self.FI_dis_error[index]}%", f"{self.RI_dis_sim[index]} in", f"{self.RI_dis_real[index]} in", f"{self.RI_dis_error[index]}%", f"{self.rpm_sim[index]}", f"{self.rpm_real[index]}", f"{self.rpm_error[index]}%"])

        f.close()

    def run_rust_code(self):
        # Paths
        working_dir = os.path.join(os.getcwd(), "validator")
        rust_exe = os.path.join(working_dir, "target", "release", "gps-data-smoothing-v2")

        # Create an executable for the Rust code.
        subprocess.run(["cargo", "build", "--release"], cwd=working_dir, check=True)
        # Run the executable that was just created
        subprocess.run([rust_exe], cwd=working_dir, check=True)

# Acts as a singleton
validator = Validation()
validator.run_validation(1, get_error=False)

data_type = validator.DataType.FI_dis
print(f"\nCorrelation coefficient: {validator.calculate_correlation_coefficient(data_type)}")
validator.graph(data_type)