import json
import os
from slides.content_extractor import extract_slide_text
from slides.ocr_reader import extract_image_text
from slide_mapper.ppt_reader import load_ppt
from slides.content_extractor import extract_context


def build_slide_index(prs, ppt_path):
    print("\n--- Extracting text from slides ---")
    text_data = extract_slide_text(prs)

    print("\n--- Running OCR on image shapes ---")
    image_data = extract_image_text(prs)

    # Safer merge (handles all slides)
    combined_elements = {}
    all_slide_nums = set(text_data.keys()).union(image_data.keys())

    for slide_num in all_slide_nums:
        combined_elements[slide_num] = (
            text_data.get(slide_num, []) +
            image_data.get(slide_num, [])
        )

    print("\n--- Building AI-friendly slide data ---")

    # Step 1: Structured extraction
    slides_data = load_ppt(ppt_path)

    # Step 2: Context strings
    context_data = extract_context(slides_data)

    # Step 3: Build FINAL JSON (AI format)
    final_index = {}

    for slide in slides_data:
        slide_number = slide["slide_number"]
        slide_key = str(slide_number)

        # Safe title fallback
        topic = slide["title"] if slide["title"] else f"Slide {slide_number}"

        # Clean summary (remove "Slide X is about")
        summary = context_data.get(slide_number, "")
        summary = summary.replace(f"Slide {slide_number} is about ", "")

        final_index[slide_key] = {
            "topic": topic,
            "summary": summary,
            "content": slide["content"],
            "notes": slide["notes"],
            "full_text": slide["full_text"]
        }

    # Save JSON
    output_path = os.path.join(os.path.dirname(__file__), "slide_index.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_index, f, indent=2, ensure_ascii=False)

    print(f"\nslide_index.json saved at: {output_path}")

    return final_index