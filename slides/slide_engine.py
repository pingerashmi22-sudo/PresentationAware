from slides.slide_indexer import build_slide_index
from slides.matcher import match_text
from slides.element_locator import get_element_coordinates

_engine_ready = False

def initialize():
    global _engine_ready
    print("=== Slide Engine Starting ===")

    filepath = get_ppt_path()
    if not filepath:
        print("No file selected.")
        return False

    prs = load_presentation(filepath)
    if not prs:
        return False

    build_slide_index(prs)
    _engine_ready = True
    print("=== Slide Engine Ready ===")
    return True

def get_slide_match(spoken_text):
    """
    Called by Member 3 every time speech comes in.
    Returns slide number + element with coordinates.
    """
    if not _engine_ready:
        print("Engine not initialized. Call initialize() first.")
        return None, None
    return match_text(spoken_text)

def get_coordinates(slide_number, keyword):
    """
    Called by Member 4 to get exact position for highlighting.
    Returns x, y, w, h coordinates.
    """
    return get_element_coordinates(slide_number, keyword)