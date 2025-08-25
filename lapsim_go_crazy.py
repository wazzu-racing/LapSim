import tkinter as tk
from PIL import ImageTk, Image
import pickle

def mouse_down(event):
    print("Mouse button pressed at", event.x, event.y)

points_x = []
points_y = []

p1x = []
p2x = []
p1y = []
p2y = []

p_width = 1400
p_height = 600
p_num = 0
clicks = 0
scale_factor = 4
y_pos = 0
x_pos = 0

move_step = 10
img_width = 0
img_height = 0

root = tk.Tk()
immage = Image.open("autocross.png")
#resize_img = image.resize((2000, 1000))
img = ImageTk.PhotoImage(immage)
panel = tk.Canvas(width=p_width, height=p_height)
image_item = panel.create_image(p_width/2, p_height/2, image=img)
panel.pack(side = "bottom", fill = "both", expand = "yes")
dots = []
pxl_to_in = 1



def record_click(event):
    global clicks, click_x, click_y, points_x, points_y, p_num, root, panel, immage, img, pxl_to_in
    clicks += 1

    click_x = (event.x + x_pos) * pxl_to_in
    click_y = (event.y + y_pos) * pxl_to_in
    points_x.append(click_x)
    points_y.append(click_y)
    print(f"{click_x}\t{click_y}")
    
    match p_num: 
        case 0:
            if clicks == 3:
                #img_width = points_x[1] - points_x[0]
                img_width = immage.width
                #img_height = points_y[1] - points_y[2]
                img_height = immage.height
                points_x = []
                points_y = []
                clicks = 0
                p_num = 1
                print(f"{img_width}\t{img_height}=========")
                #root.quit()
                
                resize_img = ImageTk.PhotoImage(immage.resize((img_width * scale_factor, img_height * scale_factor)))
                panel.itemconfig(image_item, image=resize_img)
                root.mainloop()
        case 1:
            if clicks == 2:
                pxl_to_in = int(input("ft: ")) * 12 / abs(points_x[1] - points_x[0])
                points_x = []
                points_y = []
                clicks = 0
                p_num = 2
        case 2:
            match len(p2x) % 4:
                case 0: col = "green"
                case 1: col = "red"
                case 2: col = "blue"
                case 3: col = "violet"

            x1, y1 = (event.x - 3), (event.y - 3)
            x2, y2 = (event.x + 3), (event.y + 3)
            dots.append(panel.create_oval(x1, y1, x2, y2, fill=col))
            if len(points_x) % 2:
                p1x.append(points_x[-1])
                p1y.append(points_y[-1])
            else:
                p2x.append(points_x[-1])
                p2y.append(points_y[-1])
    
    def key(event):
        global y_pos, x_pos
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
                with open('C:\\Users\\nbogd\\OneDrive\\Documents\\lapsimStuffCopy\\autocross_pts.pkl', 'wb') as f:
                    pickle.dump(data, f)
                print('[Track points saved]')
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


root.bind("<Button-1>", record_click)

root.mainloop()

