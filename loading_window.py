import tkinter
import tkinter.ttk as ttk

class LoadingWindow:
    def __init__(self):
        self.root = tkinter.Toplevel()
        self.root.title("Loading...")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry("300x50")

        self.loading_label = tkinter.Label(self.root, text="10 seconds remaining")
        self.loading_label.pack()

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

    def update_loading(self, progress, seconds_left):
        self.progress_bar.config(value=progress)
        self.loading_label.config(text=f"{seconds_left} seconds remaining")
        self.root.update_idletasks()
        if progress >= 100:
            self.close_window()
            self.progress_bar["value"] = 0

    def open_window(self):
        self.root.deiconify() # Show the window

    def close_window(self):
        self.root.withdraw()