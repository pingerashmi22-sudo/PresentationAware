import time
import os
# Member 4: Importing your specialized execution and audio modules [cite: 37]
from 05_wake_word import start_wake_word_detection
from speech_engine import SpeechEngine
from slide_controller import SlideController
from visual_highlighter import highlight_by_speech, highlight_text_on_slide

# Member 2 & 3 Modules (Keep these for system integration) [cite: 3, 32]
from context.context_manager import ContextManager

def run_system():
    print("🚀 [Member 4] Presentation System Online.")
    
    # Initialize your tools [cite: 37]
    engine = SpeechEngine()
    controller = SlideController()
    context = ContextManager()
    
    # Connect to the PowerPoint visual bridge 
    controller.connect()

    # Define the trigger for when the wake word is heard [cite: 5, 42]
    def on_wake_word_detected():
        print("\n🚨 Wake Word Detected! [Emit: Transcription Ready]")
        
        # Capture clean text after the wake word [cite: 6, 43]
        speech_text = engine.capture_and_transcribe(duration=4.0)

        if not speech_text or "exit" in speech_text.lower():
            return

        print(f"🗣️  Recognized: \"{speech_text}\"")

        # Member 2's Logic: Process text through the LLM Processor [cite: 3, 24]
        intent_data = context.process_intent(speech_text)
        
        if intent_data:
            action = intent_data.get("action")
            clean_text = speech_text.lower()
            
            # --- 1. MEMBER 4 TASK: Absolute Navigation (Priority: Slide Numbers)  ---
            if "slide" in clean_text and any(s.isdigit() for s in clean_text.split()):
                try:
                    # Extract digits for Absolute Control 
                    num = [int(s) for s in clean_text.split() if s.isdigit()][0]
                    controller.jump_to_slide(num)
                    print(f"✅ Action Executed: Jumped to slide {num}")
                except IndexError:
                    print("⚠️ No slide number detected in speech.")

            # --- 2. MEMBER 4 TASK: Fallback Navigation (Next/Back) [cite: 8] ---
            elif action == "next_slide" or "next" in clean_text:
                controller.move_next()
                print("✅ Action Executed: Next")

            elif action == "previous_slide" or "back" in clean_text:
                controller.move_previous()
                print("✅ Action Executed: Previous")

            # --- 3. MEMBER 4 TASK: Smart Highlighting [cite: 41] ---
            elif action == "highlight" or "highlight" in clean_text:
                # Use target term if provided by LLM, otherwise use current text [cite: 41]
                target_term = intent_data.get("target_term", speech_text)
                
                # Execute visual bridge action 
                highlight_text_on_slide(controller.presentation.ActiveWindow.View.Slide, target_term)
                print(f"✨ Action Executed: Highlighted '{target_term}'")

    # Start the Audio Lifecycle loop [cite: 42]
    # This sits in standby until 'Porcupine' is heard [cite: 5]
    start_wake_word_detection(callback_function=on_wake_word_detected)

if __name__ == "__main__":
    run_system()