import tkinter as tk
from PIL import ImageTk, Image
import numpy as np
import csv
import pickle

file_location = "/Users/jacobmckee/Downloads/KTM_restrictor.png"
# Initialize arrays that store 'x' and 'y' coordinates of clicked points
points_x = []
points_y = []

px = []
py = []
p_type = []

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

data_type = 'torque'

# Initialize window
root = tk.Tk()
immage = Image.open(file_location)
img = ImageTk.PhotoImage(immage)
panel = tk.Canvas(width=p_width, height=p_height)
image_item = panel.create_image(p_width/2, p_height/2, image=img)
panel.pack(side = "bottom", fill = "both", expand = "yes")
intro_text_widget = tk.Label(root, width=60, text="Click top left corner of the graph, then the bottom right corner.")
intro_text_widget.pack()
entry_widget = tk.Entry(root, width=30)
entry_text_widget = tk.Label(root, width=60, text="Enter the min bound, in rpm, of the x axis, then press Enter")
plot_text_widget = tk.Label(root, width=60, text="Click points to plot the track. Press 's' to save and 'z' to undo last point.")
dots = []
min_rpm = 0
pxl_to_rpm = 1
pxl_to_hp = 1
rpm_offset = 0
pwr_offset = 0
keys_pressed = 0

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
    global y_pos, x_pos, points_x, points_y, pxl_to_rpm, clicks, p_num, entry_widget, entry_text_widget, textboxDisplayed, line_drawn, can_drag_image, clicked, clicking_button

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
    global clicks, click_x, click_y, mouse_x, mouse_y, points_x, points_y, p_num, root, panel, immage, img, pxl_to_rpm, textboxDisplayed, dragging_line, clicked, entry_text_widget, line_drawn, time_pressed, holding_down_mouse

    time_pressed = event.time
    holding_down_mouse = True

def record_release(event):
    global clicks, click_x, click_y, mouse_x, mouse_y, points_x, points_y, p_num, root, panel, immage, img, pxl_to_rpm, textboxDisplayed, dragging_line, clicked, entry_text_widget, line_drawn, time_pressed, holding_down_mouse, gathered_held_down_pos, redo_line_button_widget, clicking_button, rpm_offset, pwr_offset, keys_pressed, min_rpm, entry_text_widget, plot_text_widget

    holding_down_mouse = False
    gathered_held_down_pos = False

    if event.time - time_pressed < 200: # Only register as a click if mouse was held down for less than 200ms
        # Only record click if mouse is within the panel (prevents inaccurate starting point for line) and the user is not also clicking the redo line button
        if mouse_x != 0 and mouse_y != 0 and not clicking_button:
            if len(points_x) > 0 and ((p_num == 0) or (p_num == 1 and keys_pressed >= 2)):
                click_x = (event.x + x_pos - rpm_offset) * pxl_to_rpm
                click_y = (event.y + y_pos - pwr_offset) * pxl_to_hp
                # Make sure the user doesn't click two points with the same x coordinate
                if click_x - points_x[0] != 0:
                    clicks += 1
                    points_x.append(click_x)
                    points_y.append(click_y)
            else:
                clicks += 1
                click_x = (event.x + x_pos) * pxl_to_rpm - rpm_offset + min_rpm
                click_y = (event.y + y_pos) * pxl_to_hp - pwr_offset
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
                rpm_offset = points_x[-1]
                pwr_offset = points_y[-1]
                points_x = []
                points_y = []
                clicks = 0
                p_num = 2
                entry_text_widget.pack_forget()
                plot_text_widget.pack()

            case 2:
                print(f'{click_x}\t{click_y}')
                col = 'blue'

                x1, y1 = (event.x - 3), (event.y - 3)
                x2, y2 = (event.x + 3), (event.y + 3)
                dots.append(panel.create_oval(x1, y1, x2, y2, fill=col))
                orig_x = (event.x - img_width_center - x_pos)/scale_factor
                orig_y = (event.y - img_height_center - y_pos)/scale_factor
                dot_positions.append((orig_x, orig_y))

                px.append(points_x[-1])
                py.append(points_y[-1])
                p_type.append(data_type)

        def key(event):
            global y_pos, x_pos, points_x, points_y, pxl_to_rpm, pxl_to_hp, clicks, p_num, entry_widget, textboxDisplayed, rpm_offset, pwr_offset
            move_x, move_y = 0, 0

            match event.keysym:
                case 'Up': move_y = move_step
                case 'Down': move_y = -move_step
                case 'Left': move_x = move_step
                case 'Right': move_x = -move_step
                case 's':
                    rpms = points_x
                    pwrs = np.array(points_y) + 10.0
                    torques = np.array(pwrs) * 9549 / np.array(rpms)

                    f = open(file_location[0:-4] + '.csv', "w", newline="")
                    writer = csv.writer(f)

                    # Write header
                    writer.writerow(["RPM", "Power", "Torque"])

                    # Write rows
                    writer.writerow(['RPM', 'Power (kW)', 'Torque (Nm)'])
                    for rpm, pwr, tq in zip(rpms, pwrs, torques):
                        writer.writerow([rpm, pwr, tq])
                    f.close()
                    print("Data saved as csv")
                case 'z':
                    print(f'undid {(points_x[-1], points_y[-1])}')
                    panel.delete(dots[-1])
                    pop_lists = [points_x, points_y]
                    for i in pop_lists: i.pop(-1)

            panel.move(image_item, move_x, move_y)
            x_pos -= move_x
            y_pos -= move_y

            for i in dots:
                panel.move(i, move_x, move_y)

        panel.bind_all("<KeyPress>", key)

def return_key(event):
    global y_pos, x_pos, points_x, points_y, pxl_to_rpm, pxl_to_hp, keys_pressed, clicks, p_num, entry_widget, entry_text_widget, textboxDisplayed, line_drawn, can_drag_image, scale_factor, resize_img, img_width_center, img_height_center, rpm_offset, pwr_offset, min_rpm, entry_text_widget
    if textboxDisplayed:
        # Calculate pixels to inches conversion factor and reset variables
        if keys_pressed == 0:
            min_rpm = int(entry_widget.get())
            keys_pressed += 1
            entry_text_widget.pack_forget()
            entry_text_widget = tk.Label(root, width=60, text="Enter the max bound, in rpm, of the x axis, then press Enter")
            entry_text_widget.pack()
        elif keys_pressed == 1:
            print(points_x)
            pxl_to_rpm = ((int(entry_widget.get()) - min_rpm) / abs(points_x[1] - points_x[0])) / 2
            print("Pixels to rpm conversion factor:", pxl_to_rpm)
            keys_pressed += 1
            entry_text_widget.pack_forget()
            entry_text_widget = tk.Label(root, width=60, text="Enter the max bound, in horsepower, of the y axis, then press Enter")
            entry_text_widget.pack()
        elif keys_pressed == 2:
            pxl_to_hp = -(int(entry_widget.get()) / abs(points_y[1] - points_y[0]))/2
            print("Pixels to horsepower conversion factor:", pxl_to_hp)
            entry_widget.destroy()
            entry_text_widget.destroy()
            redo_line_button_widget.destroy()
            panel.delete("Line")
            textboxDisplayed = False
            can_drag_image = True
            keys_pressed += 1
            p_num = 1
            entry_text_widget.pack_forget()
            entry_text_widget = tk.Label(root, width=60, text="Click on the bottom left corner of the graph to set the origin")
            entry_text_widget.pack()


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

