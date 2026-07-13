import tkinter as tk
from pose_gui import PoseTkinterGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = PoseTkinterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
