class IntentValidator:

    VALID_INTENTS = {
        "next_slide",
        "previous_slide",
        "highlight",
        "undo",
        "none"
    }

    MIN_CONFIDENCE = 0.5

    def validate(self, intent_data):

        # -------- BASIC INPUT CHECK --------
        if not isinstance(intent_data, dict):
            return False, "Invalid input format"

        intent = intent_data.get("intent")
        confidence = intent_data.get("confidence", 1.0)

        # -------- INTENT CHECK --------
        if not intent:
            return False, "No intent provided"

        if intent not in self.VALID_INTENTS:
            return False, f"Invalid intent: {intent}"

        # -------- CONFIDENCE CHECK --------
        if not isinstance(confidence, (int, float)):
            return False, "Invalid confidence value"

        if confidence < self.MIN_CONFIDENCE:
            return False, "Low confidence"

        # -------- OPTIONAL: TARGET CHECK --------
        if intent == "highlight":
            target = intent_data.get("target")
            if not target:
                return False, "Missing target for highlight"

        return True, "Valid intent"