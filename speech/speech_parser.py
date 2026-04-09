
import json
import os
from rapidfuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

# OpenAI is optional — works without it
try:
    from openai import OpenAI
    _client = OpenAI()
    _HAS_OPENAI = True
except Exception:
    _client = None
    _HAS_OPENAI = False

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


# -------- LLM NAVIGATION INTENT (optional) --------
def get_llm_navigation_intent(text):
    """
    Uses the OpenAI API to semantically detect navigation intent.
    Returns 'next_slide', 'previous_slide', or 'none'.
    Only runs if OpenAI is available and working.
    """
    if not _HAS_OPENAI or _client is None:
        return "none"

    prompt = f"""You are a helpful assistant for a presentation software.
The speaker said: "{text}"

Does this sentence indicate a slide navigation command?
- Return "next_slide" if they want to go to the NEXT slide (e.g. "go ahead", "let's move on", "jumping ahead", "skip this", "advance", "proceed", "move forward", etc.)
- Return "previous_slide" if they want to go to the PREVIOUS slide (e.g. "go back", "previous one", "rewind", "let's revisit", etc.)
- Return "none" if it is NOT a navigation command (e.g. regular speech about a topic).

Reply with ONLY one of these three words: next_slide, previous_slide, none. No explanation."""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            timeout=5.0
        )
        result = response.choices[0].message.content.strip().lower()
        if result in ("next_slide", "previous_slide"):
            return result
        return "none"
    except Exception:
        return "none"


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

    # -------- LLM NAVIGATION CHECK (primary) --------
    llm_nav = get_llm_navigation_intent(text)
    if llm_nav == "next_slide":
        return {"intent": "next_slide", "confidence": 0.95}
    elif llm_nav == "previous_slide":
        return {"intent": "previous_slide", "confidence": 0.95}

    # -------- FUZZY NEXT SLIDE (fallback) --------
    if is_match(text, ["next", "move on", "continue", "skip", "forward"]):
        return {"intent": "next_slide", "confidence": 0.9}

    # -------- FUZZY PREVIOUS SLIDE (fallback) --------
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

    # -------- KEYWORD EXTRACTION --------
    words = text.split()
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "and", "or", "but", "in", "on", "at", "to", "for", "of",
                  "with", "by", "it", "its", "this", "that", "i", "we", "you",
                  "he", "she", "they", "my", "our", "your", "can", "will",
                  "do", "does", "did", "has", "have", "had", "not", "so", "if"}
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]

    return {
        "intent": "speech",
        "keywords": keywords,
        "raw": text,
        "confidence": 0.5
    }
