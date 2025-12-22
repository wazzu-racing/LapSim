from main_menu_page import PageStack
import multiprocessing
multiprocessing.set_start_method('forkserver', force=True)
multiprocessing.freeze_support()

page_stack = PageStack()
page_stack.go_to_page("MainMenuPage")
page_stack.mainloop()