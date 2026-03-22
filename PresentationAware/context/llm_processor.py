# Brain of the Presentation Aware System — converts transcribed speech into strict JSON action commands via LLM.

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

# Local import — prompts.py must live in the same package/directory
try:
    from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES
except ImportError as exc:
    raise ImportError(
        "Cannot find 'prompts.py'. Make sure it exists alongside llm_processor.py "
        "and exports SYSTEM_PROMPT (str) and FEW_SHOT_EXAMPLES (list[dict])."
    ) from exc

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_MODEL = "gpt-4o"
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_MAX_TOKENS = 512
_DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 2  # seconds

# Exhaustive set of valid top-level actions the downstream executor recognises
VALID_ACTIONS: frozenset[str] = frozenset(
    {
        "navigate_slide",    # Move to next/previous/specific slide
        "highlight_keyword", # Highlight a repeated keyword on-screen
        "zoom_diagram",      # Zoom into a diagram/figure
        "open_url",          # Open a URL in the browser overlay
        "play_media",        # Play embedded audio or video
        "add_annotation",    # Add a text annotation to the current slide
        "reset_view",        # Reset zoom/highlights to default
        "no_op",             # No operation — speaker intent not actionable
    }
)


# ---------------------------------------------------------------------------
# Response model (plain dataclass — no Pydantic dependency required)
# ---------------------------------------------------------------------------
@dataclass
class LLMResponse:
    """
    Structured representation of the LLM's parsed output.

    Attributes:
        action:     One of the VALID_ACTIONS strings.
        payload:    Action-specific parameters dict (may be empty).
        confidence: 0.0–1.0 self-reported confidence from the LLM.
        reasoning:  Short explanation of why this action was chosen.
        raw:        The unmodified JSON string returned by the model.
    """
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    reasoning: str = ""
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON serialisation."""
        return {
            "action": self.action,
            "payload": self.payload,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


# ---------------------------------------------------------------------------
# Main processor class
# ---------------------------------------------------------------------------
class LLMProcessor:
    """
    The cognitive brain of the Presentation Aware System.

    Responsibilities:
        1. Build an enriched prompt (system prompt + few-shot examples +
           live context + transcribed text).
        2. Call the OpenAI Chat Completions API.
        3. Parse and validate the JSON response.
        4. Return a structured :class:`LLMResponse` (or a plain dict via
           ``process_input``).

    Usage::

        processor = LLMProcessor()
        result = processor.process_input(
            text="Let me show you an example of the architecture diagram",
            context={
                "current_slide": {"index": 4, "title": "System Architecture"},
                "history": [
                    {"role": "speaker", "text": "Today we discuss microservices."}
                ],
                "keyword_counts": {"microservices": 3, "docker": 1},
            }
        )
        # result -> {"action": "zoom_diagram", "payload": {"element": "auto"}, ...}
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Initialise the LLMProcessor.

        Args:
            api_key:     OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model:       Model name. Falls back to LLM_MODEL env var or gpt-4o.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens:  Maximum tokens in the completion.
            timeout:     HTTP request timeout in seconds.

        Raises:
            EnvironmentError: If no API key is found.
        """
        # Load .env file (silently ignored if not present)
        load_dotenv()

        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "OpenAI API key not found. Set OPENAI_API_KEY in your .env file "
                "or pass it as api_key= to LLMProcessor()."
            )

        self._client = OpenAI(api_key=resolved_key)

        self.model = model or os.getenv("LLM_MODEL", _DEFAULT_MODEL)
        self.temperature = temperature if temperature is not None else float(
            os.getenv("LLM_TEMPERATURE", _DEFAULT_TEMPERATURE)
        )
        self.max_tokens = max_tokens or int(
            os.getenv("LLM_MAX_TOKENS", _DEFAULT_MAX_TOKENS)
        )
        self.timeout = timeout or int(
            os.getenv("LLM_TIMEOUT", _DEFAULT_TIMEOUT)
        )

        # Load prompts from prompts.py
        self._system_prompt: str = SYSTEM_PROMPT
        self._few_shot_examples: list[dict] = FEW_SHOT_EXAMPLES

        logger.info(
            "LLMProcessor initialised | model=%s | temperature=%s | max_tokens=%s",
            self.model,
            self.temperature,
            self.max_tokens,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_input(self, text: str, context: dict) -> dict[str, Any]:
        """
        Core entry point. Converts raw transcribed speech into an executable
        action command understood by the Presentation Aware System.

        Args:
            text:    The transcribed speech snippet from the current turn.
            context: A dict containing:
                - ``current_slide``  (dict): Index, title, notes, elements, etc.
                - ``history``        (list): Previous speaker turns.
                - ``keyword_counts`` (dict): {word: count} of repeated keywords.
                - ``metadata``       (dict): Any additional session metadata.

        Returns:
            A validated dict with keys:
                - ``action``     (str):   One of VALID_ACTIONS.
                - ``payload``    (dict):  Action-specific parameters.
                - ``confidence`` (float): Model self-reported confidence (0–1).
                - ``reasoning``  (str):   Short rationale.

        Raises:
            ValueError: If the input text is empty.
            RuntimeError: If all retry attempts to the API are exhausted.
        """
        if not text or not text.strip():
            raise ValueError("'text' must be a non-empty transcribed speech string.")

        logger.debug("process_input called | text=%r | slide=%s",
                     text[:80], context.get("current_slide", {}).get("index"))

        messages = self._build_messages(text, context)
        raw_json = self._call_api_with_retries(messages)
        response = self._parse_and_validate(raw_json)

        logger.info(
            "Action decided | action=%s | confidence=%.2f | slide=%s",
            response.action,
            response.confidence,
            context.get("current_slide", {}).get("index", "?"),
        )
        return response.to_dict()

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def _build_messages(self, text: str, context: dict) -> list[dict]:
        """
        Assemble the full messages array for the Chat Completions API.

        Structure:
            [SYSTEM]       → Role, output schema, constraints
            [USER]         → Few-shot example 1
            [ASSISTANT]    → Expected response for example 1
            ...            → (repeats for all few-shot examples)
            [USER]         → Live context + current transcript

        Args:
            text:    Current transcribed utterance.
            context: Session context dictionary.

        Returns:
            List of message dicts ready for the API.
        """
        messages: list[dict] = [
            {"role": "system", "content": self._system_prompt}
        ]

        # Inject few-shot examples (user/assistant pairs)
        for example in self._few_shot_examples:
            messages.append({"role": "user", "content": example["user"]})
            messages.append({"role": "assistant", "content": example["assistant"]})

        # Build the live user turn
        messages.append({
            "role": "user",
            "content": self._format_live_turn(text, context),
        })

        return messages

    def _format_live_turn(self, text: str, context: dict) -> str:
        """
        Serialise the live context and transcript into a structured user message.

        Args:
            text:    Current transcribed utterance.
            context: Session context dict.

        Returns:
            Formatted string that the model uses to make its decision.
        """
        current_slide = context.get("current_slide", {})
        history = context.get("history", [])
        keyword_counts = context.get("keyword_counts", {})
        metadata = context.get("metadata", {})

        # Format recent history (cap at last 5 turns to stay within context)
        history_lines: list[str] = []
        for turn in history[-5:]:
            role = turn.get("role", "speaker")
            turn_text = turn.get("text", "")
            history_lines.append(f"  [{role}]: {turn_text}")
        history_block = "\n".join(history_lines) if history_lines else "  (no history)"

        # Format repeated keywords
        kw_block = ", ".join(
            f'"{w}" ×{c}' for w, c in sorted(
                keyword_counts.items(), key=lambda x: -x[1]
            )
        ) or "(none yet)"

        return (
            "=== LIVE SESSION DATA ===\n"
            f"\nCURRENT SLIDE:\n"
            f"  index   : {current_slide.get('index', 'unknown')}\n"
            f"  title   : {current_slide.get('title', 'unknown')}\n"
            f"  notes   : {current_slide.get('notes', '')}\n"
            f"  elements: {json.dumps(current_slide.get('elements', []))}\n"
            f"\nCONVERSATION HISTORY (last 5 turns):\n{history_block}\n"
            f"\nREPEATED KEYWORDS:\n  {kw_block}\n"
            f"\nSESSION METADATA:\n  {json.dumps(metadata)}\n"
            f"\nCURRENT TRANSCRIPT:\n  \"{text.strip()}\"\n"
            "\n=== INSTRUCTIONS ===\n"
            "Analyse the transcript in context. Return ONLY valid JSON matching "
            "the required schema. No prose, no markdown fences.\n"
            'Schema: {"action": string, "payload": object, '
            '"confidence": float, "reasoning": string}'
        )

    # ------------------------------------------------------------------
    # API call with retry logic
    # ------------------------------------------------------------------
    def _call_api_with_retries(self, messages: list[dict]) -> str:
        """
        Call the OpenAI API with exponential backoff retry on transient errors.

        Args:
            messages: Fully assembled messages list.

        Returns:
            Raw response string from the model.

        Raises:
            RuntimeError: After all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.debug("API call attempt %d/%d", attempt, _MAX_RETRIES)
                completion = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                    response_format={"type": "json_object"},  # Force JSON mode
                )
                raw = completion.choices[0].message.content or ""
                logger.debug("API raw response: %s", raw[:300])
                return raw

            except RateLimitError as exc:
                wait = _RETRY_BACKOFF_BASE ** attempt
                logger.warning("Rate limit hit. Retrying in %ds... (%s)", wait, exc)
                last_error = exc
                time.sleep(wait)

            except APIConnectionError as exc:
                wait = _RETRY_BACKOFF_BASE ** attempt
                logger.warning("Connection error. Retrying in %ds... (%s)", wait, exc)
                last_error = exc
                time.sleep(wait)

            except APIError as exc:
                # Non-retryable API error (e.g. invalid request)
                logger.error("Non-retryable API error: %s", exc)
                raise RuntimeError(f"LLM API error (non-retryable): {exc}") from exc

        raise RuntimeError(
            f"LLM API call failed after {_MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    # ------------------------------------------------------------------
    # Parsing & validation
    # ------------------------------------------------------------------
    def _parse_and_validate(self, raw_json: str) -> LLMResponse:
        """
        Parse the raw JSON string from the model and validate its structure.

        Handles:
            - Malformed JSON → logs warning, returns ``no_op``
            - Unknown action → logs warning, returns ``no_op``
            - Missing keys   → fills in safe defaults

        Args:
            raw_json: The raw string returned by the model.

        Returns:
            A validated :class:`LLMResponse` instance.
        """
        if not raw_json.strip():
            logger.warning("LLM returned empty response. Defaulting to no_op.")
            return self._no_op_response(raw="", reason="Empty model response")

        # Parse JSON
        try:
            data: dict = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.warning("JSON decode failed: %s | raw=%r", exc, raw_json[:200])
            return self._no_op_response(raw=raw_json, reason=f"JSON decode error: {exc}")

        # Validate action
        action = data.get("action", "").strip()
        if action not in VALID_ACTIONS:
            logger.warning(
                "Unknown action '%s' from model. Valid: %s. Defaulting to no_op.",
                action,
                sorted(VALID_ACTIONS),
            )
            return self._no_op_response(raw=raw_json, reason=f"Unknown action: {action!r}")

        # Extract remaining fields with safe defaults
        payload = data.get("payload", {})
        if not isinstance(payload, dict):
            logger.warning("'payload' is not a dict (%s). Replacing with {}.", type(payload))
            payload = {}

        confidence = float(data.get("confidence", 1.0))
        confidence = max(0.0, min(1.0, confidence))   # clamp to [0, 1]

        reasoning = str(data.get("reasoning", ""))

        return LLMResponse(
            action=action,
            payload=payload,
            confidence=confidence,
            reasoning=reasoning,
            raw=raw_json,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _no_op_response(raw: str, reason: str = "") -> LLMResponse:
        """Return a safe no-op response with an explanation in reasoning."""
        return LLMResponse(
            action="no_op",
            payload={},
            confidence=0.0,
            reasoning=reason or "Defaulted to no_op.",
            raw=raw,
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------
def create_processor(**kwargs: Any) -> LLMProcessor:
    """
    Factory function for creating a pre-configured :class:`LLMProcessor`.

    This is the recommended way to instantiate the processor in the
    orchestration layer, as it centralises configuration::

        from llm_processor import create_processor

        brain = create_processor()
        action = brain.process_input(text, context)

    Args:
        **kwargs: Forwarded verbatim to :class:`LLMProcessor.__init__`.

    Returns:
        A fully initialised :class:`LLMProcessor` instance.
    """
    return LLMProcessor(**kwargs)


# ---------------------------------------------------------------------------
# Quick smoke-test (run directly: python llm_processor.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    SAMPLE_CONTEXT: dict[str, Any] = {
        "current_slide": {
            "index": 3,
            "title": "Neural Network Architecture",
            "notes": "Explain the layers and activation functions.",
            "elements": ["figure_1", "bullet_list", "speaker_notes"],
        },
        "history": [
            {"role": "speaker", "text": "Welcome everyone to this deep learning talk."},
            {"role": "speaker", "text": "Neural networks are powerful models."},
            {"role": "speaker", "text": "Neural networks excel at pattern recognition."},
        ],
        "keyword_counts": {"neural network": 3, "deep learning": 2, "layers": 1},
        "metadata": {"session_id": "demo-001", "presenter": "Dr. Smith"},
    }

    SAMPLE_TEXTS = [
        "Let me show you an example of how a neural network processes an image.",
        "Let's move on to the next slide about training.",
        "As I mentioned, neural networks are really powerful for this.",
        "This is just a pause while I find my notes.",
    ]

    try:
        processor = create_processor()
        for sample in SAMPLE_TEXTS:
            print(f"\n{'─'*60}")
            print(f"  TRANSCRIPT: {sample!r}")
            result = processor.process_input(text=sample, context=SAMPLE_CONTEXT)
            print(f"  RESULT    : {json.dumps(result, indent=2)}")
    except EnvironmentError as e:
        print(f"\n[ERROR] {e}")
        print("Set OPENAI_API_KEY in a .env file and re-run.")
        sys.exit(1)