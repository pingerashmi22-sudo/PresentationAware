import nltk
from nltk.corpus import wordnet

# Download WordNet data (only runs once, skips if already downloaded)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

def get_synonyms(word):
  
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ').lower()
            if synonym != word.lower():
                synonyms.add(synonym)
    return synonyms

def expand_with_synonyms(text):
   
    words = text.lower().split()
    expanded = list(words)

    for word in words:
        syns = get_synonyms(word)
        expanded.extend(list(syns))

    # Remove duplicates
    seen = set()
    result = []
    for w in expanded:
        if w not in seen:
            seen.add(w)
            result.append(w)

    expanded_text = " ".join(result)
    print(f"Expanded: '{text}' → '{expanded_text}'")
    return expanded_text
