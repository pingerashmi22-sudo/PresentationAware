class SystemState:

    def __init__(self):
        self.current_slide = 0
        self.total_slides = 0
        self.last_intent = None
        self.last_target = None
        self.confidence = 1.0

    # -------- SLIDE MANAGEMENT --------
    def update_slide(self, slide_number):
        if not isinstance(slide_number, int):
            return

        if slide_number < 0:
            self.current_slide = 0
        elif self.total_slides and slide_number >= self.total_slides:
            self.current_slide = self.total_slides - 1
        else:
            self.current_slide = slide_number

    def set_total_slides(self, total):
        if isinstance(total, int) and total >= 0:
            self.total_slides = total

    # -------- ACTION TRACKING --------
    def set_last_action(self, intent, target=None, confidence=1.0):
        self.last_intent = intent
        self.last_target = target
        self.confidence = confidence

    # -------- STATE ACCESS --------
    def get_state(self):
        return {
            "current_slide": self.current_slide,
            "total_slides": self.total_slides,
            "last_intent": self.last_intent,
            "last_target": self.last_target,
            "confidence": self.confidence
        }

    # -------- OPTIONAL UTILITIES --------
    def reset(self):
        self.current_slide = 0
        self.last_intent = None
        self.last_target = None
        self.confidence = 1.0