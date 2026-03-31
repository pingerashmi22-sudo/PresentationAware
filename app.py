import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "PresentationAware"))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    speech = data.get("speech", "")

    from speech.speech_parser import parse_input
    parsed = parse_input(speech)

    keywords = parsed.get("keywords", [])
    intent = parsed.get("intent", "")

    suggestion = ""
    if intent == "next_slide":
        suggestion = "Move to next slide"
    elif intent == "previous_slide":
        suggestion = "Go back to previous slide"
    elif intent == "highlight":
        target = parsed.get("target", "")
        suggestion = "Highlight: " + str(target)
        # Include target as a keyword so the frontend can highlight it
        if target and target not in keywords:
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
    app.run(port=5000, debug=True)