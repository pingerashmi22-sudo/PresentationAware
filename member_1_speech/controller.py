import time
from speech_engine import SpeechEngine
from slide_controller import SlideController
from visual_highlighter import highlight_by_speech
import wake_word 

class PresentationController:
    def __init__(self):
        # Initialize specialized Member 4 tools [cite: 36, 37]
        self.engine = SpeechEngine()
        self.slide_ctrl = SlideController()
        self.is_running = True
        
        # Connect to PowerPoint visual bridge [cite: 7]
        self.slide_ctrl.connect() 
        print("🚀 [Member 4] Controller initialized and connected to PPT.")

    def start_lifecycle(self):
        """
        Manages the Audio Lifecycle: Wake Word -> Transcribe -> Action. [cite: 42, 43]
        """
        print("👂 [System Standby] Waiting for wake word 'Porcupine'...")
        
        try:
            while self.is_running:
                # 1. Wait for trigger from 05_wake_word.py [cite: 5, 42]
                if wake_word.detect():
                    print("🚨 Wake word detected! [Emit: Transcription Ready] [cite: 5]")
                    
                    # 2. Capture clean text via speech_engine.py [cite: 6, 17]
                    # This ensures the mic only sends 'active' speech to the AI [cite: 42, 43]
                    text = self.engine.capture_and_transcribe(duration=4.0)
                    
                    if text:
                        self.execute_action(text)
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def execute_action(self, text):
        """
        Member 4 Task: Absolute Control & Smart Highlighting. [cite: 10, 36, 40, 41]
        """
        clean_text = text.lower()
        
        # --- Task: Absolute Navigation (Priority: Slide Numbers) [cite: 40, 8] ---
        if "slide" in clean_text and any(s.isdigit() for s in clean_text.split()):
            try:
                # Extract digits for Absolute Control [cite: 40, 8]
                num = [int(s) for s in clean_text.split() if s.isdigit()][0]
                self.slide_ctrl.jump_to_slide(num)
            except IndexError:
                print("⚠️ No slide number detected in speech.")

        # --- Task: Relative Navigation (Fallback: Next/Previous) [cite: 40, 8] ---
        elif "next" in clean_text:
            print("➡️ No number detected, moving to next slide.")
            self.slide_ctrl.move_next()
            
        elif "back" in clean_text or "previous" in clean_text:
            print("⬅️ No number detected, moving to previous slide.")
            self.slide_ctrl.move_previous()

        # --- Task: Smart Highlighting [cite: 41, 9] ---
        elif "highlight" in clean_text:
            print(f"✨ [Action] Highlighting terms: {text} [cite: 41]")
            # Use LLM-detected terms for dynamic highlighting [cite: 9, 41]
            # Replace 'your_presentation.pptx' with your actual path variable
            # highlight_by_speech(text, "your_presentation.pptx")

    def stop(self):
        print("\n⏹️ Stopping Member 4 Controller...")
        self.is_running = False

if __name__ == "__main__":
    controller = PresentationController()
    controller.start_lifecycle()