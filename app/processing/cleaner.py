import json

REMOVE_PATTERNS = [
    "quick links",
    "apply now",
    "search close",
    "facebook",
    "instagram",
    "youtube",
    "linkedin",
    "copyright",
    "all rights reserved",
    "announcements",
    "menu",
    "skip to content",
    "accessibility tools",
    "privacy policy",
    "terms of use",
    "contact us",
    "student life milan"
]

def clean_data(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = []

    for item in data:

        text = item.get("text", "")

        if len(text.strip()) < 100:
            continue

        cleaned_text = text

        for pattern in REMOVE_PATTERNS:

            cleaned_text = cleaned_text.replace(
                pattern,
                ""
            )

            cleaned_text = cleaned_text.replace(
                pattern.title(),
                ""
            )

            cleaned_text = cleaned_text.replace(
                pattern.upper(),
                ""
            )

        item["text"] = cleaned_text

        cleaned.append(item)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            cleaned,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("Original Records:", len(data))
    print("Cleaned Records :", len(cleaned))