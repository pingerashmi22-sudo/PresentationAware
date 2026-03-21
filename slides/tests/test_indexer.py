from slides.ppt_loader import load_presentation
from slides.slide_indexer import build_slide_index
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ppt_path = os.path.join(BASE_DIR, "sample_presentations", "demo1.pptx")

ppt = load_presentation(ppt_path)

if ppt:
    index = build_slide_index(ppt)
    print("\n--- Final Index ---")
    print(index)
else:
    print("PPT not loaded.")
```

Run it:
```
python -m slides.tests.test_indexer