from pathlib import Path
import json
import re

UPLOAD_DIR = Path("app/05_data/uploads")
SITE_IMG_DIR = UPLOAD_DIR / "site_images"

RAW_OUT = Path("app/05_data/raw/ktr_ocr_data_raw.json")
GOOD_OUT = Path("app/05_data/raw/ktr_ocr_data.json")
RAW_OUT.parent.mkdir(parents=True, exist_ok=True)

TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

MIN_LETTERS = 5
MIN_WORDS = 1

def metrics(text: str):
    letters = len(re.findall(r"[A-Za-z]", text))
    words = len(text.split())
    return letters, words

def quality_ok(text: str) -> bool:
    letters, words = metrics(text)
    return letters >= MIN_LETTERS and words >= MIN_WORDS

def ocr_image(img_path: Path) -> str:
    from PIL import Image, ImageOps
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

    img = Image.open(img_path).convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 2, img.height * 2))
    img = img.point(lambda p: 255 if p > 170 else 0)

    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(img, config=config)
    return " ".join((text or "").split()).strip()

def gather_images():
    paths = []
    for folder in [UPLOAD_DIR, SITE_IMG_DIR]:
        if not folder.exists():
            continue
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            paths.extend(folder.glob(ext))
    return sorted(set(paths))

def main():
    images = gather_images()
    print(f"[OCR] images_found={len(images)}")
    print(f"[OCR] scanning: {UPLOAD_DIR} and {SITE_IMG_DIR}")

    raw_records = []
    good_records = []

    for p in images:
        try:
            text = ocr_image(p)
            letters, words = metrics(text)

            rec = {
                "text": text,
                "source": "ocr",
                "file_name": p.name,
                "folder": str(p.parent).replace("\\", "/"),
                "letters": letters,
                "words": words,
                "metadata": {"source": "ocr", "file_name": p.name, "folder": str(p.parent).replace("\\", "/")}
            }
            raw_records.append(rec)
            if quality_ok(text):
                good_records.append(rec)

            print(f"[OCR] {p.name:35} len={len(text):4} letters={letters:3} words={words:3}")

        except Exception as e:
            print(f"[OCR] Failed {p.name}: {e}")

    RAW_OUT.write_text(json.dumps(raw_records, indent=2, ensure_ascii=False), encoding="utf-8")
    GOOD_OUT.write_text(json.dumps(good_records, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OCR] RAW saved:  {RAW_OUT} records={len(raw_records)}")
    print(f"[OCR] GOOD saved: {GOOD_OUT} records={len(good_records)}")

if __name__ == "__main__":
    main()