import os
import pyaudio
import numpy as np
import wave
from openai import OpenAI
from dotenv import load_dotenv
# Member 4 Change: Removed intent_detection import. 
# Logic now flows to Member 2's ContextManager.

load_dotenv()

class SpeechEngine:
    def __init__(self):
        print("🚀 [Member 4] Audio Engine Active...")
        self.client = OpenAI()
        self.temp_file = "input_cache.wav"

    def capture_and_transcribe(self, duration=4.0):
        """
        Modified to focus ONLY on high-accuracy STT (Speech-to-Text).
        Member 4 Task: Send clean text strings to the ContextManager.
        """
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                        input=True, frames_per_buffer=2048)
        
        print("🎤 Listening for command...")
        frames = []
        try:
            # Capture audio for the specified duration
            for _ in range(0, int(16000 / 2048 * duration)):
                data = stream.read(2048, exception_on_overflow=False)
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # Save audio to a temporary file for Whisper API
        with wave.open(self.temp_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))

        print("☁️  Transcribing...")
        try:
            with open(self.temp_file, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            clean_text = transcript.text.strip()
            print(f"✅ Captured Text: '{clean_text}'")
            
            # Member 4 Change: We no longer detect intent here. 
            # We return the clean text to be handled by the ContextManager.
            return clean_text
            
        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            return ""

# Implementation Note for Member 4:
# In your main.py loop, you will now call:
# 1. wake_word.wait_for_trigger()
# 2. text = speech_engine.capture_and_transcribe()
# 3. context_manager.process(text)