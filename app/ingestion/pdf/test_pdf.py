import os
import json

from .pdf_parser import parse_pdf

PDF_FOLDER = (
    "app/data/uploads"
)

all_pdf_data = []

for filename in os.listdir(
    PDF_FOLDER
):

    if filename.lower().endswith(
        ".pdf"
    ):

        pdf_path = os.path.join(

            PDF_FOLDER,
            filename

        )

        print(
            f"Parsing: {filename}"
        )

        parsed_pages = parse_pdf(
            pdf_path
        )

        all_pdf_data.append({

            "file":
            filename,

            "pages":
            parsed_pages

        })

os.makedirs(

    "app/data/raw",
    exist_ok=True

)

output_path = (
    "app/data/raw/ktr_pdf_data.json"
)

with open(

    output_path,
    "w",
    encoding="utf-8"

) as f:

    json.dump(

        all_pdf_data,
        f,
        indent=4,
        ensure_ascii=False

    )

print(
    f"PDF files parsed: {len(all_pdf_data)}"
)

print(
    f"Saved to {output_path}"
)