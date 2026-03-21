from pptx import Presentation
import tkinter as tk
from tkinter import filedialog
import os

def get_ppt_path():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select your PowerPoint file",
        filetypes=[("PowerPoint files", "*.pptx")]
    )
    if not file_path:
        print("No file selected.")
        return None
    return file_path

def load_presentation(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Error loading PPT: Package not found at '{file_path}'")
            return None
        ppt = Presentation(file_path)
        print(f"Loaded: {file_path}")
        print(f"Total slides: {len(ppt.slides)}")
        return ppt
    except Exception as e:
        print("Error loading PPT:", e)
        return None