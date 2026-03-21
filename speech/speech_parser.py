import json
import os
from rapidfuzz import fuzz

MEMORY_FILE = "speech/intent_memory.json"


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
            # Safety: ignore if phrase contains protected words
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

    # -------- AUTO-LEARNING (SAFE VERSION) --------
    print("I didn't understand that.")
    user_choice = input(
        "Map this to an intent? (next / back / undo / highlight / skip / no): "
    ).strip().lower()

    intent_map = {
        "next": "next_slide",
        "back": "previous_slide",
        "undo": "undo",
        "highlight": "highlight",
        "skip": "next_slide"
    }

    if user_choice in intent_map:
        learned_intent = {
            "intent": intent_map[user_choice],
            "confidence": 0.8
        }

        # -------- PROTECTION: DON'T LEARN CRITICAL COMMANDS --------
        protected_words = ["next", "back", "undo", "highlight"]

        if not any(word in text for word in protected_words):
            memory[text] = learned_intent
            save_memory(memory)
            print("Learned for future!")
        else:
            print("Skipped learning (protected command)")

        return learned_intent

    return {"intent": "none", "confidence": 0.5}