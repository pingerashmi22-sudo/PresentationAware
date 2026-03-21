# Sends a recorded audio chunk to the OpenAI Whisper API and prints the transcribed text.

import os
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

# Load API key from .env
load_dotenv()

# Initialize the client
client = OpenAI()


def test_transcription_api():
    filepath = os.path.join("audio_samples", "test_chunk.wav")

    if not os.path.exists(filepath):
        print(f"❌ Error: {filepath} not found. Run 02_record_audio.py first!")
        return

    print("☁️ Sending audio to OpenAI API...")

    try:
        with open(filepath, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        print("\n📝 API Transcription Result:")
        print("-" * 30)
        print(transcription.text.strip())
        print("-" * 30)

    except AuthenticationError:
        print("❌ API Error: Invalid API key. Check OPENAI_API_KEY in your .env file.")
    except APIConnectionError:
        print("❌ API Error: Could not connect to OpenAI. Check your internet connection.")
    except APIError as e:
        print(f"❌ API Error: {e}")


if __name__ == "__main__":
    test_transcription_api()