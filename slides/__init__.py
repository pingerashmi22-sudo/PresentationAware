class PresentationContext:
    """
    Tracks the current state of the presentation session.
    Shared across all modules — Member 3 uses this to
    maintain context between spoken commands.
    """

    def __init__(self):
        self.current_slide      = 0
        self.total_slides       = 0
        self.last_intent        = None
        self.last_target        = None
        self.confidence         = 1.0
        self.command_history_log = []
        self.successful_commands = 0
        self.failed_commands    = 0
        self.highlights         = []
        self.is_muted           = False

    def add_highlight(self, slide_number, target):
        self.highlights.append({
            "slide":  slide_number,
            "target": target
        })

    def get_highlights_for_slide(self, slide_number):
        return [
            h for h in self.highlights
            if h["slide"] == slide_number
        ]

    def remove_last_highlight(self):
        if self.highlights:
            return self.highlights.pop()
        return None

    def log_command(self, intent, success=True):
        self.command_history_log.append({
            "intent":  intent,
            "success": success
        })
        if success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1

    def get_session_summary(self):
        return {
            "total_commands":   len(self.command_history_log),
            "successful":       self.successful_commands,
            "failed":           self.failed_commands,
            "highlights_made":  len(self.highlights)
        }