import tkinter as tk
from PIL import ImageTk, Image
import pickle

# Initialize arrays that store 'x' and 'y' coordinates of clicked points
points_x = []
points_y = []

p1x = []
p2x = []
p1y = []
p2y = []

dot_positions = []

p_width = 1400
p_height = 600
p_num = 0
clicks = 0
scale_factor = 1/2
y_pos = 0
x_pos = 0

mouse_x, mouse_y = 0, 0

time_pressed = 0.0
holding_down_mouse = False
last_held_down_pox_x, last_held_down_pox_y = 0, 0
gathered_held_down_pos = False

line_x1, line_y1, line_x2, line_y2 = 0, 0, 0, 0
dragging_line = False
clicked = False
line_drawn = False

clicking_button = False

scroll_amount = 0.1
can_drag_image = False

move_step = 10

# Initialize window
root = tk.Tk()
immage = Image.open("Images/autocross.png")
img = ImageTk.PhotoImage(immage)
panel = tk.Canvas(width=p_width, height=p_height)
image_item = panel.create_image(p_width/2, p_height/2, image=img)
panel.pack(side = "bottom", fill = "both", expand = "yes")
intro_text_widget = tk.Label(root, width=60, text="Click two points that are a known distance apart to configure measurements.")
intro_text_widget.pack()
entry_widget = tk.Entry(root, width=30)
entry_text_widget = tk.Label(root, width=60, text="Enter the distance (in feet) between the two points you clicked, then press Enter")
plot_text_widget = tk.Label(root, width=60, text="Click points to plot the track. Press 's' to save and 'z' to undo last point.")
dots = []
pxl_to_in = 1

textboxDisplayed = False

# Save image dimensions
img_width =  immage.width
img_height = immage.height

img_width_center = immage.width/2
img_height_center = immage.height/2

print(f"Image dimensions: {img_width} x {img_height}")

# Zoom image in
resize_img = ImageTk.PhotoImage(immage.resize((int(img_width*scale_factor), int(img_height*scale_factor))))
panel.itemconfig(image_item, image=resize_img)
# root.mainloop()

def reset_line():
    global y_pos, x_pos, points_x, points_y, pxl_to_in, clicks, p_num, entry_widget, entry_text_widget, textboxDisplayed, line_drawn, can_drag_image, clicked, clicking_button

    print("Redoing line...")

    clicks = 0
    entry_widget.pack_forget()
    entry_text_widget.pack_forget()
    plot_text_widget.pack_forget()
    redo_line_button_widget.pack_forget()
    panel.delete("Line")
    intro_text_widget.pack()
    textboxDisplayed = False
    can_drag_image = False
    line_drawn = False
    clicked = False
    points_x = []
    points_y = []

    clicking_button = True

redo_line_button_widget = tk.Button(root, text="Redo Line", command=reset_line)

def record_click(event):
    global clicks, click_x, click_y, mouse_x, mouse_y, points_x, points_y, p_num, root, panel, immage, img, pxl_to_in, textboxDisplayed, dragging_line, clicked, entry_text_widget, line_drawn, time_pressed, holding_down_mouse

    time_pressed = event.time

    holding_down_mouse = True

