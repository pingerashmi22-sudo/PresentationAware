import pyaudio
import wave
import os
import warnings
from openai import OpenAI  # 1. Added OpenAI client
from dotenv import load_dotenv  # 2. For secure API key management

# Load environment variables from a .env file
load_dotenv()

# Suppress minor warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Audio Configuration (Keep these the same)
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "temp_recording.wav"

# Initialize the OpenAI Client
# Make sure your API key is in a .env file as OPENAI_API_KEY=your_key
client = OpenAI()

def record_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("\n" + "="*50)
    print("  LISTENING (Speak for 5 seconds...)")
    print("="*50)
    
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        
    print("⏹️  Processing audio...")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def detect_intent(text):
    text = text.lower().strip()
    
    if "next slide" in text or "moving on" in text:
        return "⏭️  ACTION: NEXT_SLIDE"
    elif "previous slide" in text or "go back" in text:
        return "⏮️  ACTION: PREVIOUS_SLIDE"
    elif "for example" in text or "as an example" in text:
        return "🔍 ACTION: ZOOM_EXAMPLE"
    elif "highlight" in text:
        words = text.split()
        try:
            target_word = words[words.index("highlight") + 1]
            return f"🖍️  ACTION: HIGHLIGHT (Word: '{target_word}')"
        except (ValueError, IndexError):
            return "🖍️  ACTION: HIGHLIGHT (No specific word detected)"
    
    return "⏳ (Normal speech detected. No slide action taken.)"

def run_demo():
    print("🚀 Initializing API-Powered Presentation Assistant...")
    print("✅ System Ready (No heavy model loading required)!\n")
    
    try:
        while True:
            input(" Press [ENTER] when you are ready to speak (or press Ctrl+C to quit)...")
            record_audio()
            
            # 3. Transcribe using the Cloud API instead of local model
            print("☁️  Transcribing via API...")

          with open(WAVE_OUTPUT_FILENAME, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            spoken_text = result.text.strip()
            print(f"🗣️  You said: '{spoken_text}'")
            
            # 4. Detect the intent (logic remains the same)
            action = detect_intent(spoken_text)
           print(f"🤖 System Decision: {action}\n")
            
    except KeyboardInterrupt:
        print("\n👋 Exiting Demo. Great job!")
        if os.path.exists(WAVE_OUTPUT_FILENAME):
            os.remove(WAVE_OUTPUT_FILENAME)

if __name__ == "__main__":
    run_demo()