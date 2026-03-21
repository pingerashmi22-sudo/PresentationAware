import json
import os
from rapidfuzz import fuzz, process
from slides.synonym_mapper import expand_with_synonyms


def load_index():
    index_path = os.path.join(os.path.dirname(__file__), "slide_index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def score_phrase(spoken, slide_text):
    """
    Runs 4 different fuzzy scoring methods and returns the highest.
    Each method handles a different type of speech pattern:

    partial_ratio     → short phrase inside long slide text
                        "city govt" matches "Local Self Government Urban"
    token_sort_ratio  → same words, different order
                        "government urban" matches "urban government"
    token_set_ratio   → spoken words are a subset of slide words
                        "municipal body" matches "Urban Municipal Corporation Body"
    ratio             → exact closeness, good for full sentence matches
    """
    s = spoken.lower().strip()
    t = slide_text.lower().strip()

    if not s or not t:
        return 0

    s1 = fuzz.partial_ratio(s, t)
    s2 = fuzz.token_sort_ratio(s, t)
    s3 = fuzz.token_set_ratio(s, t)
    s4 = fuzz.ratio(s, t)

    return max(s1, s2, s3, s4)


def get_all_slide_texts(index):
    """
    Flattens the index into a simple list of (slide_num, element, text)
    so we can run bulk matching efficiently.
    """
    entries = []
    for slide_key, slide_content in index.items():
        slide_num = int(slide_key.split("_")[1])

        # Add each individual element
        for element in slide_content.get("elements", []):
            if element.get("text"):
                entries.append((slide_num, element, element["text"]))

        # Add keyword string as one extra entry per slide
        keywords = slide_content.get("keywords", [])
        if keywords:
            kw_text = " ".join(keywords)
            entries.append((slide_num, None, kw_text))

        # Add full flat text as one entry per slide
        all_text = slide_content.get("all_text", "")
        if all_text:
            entries.append((slide_num, None, all_text))

    return entries


def match_text(spoken_text, threshold=55):
    """
    Main function — takes any spoken phrase, returns best matching slide.

    How it works:
    1. Expands spoken text with synonyms (any topic, not hardcoded)
    2. Scores spoken text against every element, keyword, full text
    3. Uses 4 fuzzy methods per comparison, takes the best
    4. Returns slide number + element with coordinates

    Parameters:
        spoken_text : str  — raw text from speech recognition
        threshold   : int  — minimum score to accept a match (0-100)
                             55 = fairly lenient, good for natural speech
                             70 = stricter, fewer false matches
                             80 = very strict, only strong matches

    Returns:
        (slide_number, element_dict) on match
        (None, None) if no confident match found
    """
    if not spoken_text or not spoken_text.strip():
        print("Empty input received.")
        return None, None

    index = load_index()

    # Step 1: Expand with synonyms
    expanded = expand_with_synonyms(spoken_text)
    original = spoken_text.lower().strip()

    # Step 2: Get all matchable texts from index
    entries = get_all_slide_texts(index)

    if not entries:
        print("Slide index is empty. Run build_slide_index() first.")
        return None, None

    # Step 3: Score every entry
    best_score = 0
    best_slide = None
    best_element = None

    for (slide_num, element, text) in entries:

        # Score with original spoken text
        score_orig = score_phrase(original, text)

        # Score with synonym-expanded text
        score_exp = score_phrase(expanded, text)

        # Take the better score
        score = max(score_orig, score_exp)

        # Boost score if this is a title or heading — more important
        if element and element.get("type") in ("title", "heading"):
            score = min(100, score + 15)

        if score > best_score:
            best_score = score
            best_slide = slide_num

            # If element exists use it, otherwise grab first element of slide
            if element:
                best_element = element
            else:
                slide_key = f"slide_{slide_num}"
                elements = index[slide_key].get("elements", [])
                best_element = elements[0] if elements else {
                    "text": text,
                    "type": "unknown",
                    "x": 0, "y": 0, "w": 0, "h": 0
                }

    # Step 4: Return result
    if best_score >= threshold:
        print(f"\nMatch found:")
        print(f"  Slide    : {best_slide}")
        print(f"  Text     : {best_element.get('text', '')}")
        print(f"  Type     : {best_element.get('type', 'unknown')}")
        print(f"  Position : x={best_element.get('x', 0)}, "
              f"y={best_element.get('y', 0)}, "
              f"w={best_element.get('w', 0)}, "
              f"h={best_element.get('h', 0)}")
        print(f"  Score    : {best_score}")
        return best_slide, best_element

    else:
        print(f"No confident match for: '{spoken_text}' (best score: {best_score})")
        return None, None


def match_text_live(spoken_text):
    """
    Simplified version for Member 1 to call directly during live presentation.
    Uses default threshold.
    Returns (slide_number, element) or (None, None)
    """
    return match_text(spoken_text, threshold=55)