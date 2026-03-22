from context.context_manager import ContextManager
from context.intent_validator import IntentValidator
from context.llm_processor import create_processor   # use their factory function
from speech.speech_input import get_speech_input
from speech.speech_parser import parse_input
from utils.slide_controller import next_slide, previous_slide, go_to_slide
from utils.visual_highlighter import highlight_area


def run_system():
    print("Voice System Started")
    print("Say 'exit' to stop\n")

    context = ContextManager()
    llm = create_processor()          # Member 1's factory, not LLMProcessor()
    validator = IntentValidator()     # your class, not a standalone function

    context.state.set_total_slides(5)

    while True:
        # ── STEP 1: Capture raw speech ──────────────────────────────────────
        speech_text = get_speech_input()

        if not speech_text:
            continue

        if "exit" in speech_text.lower():
            print("Exiting system...")
            break

        print("RAW:", speech_text)

        # ── STEP 2: Clean the transcript ────────────────────────────────────
        clean_text = parse_input(speech_text)
        print("CLEAN TEXT:", clean_text)

        if not clean_text:
            print("Noise detected — skipping LLM call.")
            continue

        # ── STEP 3: Log transcript to rolling history ───────────────────────
        context.add_transcript(clean_text)

        # ── STEP 4: Build situational context for the LLM ───────────────────
        # Member 1's process_input expects this exact shape:
        # {
        #   "current_slide": {"index": 2, "title": "unknown"},
        #   "history":       [{"role": "speaker", "text": "..."}],
        #   "keyword_counts": {}
        # }
        base_context = context.get_llm_context()
        llm_context = {
            "current_slide": {
                "index": base_context["current_slide"],
                "title": "unknown"       # Member 3 will populate this later
            },
            "history": [
                {"role": "speaker", "text": t}
                for t in context.history.get_recent()
            ],
            "keyword_counts": {}         # Member 3 will populate this later
        }

        # ── STEP 5: Send to LLM — uses Member 1's actual method name ────────
        raw_result = llm.process_input(clean_text, llm_context)
        print("RAW LLM RESULT:", raw_result)

        # ── STEP 6: Validate — map Member 1's action names to your schema ───
        # Member 1 returns:  "navigate_slide", "highlight_keyword",
        #                    "zoom_diagram", "no_op"
        # Your validator expects: "next_slide", "highlight", "go_to_slide", "none"
        action_map = {
            "navigate_slide":    _resolve_navigate(raw_result, context),
            "highlight_keyword": "highlight",
            "zoom_diagram":      "highlight",   # treat zoom as highlight for now
            "no_op":             "none",
        }

        mapped_action = action_map.get(raw_result.get("action"), "none")
        payload = raw_result.get("payload", {})

        # Build a normalised dict your validator understands
        intent_data = {
            "intent":       mapped_action,
            "confidence":   raw_result.get("confidence", 1.0),
            "target":       payload.get("keyword") or payload.get("element"),
            "slide_number": payload.get("slide_number"),
        }

        ok, msg, intent = validator.validate_and_parse(intent_data)
        if not ok:
            print(f"Validation failed: {msg} — skipping.")
            continue

        # ── STEP 7: Execute the validated action ────────────────────────────
        action = intent.intent   # note: IntentSchema uses .intent not .action

        if action == "next_slide":
            next_slide()
            context.update_slide(context.current_slide + 1)
            print(f"Moved to slide {context.current_slide}")

        elif action == "previous_slide":
            previous_slide()
            context.update_slide(context.current_slide - 1)
            print(f"Moved back to slide {context.current_slide}")

        elif action == "go_to_slide":
            if intent.slide_number:
                go_to_slide(intent.slide_number)
                context.update_slide(intent.slide_number)
                print(f"Jumped to slide {intent.slide_number}")
            else:
                print("go_to_slide missing slide_number — skipping.")

        elif action == "highlight":
            if intent.target:
                print(f"Highlighting: {intent.target}")
                highlight_area(intent.target)
            else:
                print("highlight missing target — skipping.")

        elif action == "undo":
            print("Undo performed.")

        elif action == "none":
            print("No action taken.")

        print("-" * 40)


def _resolve_navigate(raw_result: dict, context) -> str:
    """
    Member 1's 'navigate_slide' covers next, previous, AND go_to_slide.
    Work out which one it actually is from the payload.
    """
    slide_number = raw_result.get("payload", {}).get("slide_number")
    if slide_number is not None:
        return "go_to_slide"

    # Check the reasoning text for direction hints
    reasoning = raw_result.get("reasoning", "").lower()
    if any(w in reasoning for w in ["back", "previous", "last", "return"]):
        return "previous_slide"

    return "next_slide"   # default navigation direction


if __name__ == "__main__":
    run_system()