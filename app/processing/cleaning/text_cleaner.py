import re

def clean_text(text):

    if not text:
        return ""

    noise_patterns = [

        r"Where could your journey at university take you\?",
        r"Student Life",
        r"visit campus",
        r"apply now",
        r"Admissions & Aid",
        r"Admission India",
        r"Admission International",
        r"Group Institutions",
        r"SRM University - AP",
        r"SRM University - Haryana",
        r"SRM University - Sikkim",
        r"Enjoy your Student Life & Excel at SRM",
        r"A to Z - Quicklinks",
        r"Departments Programs Faculty Search",
        r"Anti-Ragging Committee",
        r"Value Education Cell",
        r"IQAC",
        r"NIRF",
        r"Student Clubs",
        r"Prospectus",
        r"Public Disclosure",
        r"Mandatory Disclosures",
        r"How to Reach"

    ]

    for pattern in noise_patterns:

        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE
        )

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"www\.\S+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"[^\w\s.,!?():/-]",
        "",
        text
    )

    return text.strip()