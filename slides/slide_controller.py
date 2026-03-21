import win32com.client  # You must run 'pip install pywin32'

class SlideController:
    def __init__(self):
        self.ppt_app = None
        self.presentation = None
        print("🎮 [Member 4] Slide Controller initialized for Absolute Navigation.")

    def connect(self):
        """Connects to the PowerPoint instance currently running on your PC."""
        try:
            self.ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
            self.presentation = self.ppt_app.ActivePresentation
            print(f"✅ Connected to presentation: {self.presentation.Name}")
        except Exception as e:
            print(f"❌ Connection Failed: Open your PPT first! Error: {e}")

    def jump_to_slide(self, slide_index):
        """
        MEMBER 4 TASK: Absolute Control.
        Jumps directly to a slide number.
        """
        if not self.presentation:
            self.connect()
            
        try:
            # PowerPoint uses 1-based indexing for slides
            self.presentation.SlideShowWindow.View.GotoSlide(slide_index)
            print(f"🚀 Jumped to Slide {slide_index}")
        except Exception as e:
            print(f"⚠️ Could not jump to slide {slide_index}: {e}")

    def move_next(self):
        """Simple fallback for 'Next' commands."""
        try:
            self.presentation.SlideShowWindow.View.Next()
        except:
            pass

    def move_previous(self):
        """Simple fallback for 'Back' commands."""
        try:
            self.presentation.SlideShowWindow.View.Previous()
        except:
            pass