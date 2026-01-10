import tkinter
import tkinter.ttk as ttk
import tqdm as tq

class LoadingWindow:
    def __init__(self):
        # Initialize the window.
        self.root = tkinter.Toplevel()
        self.root.title("Loading...")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry("300x50")
        self.center_window_on_screen()

        self.loading_label = tkinter.Label(self.root, text="10 seconds remaining")
        self.loading_label.pack()

        # Make progress bar.
        self.progress_bar = ttk.Progressbar(self.root, orient=tkinter.HORIZONTAL, length=200, maximum=100)
        self.progress_bar["value"] = 0
        self.progress_bar.pack()

        # initiate loading logic
        self.instance = tq.tqdm(total=100) # Create instance of tqdm (library used to estimate time remaining)
        self.curr_n = 0 # Current
        self.last_n = 0 # Used to track how many n's have been added since last time loading was checked

        # Hide this window until ready to show
        self.root.withdraw()

        # Do not allow user to close window
        self.root.protocol("WM_DELETE_WINDOW", lambda: ())

    def reset(self):
        self.progress_bar["value"] = 0
        self.loading_label.config(text=f"0 seconds remaining")
        self.instance.reset()

    # Update the loading window to display a new argument progress (0-100) and the amount of seconds remaining.
    def update_loading(self, curr_n, total_n):
        # Update progress bar and loading instance
        self.instance.update((curr_n - self.last_n) / total_n * 100)
        self.progress_bar.config(value=curr_n/total_n*100)

        # Calculate the rate of loading in iterations per second. 1 if rate is None.
        rate = 1
        if self.instance.format_dict['rate']:
            rate = self.instance.format_dict['rate']

        # Calculate the amount of seconds left and display.
        seconds_left = int((100 - (curr_n / total_n * 100)) / rate)
        self.loading_label.config(text=f"{seconds_left} seconds remaining")
        self.root.update_idletasks()
        if curr_n/total_n*100 >= 100:
            self.close_window()
            self.progress_bar["value"] = 0

        self.last_n = curr_n

    def center_window_on_screen(self):
        # 1. Update idle tasks to ensure accurate dimension calculation
        self.root.update_idletasks()

        # 2. Get window dimensions (excluding title bar/borders for calculation)
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        # 3. Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 4. Calculate the center position
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # 5. Set the window's position using the geometry method
        # The format is "widthxheight+x+y"
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def open_window(self):
        self.center_window_on_screen()
        self.root.deiconify()  # Show the window

    def close_window(self):
        self.root.withdraw()

loading_window = None
def run_car_model_loading_window(car, n, func, prev_lap_data, thread, controller, run_from):
    global loading_window

    if loading_window is None:
        loading_window = LoadingWindow()
    else:
        loading_window.reset()
    loading_window.root.title("Generating car model...")
    loading_window.open_window()

    loading_window.open_window()

    def update_loading_window():
        if thread is not None and thread.is_alive(): # If loading has not finished, update the loading window to display loading progress.
            loading_window.update_loading(curr_n=len(car.AX_AY_array), total_n=n)
            loading_window.root.after(1000, update_loading_window) # Call this same function again after 1 second.
        else:
            loading_window.update_loading(100,100)
            # Once loading has finished, update the UI.
            if run_from == "create_new_car_page":
                func(controller)
            elif run_from=="display_trk":
                func(prev_lap_data)
            else:
                func()

    update_loading_window() # Call function to start the loop.