def record_release(event):
    global clicks, click_x, click_y, mouse_x, mouse_y, points_x, points_y, p_num, root, panel, immage, img, pxl_to_in, textboxDisplayed, dragging_line, clicked, entry_text_widget, line_drawn, time_pressed, holding_down_mouse, gathered_held_down_pos, redo_line_button_widget, clicking_button

    holding_down_mouse = False
    gathered_held_down_pos = False

    if event.time - time_pressed < 200: # Only register as a click if mouse was held down for less than 200ms
        # Only record click if mouse is within the panel (prevents inaccurate starting point for line) and the user is not also clicking the redo line button
        if mouse_x != 0 and mouse_y != 0 and not clicking_button:
            if len(points_x) > 0 and p_num == 0:
                click_x = (event.x + x_pos) * pxl_to_in
                click_y = (event.y + y_pos) * pxl_to_in
                # Make sure the user doesn't click two points with the same x coordinate
                if click_x - points_x[0] != 0:
                    clicks += 1
                    points_x.append(click_x)
                    points_y.append(click_y)
            else:
                clicks += 1
                click_x = (event.x + x_pos) * pxl_to_in
                click_y = (event.y + y_pos) * pxl_to_in
                points_x.append(click_x)
                points_y.append(click_y)

        clicking_button = False

        if dragging_line and clicks >= 2:
            clicked = True

        match p_num:
            case 0:
                if clicks >= 2:
                    if not textboxDisplayed:
                        line_drawn = True

                        # Get rid of intro text to make room for entry box widget
                        intro_text_widget.pack_forget()

                        # After 2 clicks, ask for scale
                        entry_widget.pack()
                        entry_text_widget.pack()
                        redo_line_button_widget.pack()
                        textboxDisplayed = True
                elif clicks == 1:
                    # Starts dragging the line that connects the two points
                    if mouse_x != 0 and mouse_y != 0: # Only record click if mouse is within the panel (prevents inaccurate starting point for line)
                        start_dragging_line()

            case 1:
                print(f"{click_x}\t{click_y}")
                match len(p2x) % 4:
                    case 0: col = "green"
                    case 1: col = "red"
                    case 2: col = "blue"
                    case 3: col = "violet"

                x1, y1 = (event.x - 3), (event.y - 3)
                x2, y2 = (event.x + 3), (event.y + 3)
                dots.append(panel.create_oval(x1, y1, x2, y2, fill=col))
                orig_x = (event.x - img_width_center - x_pos)/scale_factor
                orig_y = (event.y - img_height_center - y_pos)/scale_factor
                dot_positions.append((orig_x, orig_y))

                # Alternates between point 1 and point 2
                if len(points_x) % 2:
                    # Point 1
                    p1x.append(points_x[-1])
                    p1y.append(points_y[-1])
                else:
                    # Point 2
                    p2x.append(points_x[-1])
                    p2y.append(points_y[-1])

        def key(event):
            global y_pos, x_pos, points_x, points_y, pxl_to_in, clicks, p_num, entry_widget, textboxDisplayed
            move_x, move_y = 0, 0

            match event.keysym:
                case 'Up': move_y = move_step
                case 'Down': move_y = -move_step
                case 'Left': move_x = move_step
                case 'Right': move_x = -move_step
                case 's':
                    p1ys = []
                    for i in p1y:
                        p1ys.append(-i)
                    p2ys = []
                    for i in p2y:
                        p2ys.append(-i)
                    data = {'p1x' : p1x,
                            'p1y' : p1ys,
                            'p2x' : p2x,
                            'p2y' : p2ys}
                    with open('trck.pkl', 'wb') as f:
                        pickle.dump(data, f)
                    print('[Track points saved]')
                    print(f"points_x: {points_x}")
                    print(f"points_y: {points_y}")
                case 'z':
                    print(f'undid {(points_x[-1], points_y[-1])}')
                    panel.delete(dots[-1])
                    pop_lists = []
                    if len(p1y) > len(p2y): pop_lists = [p1x, p1y, points_x, points_y, dots]
                    else: pop_lists = [p2x, p2y, points_x, points_y, dots]
                    for i in pop_lists: i.pop(-1)
                case 'd':
                    print(f"p1x: {p1x}")
                    print(f"p1y: {p1y}")
                    print(f"p2x: {p2x}")
                    print(f"p2y: {p2y}")

            panel.move(image_item, move_x, move_y)
            x_pos -= move_x
            y_pos -= move_y

            for i in dots:
                panel.move(i, move_x, move_y)

        panel.bind_all("<KeyPress>", key)

def return_key(event):
    global y_pos, x_pos, points_x, points_y, pxl_to_in, clicks, p_num, entry_widget, entry_text_widget, textboxDisplayed, line_drawn, can_drag_image, scale_factor, resize_img, img_width_center, img_height_center
    if textboxDisplayed:
        # Calculate pixels to inches conversion factor and reset variables
        pxl_to_in = ((int(entry_widget.get()) * 12) / abs(points_x[1] - points_x[0]))/2
        print("Pixels to inches conversion factor:", pxl_to_in)
        points_x = []
        points_y = []
        clicks = 0
        p_num = 1
        entry_widget.destroy()
        entry_text_widget.destroy()
        redo_line_button_widget.destroy()
        panel.delete("Line")
        textboxDisplayed = False
        plot_text_widget.pack()
        can_drag_image = True

        # Zoom image in
        scale_factor = 1
        resize_img = ImageTk.PhotoImage(immage.resize((int(img_width*scale_factor), int(img_height*scale_factor))))
        panel.itemconfig(image_item, image=resize_img)

        img_width_center = (img_width * scale_factor)/2
        img_height_center = (img_height * scale_factor)/2

