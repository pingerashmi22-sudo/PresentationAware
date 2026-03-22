from pydantic import BaseModel, field_validator, model_validator, ValidationError
from typing import Optional, Tuple  # FIX: Tuple was missing — used in return type hints


# ═══════════════════════════════════════════════════════════════════════════
# JSON SCHEMA  —  defines exactly what the LLM is allowed to return
# ═══════════════════════════════════════════════════════════════════════════

class IntentSchema(BaseModel):
    """
    Pydantic model that acts as the strict JSON schema for every LLM response.

    The LLM must return a JSON object matching this shape:
    {
        "intent":       "next_slide" | "previous_slide" | "highlight" |
                        "go_to_slide" | "undo" | "none",
        "confidence":   0.0 – 1.0   (optional, defaults to 1.0),
        "target":       "some keyword"  (required only when intent == "highlight"),
        "slide_number": 3               (required only when intent == "go_to_slide")
    }
    """

    # FIX: moved VALID_INTENTS out of the class body into a module-level constant.
    # Pydantic v2 treats all class-level assignments as potential fields, which
    # can cause unexpected behaviour or warnings when a plain set is defined
    # inside a BaseModel.
    ...


VALID_INTENTS = {
    "next_slide",
    "previous_slide",
    "highlight",
    "go_to_slide",
    "undo",
    "none",
}


class IntentSchema(BaseModel):  # redefined cleanly below after constant is declared
    intent:       str
    confidence:   float = 1.0
    target:       Optional[str] = None
    slide_number: Optional[int] = None

    # ── Field-level validators ────────────────────────────────────────────

    @field_validator("intent")
    @classmethod
    def intent_must_be_valid(cls, v: str) -> str:
        """Reject any intent string the LLM invented that we don't support."""
        if v not in VALID_INTENTS:
            raise ValueError(
                f"'{v}' is not a recognised intent. "
                f"Must be one of: {sorted(VALID_INTENTS)}"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_in_range(cls, v: float) -> float:
        """Confidence must be a real probability between 0 and 1."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {v}"
            )
        return v

    @field_validator("slide_number")
    @classmethod
    def slide_number_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Slide numbers are 1-based — the LLM should never return 0 or negative."""
        if v is not None and v < 1:
            raise ValueError(
                f"slide_number must be a positive integer (1-based), got {v}"
            )
        return v

    @field_validator("target")
    @classmethod
    def target_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        """Catch cases where the LLM returns target: '' instead of omitting it."""
        if v is not None and not v.strip():
            raise ValueError("target must not be an empty string")
        return v.strip() if v else v

    # ── Cross-field (model-level) validators ──────────────────────────────

    @model_validator(mode="after")
    def check_intent_specific_requirements(self) -> "IntentSchema":
        """
        Rules that depend on the combination of fields, not just one field:

        - highlight    → target must be present
        - go_to_slide  → slide_number must be present
        - all others   → target and slide_number should be absent (warn only)
        """
        if self.intent == "highlight" and not self.target:
            raise ValueError(
                "intent 'highlight' requires a 'target' field "
                "(the keyword to highlight on the slide)"
            )

        if self.intent == "go_to_slide" and self.slide_number is None:
            raise ValueError(
                "intent 'go_to_slide' requires a 'slide_number' field"
            )

        return self


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATOR CLASS  —  drop-in replacement for the original IntentValidator
# ═══════════════════════════════════════════════════════════════════════════

class IntentValidator:

    MIN_CONFIDENCE = 0.5

    def validate(self, intent_data) -> Tuple[bool, str]:
        """
        Legacy entry point — keeps the original (bool, message) return shape
        so process_intent() in context_manager.py needs no changes.

        Internally runs the full Pydantic schema check first, then applies
        the confidence threshold on the validated object.
        """

        # ── Guard: input must be a dict before Pydantic even sees it ─────
        if not isinstance(intent_data, dict):
            return False, "Invalid input format: expected a JSON object (dict)"

        # ── Run full schema validation ────────────────────────────────────
        try:
            validated = IntentSchema(**intent_data)
        except ValidationError as e:
            # Collapse all Pydantic errors into one readable string
            errors = "; ".join(
                f"[{'.'.join(str(loc) for loc in err['loc'])}] {err['msg']}"
                for err in e.errors()
            )
            return False, f"Schema validation failed: {errors}"

        # ── Confidence threshold (applied after schema passes) ────────────
        if validated.confidence < self.MIN_CONFIDENCE:
            return False, (
                f"Low confidence ({validated.confidence:.2f}) — "
                f"minimum required is {self.MIN_CONFIDENCE}"
            )

        return True, "Valid intent"

    def validate_and_parse(self, intent_data) -> Tuple[bool, str, Optional[IntentSchema]]:
        """
        Extended entry point for the new LLM pipeline in main.py.

        Returns a third value — the fully parsed IntentSchema object —
        so the caller can access validated.intent, validated.target,
        validated.slide_number etc. directly without re-parsing the dict.

        Usage in main.py:
            ok, msg, intent = validator.validate_and_parse(raw_json)
            if ok:
                if intent.intent == "go_to_slide":
                    go_to_slide(intent.slide_number)
        """
        if not isinstance(intent_data, dict):
            return False, "Invalid input format: expected a JSON object (dict)", None

        try:
            validated = IntentSchema(**intent_data)
        except ValidationError as e:
            errors = "; ".join(
                f"[{'.'.join(str(loc) for loc in err['loc'])}] {err['msg']}"
                for err in e.errors()
            )
            return False, f"Schema validation failed: {errors}", None

        if validated.confidence < self.MIN_CONFIDENCE:
            return False, (
                f"Low confidence ({validated.confidence:.2f}) — "
                f"minimum required is {self.MIN_CONFIDENCE}"
            ), None

        return True, "Valid intent", validated