import pyaudio
import wave
import os

def record_audio():
    # Configuration
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000 
    RECORD_SECONDS = 5
    OUTPUT_DIR = "audio_samples"
    OUTPUT_FILENAME = "test_chunk.wav"

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)

    print(f"🔴 Recording for {RECORD_SECONDS} seconds... Speak now!")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("⏹️ Recording finished.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to file
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        
    print(f"💾 Audio saved to {filepath}")

if __name__ == "__main__":
    record_audio()