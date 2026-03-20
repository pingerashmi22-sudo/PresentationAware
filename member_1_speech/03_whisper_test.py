import os
from openai import OpenAI

# Initialize the client 
# It's best to set your API key as an environment variable, 
# but for a quick test: client = OpenAI(api_key="your-key-here")
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
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    test_transcription_api()