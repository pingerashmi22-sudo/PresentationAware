class HistoryManager:

    def __init__(self, max_size=50):
        self.history = []
        self.max_size = max_size

    def add_action(self, intent, target=None):
        action = {
            "intent": intent,
            "target": target
        }

        # Maintain max history size
        if len(self.history) >= self.max_size:
            self.history.pop(0)

        self.history.append(action)

    def undo(self):
        if self.history:
            return self.history.pop()
        return None

    def peek_last(self):
        if self.history:
            return self.history[-1]
        return None

    def clear(self):
        self.history.clear()

    def show_history(self):
        return list(self.history)