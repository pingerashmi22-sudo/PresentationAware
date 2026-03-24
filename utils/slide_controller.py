import pyautogui
import time

# ── Assumes PowerPoint is the active/focused window ──

def next_slide():
    """Press Right Arrow to advance one slide."""
    pyautogui.press('right')
    time.sleep(0.2)


def previous_slide():
    """Press Left Arrow to go back one slide."""
    pyautogui.press('left')
    time.sleep(0.2)


def goto_slide(slide_number: int):
    """
    Jump directly to any slide number in PowerPoint.
    Works during a slideshow: type the number then press Enter.
    """
    print(f"[slide_controller] Jumping to slide {slide_number}")
    pyautogui.typewrite(str(slide_number), interval=0.05)
    pyautogui.press('enter')
    time.sleep(0.3)