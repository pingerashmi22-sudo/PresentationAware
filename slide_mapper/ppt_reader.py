from pptx import Presentation


def load_ppt(file_path):
    prs = Presentation(file_path)

    slides_data = {}

    for i, slide in enumerate(prs.slides):
        slide_content = {}

        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text.strip().lower()

                words = text.split()

                for word in words:
                    slide_content[word] = (100, 100)

        slides_data[i] = slide_content

    return slides_data