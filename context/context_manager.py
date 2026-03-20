from context.state import SystemState
from context.history_manager import HistoryManager
from context.intent_validator import IntentValidator
from slide_mapper.mapper import find_target


class ContextManager:

    def __init__(self):
        self.state = SystemState()
        self.history = HistoryManager()
        self.validator = IntentValidator()

    def process_intent(self, intent_data):

        # -------- VALIDATE INTENT --------
        valid, message = self.validator.validate(intent_data)

        if not valid:
            print("Intent rejected:", message)
            return {
                "status": "error",
                "message": message
            }

        intent = intent_data["intent"]
        target = intent_data.get("target")

        # -------- CONTEXT AWARENESS --------
        if target == "this":
            target = self.state.last_target

        action_result = {}

        # -------- SLIDE NAVIGATION --------
        if intent == "next_slide":
            if self.state.current_slide < self.state.total_slides - 1:
                self.state.update_slide(self.state.current_slide + 1)
                action_result = {
                    "action": "next_slide",
                    "current_slide": self.state.current_slide
                }
            else:
                print("Already at last slide")
                return {
                    "status": "error",
                    "message": "Already at last slide"
                }

        elif intent == "previous_slide":
            if self.state.current_slide > 0:
                self.state.update_slide(self.state.current_slide - 1)

            action_result = {
                "action": "previous_slide",
                "current_slide": self.state.current_slide
            }

        # -------- UNDO --------
        elif intent == "undo":
            last_action = self.history.undo()

            if last_action:
                if last_action["intent"] == "next_slide":
                    self.state.update_slide(max(0, self.state.current_slide - 1))

                elif last_action["intent"] == "previous_slide":
                    self.state.update_slide(self.state.current_slide + 1)

                elif last_action["intent"] == "highlight":
                    print("Undo highlight:", last_action["target"])

                print("Undo:", last_action)

                return {
                    "action": "undo",
                    "reversed_action": last_action,
                    "current_slide": self.state.current_slide
                }

            return {
                "status": "error",
                "message": "Nothing to undo"
            }

        # -------- HIGHLIGHT --------
        elif intent == "highlight":
            result = find_target(self.state.current_slide, target)

            if result:
                word = result["word"]
                position = result["position"]

                print(f"Highlighting '{word}' at position {position}")

                self.state.set_last_action(intent, target)
                self.history.add_action(intent, target)

                return {
                    "action": "highlight",
                    "target": word,
                    "position": position,
                    "current_slide": self.state.current_slide
                }
            else:
                print("Target not found")
                return {
                    "action": "highlight_failed",
                    "target": target
                }
            
        # -------- STORE ACTION --------
        self.state.set_last_action(intent, target)
        self.history.add_action(intent, target)

        print("Current state:", self.state.get_state())

        return action_result