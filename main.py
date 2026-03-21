from context.context_manager import ContextManager
from speech.speech_input import get_speech_input
from speech.speech_parser import parse_input
from utils.slide_controller import next_slide, previous_slide
from utils.visual_highlighter import highlight_area

def run_system():
    print("Voice System Started")
    print("Say 'exit' to stop\n")

    context = ContextManager()

    # OPTIONAL: set total slides manually for now
    context.state.set_total_slides(5)

    while True:
        speech_text = get_speech_input()

        if not speech_text:
            continue

        if "exit" in speech_text:
            print("Exiting system...")
            break

        print("RAW:", speech_text)

        intent_data = parse_input(speech_text)

        print("INTENT DATA:", intent_data)

        if intent_data["intent"] == "none":
            continue

        # GET RESULT FROM CONTEXT
        result = context.process_intent(intent_data)

        # HANDLE OUTPUT PROPERLY
        if result:
            action = result.get("action")

            if action == "next_slide":
                next_slide()
                print(f"Moved to slide {result['current_slide']}")

            elif action == "previous_slide":
                previous_slide()
                print(f"Moved back to slide {result['current_slide']}")

            elif action == "highlight":
                target = result.get("target")
                position = result.get("position", (300, 300))

                print(f"Highlighting: {target}")

                x, y = position
                highlight_area(x + 500, y + 200)

            elif action == "undo":
                print(f"Undo performed")

        print("-" * 40)


if __name__ == "__main__":
    run_system()