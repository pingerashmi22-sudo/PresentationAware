import json
import os

def get_element_coordinates(slide_number, keyword):
    """
    Given a slide number and a keyword,
    returns the x, y, w, h coordinates of that element.
    Used by Member 4 to draw highlights on screen.
    """
    index_path = os.path.join(os.path.dirname(__file__), "slide_index.json")

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    slide_key = f"slide_{slide_number}"
    if slide_key not in index:
        print(f"Slide {slide_number} not found in index.")
        return None

    elements = index[slide_key].get("elements", [])

    for element in elements:
        if keyword.lower() in element.get("text", "").lower():
            return {
                "x": element.get("x", 0),
                "y": element.get("y", 0),
                "w": element.get("w", 0),
                "h": element.get("h", 0),
                "text": element.get("text", ""),
                "type": element.get("type", "")
            }

    # If exact match not found, return first element of slide
    if elements:
        return {
            "x": elements[0].get("x", 0),
            "y": elements[0].get("y", 0),
            "w": elements[0].get("w", 0),
            "h": elements[0].get("h", 0),
            "text": elements[0].get("text", ""),
            "type": elements[0].get("type", "")
        }

    return None