from context.state import SystemState
from context.history_manager import HistoryManager
from context.intent_validator import IntentValidator
from slide_mapper.mapper import find_target


class ContextManager:

    def __init__(self):
        self.state = SystemState()
        self.history = HistoryManager()
        self.validator = IntentValidator()

        # ── Current Slide State tracking ──────────────────────────────────
        # Mirrors state.current_slide but exposed directly on ContextManager
        # so main.py and the LLM pipeline can read it without going through
        # the full SystemState object.
        self.current_slide = self.state.current_slide

    # ── PUBLIC: called by main.py after every LLM-driven slide change ─────
    def update_slide(self, slide_number: int):
        """
        Moves to slide_number (1-based externally, 0-based in SystemState).
        Clamps to valid range so the LLM can never push us out of bounds.
        """
        total = self.state.total_slides
        # Clamp to 1-based range first, then convert to 0-based for SystemState
        clamped_1based = max(1, min(slide_number, total))
        self.state.update_slide(clamped_1based - 1)  # SystemState is 0-based
        self.current_slide = clamped_1based           # ContextManager stays 1-based

    # ── PUBLIC: called by main.py after every transcript arrives ──────────
    def add_transcript(self, text: str):
        """Logs cleaned STT text into the rolling history window."""
        self.history.add(text)

    # ── PUBLIC: called by main.py just before each LLM call ───────────────
    def get_llm_context(self) -> dict:
        """
        Returns a snapshot of current situational awareness for the LLM.

        The LLM receives this alongside the transcript so it can make
        context-aware decisions, e.g.:
          - "We are on slide 3 of 8, so 'go back' means slide 2"
          - "The speaker mentioned scalability 15 seconds ago, so
             highlight that on the current slide"

        Shape:
        {
            "current_slide":  int,   # 1-based slide number
            "total_slides":   int,   # total slides in the loaded PPT
            "recent_speech":  str    # last ~30 s of transcripts joined by " | "
        }
        """
        return {
            "current_slide": self.current_slide,
            "total_slides":  self.state.total_slides,  # raw count — correct as-is
            "recent_speech": self.history.get_as_string(),
        }

    # ── LEGACY: kept for any old code paths that still call process_intent ─
    def process_intent(self, intent_data: dict) -> dict:
        """
        Original rule-based intent handler.
        Still used as a fallback; new LLM pipeline calls update_slide()
        and get_llm_context() directly instead.
        """

        # -------- VALIDATE INTENT ----------------------------------------
        valid, message = self.validator.validate(intent_data)

        if not valid:
            print("Intent rejected:", message)
            return {"status": "error", "message": message}

        intent = intent_data["intent"]
        target = intent_data.get("target")

        # -------- CONTEXT AWARENESS --------------------------------------
        if target == "this":
            target = self.state.last_target

        action_result = {}

        # -------- SLIDE NAVIGATION ---------------------------------------
        if intent == "next_slide":
            # state.current_slide is 0-based; total_slides - 1 is last valid 0-based index
            if self.state.current_slide < self.state.total_slides - 1:
                self.update_slide(self.current_slide + 1)  # pass 1-based to update_slide
                action_result = {
                    "action": "next_slide",
                    "current_slide": self.current_slide
                }
            else:
                print("Already at last slide")
                return {"status": "error", "message": "Already at last slide"}

        elif intent == "previous_slide":
            # self.current_slide is 1-based, so > 1 means there's a slide before this
            if self.current_slide > 1:
                self.update_slide(self.current_slide - 1)
            else:
                print("Already at first slide")
                return {"status": "error", "message": "Already at first slide"}

            action_result = {
                "action": "previous_slide",
                "current_slide": self.current_slide
            }

        # -------- UNDO ---------------------------------------------------
        elif intent == "undo":
            last_action = self.history.undo()

            if last_action:
                if last_action["intent"] == "next_slide":
                    self.update_slide(max(1, self.current_slide - 1))

                elif last_action["intent"] == "previous_slide":
                    self.update_slide(self.current_slide + 1)

                elif last_action["intent"] == "highlight":
                    print("Undo highlight:", last_action["target"])

                print("Undo:", last_action)

                return {
                    "action": "undo",
                    "reversed_action": last_action,
                    "current_slide": self.current_slide
                }

            return {"status": "error", "message": "Nothing to undo"}

        # -------- HIGHLIGHT ----------------------------------------------
        elif intent == "highlight":
            result = find_target(self.current_slide, target)

            if result:
                word     = result["word"]
                position = result["position"]

                print(f"Highlighting '{word}' at position {position}")

                self.state.set_last_action(intent, target)
                self.history.add_action(intent, target)

                return {
                    "action": "highlight",
                    "target": word,
                    "position": position,
                    "current_slide": self.current_slide
                }
            else:
                print("Target not found")
                return {"action": "highlight_failed", "target": target}

        # -------- STORE ACTION -------------------------------------------
        self.state.set_last_action(intent, target)
        self.history.add_action(intent, target)

        print("Current state:", self.state.get_state())

        return action_result