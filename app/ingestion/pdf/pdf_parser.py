import pytesseract
from PIL import Image
import sys
import os

# Handle both relative and absolute imports
try:
    from .pdf_loader import load_pdf
except ImportError:
    # Add parent directory to path for absolute imports
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    from pdf_loader import load_pdf

def parse_pdf(pdf_path):

    doc = load_pdf(pdf_path)

    if doc is None:

        return []

    parsed_pages = []

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)

        text = page.get_text("text")

        if len(text.strip()) == 0:

            print(
                f"Page {page_num+1}: OCR fallback"
            )

            pix = page.get_pixmap()

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            img = img.convert(
                "L"
            )

            text = pytesseract.image_to_string(
                img,
                lang="eng"
            )

        print(
            f"Page {page_num+1} chars:",
            len(text)
        )

        parsed_pages.append({

            "page":
            page_num + 1,

            "text":
            text

        })

    doc.close()

    return parsed_pages