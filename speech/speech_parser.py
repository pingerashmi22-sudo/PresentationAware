import json
import os
from rapidfuzz import fuzz

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "intent_memory.json")
SLIDE_INDEX_FILE = os.path.join(os.path.dirname(__file__), "..", "slides", "slide_index.json")


# -------- MEMORY FUNCTIONS --------
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)


# -------- LOAD SLIDE INDEX --------
def load_slide_index():
    if os.path.exists(SLIDE_INDEX_FILE):
        with open(SLIDE_INDEX_FILE, "r") as f:
            return json.load(f)
    return {}


# -------- FUZZY MATCH --------
def is_match(text, keywords, threshold=80):
    for kw in keywords:
        score = fuzz.partial_ratio(text, kw)
        if score >= threshold and len(kw.split()) <= len(text.split()):
            return True
    return False


# -------- SLIDE KEYWORD MATCH --------
def find_slide_by_keywords(text, threshold=75):
    """
    Scans all slides in slide_index.json.
    If spoken text fuzzy-matches keywords/content of ANY slide,
    returns that slide number — even if you're on a different slide.
    """
    slide_index = load_slide_index()
    best_slide = None
    best_score = 0

    for slide_number, slide_data in slide_index.items():
        score = 0

        # Check topic/title
        topic = slide_data.get("topic", "")
        topic_score = fuzz.partial_ratio(text, topic.lower())
        if topic_score >= threshold:
            score += topic_score * 0.4  # weight for topic match

        # Check content lines
        content = slide_data.get("content", [])
        for line in content:
            line_score = fuzz.partial_ratio(text, line.lower())
            if line_score >= threshold:
                score += line_score * 0.3  # weight per content match

        # Check full_text
        full_text = slide_data.get("full_text", "")
        full_score = fuzz.partial_ratio(text, full_text.lower())
        if full_score >= threshold:
            score += full_score * 0.3

        if score > best_score:
            best_score = score
            best_slide = int(slide_number)

    # Only return if confidence is meaningfully high
    if best_score >= threshold:
        return best_slide, round(best_score / 100, 2)

    return None, 0.0


# -------- MAIN PARSER --------
def parse_input(text):
    text = text.lower().strip()

    # -------- NORMALIZATION --------
    text = text.replace("and do", "undo")
    text = text.replace("end do", "undo")

    # -------- NOISE FILTER --------
    noise_words = [
        "hello", "hi", "okay", "ok", "yes", "yeah",
        "hmm", "huh", "thanks", "thank you"
    ]

    if len(text.split()) == 1 and text in noise_words:
        return {"intent": "none", "confidence": 0.0}

    # -------- LOAD MEMORY --------
    memory = load_memory()

    # -------- CHECK LEARNED PHRASES --------
    for phrase, intent_data in memory.items():
        if phrase in text:
            protected_words = ["next", "back", "undo", "highlight"]
            if any(word in phrase for word in protected_words):
                continue
            return intent_data

    # -------- NEXT SLIDE --------
    if is_match(text, ["next", "move on", "continue", "skip", "forward"]):
        return {"intent": "next_slide", "confidence": 0.9}

    # -------- PREVIOUS SLIDE --------
    if is_match(text, ["back", "previous", "go back", "last slide"]):
        return {"intent": "previous_slide", "confidence": 0.9}

    # -------- UNDO --------
    if is_match(text, ["undo", "cancel", "reverse", "go back action"]):
        return {"intent": "undo", "confidence": 0.95}

    # -------- CONTEXTUAL HIGHLIGHT --------
    if is_match(text, [
        "this is important",
        "this is critical",
        "important point",
        "key takeaway",
        "focus on this"
    ]):
        return {
            "intent": "highlight",
            "target": "current_context",
            "confidence": 0.85
        }

    # -------- DIRECT HIGHLIGHT --------
    if "highlight" in text:
        words = text.split()
        target = words[-1] if len(words) > 1 else None
        return {
            "intent": "highlight",
            "target": target,
            "confidence": 0.85
        }

    # -------- SLIDE KEYWORD JUMP (NEW) --------
    # Check if the spoken text matches keywords of ANY slide
    target_slide, confidence = find_slide_by_keywords(text)
    if target_slide is not None:
        return {
            "intent": "goto_slide",
            "slide_number": target_slide,
            "confidence": confidence,
            "raw": text
        }

    # -------- FALLBACK: generic speech --------
    words = text.split()
    keywords = [w for w in words if len(w) > 4]

    return {
        "intent": "speech",
        "keywords": keywords,
        "raw": text,
        "confidence": 0.5
    }