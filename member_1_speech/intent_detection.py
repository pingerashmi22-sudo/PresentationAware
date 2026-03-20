def detect_intent_llm(text, client):
    # Use GPT to decide what the user wants to do
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a presentation assistant. Map the user's speech to one of these actions: NEXT_SLIDE, PREVIOUS_SLIDE, ZOOM_IN, or NONE. Respond ONLY with the action name."},
            {"role": "user", "content": text}
        ]
    )
    return {"action": response.choices[0].message.content.strip()}