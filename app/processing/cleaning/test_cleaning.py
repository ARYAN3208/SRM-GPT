import json
import os

from .text_cleaner import clean_text

RAW_FILES = [

    "app/05_data/raw/ktr_website_data.json",
    "app/05_data/raw/ktr_pdf_data.json",
    "app/05_data/raw/ktr_ocr_data.json"

]

cleaned_output = []

for file_path in RAW_FILES:

    if not os.path.exists(file_path):

        print(
            f"Missing: {file_path}"
        )

        continue

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    text = json.dumps(
        data,
        ensure_ascii=False
    )

    cleaned = clean_text(
        text
    )

    cleaned_output.append({

        "source":
        file_path,

        "cleaned_text":
        cleaned

    })

os.makedirs(
    "app/05_data/processed",
    exist_ok=True
)

output_path = (
    "app/05_data/processed/cleaned_data.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        cleaned_output,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"Saved cleaned data to {output_path}"
)