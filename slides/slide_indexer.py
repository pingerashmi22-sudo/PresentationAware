import json
import os
from slides.content_extractor import extract_slide_text
from slides.ocr_reader import extract_image_text
from slides.keyword_extractor import extract_keywords_for_all_slides

def build_slide_index(prs):
    print("\n--- Extracting text from slides ---")
    text_data = extract_slide_text(prs)

    print("\n--- Running OCR on image shapes ---")
    image_data = extract_image_text(prs)

    # Merge text + OCR per slide
    combined_elements = {}
    for slide_num in text_data:
        all_elements = text_data[slide_num] + image_data.get(slide_num, [])
        combined_elements[slide_num] = all_elements

    print("\n--- Extracting keywords per slide ---")
    slide_keywords = extract_keywords_for_all_slides(combined_elements)

    # Build final index
    final_index = {}
    for slide_num, elements in combined_elements.items():
        final_index[f"slide_{slide_num}"] = {
            "elements": elements,           # full list with text + type + coordinates
            "keywords": slide_keywords.get(slide_num, []),   # top keywords
            "all_text": " ".join([el["text"] for el in elements])  # flat string for quick matching
        }

    # Save to slides/slide_index.json
    output_path = os.path.join(os.path.dirname(__file__), "slide_index.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_index, f, indent=2, ensure_ascii=False)

    print(f"\nslide_index.json saved at: {output_path}")
    return final_index