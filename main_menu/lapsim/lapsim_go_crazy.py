import tkinter
from tkinter import filedialog

from PIL import ImageTk, Image
import pickle

from main_menu.manage_data.files import get_save_files_folder_abs_dir


class LapSimGoCrazy:

    def __init__(self, image_path=None, track_file=None):

        # Check if there is a track file to load stuff from. If there is, load the stuff from the file.
        if track_file is None:
            # Initialize arrays that store 'x' and 'y' coordinates of self.clicked points
            self.points_x = []
            self.points_y = []

            self.p1x = []
            self.p2x = []
            self.p1y = []
            self.p2y = []

            self.x1 = []

            self.dot_positions = []
            self.pxl_to_in = 1

            self.p_num = 0
            self.clicks = 0
            self.scale_factor = 1/2

            self.line_drawn = False
            self.can_drag_image = False
            self.textboxDisplayed = False

            self.image_path_saved = image_path
        else:
            with open(track_file, 'rb') as f:
                track = pickle.load(file=f)
            self.points_x = track['points_x']
            self.points_y = track['points_y']

            self.p1x = track['p1x']
            self.p2x = track['p2x']
            self.p1y = track['p1y']
            self.p2y = track['p2y']

            self.dot_positions = track['dot_positions']
            self.pxl_to_in = track['pxl_to_in']

            self.p_num = track['p_num']
            self.scale_factor = track['scale_factor']

            # If there is only 1 click saved, reset clicks to 0 so user can draw the line (1 click is when user clicked 1 point but didn't finish drawing the line)
            if track['clicks'] == 1:
                self.clicks = 0
            else:
                self.clicks = track['clicks']

            self.line_drawn = track['line_drawn']
            self.can_drag_image = track['can_drag_image']
            self.textboxDisplayed = track['textboxDisplayed']

            self.image_path_saved = track['image_path_saved']

        self.go_crazy_root = None

        self.p_width = 1400
        self.p_height = 600
        self.y_pos = 0
        self.x_pos = 0

        self.dots = []

        self.mouse_x, self.mouse_y = 0, 0

        self.time_pressed = 0.0
        self.holding_down_mouse = False
        self.last_held_down_pox_x, self.last_held_down_pox_y = 0, 0
        self.gathered_held_down_pos = False

        self.line_x1, self.line_y1, self.line_x2, self.line_y2 = 0, 0, 0, 0
        self.dragging_line = False
        self.clicked = False

        self.clicking_button = False

        scroll_amount = 0.1

        self.move_step = 10

        # Initialize window
        self.go_crazy_root = tkinter.Toplevel()
        self.go_crazy_root.title("Plot LapSim Track")

        # Only allow the user to hide the window, not close it
        self.go_crazy_root.protocol("WM_DELETE_WINDOW", self.go_crazy_root.withdraw)

        self.immage = Image.open(self.image_path_saved)
        self.img = ImageTk.PhotoImage(self.immage)
        self.panel = tkinter.Canvas(master=self.go_crazy_root, width=self.p_width, height=self.p_height)
        self.image_item = self.panel.create_image(self.p_width/2, self.p_height/2, image=self.img)
        self.panel.pack(side = "bottom", fill = "both", expand = "yes")
        self.intro_text_widget = tkinter.Label(self.go_crazy_root, width=60, text="Click two points that are a known distance apart to configure measurements.")
        self.intro_text_widget.pack()
        self.entry_widget = tkinter.Entry(self.go_crazy_root, width=30)
        self.entry_text_widget = tkinter.Label(self.go_crazy_root, width=60, text="Enter the distance (in feet) between the two points you self.clicked, then press Enter")
        self.plot_text_widget = tkinter.Label(self.go_crazy_root, width=60, text="Click points to plot the track. Press 's' to save and 'z' to undo last point.")

        # Save image dimensions
        self.img_width =  self.immage.width
        self.img_height = self.immage.height

        self.img_width_center = self.immage.width/2
        self.img_height_center = self.immage.height/2

        print(f"Image dimensions: {self.img_width} x {self.img_height}")

        # Plot saved points if there are any
        if track_file is not None:
            self.plot_saved_points()
            # Configure label based on current state
            self.configure_label()

        # Zoom image in
        self.resize_img = ImageTk.PhotoImage(self.immage.resize((int(self.img_width*self.scale_factor), int(self.img_height*self.scale_factor))))
        self.panel.itemconfig(self.image_item, image=self.resize_img)

        # Set redo line button widget to connect to reset_line function
        self.redo_line_button_widget = tkinter.Button(self.go_crazy_root, text="Redo Line", command=self.reset_line)

        bind_keys(self.go_crazy_root, self)

        self.initial_dir = ""
        self.set_initial_dir()

        self.go_crazy_root.mainloop()

    # Initializes the initial_dir variable, which points to the absolute directory of the saved_files folder.
    def set_initial_dir(self):
        self.initial_dir = get_save_files_folder_abs_dir()

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

    def record_click(self, event):
        print("Recording click...")
        self.time_pressed = event.time

        self.holding_down_mouse = True

    def record_release(self, event):
        self.holding_down_mouse = False
        self.gathered_held_down_pos = False

        if event.time - self.time_pressed < 200: # Only register as a click if mouse was held down for less than 200ms
            print("Recording release...")
            # Only record click if mouse is within the self.panel (prevents inaccurate starting point for line) and the user is not also clicking the redo line button
            if self.mouse_x != 0 and self.mouse_y != 0 and not self.clicking_button:
                if len(self.points_x) > 0 and self.p_num == 0:
                    self.click_x = (event.x + self.x_pos) * self.pxl_to_in
                    self.click_y = (event.y + self.y_pos) * self.pxl_to_in
                    # Make sure the user doesn't click two points with the same x coordinate
                    if self.click_x - self.points_x[0] != 0:
                        self.clicks += 1
                        self.points_x.append(self.click_x)
                        self.points_y.append(self.click_y)
                else:
                    self.clicks += 1
                    self.click_x = (event.x + self.x_pos) * self.pxl_to_in
                    self.click_y = (event.y + self.y_pos) * self.pxl_to_in
                    self.points_x.append(self.click_x)
                    self.points_y.append(self.click_y)

            self.clicking_button = False

            if self.dragging_line and self.clicks >= 2:
                self.clicked = True

            match self.p_num:
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
                case 1:
                    col = ""
                    print(f"{self.click_x}\t{self.click_y}")
                    match len(self.p2x) % 4:
                        case 0: col = "green"
                        case 1: col = "red"
                        case 2: col = "blue"
                        case 3: col = "violet"

                    self.x1, self.y1 = (event.x - 3), (event.y - 3)
                    self.x2, self.y2 = (event.x + 3), (event.y + 3)
                    self.dots.append(self.panel.create_oval(self.x1, self.y1, self.x2, self.y2, fill=col))
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

    def key(self, event):
        self.move_x, self.move_y = 0, 0

        match event.keysym:
            case 'Up': self.move_y = self.move_step
            case 'Down': self.move_y = -self.move_step
            case 'Left': self.move_x = self.move_step
            case 'Right': self.move_x = -self.move_step
            case 's':
                if len(self.points_x) >= 4:
                    print("Saving track points...")
                    self.p1ys = []
                    for i in self.p1y:
                        self.p1ys.append(-i)
                    self.p2ys = []
                    for i in self.p2y:
                        self.p2ys.append(-i)
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
                    with open(get_file_from_user(self), 'wb') as f:
                        pickle.dump(obj=data, file=f)
                    print('[Track points saved]')
                    print(f"points_x: {self.points_x}")
                    print(f"points_y: {self.points_y}")
            case 'z':
                print(f'undid {(self.points_x[-1], self.points_y[-1])}')
                self.panel.delete(self.dots[-1])
                pop_lists = []
                if len(self.p1y) > len(self.p2y): pop_lists = [self.p1x, self.p1y, self.points_x, self.points_y, self.dots]
                else: pop_lists = [self.p2x, self.p2y, self.points_x, self.points_y, self.dots]
                for i in pop_lists: i.pop(-1)
            case 'd':
                print(f"p1x: {self.p1x}")
                print(f"p1y: {self.p1y}")
                print(f"p2x: {self.p2x}")
                print(f"p2y: {self.p2y}")

        self.panel.move(self.image_item, self.move_x, self.move_y)
        self.x_pos -= self.move_x
        self.y_pos -= self.move_y

        for index, dot in enumerate(self.dots):
            self.panel.move(dot, self.move_x, self.move_y)
            self.dot_positions[index] -= (self.move_x, self.move_y)

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

    def start_dragging_line(self):
        if not self.line_drawn: # Prevents multiple lines from being drawn
            self.dragging_line = True
            self.line_x1, self.line_y1 = self.mouse_x, self.mouse_y
            print(f"line start: {self.line_x1}, {self.line_y1}")
            self.match_line_with_mouse()
            self.update_line()

    def update_line(self):
        if self.dragging_line:
            if not self.clicked:
                self.panel.pack(expand = True, fill=tkinter.BOTH)
                self.panel.delete("Line")
                self.panel.create_line(self.line_x1, self.line_y1, self.line_x2, self.line_y1, fill="black", width=4, tags="Line", smooth=True, dash=(10, 5))

    def match_line_with_mouse(self):
        self.line_x2, self.line_y2 = self.mouse_x, self.mouse_y

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

    def update_image_drag(self, event):
        self.last_held_down_pox_x, self.last_held_down_pox_y = 0, 0

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

    def configure_label(self):
        self.intro_text_widget.forget()
        self.plot_text_widget.pack()

    def plot_saved_points(self):
        for index, position in enumerate(reversed(self.dot_positions)):
            col = ""
            col_num = index % 8
            if col_num <= 1: col = "green"
            elif col_num <= 3: col = "red"
            elif col_num <= 5: col = "blue"
            elif col_num <= 7: col = "violet"

            new_x = (self.img_width_center + self.x_pos + position[0]) * self.scale_factor
            new_y = (self.img_height_center + self.y_pos + position[1]) * self.scale_factor
            x1, y1 = (new_x - 3), (new_y - 3)
            x2, y2 = (new_x + 3), (new_y + 3)
            self.dots.append(self.panel.create_oval(x1, y1, x2, y2, fill=col))

def get_file_from_user(self):
    # Asks the user to choose an image file to create the track with.
    file_path = filedialog.asksaveasfilename(title="Select a place to save the track", initialdir=self.initial_dir, filetypes=[("Pickle files", "*.pkl")])
    # if the file_path is not nothing, the image file is saved and the user can use the image to create the track.
    if file_path:
        return file_path
    else:
        print("No file selected")
        return None

def bind_keys(root, self):
    root.bind("<ButtonPress-1>", self.record_click)
    root.bind("<ButtonRelease-1>", self.record_release)
    root.bind("<Return>", self.return_key)
    root.bind("<Motion>", self.get_mouse_pos)
    root.bind("<Key>", self.key)

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
