from pathlib import Path

from utils import (
    RAW_DIR,
    UPLOADS_DIR,
    load_json,
    percentage
)

PDF_DATA_FILE = RAW_DIR / "ktr_pdf_data.json"


def audit_ocr():
    print("\nAuditing OCR...")

    records = load_json(PDF_DATA_FILE)

    scanned_pdfs = 0
    ocr_completed = 0
    ocr_missing = 0
    searchable_pdfs = 0

    missing_files = []

    for record in records:

        if not isinstance(record, dict):
            continue

        file_name = record.get("file", "").strip()

        if not file_name:
            continue

        pdf_path = UPLOADS_DIR / Path(file_name).name

        if not pdf_path.exists():
            missing_files.append(file_name)
            continue

        pages = record.get("pages", [])

        total_chars = 0
        empty_pages = 0

        for page in pages:

            if not isinstance(page, dict):
                continue

            text = page.get("text", "").strip()

            total_chars += len(text)

            if not text:
                empty_pages += 1

        if not pages:
            ocr_missing += 1
            scanned_pdfs += 1
            continue

        average_chars = total_chars / len(pages)

        if average_chars < 40:

            scanned_pdfs += 1

            if total_chars > 100:
                ocr_completed += 1
            else:
                ocr_missing += 1

        else:

            searchable_pdfs += 1

    coverage = percentage(
        ocr_completed,
        scanned_pdfs
    )

    print(f"Searchable PDFs   : {searchable_pdfs}")
    print(f"Scanned PDFs      : {scanned_pdfs}")
    print(f"OCR Completed     : {ocr_completed}")
    print(f"OCR Missing       : {ocr_missing}")
    print(f"OCR Coverage      : {coverage}%")
    print(f"Missing PDF Files : {len(missing_files)}")

    return {
        "coverage": coverage,
        "searchable_pdfs": searchable_pdfs,
        "scanned_pdfs": scanned_pdfs,
        "ocr_completed": ocr_completed,
        "ocr_missing": ocr_missing,
        "missing_pdf_files": len(missing_files),
        "missing_pdf_file_list": sorted(missing_files)
    }