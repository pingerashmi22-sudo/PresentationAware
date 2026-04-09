import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "PresentationAware"))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

import json
import base64
import tempfile
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def extract_physical_emphasis(audio_b64, slide_text):
    if not audio_b64:
        return []
        
    if "," in audio_b64:
        audio_b64 = audio_b64.split(",")[1]
        
    try:
        audio_data = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
            
        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                timeout=5.0
            )
            
        os.remove(tmp_path)
        
        words_data = getattr(transcript, 'words', [])
        if not words_data:
            return []
            
        scored_words = []
        slide_text_lower = slide_text.lower()
        
        for i, w in enumerate(words_data):
            # w has .word, .start, .end
            text = w.word.strip().lower()
            text = re.sub(r'[^\w\s]', '', text)
            
            if len(text) <= 2 or text in {"the","and","this","that","with","for","from","are","was","were","been"}:
                continue
                
            duration = w.end - w.start
            pause_after = 0.0
            if i + 1 < len(words_data):
                pause_after = words_data[i+1].start - w.end
                if pause_after < 0:
                    pause_after = 0.0
                    
            char_dur = duration / len(text) if len(text) > 0 else 0
            score = (char_dur * 10) + (pause_after * 2)
            
            if text in slide_text_lower:
                score += 5.0
                
            scored_words.append((score, text))
            
        scored_words.sort(reverse=True, key=lambda x: x[0])
        limit = 2 if len(words_data) < 10 else 3
        return [w[1] for w in scored_words[:limit]]
        
    except Exception as e:
        print("Physical Emphasis extraction failed:", e)
        return []

def get_smart_keywords(speech, slide_text):
    if not speech.strip():
        return []
        
    prompt = f"""
    The user is presenting a slide. 
    Slide text: "{slide_text}"
    Speaker said: "{speech}"
    
    Extract the most important keywords from the speaker's sentence that they likely emphasized intellectually.
    Prioritize words that relate to the slide context or are directly on the slide.
    If the spoken sentence is < 10 words, return a maximum of 1 or 2 words.
    If the spoken sentence is >= 10 words, return a maximum of 2 or 3 words.
    Return ONLY a raw JSON array of strings in lowercase (e.g. ["keyword1", "keyword2"]). Do not include markdown formatting or extra text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            timeout=5.0
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        keywords = json.loads(content)
        if isinstance(keywords, list):
            return [str(k).lower().strip() for k in keywords]
    except Exception as e:
        print("OpenAI Keyword Extraction Error:", e)
        
    # Fallback simple extraction
    words = speech.split()
    return [w for w in words if len(w) > 3][:3]

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    speech = data.get("speech", "")
    slide_text = data.get("slide_text", "")
    audio_b64 = data.get("audio_b64", "")

    from speech.speech_parser import parse_input
    parsed = parse_input(speech)

    keywords = parsed.get("keywords", [])
    intent = parsed.get("intent", "")

    if intent == "speech":
        # Extract physical pitch/emphasis logic 
        if audio_b64:
            phys_kw = extract_physical_emphasis(audio_b64, slide_text)
            if phys_kw:
                keywords = phys_kw
            else:
                smart_kw = get_smart_keywords(speech, slide_text)
                if smart_kw:
                    keywords = smart_kw
        else:
            smart_kw = get_smart_keywords(speech, slide_text)
            if smart_kw:
                keywords = smart_kw

    suggestion = ""
    if intent == "next_slide":
        suggestion = "Move to next slide"
    elif intent == "previous_slide":
        suggestion = "Go back to previous slide"
    elif intent == "highlight":
        target = parsed.get("target", "")
        suggestion = "Highlight: " + str(target)
        # Include target as a keyword so the frontend can highlight it
        if target == "current_context":
            smart_kw = get_smart_keywords(speech, slide_text)
            if smart_kw:
                keywords.extend(smart_kw)
        elif target and target not in keywords:
            keywords.append(target)
    elif intent == "speech":
        suggestion = "Speaking about: " + ", ".join(keywords)
        # Always highlight for speech intent
        intent = "highlight"

    return jsonify({
        "keywords": keywords,
        "intent": intent,
        "suggestions": [suggestion] if suggestion else [],
        "target_slide": None
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
