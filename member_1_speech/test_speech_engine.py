from speech_engine import SpeechEngine

def start_demo():
    engine = SpeechEngine()
    print("\n✅ System Online! Presentation Assistant is ready.")
    print("-" * 50)
    
    try:
        while True:
            input("\n👉 Press [Enter] to start speaking...") 
            
            # Updated to match the method name in speech_engine.py
            data = engine.process_audio(duration=4)
            
            print(f"🤖 Action Detected: {data['intent']['action']}")
            print("-" * 30)
                
    except KeyboardInterrupt:
        print("\n\n👋 Demo Stopped.")

if __name__ == "__main__":
    start_demo()