from slides.ppt_loader import load_presentation
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

ppt_path = os.path.join(BASE_DIR, "sample_presentations", "demo1.pptx")

print("Trying to load:", ppt_path)

if not os.path.exists(ppt_path):
    print("FILE NOT FOUND. Check if demo1.pptx is in the sample_presentations folder.")
else:
    ppt = load_presentation(ppt_path)
    if ppt:
        print("Presentation loaded successfully")
        print("Number of slides:", len(ppt.slides))
    else:
        print("Failed to load presentation")