import threading

from gen_lapsim import spline_track as spln
import pickle
import tqdm as tq

from loading_window import LoadingWindow

class DisplayTrack:

    def __init__(self, ui_instance, nodes = 5000):

        print("[Displaying Track...]")

        self.nodes = nodes

        self.ui_instance = ui_instance

        # Will set later.
        self.loading_window = None

        # DisplayTrack has these if the track was not generated beforehand
        self.points = []
        self.points_x =[]
        self.points_y =[]
        self.points_x2 =[]
        self.points_y2 = []

    # Saves data from lap_data.points into organized arrays.
    def initialize_notgenerated_track(self, lap_data):
        # Guard code to make sure user has given points file and car file. (should never really be activated, just a precaution)
        if lap_data.points is not None and lap_data.car is not None:
            # loading points
            self.points = lap_data.points

            self.car = lap_data.car

            # defining different points
            try: # try-except to account for different point storage formats (this first one is the newer format)
                self.points_x =  self.points['p1x']
                self.points_y =  self.points['p1y']
                self.points_x2 =  self.points['p2x']
                self.points_y2 =  self.points['p2y']
            except TypeError: # Older format - not in use anymore but kept for backwards compatibility
                self.points_x = []
                self.points_y = []
                self.points_x2 = []
                self.points_y2 = []
                for i in self.points.nds:
                    self.points_x.append(i.x1)
                    self.points_y.append(i.y1)
                    self.points_x2.append(i.x2)
                    self.points_y2.append(i.y2)

    # Either load or show a track depending on what is available in lap_data.
    def run_lap_data(self, display_track, lap_data):
        # if there is a generated track already in the lap_data file, then use that. If not, make a generated track.
        if lap_data.points is not None and lap_data.generated_track is None:
            self.create_and_show_notgenerated_track(display_track, lap_data)
        elif lap_data.generated_track is not None:
            self.show_generated_track(display_track, lap_data)

    # Go through the process of generating a track, using a loading window, and displaying the track.
    def create_and_show_notgenerated_track(self,display_track, lap_data, prev_lap_data = None, generate_report = False, changed_car_model = False):

        x = None # will be used later.

        # Function that saves lap_data from generated track. Used later in function as argument.
        def save_lap_data():
            # Save updated lap_data instance with generated track
            lap_data.generated_track = self.notgenerated_trk
            print(f"Generated Track: {lap_data.generated_track is not None}")
            with open(lap_data.file_location, "wb") as f:
                pickle.dump(lap_data, f)

        # Run lapsim and plot the track.
        def run_and_plot():
            #run sim to get data
            self.notgenerated_trk.run_sim(car=lap_data.car, nodes=self.nodes)

            # If no previous lap data, just plot the lap. Else, give the user a REPORT.
            if prev_lap_data is None:
                self.notgenerated_trk.plot(lap_data_stuff=lap_data, save_lap_data_func=save_lap_data, display_track=display_track, ui_instance=self.ui_instance) # displaying optimized track
            else:
                self.notgenerated_trk.plot(lap_data_stuff=lap_data, prev_lap_data=prev_lap_data, save_lap_data_func=save_lap_data, display_track=display_track, ui_instance=self.ui_instance, generate_report=generate_report, changed_car_model=changed_car_model) # displaying optimized track

        # initialize points and stuff
        self.initialize_notgenerated_track(lap_data)

        # close track graph if open, also need this if statement to run without errors
        if self.ui_instance is not None:
            self.ui_instance.close_LapsimUI_window()
            self.ui_instance.running_from_ungenerated_track = True

        # creating track object
        self.notgenerated_trk = spln.track(self.points_x, self.points_y, self.points_x2, self.points_y2, lap_data.car)

        # optimizing track
        if len(self.points_x) > 5:
            x = threading.Thread(target=self.notgenerated_trk.adjust_track, args=([40, 30, 30, 80],[100, 30, 10, 5],))
            x.daemon = True
            x.start()

        # If a loading window has already been created, then reset the window. If it has not, then create the window.
        if self.loading_window is None:
            self.loading_window = LoadingWindow()
        else:
            self.loading_window.reset()
        if len(self.points_x) > 18: # Loading window will stay on screen if there is not enough to load, so set a minimum.
            self.loading_window.open_window()

        instance = tq.tqdm(total=100) # Create instance of tqdm (library used to estimate time remaining)
        self.last_k = 0 # Set last_k to 0 for now, used to track how many k's have been added since last time loading was checked
        def update_loading_window():
            # update instance to contain how many k's have been added since last time loading was checked
            instance.update((spln.k - self.last_k) / spln.len_s * 100)

            # Use tqdm library to calculate rate of loading in iterations per second. 1 if rate is None.
            rate = 1
            if instance.format_dict['rate']:
                rate = instance.format_dict['rate']

            # Calculate the amount of seconds left.
            seconds_left = int((100 - (spln.k / spln.len_s * 100)) / rate)
            self.last_k = spln.k # Set last k to the current k so we can use it in the next iteration.
            if x is not None and x.is_alive(): # If loading has not finished, update the loading window to display loading progress.
                self.loading_window.update_loading(spln.k / spln.len_s * 100, seconds_left)
                spln.track_root.after(100, update_loading_window) # Call this same function again after 0.1 seconds.
            else:
                self.loading_window.update_loading(100,0)
                run_and_plot() # Once loading is done, run the LapSimUI class and plot the track.

        update_loading_window() # Call function to start the loop.

    # Show the generated track within lap_data.
    def show_generated_track(self, display_track, lap_data):
        # close track graph if open, also need this if statement to run without errors
        if self.ui_instance is not None:
            self.ui_instance.close_LapsimUI_window()
            self.ui_instance.running_from_ungenerated_track = False
        lap_data.generated_track.plot(lap_data_stuff=lap_data, display_track=display_track, ui_instance=self.ui_instance)