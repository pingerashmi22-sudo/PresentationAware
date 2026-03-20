import pyaudio

def test_microphone():
    print("🎙️ Initializing PyAudio...")
    audio = pyaudio.PyAudio()

    print("\nTesting default microphone stream...")
    try:
        stream = audio.open(format=pyaudio.paInt16, channels=1,
                            rate=16000, input=True,
                            frames_per_buffer=1024)
        print("✅ Success! Default microphone is working and ready to record.")
        stream.close()
    except Exception as e:
        print(f"❌ Error opening microphone: {e}")
    finally:
        audio.terminate()

if __name__ == "__main__":
    test_microphone()