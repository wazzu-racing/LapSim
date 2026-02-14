import csv
import os
from enum import Enum

import numpy as np

from gen_lapsim.lapsim import LapSimData
from lapsim_validation import Validation_Track
from models.car_model import Car


class Validation:

    class Data_Node:
        def __init__(self, AX, AY, AZ, roll, yaw, front_left_dis, front_right_dis, rear_left_dis, rear_right_dis, rpm):
            self.AX = AX
            self.AY = AY
            self.AZ = AZ
            self.roll = roll
            self.yaw = yaw
            self.front_left_dis = front_left_dis
            self.front_right_dis = front_right_dis
            self.rear_left_dis = rear_left_dis
            self.rear_right_dis = rear_right_dis
            self.rpm = rpm

        AX: float = 0
        AY: float = 0
        AZ: float = 0
        roll: float = 0
        yaw: float = 0
        front_left_dis: float = 0
        front_right_dis: float = 0
        rear_left_dis: float = 0
        rear_right_dis: float = 0
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

        distance_along_segment: float = 0
        data_nodes: list[Validation.Data_Node] = []
        turn: Turn = Turn.LEFT

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

                data_node.distance_since_arc_start = data_node.distance_along_segment - self.arcs[arc_index].distance_along_segment

    arcs = [] # The curves between every single point
    segments = [] # Collections of arcs. This is "good" data. Only contains a segment where there is both velocity and spline data.
    lapsim_data = [] # Data collected by running the lapsim. Contains segments number of LapSimData objects.

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
            arc.arc_id = float(line[1])
            arc.radius = float(line[4])
            arc.start_x = float(line[7])
            arc.start_y = float(line[8])
            arc.end_x = float(line[9])
            arc.end_y = float(line[10])
            arc.length = float(line[11])

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

        # Read into string
        csv_file = open(csv_path, newline='\n')
        reader = csv.reader(csv_file)

        for index, line in enumerate(reader):
            # Skip the first line, as it is just headers
            if index == 0:
                continue

            # TODO: Parse data

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
            self.parse_arc_data("lapsim_validation/output/04_arcs.csv")

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

        # for segment in self.segments:
        #     print(f"id: {segment.segment_id}, start_x: {segment.start_x}, start_y: {segment.start_y}, end_x: {segment.end_x}, end_y: {segment.end_y}")

    def get_segment_index(self, segment_id):
        for index, segment in enumerate(self.segments):
            if segment.segment_id == segment_id:
                return index
        return None

    def fill_missing_segment(self, segment_id):
        prev_id = self.segments[0].segment_id
        for index, segment in enumerate(self.segments):
            if segment_id < segment.segment_id:
                new_segment = self.Segment(segment_id, -1, -1, -1, -1)
                self.segments.insert(index, new_segment)
            prev_id = segment.segment_id

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

    def parse_data(self):
        validator.parse_arc_data("lapsim_validation/output/04_arcs.csv")
        validator.parse_spline_data("lapsim_validation/output/03_spline_points.csv")
        validator.parse_velocity_data("lapsim_validation/output/05_velocities.csv")
        # validator.parse_data_nodes("") # TODO

        # # Compute numbers for data nodes (places where actual data is collected by data acq)
        # for segment in self.segments:
        #     segment.do_data_node_computations()

    def run_validation(self, car=None):

        def lerp(x, x1, x2, y1, y2):
            return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

        car = Car(resolution=100)

        testing = True

        self.parse_data()
        self.convert_units()

        data_nodes = []

        if testing:
            data1 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data1.distance_along_segment = 0
            data2 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data2.distance_along_segment = 64
            data3 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data3.distance_along_segment = 130
            data4 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data4.distance_along_segment = 200
            data5 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data5.distance_along_segment = 250
            data6 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data6.distance_along_segment = 280
            data7 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            data7.distance_along_segment = 360
            data8 = Validation.Data_Node(AX = 1, AY = 0.3, AZ = 0, roll = 0, yaw = 0, front_left_dis = 0, front_right_dis = 0, rear_left_dis = 0, rear_right_dis = 0, rpm = 0)
            # data8.distance_along_segment = self.segments[0].distance_travelled
            data8.distance_along_segment = 450
            print(f"distance travelled: {self.segments[0].distance_travelled}")

            data_nodes = [data1, data2, data3, data4, data5, data6, data7, data8]

            segment = self.segments[0]
            segment.data_nodes = data_nodes

        if testing:
            for index, arc in enumerate(self.segments[0].arcs):
                match index:
                    case 0:
                        arc.length = 60.2
                    case 1:
                        arc.length = 62.4
                    case 2:
                        arc.length = 70.8
                    case 3:
                        arc.length = 40.9
                    case 4:
                        arc.length = 31.1
                    case 5:
                        arc.length = 90.4
                    case 6:
                        arc.length = 83.2
                    case 7:
                        arc.length = 91.1

        # Compute numbers for data nodes (places where actual data is collected by data acq)
        if testing:
            self.segments[0].compute_arc_segment_distances()
            self.segments[0].calculate_distance_differences()
        else:
            for segment in self.segments:
                segment.compute_arc_segment_distances()
                segment.calculate_distance_differences()

        if testing:
            val_track = Validation_Track([self.segments[0]], car)
            self.lapsim_data = val_track.run()

            for data in self.lapsim_data:
                for index, AX in enumerate(data.AX):
                    print(f"AX: {AX} g's, AY: {data.AY[index]} g's\nFO_dis: {data.front_outer_displacement[index]} in, RO_dis: {data.rear_outer_displacement[index]} in, FI_dis: {data.front_inner_displacement[index]} in, RI_dis: {data.rear_inner_displacement[index]} in,")
        else:
            val_track = Validation_Track(self.segments, car)
            val_track.run()

        # Lerp sim data to match the position of real data
        lerped_data = []
        for seg_index, segment in enumerate([self.segments[0]]):
            count = 0
            lerped_data.append(LapSimData())
            lerped_data[-1].initialize(len(segment.data_nodes))
            for arc_index, arc in enumerate(segment.arcs):
                print(f"data nodes in arc: {arc.data_nodes}")
                for data_index, data_node in enumerate(arc.data_nodes):
                    lerped_data[-1].AX[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].AX[arc_index], self.lapsim_data[seg_index].AX[arc_index+1])
                    lerped_data[-1].AY[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].AY[arc_index], self.lapsim_data[seg_index].AY[arc_index+1])
                    lerped_data[-1].front_outer_displacement[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].front_outer_displacement[arc_index], self.lapsim_data[seg_index].front_outer_displacement[arc_index+1])
                    lerped_data[-1].rear_outer_displacement[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].rear_outer_displacement[arc_index], self.lapsim_data[seg_index].rear_outer_displacement[arc_index+1])
                    lerped_data[-1].front_inner_displacement[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].front_inner_displacement[arc_index], self.lapsim_data[seg_index].front_inner_displacement[arc_index+1])
                    lerped_data[-1].rear_inner_displacement[count] = lerp(data_node.distance_since_arc_start/data_node.arc.length, 0, 1, self.lapsim_data[seg_index].rear_inner_displacement[arc_index], self.lapsim_data[seg_index].rear_inner_displacement[arc_index+1])
                    count += 1
                lerped_data[-1].time_array[0] = self.lapsim_data[seg_index].time_array[-1] # Store time var

        # Store all data in a csv-friendly format
        time_sim = 0
        time_real = 0
        time_error = 0 # percent
        arc_id = []
        AX_sim, AY_sim = [], []
        AX_real, AY_real = [], []
        AX_error, AY_error = [], []
        FO_dis_sim, RO_dis_sim, FI_dis_sim, RI_dis_sim = [], [], [], []
        FO_dis_real, RO_dis_real, FI_dis_real, RI_dis_real = [], [], [], []
        FO_dis_error, RO_dis_error, FI_dis_error, RI_dis_error = [], [], [], []
        for seg_index, segment in enumerate([self.segments[0]]):
            # Store time only once per segment, since only the time from the beginning to the end of the segment is collected.
            time_sim = lerped_data[seg_index].time_array[0]
            time_real = segment.time
            time_error = ((time_sim - time_real)/time_real)*100 if time_real != 0 else -1
            for data_index, data_node in enumerate(segment.data_nodes):
                # Arc ID
                arc_id.append(data_node.arc.arc_id)
                # AX
                AX_sim.append(lerped_data[seg_index].AX[data_index])
                AX_real.append(data_node.AX)
                AX_error.append(((lerped_data[seg_index].AX[data_index] - data_node.AX)/data_node.AX)*100)
                # AY
                AY_sim.append(lerped_data[seg_index].AY[data_index])
                AY_real.append(data_node.AY)
                AY_error.append(((lerped_data[seg_index].AY[data_index] - data_node.AY)/data_node.AY)*100)
                # FO
                front_outer_dis = data_node.front_right_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.front_left_dis
                front_outer_error = ((lerped_data[seg_index].front_outer_displacement[data_index] - front_outer_dis)/front_outer_dis)*100 if front_outer_dis != 0 else -1
                FO_dis_sim.append(lerped_data[seg_index].front_outer_displacement[data_index])
                FO_dis_real.append(front_outer_dis)
                FO_dis_error.append(front_outer_error)
                # RO
                rear_outer_dis = data_node.rear_right_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.rear_left_dis
                rear_outer_error = ((lerped_data[seg_index].rear_outer_displacement[data_index] - rear_outer_dis)/rear_outer_dis)*100 if rear_outer_dis != 0 else -1
                RO_dis_sim.append(lerped_data[seg_index].rear_outer_displacement[data_index])
                RO_dis_real.append(rear_outer_dis)
                RO_dis_error.append(rear_outer_error)
                # FI
                front_inner_dis = data_node.front_left_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.front_right_dis
                front_inner_error = ((lerped_data[seg_index].front_inner_displacement[data_index] - front_inner_dis)/front_inner_dis)*100 if front_inner_dis != 0 else -1
                FI_dis_sim.append(lerped_data[seg_index].front_inner_displacement[data_index])
                FI_dis_real.append(front_inner_dis)
                FI_dis_error.append(front_inner_error)
                # RI
                rear_inner_dis = data_node.rear_left_dis if data_node.arc.turn == Validation.Arc.Turn.LEFT else data_node.rear_right_dis
                rear_inner_error = ((lerped_data[seg_index].rear_inner_displacement[data_index] - rear_inner_dis)/rear_inner_dis)*100 if rear_inner_dis != 0 else -1
                RI_dis_sim.append(lerped_data[seg_index].rear_inner_displacement[data_index])
                RI_dis_real.append(rear_inner_dis)
                RI_dis_error.append(rear_inner_error)

        # Write data into csv
        f = open(os.path.join(os.getcwd(), "validation.csv"), "w")
        writer = csv.writer(f)
        writer.writerow(["Segment #", "Arc #", "Time Sim", "Time Real", "Time Error", "AX Sim", "AX real", "AX Error", "AY Sim", "AY real", "AY Error", "FO Sim", "FO Real", "FO Error", "RO Sim", "RO Real", "RO Error", "FI Sim", "FI Real", "FI Error", "RI Sim", "RI Real", "RI Error"])
        for seg_index, segment in enumerate([self.segments[0]]):
            writer.writerow([f"Segment {seg_index}", None, f"{time_sim} secs", f"{time_real} secs", f"{time_error}%"])
            for index, AX in enumerate(AX_sim):
                writer.writerow([f"Segment {seg_index}", f"Arc {index}", None, None, None, f"{AX} g's", f"{AX_real[index]} g's", f"{AX_error[index]}%", f"{AY_sim[index]} g's", f"{AY_real[index]} g's", f"{AY_error[index]}%", f"{FO_dis_sim[index]} in", f"{FO_dis_real[index]} in", f"{FO_dis_error[index]}%", f"{RO_dis_sim[index]} in", f"{RO_dis_real[index]} in", f"{RO_dis_error[index]}%", f"{FI_dis_sim[index]} in", f"{FI_dis_real[index]} in", f"{FI_dis_error[index]}%", f"{RI_dis_sim[index]} in", f"{RI_dis_real[index]} in", f"{RI_dis_error[index]}%"])
            writer.writerow([]) # skip line after each segment
        f.close()

        # val_track.segment_data[0].AX

        # val_track.run_sim(car, nodes=1000, initial_velocity=0)
        # val_track.plt_track(self.arcs)

        # for segment in self.segments:
        #     print(f"ID: {segment.segment_id}")
        #     print(f"velocity: {segment.starting_velocity}")
        #     print(f"distance travelled: {segment.compute_distance_travelled()}")

    def run_rust_code(self):
        pass

# Acts as a singleton
validator = Validation()
validator.run_validation()