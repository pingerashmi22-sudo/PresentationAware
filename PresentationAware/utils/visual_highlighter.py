import tkinter as tk
import threading


def _show_highlight(x, y, size):
    root = tk.Tk()

    root.overrideredirect(True)
    root.attributes("-topmost", True)

    # Slight transparency (balanced)
    root.attributes("-alpha", 0.5)

    root.geometry(f"{size}x{size}+{x}+{y}")

    canvas = tk.Canvas(root, width=size, height=size, bg="white", highlightthickness=0)
    canvas.pack()

    # Thick red border
    canvas.create_rectangle(5, 5, size-5, size-5, outline="red", width=5)

    # Stay longer (better visibility)
    root.after(2000, root.destroy)

    root.mainloop()


def highlight_area(x=300, y=300, size=200):
    threading.Thread(
        target=_show_highlight,
        args=(x, y, size),
        daemon=True
    ).start()