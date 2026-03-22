from slide_mapper.ppt_reader import load_ppt

slides = load_ppt("Sem-IV(Mini-Project)-PPT1.pptx")   #  your PPT file


def find_target(current_slide, target):
    if not target:
        return None

    slide_content = slides.get(current_slide, {})

    for word, position in slide_content.items():
        if target.lower() in word.lower():
            return {
                "word": word,
                "position": position
            }

    return None