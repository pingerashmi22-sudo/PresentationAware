from slides.ppt_loader import load_presentation
from slides.content_extractor import extract_slide_text
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ppt_path = os.path.join(BASE_DIR, "sample_presentations", "demo1.pptx")

ppt = load_presentation(ppt_path)

if ppt:
    print("\n--- Extracting text from all slides ---\n")
    data = extract_slide_text(ppt)
    print("\n--- Final extracted data ---")
    print(data)
else:
    print("PPT not loaded, cannot extract.")
```

Run it in terminal:
```
python -m slides.tests.test_extract
```

You should see every slide's text printed out like:
```
Slide 1: ['Revenue Growth', 'Q3 2024']
Slide 2: ['15% increase', 'Customer retention']