def start_dragging_line():
    global dragging_line, line_x1, line_y1, mouse_x, mouse_y
    if not line_drawn: # Prevents multiple lines from being drawn
        dragging_line = True
        line_x1, line_y1 = mouse_x, mouse_y
        print(f"line start: {line_x1}, {line_y1}")
        match_line_with_mouse()
        update_line()

def update_line():
    global root
    if dragging_line:
        if not clicked:
            panel.pack(expand = True, fill=tk.BOTH)
            panel.delete("Line")
            panel.create_line(line_x1, line_y1, line_x2, line_y1, fill="black", width=4, tags="Line", smooth=True, dash=(10, 5))

def match_line_with_mouse():
    global line_x2, line_y2
    line_x2, line_y2 = mouse_x, mouse_y

def get_mouse_pos(event):
    global mouse_x, mouse_y, dragging_line, clicked
    mouse_x, mouse_y = event.x, event.y
    if(dragging_line and not clicked):
        match_line_with_mouse()
        update_line()
    elif(dragging_line and line_drawn):
        dragging_line = False
        print(f"line end: {line_x2}, {line_y1}")
    if holding_down_mouse and can_drag_image:
        update_image_drag(event)

def update_image_drag(event):
    global last_held_down_pos_x, last_held_down_pos_y, move_x, move_y, gathered_held_down_pos, x_pos, y_pos

    if not gathered_held_down_pos:
        last_held_down_pos_x, last_held_down_pos_y = event.x, event.y
        gathered_held_down_pos = True

    move_x = event.x - last_held_down_pos_x
    move_y = event.y - last_held_down_pos_y
    panel.move(image_item, move_x, move_y)
    x_pos -= move_x
    y_pos -= move_y

    # Move the placed dots as well as the image
    for i in dots:
        panel.move(i, move_x, move_y)

    last_held_down_pos_x, last_held_down_pos_y = event.x, event.y


# Uncompleted function to zoom in and out with mouse wheel. Issues w/ scaling the dots along the resized image.
# def mouse_wheel(event):
#     global scale_factor, scroll_amount, img_width, img_height, resize_img, x_pos, y_pos, can_drag_image, panel, dot_positions, img_width_center, img_height_center
#     if can_drag_image:
#         old_image_width = int(img_width * scale_factor)
#         old_image_height = int(img_height * scale_factor)
#         if event.delta > 0 and scale_factor < 2:
#             scale_factor += scroll_amount
#
#             if points_x and points_y:
#                 for index, dot in enumerate(dots):
#                     orig_x, orig_y = dot_positions[index]
#                     # Calculate new scaled position
#                     new_x = img_width_center + x_pos + orig_x * scale_factor
#                     new_y = img_height_center + y_pos + orig_y * scale_factor
#                     # Update the oval's position (assuming 6x6 ovals centered at (new_x, new_y))
#                     panel.coords(dot, new_x - 3, new_y - 3, new_x + 3, new_y + 3)
#                     print(f"Dot index: {index}, New Position: ({new_x}, {new_y}), Original Position: ({orig_x}, {orig_y})")
#
#         elif event.delta < 0 and scale_factor > scroll_amount + 0.5:
#             scale_factor -= scroll_amount
#
#             if points_x and points_y:
#                 for index, dot in enumerate(dots):
#                     orig_x, orig_y = dot_positions[index]
#                     # Calculate new scaled position
#                     new_x = img_width_center + x_pos + orig_x * scale_factor
#                     new_y = img_height_center + y_pos + orig_y * scale_factor
#                     # Update the oval's position (assuming 6x6 ovals centered at (new_x, new_y))
#                     panel.coords(dot, new_x - 3, new_y - 3, new_x + 3, new_y + 3)
#
#         resize_img = ImageTk.PhotoImage(immage.resize((round(img_width * scale_factor), round(img_height * scale_factor))))
#         panel.itemconfig(image_item, image=resize_img)
#
#         img_width_center = round((img_width * scale_factor))/2
#         img_height_center = round((img_height * scale_factor))/2
#
#         panel.pack()

root.bind("<ButtonPress-1>", record_click)
root.bind("<ButtonRelease-1>", record_release)
root.bind("<Return>", return_key)
root.bind("<Motion>", get_mouse_pos)
# root.bind("<MouseWheel>", mouse_wheel)

root.mainloop()

