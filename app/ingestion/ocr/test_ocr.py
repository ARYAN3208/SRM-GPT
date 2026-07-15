import json
import os

from .ocr_parser import parse_image

UPLOADS_DIR = (
   "app/05_data/uploads/site_images"
)

all_ocr_data = []

for filename in os.listdir(
    UPLOADS_DIR
):

    if filename.lower().endswith(
        (
            ".png",
            ".jpg",
            ".jpeg"
        )
    ):

        image_path = os.path.join(
            UPLOADS_DIR,
            filename
        )

        print(
            f"OCR Processing: {filename}"
        )

        try:

            text = parse_image(
                image_path
            )

            all_ocr_data.append({

                "file":
                filename,

                "text":
                text

            })

            print(
                f"OCR chars: {len(text)}"
            )

        except Exception as e:

            print(
                f"Failed: {filename}"
            )

            print(e)

os.makedirs(

    "app/05_data/raw",
    exist_ok=True

)

output_path = (
    "app/05_data/raw/ktr_ocr_data.json"
)

with open(

    output_path,
    "w",
    encoding="utf-8"

) as f:

    json.dump(

        all_ocr_data,
        f,
        indent=4,
        ensure_ascii=False

    )

print(
    f"Images processed: {len(all_ocr_data)}"
)

print(
    f"Saved to {output_path}"
)