from pptx import Presentation
import tkinter as tk
from tkinter import filedialog
import os

# IMPORT YOUR MODULES 
from slide_mapper.ppt_reader import load_ppt
from slides.content_extractor import extract_context


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

        
        print("\nBuilding slide knowledge base...")

        # Step 1: Extract structured slide data
        slides_data = load_ppt(file_path)

        # Step 2: Convert into context strings
        context_data = extract_context(slides_data)

        print("Context ready for AI")

        # You can return everything for later use
        return {
            "presentation": ppt,
            "slides_data": slides_data,
            "context_data": context_data
        }

    except Exception as e:
        print("Error loading PPT:", e)
        return None