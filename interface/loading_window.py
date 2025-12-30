import tkinter
import tkinter.ttk as ttk

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

        # Hide this window until ready to show
        self.root.withdraw()

        # Do not allow user to close window
        self.root.protocol("WM_DELETE_WINDOW", lambda: ())

    def reset(self):
        self.progress_bar["value"] = 0
        self.loading_label.config(text=f"0 seconds remaining")

    # Update the loading window to display a new argument progress (0-100) and the amount of seconds remaining.
    def update_loading(self, progress, seconds_left):
        self.progress_bar.config(value=progress)
        self.loading_label.config(text=f"{seconds_left} seconds remaining")
        self.root.update_idletasks()
        if progress >= 100:
            self.close_window()
            self.progress_bar["value"] = 0

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
