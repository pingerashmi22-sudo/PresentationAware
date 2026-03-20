from PIL import Image
import pytesseract
import io
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def clean_ocr_text(text):
    """Clean up common OCR artifacts."""
    text = re.sub(r'[|\\/_]{2,}', '', text)        # remove repeated symbols
    text = re.sub(r'[^\x20-\x7E\n]', '', text)     # remove non-printable
    text = re.sub(r'[ \t]+', ' ', text)             # collapse spaces
    text = re.sub(r'\n+', '\n', text)               # collapse newlines
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
    return lines

def emu_to_px(emu_value):
    return round(emu_value / 914400 * 96)

def extract_image_text(prs):
    """
    Returns same structure as content_extractor:
    { slide_number: [ {"text": ..., "type": "ocr", "x":..., ...} ] }
    """
    image_texts = {}

    for i, slide in enumerate(prs.slides):
        slide_number = i + 1
        elements = []

        for shape in slide.shapes:
            if shape.shape_type == 13:  # picture
                x = emu_to_px(shape.left)  if shape.left  else 0
                y = emu_to_px(shape.top)   if shape.top   else 0
                w = emu_to_px(shape.width) if shape.width else 0
                h = emu_to_px(shape.height)if shape.height else 0

                try:
                    image_data = shape.image.blob
                    image = Image.open(io.BytesIO(image_data))
                    raw_text = pytesseract.image_to_string(image)
                    lines = clean_ocr_text(raw_text)
                    for line in lines:
                        elements.append({
                            "text": line,
                            "type": "ocr",
                            "x": x, "y": y, "w": w, "h": h
                        })
                except Exception as e:
                    print(f"OCR error on slide {slide_number}: {e}")

        image_texts[slide_number] = elements
        if elements:
            print(f"Slide {slide_number} OCR: {len(elements)} text items found")

    return image_texts