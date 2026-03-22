import time
from collections import deque


class HistoryManager:

    def __init__(self, max_size: int = 50, transcript_window_seconds: int = 30):
        # ── Action history (undo stack) ───────────────────────────────────
        # Unchanged from original — stores intent/target dicts for undo.
        self.max_size = max_size
        self.history = []

        # ── Transcript rolling log (Contextual Memory) ────────────────────
        # A deque of {"timestamp": float, "text": str} entries.
        # Only entries from the last `transcript_window_seconds` are kept.
        # Used to give the LLM awareness of what the speaker said recently.
        self.transcript_window_seconds = transcript_window_seconds
        self._transcripts = deque()

    # ═════════════════════════════════════════════════════════════════════
    # TRANSCRIPT MEMORY  (new — feeds the LLM context)
    # ═════════════════════════════════════════════════════════════════════

    def add(self, text: str):
        """
        Log a cleaned STT transcript with the current timestamp.
        Old entries outside the rolling window are pruned automatically.
        Called by ContextManager.add_transcript() after every speech event.
        """
        if not text or not text.strip():
            return

        self._transcripts.append({
            "timestamp": time.time(),
            "text": text.strip()
        })
        self._prune_transcripts()

    def get_recent(self) -> list[str]:
        """
        Return transcript strings from the last N seconds as a plain list.
        Automatically drops anything outside the time window before returning.

        Example return value:
            ["let's talk about scalability", "next topic please"]
        """
        self._prune_transcripts()
        return [entry["text"] for entry in self._transcripts]

    def get_as_string(self) -> str:
        """
        Return recent transcripts as a single string joined by ' | '.
        This is what gets passed directly into the LLM context dict.

        Example return value:
            "let's talk about scalability | next topic please"
        """
        return " | ".join(self.get_recent())

    def clear_transcripts(self):
        """Wipe only the transcript log, leaving the action undo stack intact."""
        self._transcripts.clear()

    def _prune_transcripts(self):
        """
        Remove entries older than transcript_window_seconds from the left
        of the deque. Uses a deque so pruning is O(1) per removal.
        """
        cutoff = time.time() - self.transcript_window_seconds
        while self._transcripts and self._transcripts[0]["timestamp"] < cutoff:
            self._transcripts.popleft()

    # ═════════════════════════════════════════════════════════════════════
    # ACTION HISTORY  (original — unchanged, used for undo)
    # ═════════════════════════════════════════════════════════════════════

    def add_action(self, intent: str, target=None):
        """Log a completed intent action. Maintains a fixed-size undo stack."""
        action = {
            "intent": intent,
            "target": target
        }

        if len(self.history) >= self.max_size:
            self.history.pop(0)

        self.history.append(action)

    def undo(self):
        """Pop and return the most recent action, or None if stack is empty."""
        if self.history:
            return self.history.pop()
        return None

    def peek_last(self):
        """Return the most recent action without removing it."""
        if self.history:
            return self.history[-1]
        return None

    def clear(self):
        """Wipe the action undo stack. Does not affect transcript memory."""
        self.history.clear()

    def show_history(self):
        """Return a copy of the full action history list."""
        return list(self.history)