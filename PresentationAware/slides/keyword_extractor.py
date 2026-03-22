import re
from collections import Counter

# Common words to ignore (stop words)
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "it", "its", "this", "that", "we", "our", "you", "your", "they",
    "their", "be", "been", "has", "have", "had", "will", "can", "may",
    "as", "into", "than", "then", "so", "if", "about", "up", "out",
    "more", "also", "all", "not", "no", "do", "did", "does"
}

def extract_keywords(text_list, top_n=10):
    """
    Takes a list of text strings from one slide.
    Returns top N important keywords.
    """
    all_words = []

    for text in text_list:
        # Lowercase, split on non-alpha characters
        words = re.findall(r'[a-zA-Z]{3,}', text.lower())
        for word in words:
            if word not in STOP_WORDS:
                all_words.append(word)

    # Count and return top N
    counter = Counter(all_words)
    keywords = [word for word, count in counter.most_common(top_n)]
    return keywords

def extract_keywords_for_all_slides(slide_data):
    """
    slide_data = { slide_number: [ {text:..., type:...}, ... ] }
    Returns { slide_number: ["keyword1", "keyword2", ...] }
    """
    slide_keywords = {}

    for slide_num, elements in slide_data.items():
        texts = [el["text"] for el in elements if el.get("text")]
        keywords = extract_keywords(texts)
        slide_keywords[slide_num] = keywords
        print(f"Slide {slide_num} keywords: {keywords}")

    return slide_keywords