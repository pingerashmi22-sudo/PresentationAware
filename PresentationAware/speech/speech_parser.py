import os

from dotenv import load_dotenv
from openai import OpenAI

from context.prompts import CLEANER_PROMPT

# ---------------------------------------------------------------------------
# FIX: load_dotenv() must be called BEFORE os.getenv() and OpenAI client
# initialisation. In the original, the client was created at module load time
# with os.getenv("OPENAI_API_KEY") — but load_dotenv() was called on the line
# just above it, which is fine order-wise. However the OpenAI client was being
# instantiated at import time (module level), meaning if the .env file is
# missing or the key is wrong, the entire module fails to import.
# Moved client creation inside a lazy initialiser so failures are localised.
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path="member_1_speech/.env")

# Lazy client — created once on first use, not at import time
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Returns a cached OpenAI client, initialising it on first call."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "[SpeechParser] OPENAI_API_KEY not found. "
                "Check that member_1_speech/.env exists and contains the key."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def parse_input(raw_text: str) -> str:
    """
    Sends raw STT transcript to the LLM for intelligent cleaning.
    Returns a cleaned string, or "" if the LLM identifies it as noise.
    """
    if not raw_text or not raw_text.strip():
        return ""

    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",  # fast + cheap — cleaning is a simple task
            max_tokens=100,
            temperature=0,        # deterministic — no creativity needed
            messages=[
                {"role": "system", "content": CLEANER_PROMPT},
                {"role": "user",   "content": raw_text.strip()}
            ]
        )

        cleaned = response.choices[0].message.content.strip()

        # FIX: original compared cleaned.upper() == "NOISE" which would miss
        # cases where the LLM returns "noise" or "Noise" — .upper() already
        # handles this, but added .strip() defensively in case of whitespace
        if cleaned.strip().upper() == "NOISE":
            return ""

        return cleaned.lower()

    except Exception as e:
        # Graceful degradation — don't crash the live loop
        print(f"[SpeechParser] LLM cleaning failed: {e} — using raw text")
        return raw_text.lower().strip()