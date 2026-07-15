import re

from .ocr_loader import (
    extract_text
)

def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()

def parse_image(image_path):

    raw_text = extract_text(
        image_path
    )

    cleaned = clean_text(
        raw_text
    )

    return {

        "image":
        image_path,

        "text":
        cleaned

    }