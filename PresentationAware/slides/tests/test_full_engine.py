from slides.slide_engine import initialize, get_slide_match

success = initialize()

if success:
    print("\n=== Fuzzy Match Test — Natural Spoken Phrases ===\n")

    # These simulate what someone would naturally SAY
    # They are NOT copied from the slide
    # This properly tests if fuzzy matching works
    spoken_phrases = [
        "who controls the city",
        "local area management",
        "urban administration",
        "city level government",
        "municipal body",
        "self governance",
        "urban local body",
        "civic administration",
        "town management",
        "city corporation",
        "heli shah",
        "history and civics",
        "local self government",
    ]

    matched = 0
    total = len(spoken_phrases)

    for phrase in spoken_phrases:
        print(f"Spoken : '{phrase}'")
        slide, element = get_slide_match(phrase)
        if slide:
            print(f"Matched : Slide {slide} — '{element['text']}'\n")
            matched += 1
        else:
            print(f"No match found.\n")

    print(f"=== Result: {matched}/{total} phrases matched ===")