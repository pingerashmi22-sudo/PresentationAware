import pyautogui
import time
import os
from speech_engine import SpeechEngine

def main():
    # Clean up old cache files if they exist
    if os.path.exists("input_cache.wav"):
        try:
            os.remove("input_cache.wav")
        except:
            pass

    # Initialize the new API-powered engine
    engine = SpeechEngine()
    print("🚀 Presentation System Online.")
    print("🎤 Ready for voice commands (e.g., 'Next slide', 'Go back').")
    print("---------------------------------------------------------")

    try:
        while True:
            # Trigger processing (3 second window)
            # In a real presentation, you might trigger this with a key or wake word
            data = engine.process_audio(duration=3.0)
            
            action = data['intent']['action']
            text = data['text']

            if len(text) > 1:
                print(f"🗣️  Recognized: \"{text}\"")
                print(f"🤖 Action: {action}")

            # Execution Logic
            if action == "NEXT_SLIDE":
                pyautogui.press('right')
                print("✅ Action Executed: Next")
                time.sleep(0.5) 
                
            elif action == "PREVIOUS_SLIDE":
                pyautogui.press('left')
                print("✅ Action Executed: Previous")
                time.sleep(0.5)
                
            elif action == "ZOOM_IN":
                pyautogui.hotkey('ctrl', '=')
                print("✅ Action Executed: Zoom In")
                # Auto-reset zoom after 3 seconds for convenience
                time.sleep(3.0)
                pyautogui.hotkey('ctrl', '0')
                print("🔄 Zoom Reset")
            
            # Small pause to keep the CPU cool
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n⏹️ Stopping Presentation Assistant...")

if __name__ == "__main__":
    main()