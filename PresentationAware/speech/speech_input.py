import speech_recognition as sr

# Initialize ONCE
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True

mic = sr.Microphone()

def get_speech_input():
    global recognizer, mic

    with mic as source:
        print("\nListening...")

        
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=3,
                phrase_time_limit=4
            )
        except sr.WaitTimeoutError:
            print("No speech detected")
            return ""

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()

    except sr.UnknownValueError:
        print("Could not understand")
        return ""

    except sr.RequestError:
        print("API error")
        return ""