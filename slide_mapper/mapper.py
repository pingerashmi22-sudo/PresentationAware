from slide_mapper.ppt_reader import load_ppt

slides = load_ppt("Sem-IV(Mini-Project)-PPT1.pptx")


def find_target(target):
    if not target:
        return None

    target = target.lower()

    best_match = None
    best_score = 0

    for slide in slides:
        score = 0

        # Check title
        if target in slide["title"].lower():
            score += 3

        # Check content
        for line in slide["content"]:
            if target in line.lower():
                score += 2

        # Check notes
        if target in slide["notes"].lower():
            score += 1

        # Track best match
        if score > best_score:
            best_score = score
            best_match = slide["slide_number"]

    return best_match