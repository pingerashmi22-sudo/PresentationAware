import pvporcupine
import pyaudio
import struct

def test_wake_word():
    # ⚠️ REPLACE WITH YOUR FREE PICOVOICE ACCESS KEY
    ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE" 
    
    if ACCESS_KEY == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
        print("❌ Please add your Picovoice Access Key to the script.")
        return

    print("🦔 Initializing Porcupine...")
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=['porcupine'])
    
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)

    print("👂 Listening for the wake word 'Porcupine' (Press Ctrl+C to stop)...")

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("🚨 Wake word 'Porcupine' detected!")
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    finally:
        audio_stream.close()
        pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    test_wake_word()