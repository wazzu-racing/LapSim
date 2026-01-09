import tkinter

from PIL import ImageTk, Image
import pickle

from interface.file_management.file_manager import file_manager
from LapData import LapData

class LapSimGoCrazy:

    def __init__(self, image_path=None, track_file=None, editing = False):

        # Check if there is a track file to load stuff from. If there is, load the stuff from the file.
        if track_file is None:
            # Initialize arrays that store 'x' and 'y' coordinates of self.clicked points
            self.points_x = []
            self.points_y = []

            # Arrays that hold the x and y positions of the alternating points. (points alternate between being
            # appended in p1x/p1y and p2x/p2y.)
            self.p1x = []
            self.p1y = []
            self.p2x = []
            self.p2y = []

            # Keeps track of the current points.
            self.x1, self.y1 = 0, 0
            self.x2, self.y2 = 0, 0

            self.dot_positions = [] # Stores the positions of the dots in tuples.
            self.pxl_to_in = 1 # pxl to in ratio when displaying the track.

            self.p_num = 0 # Keeps track of which part of the track-making process the user is in.
            self.clicks = 0 # Keeps track of how many times the user has clicked.
            self.scale_factor = 1/2 # scale factor for the image on the screen.

            self.line_drawn = False # Keeps track of whether the line to measure pxl to in ratio has been drawn.
            self.can_drag_image = False # Allows user to drag the image across the screen.
            self.textboxDisplayed = False # Tracks whether the feet entry widget is currently displayed.

            self.image_path_saved = image_path
        else:
            with open(track_file, 'rb') as f:
                track = pickle.load(file=f)
            track_points = track.points

            self.points_x = track_points['points_x']
            self.points_y = track_points['points_y']

            self.p1x = track_points['p1x']
            self.p2x = track_points['p2x']
            self.p1y = track_points['p1y']
            self.p2y = track_points['p2y']

            self.dot_positions = track_points['dot_positions']
            self.pxl_to_in = track_points['pxl_to_in']

            self.p_num = track_points['p_num']
            self.scale_factor = track_points['scale_factor']

            # If there is only 1 click saved, reset clicks to 0 so user can draw the line (1 click is when user clicked 1 point but didn't finish drawing the line)
            if track_points['clicks'] == 1:
                self.clicks = 0
            else:
                self.clicks = track_points['clicks']

            self.line_drawn = track_points['line_drawn']
            self.can_drag_image = track_points['can_drag_image']
            self.textboxDisplayed = track_points['textboxDisplayed']

            self.image_path_saved = track_points['image_path_saved']

        # will be set later.
        self.go_crazy_root = None

        # If the user is editing the track.
        self.editing = editing

        # Height and width of window.
        self.p_width = 1400
        self.p_height = 600

        # Position of the window that the user moves around.
        self.y_pos = 0
        self.x_pos = 0

        # array of visual oval objects. (dots)
        self.dots = []

        # position of mouse
        self.mouse_x, self.mouse_y = 0, 0

        self.time_pressed = 0.0 # Time that the user has been pressing down their mouse button.
        self.holding_down_mouse = False
        self.last_held_down_pos_x, self.last_held_down_pos_y = 0, 0 # Where the user first held down their mouse when dragging the window around.
        self.gathered_held_down_pos = False # If last_held_down_pos's have been collected.

        self.line_x1, self.line_y1, self.line_x2, self.line_y2 = 0, 0, 0, 0 # Position of the dragged line.
        self.dragging_line = False # Is currently dragging the line.
        self.clicked = False # If the user has clicked and they are dragging the line.

        self.clicking_button = False # If the user is clicking the line reset button.

        # How far the window moves when the user uses arrow keys to move window.
        self.move_step = 10

        # Initialize window
        self.go_crazy_root = tkinter.Toplevel()
        self.go_crazy_root.title("Plot LAPSIM Track")

        # If the image is not none, set a bunch of vars.
        if self.image_path_saved is not None:
            self.immage = Image.open(self.image_path_saved)
            self.img = ImageTk.PhotoImage(self.immage)

            # Save image dimensions
            self.img_width =  self.immage.width
            self.img_height = self.immage.height
            self.img_width_center = self.immage.width/2
            self.img_height_center = self.immage.height/2
            self.resize_img = ImageTk.PhotoImage(self.immage.resize((int(self.img_width*self.scale_factor), int(self.img_height*self.scale_factor))))
        else:
            self.immage = None
            self.img = None
            self.img_width =  1000
            self.img_height = 1000
            self.img_width_center = 500
            self.img_height_center = 500
            self.resize_img = None
        # Initialize tkinter widgets
        self.panel = tkinter.Canvas(master=self.go_crazy_root, width=self.p_width, height=self.p_height)
        self.image_item = self.panel.create_image(self.p_width/2, self.p_height/2, image=self.img)
        self.panel.pack(side = "bottom", fill = "both", expand = "yes")
        self.intro_text_widget = tkinter.Label(self.go_crazy_root, width=60, text="Click two points that are a known distance apart to configure measurements.")
        self.intro_text_widget.pack()
        self.entry_widget = tkinter.Entry(self.go_crazy_root, width=30)
        self.entry_text_widget = tkinter.Label(self.go_crazy_root, width=60, text="Enter the distance (in feet) between the two points you self.clicked, then press Enter")
        self.plot_text_widget = tkinter.Label(self.go_crazy_root, width=150, text="Click points to make gates. Each gate has 2 points. The car will drive through these gates.\nPress 's' to save your track and 'z' to undo last point.")

        print(f"Image dimensions: {self.img_width} x {self.img_height}")

        # Plot saved points if there are any
        if track_file is not None:
            self.plot_saved_points()
            # Configure label based on current state
            self.configure_label()

        # Zoom image in
        if self.resize_img is not None:
            self.panel.itemconfig(self.image_item, image=self.resize_img)

        # Set redo line button widget to connect to reset_line function
        self.redo_line_button_widget = tkinter.Button(self.go_crazy_root, text="Redo Line", command=self.reset_line)

        # bind keys
        self.bind_go_crazy_keys()

        # self.save_ungenerated_track()

        self.go_crazy_root.withdraw()

        # Only allow the user to hide the window, not close it
        self.go_crazy_root.protocol("WM_DELETE_WINDOW", self.close_window())

    def open_window(self):
        self.go_crazy_root.deiconify()

    def close_window(self):
        self.go_crazy_root.withdraw()

    # Reset the line the user drew.
    def reset_line(self):
        print("Redoing line...")

        self.clicks = 0
        self.entry_widget.pack_forget()
        self.entry_text_widget.pack_forget()
        self.plot_text_widget.pack_forget()
        self.redo_line_button_widget.pack_forget()
        self.panel.delete("Line")
        self.intro_text_widget.pack()
        self.textboxDisplayed = False
        self.can_drag_image = False
        self.line_drawn = False
        self.clicked = False
        self.points_x = []
        self.points_y = []

        self.clicking_button = True

    # Record the time that the user clicks.
    def record_click(self, event):
        self.time_pressed = event.time

        self.holding_down_mouse = True

    # When the user releases their click, process what should happen.
    def record_release(self, event):
        self.holding_down_mouse = False
        self.gathered_held_down_pos = False

        if event.time - self.time_pressed < 200: # Only register as a click if mouse was held down for less than 200ms
            # Only record click if mouse is within the self.panel (prevents inaccurate starting point for line) and the user is not also clicking the redo line button
            if self.mouse_x != 0 and self.mouse_y != 0 and not self.clicking_button:
                # Record data where the user clicked.
                if len(self.points_x) > 0 and self.p_num == 0:
                    self.click_x = (event.x + self.x_pos) * self.pxl_to_in
                    self.click_y = (event.y + self.y_pos) * self.pxl_to_in
                    # Make sure the user doesn't click two points with the same x coordinate
                    if self.click_x - self.points_x[0] != 0:
                        self.clicks += 1
                        self.points_x.append(self.click_x)
                        self.points_y.append(self.click_y)
                # Record data where the user clicked. (but don't check for dots with duplicate x-coordinates)
                else:
                    self.clicks += 1
                    self.click_x = (event.x + self.x_pos) * self.pxl_to_in
                    self.click_y = (event.y + self.y_pos) * self.pxl_to_in
                    self.points_x.append(self.click_x)
                    self.points_y.append(self.click_y)

            self.clicking_button = False # Not clicking the reset button.

            # The user has drawn the line.
            if self.dragging_line and self.clicks >= 2:
                self.clicked = True

            match self.p_num:
                # If p_num == 0, user is drawing the line.
                case 0:
                    if self.clicks >= 2:
                        if not self.textboxDisplayed:
                            self.line_drawn = True

                            # Get rid of intro text to make room for entry box widget
                            self.intro_text_widget.pack_forget()

                            # After 2 self.clicks, ask for scale
                            self.entry_widget.pack()
                            self.entry_text_widget.pack()
                            self.redo_line_button_widget.pack()
                            self.textboxDisplayed = True
                    elif self.clicks == 1:
                        # Starts dragging the line that connects the two points
                        if self.mouse_x != 0 and self.mouse_y != 0: # Only record click if mouse is within the self.panel (prevents inaccurate starting point for line)
                            self.start_dragging_line()
                # if p_num == 1, draw a dot.
                case 1:
                    # Figure out what color the dot should be.
                    color = ""
                    color_num = len(self.dot_positions) % 8
                    if color_num <= 1: color = "green"
                    elif color_num <= 3: color = "red"
                    elif color_num <= 5: color = "blue"
                    elif color_num <= 7: color = "violet"

                    # record stuff.
                    self.x1, self.y1 = (event.x - 3), (event.y - 3)
                    self.x2, self.y2 = (event.x + 3), (event.y + 3)
                    self.dots.append(self.panel.create_oval(self.x1, self.y1, self.x2, self.y2, fill=color))
                    self.orig_x = (event.x - self.img_width_center - self.x_pos)/self.scale_factor
                    self.orig_y = (event.y - self.img_height_center - self.y_pos)/self.scale_factor
                    self.dot_positions.append((self.orig_x, self.orig_y))

                    # Alternates between point 1 and point 2
                    if len(self.points_x) % 2:
                        # Point 1
                        self.p1x.append(self.points_x[-1])
                        self.p1y.append(self.points_y[-1])
                    else:
                        # Point 2
                        self.p2x.append(self.points_x[-1])
                        self.p2y.append(self.points_y[-1])

    # Processes all key inputs.
    def key(self, event):
        move_x, move_y = 0, 0
        self.p1ys = []
        self.p2ys = []
        match event.keysym:
            case 'Up': move_y = self.move_step
            case 'Down': move_y = -self.move_step
            case 'Left': move_x = self.move_step
            case 'Right': move_x = -self.move_step
            case 's': # Save the track.
                if len(self.points_x) >= 4 and len(self.p2y) == len(self.p1y):
                    print("Saving track points...")
                    # If the user is editing the track, there is no need to flip the coordinates as they were already flipped when creating the track the first time
                    if not self.editing:
                        self.p1ys = []
                        for i in self.p1y:
                            self.p1ys.append(-i)
                        self.p2ys = []
                        for i in self.p2y:
                            self.p2ys.append(-i)
                    else:
                        self.p1ys = self.p1y
                        self.p2ys = self.p2y
                    data = {'p1x' : self.p1x,
                            'p1y' : self.p1ys,
                            'p2x' : self.p2x,
                            'p2y' : self.p2ys,
                            'points_x' : self.points_x,
                            'points_y' : self.points_y,
                            'dot_positions' : self.dot_positions,
                            'dots' : self.dots,
                            'pxl_to_in' : self.pxl_to_in,
                            'p_num' : self.p_num,
                            'clicks' : self.clicks,
                            'scale_factor' : self.scale_factor,
                            'line_drawn' : self.line_drawn,
                            'can_drag_image' : self.can_drag_image,
                            'textboxDisplayed' : self.textboxDisplayed,
                            'image_path_saved' : self.image_path_saved}
                    with open(file_manager.get_file_from_user(file_types=[("Pickle files", "*.pkl")], default_exension="*.pkl"), 'wb') as f:
                        new_track_data = LapData(data)
                        pickle.dump(obj=new_track_data, file=f)
                    print('[Track points saved]')
                    print(f"points_x: {self.points_x}")
                    print(f"points_y: {self.points_y}")

                    self.close_window()
            case 'z': # Undo the dot the user last placed.
                print(f'undid {(self.points_x[-1], self.points_y[-1])}')
                self.panel.delete(self.dots[-1])
                pop_lists = []
                if len(self.p1y) > len(self.p2y): pop_lists = [self.p1x, self.p1y, self.points_x, self.points_y, self.dots, self.dot_positions]
                else: pop_lists = [self.p2x, self.p2y, self.points_x, self.points_y, self.dots, self.dot_positions]
                for i in pop_lists: i.pop(-1)
            case 'd': # print for debugging.
                print(f"p1x: {self.p1x}")
                print(f"p2x: {self.p2x}")
                print(f"p1y: {self.p1y}")
                print(f"p2y: {self.p2y}")

        # Move all dots when the user uses arrow keys to move window.
        self.panel.move(self.image_item, move_x, move_y)
        self.x_pos -= move_x
        self.y_pos -= move_y
        # Move the placed self.dots as well as the image
        for i in self.dots:
            self.panel.move(i, move_x, move_y)

    def return_key(self, event):
        if self.textboxDisplayed:
            # Calculate pixels to inches conversion factor and reset variables
            self.pxl_to_in = ((int(self.entry_widget.get()) * 12) / abs(self.points_x[1] - self.points_x[0]))/2
            print("Pixels to inches conversion factor:", self.pxl_to_in)
            self.points_x = []
            self.points_y = []
            self.clicks = 0
            self.p_num = 1
            self.entry_widget.destroy()
            self.entry_text_widget.destroy()
            self.redo_line_button_widget.destroy()
            self.panel.delete("Line")
            self.textboxDisplayed = False
            self.plot_text_widget.pack()
            self.can_drag_image = True

            # Zoom image in
            self.scale_factor = 1
            self.resize_img = ImageTk.PhotoImage(self.immage.resize((int(self.img_width*self.scale_factor), int(self.img_height*self.scale_factor))))
            self.panel.itemconfig(self.image_item, image=self.resize_img)

            self.img_width_center = (self.img_width * self.scale_factor)/2
            self.img_height_center = (self.img_height * self.scale_factor)/2

    # Collect data about where the user starts the line.
    def start_dragging_line(self):
        if not self.line_drawn: # Prevents multiple lines from being drawn
            self.dragging_line = True
            self.line_x1, self.line_y1 = self.mouse_x, self.mouse_y
            print(f"line start: {self.line_x1}, {self.line_y1}")
            self.match_line_with_mouse()
            self.update_line()

    # Update teh line visually as the user is dragging it.
    def update_line(self):
        if self.dragging_line and not self.clicked:
            self.panel.pack(expand = True, fill=tkinter.BOTH)
            self.panel.delete("Line")
            self.panel.create_line(self.line_x1, self.line_y1, self.line_x2, self.line_y1, fill="black", width=4, tags="Line", smooth=True, dash=(10, 5))

    # Update ending coords for line
    def match_line_with_mouse(self):
        self.line_x2, self.line_y2 = self.mouse_x, self.mouse_y

    # Get mouse position and update line.
    def get_mouse_pos(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y
        if(self.dragging_line and not self.clicked):
            self.match_line_with_mouse()
            self.update_line()
        elif(self.dragging_line and self.line_drawn):
            self.dragging_line = False
            print(f"line end: {self.line_x2}, {self.line_y1}")
        if self.holding_down_mouse and self.can_drag_image:
            self.update_image_drag(event)

    # Update both the position of the image and position of dots as the user drags with their mouse.
    def update_image_drag(self, event):
        if not self.gathered_held_down_pos:
            self.last_held_down_pos_x, self.last_held_down_pos_y = event.x, event.y
            self.gathered_held_down_pos = True

        move_x = event.x - self.last_held_down_pos_x
        move_y = event.y - self.last_held_down_pos_y
        self.panel.move(self.image_item, move_x, move_y)
        self.x_pos -= move_x
        self.y_pos -= move_y

        # Move the placed self.dots as well as the image
        for i in self.dots:
            self.panel.move(i, move_x, move_y)

        self.last_held_down_pos_x, self.last_held_down_pos_y = event.x, event.y

    # Change label on top to new label
    def configure_label(self):
        self.intro_text_widget.forget()
        self.plot_text_widget.pack()

    # When loading in a track to edit it, draw all dots onto the screen.
    def plot_saved_points(self):
        for index, position in enumerate(self.dot_positions):
            color = ""
            color_num = index % 8
            if color_num <= 1: color = "green"
            elif color_num <= 3: color = "red"
            elif color_num <= 5: color = "blue"
            elif color_num <= 7: color = "violet"

            new_x = (self.img_width_center + self.x_pos + position[0]) * self.scale_factor
            new_y = (self.img_height_center + self.y_pos + position[1]) * self.scale_factor
            x1, y1 = (new_x - 3), (new_y - 3)
            x2, y2 = (new_x + 3), (new_y + 3)
            self.dots.append(self.panel.create_oval(x1, y1, x2, y2, fill=color))

    # Function not used in UI. This saves a track as a points file by manually typing in points here.
    def save_custom_ungenerated_track(self):
        self.p1x = [
            0, 0, 418.307087, 718.50394, 418.307087, 0, 418.307087, 718.50394, 418.307087, 0,
            -300.1970125, -718.50394, -300.1970125, 0, -300.1970125, -718.50394, -300.1970125, 0, 0
        ]
        self.p1y = [
            0, 418.307087, 836.614174, 418.307087, 118.11, 418.307087, 836.614174, 418.307087, 118.11, 418.307087,
            836.614174, 418.307087, 118.11, 418.307087, 836.614174, 418.307087, 118.11, 418.307087, 836.614625
        ]
        self.p2x = [
            118.11, 118.11, 418.307087, 836.614174, 418.307087, 118.11, 418.307087, 836.614174, 418.307087, 118.11,
            -300.1970125, -600.394025, -300.1970125, 118.11, -300.1970125, -600.394025, -300.1970125, 118.11, 118.1103
        ]
        self.p2y = [
            0, 418.307087, 718.504325, 418.307087, 0, 418.307087, 718.504325, 418.307087, 0, 418.307087,
            718.504325, 418.307087, 0, 418.307087, 718.504325, 418.307087, 0, 418.307087, 836.614625
        ]
        self.points_x = [0, 118.11, 0, 118.11, 418.307087, 418.307087, 718.50394, 836.614174, 418.307087, 418.307087,
                         0, 118.11, 418.307087, -300.1970125, 718.50394, -600.394025, 418.307087, -300.1970125, 0, 118.11,
                         -300.1970125, 418.307087, -718.50394, 836.614174, -300.1970125, 418.307087, 0, 118.11]
        self.points_y = [0, 0, 418.307087, 418.307087, 836.614174, 718.504325, 418.307087, 418.307087, 118.11, 0,
                         418.307087, 418.307087, 836.614174, 0, 418.307087, 718.504325, 836.614174, 418.307087, 118.11, 418.307087,
                         418.307087, 718.504325, 418.307087, 836.614174, 118.11, 418.307087, 418.307087, 836.614625]
        self.dot_positions = [
            (0, 0), (118.11, 0), (0, 418.307087), (118.11, 418.307087),
            (418.307087, 836.614174), (418.307087, 718.504325), (718.50394, 418.307087), (836.614174, 418.307087),
            (418.307087, 118.11), (418.307087, 0), (0, 418.307087), (118.11, 418.307087),
            (418.307087, 836.614174), (-300.1970125, 0), (718.50394, 418.307087), (-600.394025, 718.504325),
            (418.307087, 836.614174), (-300.1970125, 418.307087), (0, 118.11), (118.11, 418.307087),
            (-300.1970125, 418.307087), (418.307087, 718.504325), (-718.50394, 418.307087), (836.614174, 836.614174),
            (-300.1970125, 118.11), (418.307087, 418.307087), (0, 418.307087), (118.11, 836.614625)
        ]
        data2 = {
            'p1x' : self.p1x,
            'p1y' : self.p1y,
            'p2x' : self.p2x,
            'p2y' : self.p2y,
            'points_x' : self.points_x,
            'points_y' : self.points_y,
            'dot_positions' : self.dot_positions,
            'dots' : [],
            'pxl_to_in' : 1,
            'p_num' : 1,
            'clicks' : 4,
            'scale_factor' : 1,
            'line_drawn' : True,
            'can_drag_image' : True,
            'textboxDisplayed' : False,
            'image_path_saved' : ""
        }
        with open("/Data/Tracks/skidpad_trk.pkl", 'wb') as f:
            pickle.dump(obj=data2, file=f)

    # Bind keys to functions.
    def bind_go_crazy_keys(self):
        self.go_crazy_root.bind("<ButtonPress-1>", self.record_click)
        self.go_crazy_root.bind("<ButtonRelease-1>", self.record_release)
        self.go_crazy_root.bind("<Return>", self.return_key)
        self.go_crazy_root.bind("<Motion>", self.get_mouse_pos)
        self.go_crazy_root.bind("<Key>", self.key)

    # Uncompleted function to zoom in and out with mouse wheel. Issues w/ scaling the self.dots along the resized image.
    # def mouse_wheel(event):
    #     global self.scale_factor, scroll_amount, self.img_width, self.img_height, self.resize_img, self.x_pos, self.y_pos, self.can_drag_image, self.panel, self.dot_positions, self.img_width_center, self.img_height_center
    #     if self.can_drag_image:
    #         old_image_width = int(self.img_width * self.scale_factor)
    #         old_image_height = int(self.img_height * self.scale_factor)
    #         if event.delta > 0 and self.scale_factor < 2:
    #             self.scale_factor += scroll_amount
    #
    #             if self.points_x and self.points_y:
    #                 for index, dot in enumerate(self.dots):
    #                     self.orig_x, self.orig_y = self.dot_positions[index]
    #                     # Calculate new scaled position
    #                     new_x = self.img_width_center + self.x_pos + self.orig_x * self.scale_factor
    #                     new_y = self.img_height_center + self.y_pos + self.orig_y * self.scale_factor
    #                     # Update the oval's position (assuming 6x6 ovals centered at (new_x, new_y))
    #                     self.panel.coords(dot, new_x - 3, new_y - 3, new_x + 3, new_y + 3)
    #                     print(f"Dot index: {index}, New Position: ({new_x}, {new_y}), Original Position: ({self.orig_x}, {self.orig_y})")
    #
    #         elif event.delta < 0 and self.scale_factor > scroll_amount + 0.5:
    #             self.scale_factor -= scroll_amount
    #
    #             if self.points_x and self.points_y:
    #                 for index, dot in enumerate(self.dots):
    #                     self.orig_x, self.orig_y = self.dot_positions[index]
    #                     # Calculate new scaled position
    #                     new_x = self.img_width_center + self.x_pos + self.orig_x * self.scale_factor
    #                     new_y = self.img_height_center + self.y_pos + self.orig_y * self.scale_factor
    #                     # Update the oval's position (assuming 6x6 ovals centered at (new_x, new_y))
    #                     self.panel.coords(dot, new_x - 3, new_y - 3, new_x + 3, new_y + 3)
    #
    #         self.resize_img = ImageTk.PhotoImage(self.immage.resize((round(self.img_width * self.scale_factor), round(self.img_height * self.scale_factor))))
    #         self.panel.itemconfig(self.image_item, image=self.resize_img)
    #
    #         self.img_width_center = round((self.img_width * self.scale_factor))/2
    #         self.img_height_center = round((self.img_height * self.scale_factor))/2
    #
    #         self.panel.pack()