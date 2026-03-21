import pvporcupine
import pyaudio
import struct

# Member 4: The Execution & Audio Lead
# Action: Trigger the "Listening" state only after the wake word.

def start_wake_word_detection(callback_function):
    """
    Modified to accept a callback. When the wake word is heard, 
    it triggers the 'Listening' state in the main system[cite: 42, 43].
    """
    ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE" 
    
    if ACCESS_KEY == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
        print("❌ Please add your Picovoice Access Key.")
        return

    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=['porcupine'])
    
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)

    print("👂 System Standby: Waiting for Wake Word...")

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("🚨 Wake Word Detected! Activating AI Listening State...")
                # MEMBER 4 CHANGE: Instead of just printing, we trigger the next step.
                callback_function() 
                
    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    finally:
        audio_stream.close()
        pa.terminate()
        porcupine.delete()

def trigger_audio_capture():
    """
    This function will eventually live in speech_engine.py or main.py.
    Member 4 logic: Only send 'active' speech to AI after this is called.
    """
    print("🎤 [System Action] Now recording your command for Member 1's LLM...")

if __name__ == "__main__":
    # Start detection and pass the trigger function
    start_wake_word_detection(trigger_audio_capture)