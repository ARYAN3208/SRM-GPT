import pytesseract
from PIL import Image, ImageFilter, ImageOps

def parse_image(image_path):

    try:

        image = Image.open(
            image_path
        )

        image = image.convert(
            "L"
        )

        width, height = image.size

        image = image.resize(

            (
                width * 3,
                height * 3
            ),

            Image.LANCZOS

        )

        image = ImageOps.autocontrast(
            image
        )

        image = image.filter(
            ImageFilter.SHARPEN
        )

        image = image.point(

            lambda p:
            255 if p > 150 else 0

        )

        text = pytesseract.image_to_string(

            image,

            lang="eng",

            config=r"--oem 3 --psm 6"

        )

        print(
            "OCR chars:",
            len(text)
        )

        return text

    except Exception as e:

        print(
            "OCR Error:",
            e
        )

        return ""