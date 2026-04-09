import os
import json
from collections import deque
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer

# Try to import OpenAI, but don't crash if missing
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library not installed. Install with: pip install openai")

load_dotenv()
app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

# ----------------------------
# Global state
# ----------------------------
slide_index = {}
slide_embeddings = {}
model = SentenceTransformer('all-MiniLM-L6-v2')
context_windows = {}
WINDOW_SIZE = 7

# ----------------------------
# Initialize OpenAI client (if available)
# ----------------------------
client = None
if OPENAI_AVAILABLE:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
    else:
        print("⚠️ OPENAI_API_KEY not found in .env file")
        client = None
else:
    print("⚠️ OpenAI library not installed, using fallback parser")

# ----------------------------
# Fallback parser (keyword + rule-based)
# ----------------------------
def fallback_parse_intent(speech):
    """Rule-based parser used when OpenAI is unavailable."""
    speech_lower = speech.lower()
    # Navigation keywords
    next_words = ["next", "forward", "ahead", "continue", "proceed", "move forward", "going forward", "jump ahead"]
    prev_words = ["previous", "back", "backward", "go back", "moving back", "jump back"]
    
    for w in next_words:
        if w in speech_lower:
            return {"intent": "next_slide", "keywords": [], "target": ""}
    for w in prev_words:
        if w in speech_lower:
            return {"intent": "previous_slide", "keywords": [], "target": ""}
    
    if "highlight" in speech_lower:
        words = speech_lower.split()
        try:
            idx = words.index("highlight")
            target = words[idx+1] if idx+1 < len(words) else "current_context"
        except:
            target = "current_context"
        return {"intent": "highlight", "keywords": [], "target": target}
    
    # Normal speech: extract simple keywords (nouns longer than 3 letters)
    keywords = [w for w in speech_lower.split() if len(w) > 3][:3]
    return {"intent": "speech", "keywords": keywords, "target": ""}

# ----------------------------
# GPT intent parser (if available)
# ----------------------------
def gpt_parse_intent(speech):
    if client is None:
        return fallback_parse_intent(speech)
    
    prompt = f"""
You are a presentation control assistant. Classify the user's sentence into one of these intents:

- "next_slide": user wants to advance to the next slide (e.g., "next slide", "go forward", "move ahead", "continue", "next", "moving forward", "jump ahead", "skip ahead", "forward")
- "previous_slide": user wants to go back (e.g., "previous slide", "go back", "move back", "back", "previous", "moving back", "jump back", "backward")
- "highlight": user wants to highlight a specific word or phrase on the current slide (e.g., "highlight responsibility", "emphasize education")
- "speech": user is making a normal statement about the content, not a command (e.g., "let's discuss moral values", "education builds character")

For "highlight", also extract the exact target word/phrase.
For "speech", extract up to 3 important keywords (nouns/concepts).
For navigation intents, keywords can be empty.

Return ONLY valid JSON. Example responses:
{{"intent": "next_slide", "keywords": [], "target": ""}}
{{"intent": "previous_slide", "keywords": [], "target": ""}}
{{"intent": "highlight", "keywords": [], "target": "responsibility"}}
{{"intent": "speech", "keywords": ["moral", "values"], "target": ""}}

User said: "{speech}"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" for cheaper
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            timeout=5.0
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        parsed = json.loads(content)
        print(f"[GPT] {parsed}")
        return parsed
    except Exception as e:
        print(f"[GPT] Error: {e}")
        return fallback_parse_intent(speech)

# ----------------------------
# Slide indexing endpoint
# ----------------------------
@app.route("/update_slides", methods=["POST"])
def update_slides():
    global slide_index, slide_embeddings
    data = request.json.get("slides", {})
    slide_index = data
    slide_embeddings = {}
    for slide_num, slide_data in slide_index.items():
        sn = int(slide_num)
        if isinstance(slide_data, dict):
            headings = slide_data.get("headings", [])
        else:
            headings = slide_data
        slide_text = " ".join(headings).strip()
        if slide_text:
            slide_embeddings[sn] = model.encode(slide_text, normalize_embeddings=True)
        else:
            slide_embeddings[sn] = None
    print(f"✅ Updated {len(slide_index)} slides. Embeddings ready: {list(slide_embeddings.keys())}")
    return jsonify({"status": "ok", "slides": len(slide_index)})

# ----------------------------
# Main processing endpoint
# ----------------------------
@app.route("/process", methods=["POST"])
def process():
    data = request.json
    speech = data.get("speech", "")
    current_slide = data.get("current_slide", 1)
    session_id = data.get("session_id", request.remote_addr)

    print(f"\n[REQUEST] speech='{speech}' | current_slide={current_slide}")

    # Parse intent (GPT if available, else fallback)
    parsed = gpt_parse_intent(speech)
    intent = parsed.get("intent", "speech")
    keywords = parsed.get("keywords", [])
    target = parsed.get("target", "")

    target_slide = None
    suggestion = ""

    if intent == "next_slide":
        target_slide = current_slide + 1
        suggestion = "Moving to next slide"
    elif intent == "previous_slide":
        target_slide = current_slide - 1
        suggestion = "Going back to previous slide"
    elif intent == "highlight":
        if not target and keywords:
            target = keywords[0]
        suggestion = f"Highlight: {target if target else 'current context'}"
    elif intent == "speech":
        # Semantic matching
        if session_id not in context_windows:
            context_windows[session_id] = deque(maxlen=WINDOW_SIZE)
        context_windows[session_id].extend(speech.lower().split())
        context_str = " ".join(context_windows[session_id])
        print(f"[CONTEXT] '{context_str}'")
        ctx_emb = model.encode(context_str, normalize_embeddings=True)
        best_slide = None
        best_sim = -1
        for sn, emb in slide_embeddings.items():
            if emb is None or sn == current_slide:
                continue
            sim = np.dot(ctx_emb, emb)
            if sim > best_sim:
                best_sim = sim
                best_slide = sn
        print(f"[SIMILARITIES] best slide {best_slide} sim {best_sim:.3f}")
        if best_slide and best_sim >= 0.35:
            target_slide = best_slide
            suggestion = f"Jump to slide {best_slide} (similarity {best_sim:.2f})"
        else:
            suggestion = f"No clear match (best {best_sim:.2f})"
        intent = "highlight"
        if not keywords:
            keywords = [w for w in speech.lower().split() if len(w) > 3][:3]

    response = {
        "keywords": keywords,
        "intent": intent,
        "suggestions": [suggestion] if suggestion else [],
        "target_slide": target_slide
    }
    print(f"[RESPONSE] {response}")
    return jsonify(response)

# ----------------------------
# Debug endpoint
# ----------------------------
@app.route("/debug/slides", methods=["GET"])
def debug_slides():
    return jsonify({
        "slides_loaded": list(slide_index.keys()),
        "embeddings_ready": list(slide_embeddings.keys())
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)