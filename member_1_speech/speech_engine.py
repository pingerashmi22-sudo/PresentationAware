import os
import pyaudio
import numpy as np
import wave
import warnings
from openai import OpenAI
from dotenv import load_dotenv
from intent_detection import detect_intent_llm

# Load API key from .env file
load_dotenv()

class SpeechEngine:
    def __init__(self):
        print("🚀 Initializing API-Powered Speech Engine...")
        # Use your API key securely
        self.client = OpenAI()
        self.temp_file = "input_cache.wav"

    def process_audio(self, duration=3.0):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                        input=True, frames_per_buffer=2048)
        
        print("👂 Listening...")
        frames = []
        try:
            for _ in range(0, int(16000 / 2048 * duration)):
                data = stream.read(2048, exception_on_overflow=False)
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # Save audio to a temporary file
        with wave.open(self.temp_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))

        print("☁️  Transcribing via Cloud...")
        try:
            # 1. Transcribe using OpenAI Whisper API
            with open(self.temp_file, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            transcription = transcript.text.strip()
            
            # 2. Use the LLM version of intent detection
            print(f"🗣️  You said: '{transcription}'")
            intent = detect_intent_llm(transcription, self.client)
            
            return {
                "text": transcription, 
                "intent": intent
            }
        except Exception as e:
            print(f"❌ API Error: {e}")
            return {"text": "", "intent": {"action": "NONE"}}