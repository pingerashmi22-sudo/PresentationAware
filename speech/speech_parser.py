
import json
import os
from rapidfuzz import fuzz

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "intent_memory.json")


# -------- MEMORY FUNCTIONS --------
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)


# -------- FUZZY MATCH --------
def is_match(text, keywords, threshold=80):
    for kw in keywords:
        score = fuzz.partial_ratio(text, kw)
        if score >= threshold and len(kw.split()) <= len(text.split()):
            return True
    return False


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

    # -------- KEYWORD EXTRACTION (replaces input() for web use) --------
    words = text.split()
    keywords = [w for w in words if len(w) > 4]  # simple keyword filter

    return {
        "intent": "speech",
        "keywords": keywords,
        "raw": text,
        "confidence": 0.5
    }
